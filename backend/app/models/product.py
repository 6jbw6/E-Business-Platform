"""商品表模型。"""

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, Numeric, SmallInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin

if TYPE_CHECKING:
    from backend.app.models.category import Category

STATUS_OFF_SHELF = 0
STATUS_ON_SALE = 1


class Product(Base, TimestampMixin):
    __tablename__ = "products"
    __table_args__ = (
        Index("idx_products_category", "category_id"),
        Index("idx_products_status", "status"),
        {"comment": "商品表：价格、库存与上下架状态", "mysql_charset": "utf8mb4"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="商品ID")
    category_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False, comment="所属类别ID"
    )
    name: Mapped[str] = mapped_column(String(120), nullable=False, comment="商品名称")
    subtitle: Mapped[str] = mapped_column(
        String(200), nullable=False, default="", comment="副标题/卖点"
    )
    main_image: Mapped[str] = mapped_column(
        String(255), nullable=False, default="", comment="主图地址"
    )
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False, comment="售价（元）")
    original_price: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False, default=Decimal("0.00"), comment="划线价（元）"
    )
    stock: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="可售库存")
    sales: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="累计销量")
    unit: Mapped[str] = mapped_column(String(16), nullable=False, default="件", comment="计量单位")
    detail: Mapped[str] = mapped_column(Text, nullable=True, comment="图文详情")
    status: Mapped[int] = mapped_column(
        SmallInteger,
        nullable=False,
        default=STATUS_ON_SALE,
        comment="状态：1=在售，0=下架",
    )

    category: Mapped["Category"] = relationship(backref="products")

    @property
    def available(self) -> bool:
        return self.status == STATUS_ON_SALE and self.stock > 0
