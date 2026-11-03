"""商品类别表模型（两级分类，自关联）。"""

from sqlalchemy import ForeignKey, Index, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.db.base import Base, TimestampMixin

STATUS_DISABLED = 0
STATUS_NORMAL = 1


class Category(Base, TimestampMixin):
    __tablename__ = "categories"
    __table_args__ = (
        Index("idx_categories_parent", "parent_id"),
        {"comment": "商品类别表：支持一级/二级分类的自关联树", "mysql_charset": "utf8mb4"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="类别ID")
    name: Mapped[str] = mapped_column(String(50), nullable=False, comment="类别名称")
    parent_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("categories.id", ondelete="CASCADE"), nullable=True, comment="父类别ID，顶级为空"
    )
    level: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=1, comment="层级：1=一级分类，2=二级分类"
    )
    icon: Mapped[str] = mapped_column(String(255), nullable=False, default="", comment="类别图标")
    sort_order: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0, comment="同级排序，越小越靠前"
    )
    status: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=STATUS_NORMAL, comment="状态：1=显示，0=隐藏"
    )

    parent: Mapped["Category | None"] = relationship(
        back_populates="children", remote_side="Category.id"
    )
    children: Mapped[list["Category"]] = relationship(
        back_populates="parent", cascade="all, delete-orphan", order_by="Category.sort_order"
    )
