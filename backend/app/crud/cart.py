"""购物车数据访问。"""

from decimal import Decimal

from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from backend.app.core.exceptions import (
    CODE_BAD_REQUEST,
    BizError,
    conflict,
    not_found,
)
from backend.app.models.cart import CartItem
from backend.app.models.product import STATUS_ON_SALE, Product


def _stock_error(product: Product) -> BizError:
    return BizError(
        f"库存不足，当前仅剩 {product.stock} {product.unit}",
        code=CODE_BAD_REQUEST,
        http_status=400,
    )


def list_items(db: Session, user_id: int) -> list[CartItem]:
    stmt = (
        select(CartItem)
        .where(CartItem.user_id == user_id)
        .options(selectinload(CartItem.product))
        .order_by(CartItem.updated_at.desc(), CartItem.id.desc())
    )
    return list(db.scalars(stmt))


def get_owned(db: Session, user_id: int, item_id: int) -> CartItem:
    item = db.scalar(
        select(CartItem)
        .where(CartItem.id == item_id, CartItem.user_id == user_id)
        .options(selectinload(CartItem.product))
    )
    if item is None:
        raise not_found(f"购物车记录 {item_id} 不存在")
    return item


def add(db: Session, user_id: int, product_id: int, quantity: int) -> CartItem:
    product = db.get(Product, product_id)
    if product is None:
        raise not_found(f"商品 {product_id} 不存在")
    if product.status != STATUS_ON_SALE:
        raise conflict("该商品已下架，无法加入购物车")

    item = db.scalar(
        select(CartItem).where(CartItem.user_id == user_id, CartItem.product_id == product_id)
    )
    target = (item.quantity if item else 0) + quantity
    if target > product.stock:
        raise _stock_error(product)

    if item is None:
        item = CartItem(user_id=user_id, product_id=product_id, quantity=target, checked=1)
        db.add(item)
    else:
        item.quantity = target
        item.checked = 1
    db.commit()
    db.refresh(item)
    return item


def update_item(
    db: Session, user_id: int, item_id: int, quantity: int | None, checked: int | None
) -> CartItem:
    item = get_owned(db, user_id, item_id)
    if quantity is not None:
        if item.product.status != STATUS_ON_SALE:
            raise conflict("该商品已下架，无法修改数量")
        if quantity > item.product.stock:
            raise _stock_error(item.product)
        item.quantity = quantity
    if checked is not None:
        item.checked = checked
    db.commit()
    db.refresh(item)
    return item


def remove(db: Session, user_id: int, item_id: int) -> None:
    db.delete(get_owned(db, user_id, item_id))
    db.commit()


def clear(db: Session, user_id: int) -> int:
    result = db.execute(delete(CartItem).where(CartItem.user_id == user_id))
    db.commit()
    return int(result.rowcount or 0)


def remove_by_ids(db: Session, user_id: int, item_ids: list[int]) -> None:
    if not item_ids:
        return
    db.execute(
        delete(CartItem).where(CartItem.user_id == user_id, CartItem.id.in_(item_ids))
    )


def totals(items: list[CartItem]) -> tuple[int, Decimal, int]:
    """返回 (勾选总件数, 勾选总金额, 勾选种数)。"""
    checked = [i for i in items if i.checked == 1]
    total_quantity = sum(i.quantity for i in checked)
    total_amount = sum((i.product.price * i.quantity for i in checked), Decimal("0.00"))
    return total_quantity, total_amount, len(checked)
