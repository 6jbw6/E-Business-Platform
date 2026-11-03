"""用户数据访问。"""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from backend.app.core.exceptions import (
    CODE_UNAUTHORIZED,
    BizError,
    conflict,
    unauthorized,
)
from backend.app.core.security import hash_password, verify_password
from backend.app.models.user import ROLE_USER, STATUS_DISABLED, STATUS_NORMAL, User


def get_by_username(db: Session, username: str) -> User | None:
    return db.scalar(select(User).where(User.username == username))


def get_by_id(db: Session, user_id: int) -> User | None:
    return db.get(User, user_id)


def register(
    db: Session,
    *,
    username: str,
    password: str,
    nickname: str = "",
    phone: str | None = None,
    email: str | None = None,
) -> User:
    if get_by_username(db, username) is not None:
        raise conflict(f"登录名 {username} 已被注册")

    user = User(
        username=username,
        password_hash=hash_password(password),
        nickname=nickname or username,
        phone=phone,
        email=email,
        role=ROLE_USER,
        status=STATUS_NORMAL,
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        # 并发注册同名账号时由唯一索引兜底
        db.rollback()
        raise conflict("登录名已被占用，请换一个") from exc
    db.refresh(user)
    return user


def authenticate(db: Session, username: str, password: str) -> User:
    user = get_by_username(db, username)
    # 用户不存在与密码错误返回同一句话，避免枚举出哪些登录名已注册
    if user is None or not verify_password(password, user.password_hash):
        raise unauthorized("登录名或密码错误")
    if user.status == STATUS_DISABLED:
        raise BizError("账号已被禁用，请联系管理员", code=CODE_UNAUTHORIZED, http_status=401)
    return user


def update_profile(db: Session, user: User, **fields: object) -> User:
    for key, value in fields.items():
        if value is not None:
            setattr(user, key, value)
    db.commit()
    db.refresh(user)
    return user
