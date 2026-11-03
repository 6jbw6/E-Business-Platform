"""购物车表模型。"""

from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, SmallInteger, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.product import Product
    from backend.app.models.user import User


class CartItem(Base, TimestampMixin):
    __tablename__ = "cart_items"
    __table_args__ = (
        UniqueConstraint("user_id", "product_id", name="uk_cart_user_product"),
        {"comment": "购物车表：同一用户同一商品只保留一条，重复加购累加数量", "mysql_charset": "utf8mb4"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="购物车行ID")
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID"
    )
    product_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("products.id", ondelete="CASCADE"), nullable=False, comment="商品ID"
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1, comment="数量")
    checked: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=1, comment="是否勾选结算：1=勾选，0=未勾选"
    )

    user: Mapped["User"] = relationship(backref="cart_items")
    product: Mapped["Product"] = relationship(backref="cart_items")
