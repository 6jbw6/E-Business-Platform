"""订单主表与订单明细表模型。"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, Integer, Numeric, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.product import Product
    from backend.app.models.user import User

# 订单状态机：只能沿箭头方向流转，取消仅允许在待发货前发生
ORDER_STATUS_PENDING_PAYMENT = 0
ORDER_STATUS_PENDING_SHIPMENT = 1
ORDER_STATUS_PENDING_RECEIPT = 2
ORDER_STATUS_FINISHED = 3
ORDER_STATUS_CANCELLED = 4

ORDER_STATUS_LABELS = {
    ORDER_STATUS_PENDING_PAYMENT: "待付款",
    ORDER_STATUS_PENDING_SHIPMENT: "待发货",
    ORDER_STATUS_PENDING_RECEIPT: "待收货",
    ORDER_STATUS_FINISHED: "已完成",
    ORDER_STATUS_CANCELLED: "已取消",
}

FREEZE_STATUS = {
    ORDER_STATUS_PENDING_PAYMENT,
    ORDER_STATUS_PENDING_SHIPMENT,
    ORDER_STATUS_PENDING_RECEIPT,
}


class Order(Base, TimestampMixin):
    __tablename__ = "orders"
    __table_args__ = (
        Index("idx_orders_user_status", "user_id", "status"),
        {"comment": "订单主表：收货信息、金额与状态", "mysql_charset": "utf8mb4"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="订单ID")
    order_no: Mapped[str] = mapped_column(
        String(24), nullable=False, unique=True, comment="订单号，对外展示用"
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="RESTRICT"), nullable=False, comment="下单用户ID"
    )
    total_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, comment="商品总额（元）"
    )
    freight: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00"), comment="运费（元）"
    )
    pay_amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), nullable=False, comment="实付金额=商品总额+运费"
    )
    status: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=ORDER_STATUS_PENDING_PAYMENT,
        comment="状态：0待付款 1待发货 2待收货 3已完成 4已取消",
    )
    receiver_name: Mapped[str] = mapped_column(String(32), nullable=False, comment="收货人")
    receiver_phone: Mapped[str] = mapped_column(String(20), nullable=False, comment="收货电话")
    receiver_address: Mapped[str] = mapped_column(String(255), nullable=False, comment="收货地址")
    remark: Mapped[str] = mapped_column(String(255), nullable=False, default="", comment="买家备注")
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="支付时间")
    shipped_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="发货时间")
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="完成时间")
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="取消时间")

    user: Mapped["User"] = relationship(backref="orders")
    items: Mapped[list["OrderItem"]] = relationship(
        back_populates="order", cascade="all, delete-orphan", lazy="selectin"
    )


class OrderItem(Base, TimestampMixin):
    __tablename__ = "order_items"
    __table_args__ = (
        Index("idx_order_items_order", "order_id"),
        {
            "comment": "订单明细表：下单时快照商品名称与价格，不受后续改价影响",
            "mysql_charset": "utf8mb4",
        },
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="明细ID")
    order_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, comment="订单ID"
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, comment="商品ID"
    )
    product_name: Mapped[str] = mapped_column(String(120), nullable=False, comment="商品名称快照")
    product_image: Mapped[str] = mapped_column(
        String(255), nullable=False, default="", comment="商品主图快照"
    )
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, comment="成交单价快照")
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, comment="购买数量")
    subtotal: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False, comment="小计金额")

    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(backref="order_items")
