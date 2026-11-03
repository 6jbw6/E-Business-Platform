"""商品数据访问。"""

from collections.abc import Sequence
from decimal import Decimal

from sqlalchemy import Select, func, or_, select
from sqlalchemy.orm import Session

from backend.app.core.exceptions import conflict, not_found
from backend.app.models.category import Category
from backend.app.models.product import STATUS_ON_SALE, Product

SORT_FIELDS = {
    "default": (Product.id, "asc"),
    "price_asc": (Product.price, "asc"),
    "price_desc": (Product.price, "desc"),
    "sales_desc": (Product.sales, "desc"),
    "newest": (Product.id, "desc"),
}


def _apply_filters(
    stmt: Select,
    *,
    keyword: str | None,
    category_id: int | None,
    status: int | None,
    min_price: Decimal | None,
    max_price: Decimal | None,
) -> Select:
    if keyword:
        like = f"%{keyword.strip()}%"
        stmt = stmt.where(or_(Product.name.like(like), Product.subtitle.like(like)))
    if category_id is not None:
        # 传一级分类时，把它下面所有二级分类的商品一并带上
        stmt = stmt.where(
            or_(
                Product.category_id == category_id,
                Product.category_id.in_(
                    select(Category.id).where(Category.parent_id == category_id)
                ),
            )
        )
    if status is not None:
        stmt = stmt.where(Product.status == status)
    if min_price is not None:
        stmt = stmt.where(Product.price >= min_price)
    if max_price is not None:
        stmt = stmt.where(Product.price <= max_price)
    return stmt


def paginate(
    db: Session,
    *,
    keyword: str | None = None,
    category_id: int | None = None,
    status: int | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    sort: str = "default",
    page: int = 1,
    page_size: int = 10,
) -> tuple[list[tuple[Product, str]], int]:
    filters = {
        "keyword": keyword,
        "category_id": category_id,
        "status": status,
        "min_price": min_price,
        "max_price": max_price,
    }
    total = db.scalar(
        _apply_filters(select(func.count()).select_from(Product), **filters)  # type: ignore[arg-type]
    )

    sort_col, direction = SORT_FIELDS.get(sort, SORT_FIELDS["default"])
    order = sort_col.asc() if direction == "asc" else sort_col.desc()
    stmt = (
        _apply_filters(select(Product, Category.name).join(Category, Product.category_id == Category.id), **filters)
        .order_by(order, Product.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(db.execute(stmt)), int(total or 0)


def get_or_404(db: Session, product_id: int) -> Product:
    product = db.get(Product, product_id)
    if product is None:
        raise not_found(f"商品 {product_id} 不存在")
    return product


def get_detail(db: Session, product_id: int) -> tuple[Product, str]:
    row = db.execute(
        select(Product, Category.name)
        .join(Category, Product.category_id == Category.id)
        .where(Product.id == product_id)
    ).first()
    if row is None:
        raise not_found(f"商品 {product_id} 不存在")
    return row


def create(db: Session, **fields: object) -> Product:
    category_id = int(fields["category_id"])  # type: ignore[arg-type]
    if db.get(Category, category_id) is None:
        raise not_found(f"分类 {category_id} 不存在")
    if db.scalar(select(func.count()).select_from(Product).where(Product.name == fields["name"])):
        raise conflict(f"商品「{fields['name']}」已存在")

    product = Product(**fields)  # type: ignore[arg-type]
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update(db: Session, product_id: int, **fields: object) -> Product:
    product = get_or_404(db, product_id)
    if fields.get("category_id") and db.get(Category, int(fields["category_id"])) is None:  # type: ignore[arg-type]
        raise not_found(f"分类 {fields['category_id']} 不存在")
    for key, value in fields.items():
        if value is not None:
            setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


def delete(db: Session, product_id: int) -> Product:
    """下架并从商品列表隐藏；历史订单靠明细快照仍能展示。"""
    product = get_or_404(db, product_id)
    product.status = 0
    db.commit()
    return product


def lock_for_update(db: Session, product_ids: Sequence[int]) -> dict[int, Product]:
    """按主键升序加行锁，避免多商品下单时的交叉死锁。"""
    stmt = (
        select(Product).where(Product.id.in_(list(product_ids))).order_by(Product.id).with_for_update()
    )
    return {p.id: p for p in db.scalars(stmt)}


def is_on_sale(product: Product) -> bool:
    return product.status == STATUS_ON_SALE
