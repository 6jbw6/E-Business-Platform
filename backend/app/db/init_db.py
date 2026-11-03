"""建库、建表与演示数据初始化。"""

from decimal import Decimal

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from backend.app.core.config import PROJECT_ROOT, Settings, settings
from backend.app.core.security import hash_password
from backend.app.db.session import SessionLocal, engine
from backend.app.models import Base, Category, Product, User

# 演示数据与 sql/02_seed.sql 一一对应：同样的主键 ID、同样的名称与价格，
# 这样文档里写的 product_id=101 之类的示例，两条初始化路径下都成立。

# (id, username, 明文密码, 昵称, 手机号, 邮箱, 角色)
SEED_USERS: list[tuple[int, str, str, str, str, str, str]] = [
    (1, "admin", "123456", "平台管理员", "13800000000", "admin@example.com", "admin"),
    (2, "student01", "123456", "演示买家", "13800001111", "student01@example.com", "user"),
]

# (id, 名称, 父ID, 层级, 图标, 排序)
SEED_CATEGORIES: list[tuple[int, str, int | None, int, str, int]] = [
    (1, "手机数码", None, 1, "/static/cat/digital.png", 1),
    (2, "家用电器", None, 1, "/static/cat/appliance.png", 2),
    (3, "服饰鞋包", None, 1, "/static/cat/clothing.png", 3),
    (11, "智能手机", 1, 2, "", 1),
    (12, "笔记本电脑", 1, 2, "", 2),
    (13, "智能穿戴", 1, 2, "", 3),
    (21, "厨房电器", 2, 2, "", 1),
    (22, "生活电器", 2, 2, "", 2),
    (31, "男装", 3, 2, "", 1),
    (32, "女鞋", 3, 2, "", 2),
]

# (id, category_id, 名称, 售价, 划线价, 库存, 销量, 单位, 详情)
# 105 号库存为 0，专门用来演示「库存不足」分支
SEED_PRODUCTS: list[tuple[int, int, str, Decimal, Decimal, int, int, str, str]] = [
    (101, 11, "星海 12 Pro 5G 手机", Decimal("3999.00"), Decimal("4199.00"), 120, 36, "台",
     "<p>6.7 英寸直屏，5000mAh 电池。</p>"),
    (102, 11, "轻氧 Air 折叠屏手机", Decimal("6899.00"), Decimal("7099.00"), 30, 12, "台",
     "<p>折叠形态，2 英寸外屏。</p>"),
    (103, 12, "木鱼 Book 14 轻薄本", Decimal("5299.00"), Decimal("5499.00"), 45, 20, "台",
     "<p>1.2kg 机身，14 小时续航。</p>"),
    (104, 13, "潮汐 Watch 运动手表", Decimal("899.00"), Decimal("1099.00"), 200, 40, "只",
     "<p>双频 GPS，14 天续航。</p>"),
    (105, 13, "云感 降噪耳机", Decimal("499.00"), Decimal("599.00"), 0, 8, "副",
     "<p>主动降噪，单次 8 小时。</p>"),
    (106, 21, "山泉 破壁料理机", Decimal("1299.00"), Decimal("1499.00"), 60, 15, "台",
     "<p>38000 转/分钟破壁。</p>"),
    (107, 22, "暖阳 变频空调", Decimal("2799.00"), Decimal("2999.00"), 18, 6, "台",
     "<p>新一级能效，1.5 匹。</p>"),
    (108, 31, "简白 纯棉短袖 T 恤", Decimal("89.00"), Decimal("129.00"), 500, 48, "件",
     "<p>220g 重磅纯棉。</p>"),
    (109, 32, "踏云 轻便跑步鞋", Decimal("329.00"), Decimal("399.00"), 150, 22, "双",
     "<p>回弹中底，单只 210g。</p>"),
]


def build_engine(*, with_database: bool = True, cfg: Settings = settings) -> Engine:
    uri = cfg.sqlalchemy_uri if with_database else cfg.server_uri
    return create_engine(uri, pool_pre_ping=True, future=True)


def create_database_if_absent(cfg: Settings = settings) -> None:
    """库不存在时创建，避免第一次部署直接报 Unknown database。"""
    server_engine = build_engine(with_database=False, cfg=cfg)
    with server_engine.connect() as conn:
        conn.execute(
            text(
                f"CREATE DATABASE IF NOT EXISTS `{cfg.mysql_database}` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci"
            )
        )
        conn.commit()
    server_engine.dispose()


def create_tables(target_engine: Engine = engine) -> None:
    Base.metadata.create_all(bind=target_engine)


def seed(db: Session) -> dict[str, int]:
    """幂等播种：按主键判断是否已存在，可反复执行。"""
    counts = {"users": 0, "categories": 0, "products": 0}

    for user_id, username, password, nickname, phone, email, role in SEED_USERS:
        if db.get(User, user_id) is not None:
            continue
        db.add(
            User(
                id=user_id,
                username=username,
                password_hash=hash_password(password),
                nickname=nickname,
                phone=phone,
                email=email,
                role=role,
                status=1,
            )
        )
        counts["users"] += 1
    db.flush()

    category_names: dict[int, str] = {}
    for cat_id, name, parent_id, level, icon, sort_order in SEED_CATEGORIES:
        category_names[cat_id] = name
        if db.get(Category, cat_id) is not None:
            continue
        db.add(
            Category(
                id=cat_id,
                name=name,
                parent_id=parent_id,
                level=level,
                icon=icon,
                sort_order=sort_order,
                status=1,
            )
        )
        counts["categories"] += 1
    db.flush()

    for prod_id, category_id, name, price, original_price, stock, sales, unit, detail in SEED_PRODUCTS:
        if db.get(Product, prod_id) is not None:
            continue
        db.add(
            Product(
                id=prod_id,
                category_id=category_id,
                name=name,
                subtitle=f"{category_names[category_id]}·热销款",
                main_image=f"/static/goods/{prod_id - 100:04d}.jpg",
                price=price,
                original_price=original_price,
                stock=stock,
                sales=sales,
                unit=unit,
                detail=detail,
                status=1,
            )
        )
        counts["products"] += 1

    db.commit()
    return counts


def init_db(*, cfg: Settings = settings, with_seed: bool = True) -> dict[str, int]:
    create_database_if_absent(cfg)
    target = build_engine(with_database=True, cfg=cfg)
    create_tables(target)
    if not with_seed:
        return {}
    session = Session(bind=target)
    try:
        return seed(session)
    finally:
        session.close()
        target.dispose()


__all__ = [
    "PROJECT_ROOT",
    "SessionLocal",
    "create_database_if_absent",
    "create_tables",
    "init_db",
    "seed",
]
