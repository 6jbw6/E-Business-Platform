"""商品类别数据访问。"""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from backend.app.core.exceptions import CODE_CONFLICT, BizError, conflict, not_found
from backend.app.models.category import Category
from backend.app.models.product import Product


def list_all(db: Session, *, include_hidden: bool = False) -> list[Category]:
    stmt = select(Category).order_by(Category.level, Category.sort_order, Category.id)
    if not include_hidden:
        stmt = stmt.where(Category.status == 1)
    return list(db.scalars(stmt))


def get_or_404(db: Session, category_id: int) -> Category:
    category = db.get(Category, category_id)
    if category is None:
        raise not_found(f"分类 {category_id} 不存在")
    return category


def group_by_parent(categories: list[Category]) -> dict[int | None, list[Category]]:
    """按父ID分组，供路由层拼装分类树；不改动 ORM 关系对象。"""
    grouped: dict[int | None, list[Category]] = {}
    for c in categories:
        grouped.setdefault(c.parent_id, []).append(c)
    return grouped


def create(db: Session, *, name: str, parent_id: int | None = None, icon: str = "",
           sort_order: int = 0, status: int = 1) -> Category:
    level = 1
    if parent_id is not None:
        parent = get_or_404(db, parent_id)
        if parent.level >= 2:
            raise BizError("最多支持两级分类", code=CODE_CONFLICT, http_status=409)
        level = parent.level + 1

    if db.scalar(select(func.count()).select_from(Category).where(Category.name == name,
                                                                  Category.parent_id == parent_id)):
        raise conflict(f"同级下已存在分类「{name}」")

    category = Category(
        name=name, parent_id=parent_id, level=level, icon=icon, sort_order=sort_order, status=status
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update(db: Session, category_id: int, **fields: object) -> Category:
    category = get_or_404(db, category_id)
    for key, value in fields.items():
        if value is not None:
            setattr(category, key, value)
    db.commit()
    db.refresh(category)
    return category


def delete(db: Session, category_id: int) -> None:
    category = get_or_404(db, category_id)
    child_count = db.scalar(
        select(func.count()).select_from(Category).where(Category.parent_id == category_id)
    )
    if child_count:
        raise conflict("该分类下还有子分类，请先删除子分类")
    product_count = db.scalar(
        select(func.count()).select_from(Product).where(Product.category_id == category_id)
    )
    if product_count:
        raise conflict(f"该分类下还有 {product_count} 个商品，无法删除")
    db.delete(category)
    db.commit()
