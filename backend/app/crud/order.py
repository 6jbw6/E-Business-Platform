"""订单数据访问：下单扣库存、状态机流转、取消回滚。"""

import secrets
from datetime import datetime
from decimal import Decimal

from sqlalchemy import delete, func, select
from sqlalchemy.orm import Session, selectinload

from backend.app.core.exceptions import (
    CODE_BAD_REQUEST,
    BizError,
    forbidden,
    not_found,
)
from backend.app.crud import product as product_crud
from backend.app.models.cart import CartItem
from backend.app.models.order import (
    ORDER_STATUS_CANCELLED,
    ORDER_STATUS_FINISHED,
    ORDER_STATUS_LABELS,
    ORDER_STATUS_PENDING_PAYMENT,
    ORDER_STATUS_PENDING_RECEIPT,
    ORDER_STATUS_PENDING_SHIPMENT,
    Order,
    OrderItem,
)
from backend.app.models.product import STATUS_ON_SALE, Product
from backend.app.models.user import ROLE_ADMIN, User

FREIGHT = Decimal("10.00")
FREE_FREIGHT_THRESHOLD = Decimal("99.00")


def _order_no() -> str:
    return datetime.now().strftime("%Y%m%d%H%M%S%f")[:-4] + f"{secrets.randbelow(100000):05d}"


def _transition(order: Order, expected: set[int], target: int) -> None:
    if order.status not in expected:
        current = ORDER_STATUS_LABELS.get(order.status, "未知")
        raise BizError(
            f"当前状态为「{current}」，不能执行该操作",
            code=CODE_BAD_REQUEST,
            http_status=400,
        )
    order.status = target


def create_order(
    db: Session,
    user: User,
    *,
    receiver_name: str,
    receiver_phone: str,
    receiver_address: str,
    remark: str = "",
    items: list[tuple[int, int]] | None = None,
) -> Order:
    """items 为空表示结算购物车中已勾选的商品；否则为直接购买清单。"""
    cart_items: list[CartItem] = []
    if items is None:
        cart_items = list(
            db.scalars(
                select(CartItem)
                .where(CartItem.user_id == user.id, CartItem.checked == 1)
                .options(selectinload(CartItem.product))
            )
        )
        if not cart_items:
            raise BizError("购物车里没有勾选任何商品", code=CODE_BAD_REQUEST, http_status=400)
        items = [(c.product_id, c.quantity) for c in cart_items]

    merged: dict[int, int] = {}
    for product_id, quantity in items:
        if quantity < 1:
            raise BizError("购买数量必须大于 0", code=CODE_BAD_REQUEST, http_status=400)
        merged[product_id] = merged.get(product_id, 0) + quantity

    locked = product_crud.lock_for_update(db, list(merged))
    lines: list[tuple[Product, int]] = []
    for product_id, quantity in merged.items():
        product = locked.get(product_id)
        if product is None:
            raise not_found(f"商品 {product_id} 不存在")
        if product.status != STATUS_ON_SALE:
            raise BizError(f"商品「{product.name}」已下架", code=CODE_BAD_REQUEST, http_status=400)
        if product.stock < quantity:
            raise BizError(
                f"商品「{product.name}」库存不足，仅剩 {product.stock} {product.unit}",
                code=CODE_BAD_REQUEST,
                http_status=400,
            )
        lines.append((product, quantity))

    total_amount = sum((p.price * q for p, q in lines), Decimal("0.00"))
    freight = Decimal("0.00") if total_amount >= FREE_FREIGHT_THRESHOLD else FREIGHT

    order = Order(
        order_no=_order_no(),
        user_id=user.id,
        total_amount=total_amount,
        freight=freight,
        pay_amount=total_amount + freight,
        status=ORDER_STATUS_PENDING_PAYMENT,
        receiver_name=receiver_name,
        receiver_phone=receiver_phone,
        receiver_address=receiver_address,
        remark=remark,
    )
    for product, quantity in lines:
        order.items.append(
            OrderItem(
                product_id=product.id,
                product_name=product.name,
                product_image=product.main_image,
                price=product.price,
                quantity=quantity,
                subtotal=product.price * quantity,
            )
        )
        # 下单即锁定库存，避免超卖
        product.stock -= quantity

    db.add(order)
    db.flush()

    if cart_items:
        db.execute(
            delete(CartItem).where(
                CartItem.user_id == user.id,
                CartItem.id.in_([c.id for c in cart_items]),
            )
        )
    db.commit()
    db.refresh(order)
    return order


def list_orders(
    db: Session, user_id: int, *, status: int | None = None, page: int = 1, page_size: int = 10
) -> tuple[list[Order], int]:
    stmt = select(Order).where(Order.user_id == user_id)
    if status is not None:
        stmt = stmt.where(Order.status == status)
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    rows = db.scalars(
        stmt.options(selectinload(Order.items))
        .order_by(Order.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return list(rows), int(total or 0)


def get_order(db: Session, user: User, order_id: int) -> Order:
    order = db.scalar(
        select(Order).where(Order.id == order_id).options(selectinload(Order.items))
    )
    if order is None:
        raise not_found(f"订单 {order_id} 不存在")
    if order.user_id != user.id and user.role != ROLE_ADMIN:
        raise forbidden("只能操作自己的订单")
    return order


def pay(db: Session, order: Order) -> Order:
    _transition(order, {ORDER_STATUS_PENDING_PAYMENT}, ORDER_STATUS_PENDING_SHIPMENT)
    order.paid_at = datetime.now()
    for item in order.items:
        product = db.get(Product, item.product_id)
        if product is not None:
            product.sales += item.quantity
    db.commit()
    db.refresh(order)
    return order


def ship(db: Session, order: Order) -> Order:
    _transition(order, {ORDER_STATUS_PENDING_SHIPMENT}, ORDER_STATUS_PENDING_RECEIPT)
    order.shipped_at = datetime.now()
    db.commit()
    db.refresh(order)
    return order


def receive(db: Session, order: Order) -> Order:
    _transition(order, {ORDER_STATUS_PENDING_RECEIPT}, ORDER_STATUS_FINISHED)
    order.finished_at = datetime.now()
    db.commit()
    db.refresh(order)
    return order


def cancel(db: Session, order: Order) -> Order:
    """待付款可直接取消；已付款取消时回滚库存与销量，退款走线下。"""
    was_paid = order.status == ORDER_STATUS_PENDING_SHIPMENT
    _transition(
        order,
        {ORDER_STATUS_PENDING_PAYMENT, ORDER_STATUS_PENDING_SHIPMENT},
        ORDER_STATUS_CANCELLED,
    )
    order.cancelled_at = datetime.now()
    for item in order.items:
        product = db.get(Product, item.product_id)
        if product is not None:
            product.stock += item.quantity
            if was_paid:
                product.sales = max(0, product.sales - item.quantity)
    db.commit()
    db.refresh(order)
    return order


def status_label(status: int) -> str:
    return ORDER_STATUS_LABELS.get(status, "未知状态")
