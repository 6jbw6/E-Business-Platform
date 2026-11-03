"""用户表模型。"""

from sqlalchemy import Index, Integer, SmallInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.db.base import Base, TimestampMixin

ROLE_USER = "user"
ROLE_ADMIN = "admin"
STATUS_DISABLED = 0
STATUS_NORMAL = 1


class User(Base, TimestampMixin):
    __tablename__ = "users"
    __table_args__ = (
        Index("idx_users_phone", "phone"),
        {"comment": "用户表：账号、密码散列与基础资料", "mysql_charset": "utf8mb4"},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True, comment="用户ID")
    username: Mapped[str] = mapped_column(
        String(32), nullable=False, unique=True, index=True, comment="登录名，唯一"
    )
    password_hash: Mapped[str] = mapped_column(
        String(128), nullable=False, comment="bcrypt 密码散列，不保存明文"
    )
    nickname: Mapped[str] = mapped_column(String(32), nullable=False, default="", comment="昵称")
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="手机号")
    email: Mapped[str | None] = mapped_column(String(128), nullable=True, comment="邮箱")
    avatar: Mapped[str] = mapped_column(
        String(255), nullable=False, default="", comment="头像地址"
    )
    role: Mapped[str] = mapped_column(
        String(16), nullable=False, default=ROLE_USER, comment="角色：user=普通用户，admin=管理员"
    )
    status: Mapped[int] = mapped_column(
        SmallInteger, nullable=False, default=STATUS_NORMAL, comment="状态：1=正常，0=禁用"
    )

    @property
    def is_admin(self) -> bool:
        return self.role == ROLE_ADMIN
