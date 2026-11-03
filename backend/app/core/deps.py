"""依赖注入：取当前登录用户、管理员校验。"""

from typing import Annotated

import jwt
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from backend.app.core.exceptions import forbidden, unauthorized
from backend.app.core.security import decode_access_token
from backend.app.db.session import get_db
from backend.app.models.user import ROLE_ADMIN, STATUS_NORMAL, User

# auto_error=False：缺令牌时由我们自己抛出统一的 401 响应体
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="api/v1/auth/login", auto_error=False, description="登录后拿到的 JWT"
)

DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    token: Annotated[str | None, Depends(oauth2_scheme)] = None,
) -> User:
    if not token:
        raise unauthorized("请先登录")
    try:
        payload = decode_access_token(token)
    except jwt.ExpiredSignatureError as exc:
        raise unauthorized("登录已过期，请重新登录") from exc
    except jwt.PyJWTError as exc:
        raise unauthorized("登录凭证无效，请重新登录") from exc

    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise unauthorized("账号不存在或已被删除")
    if user.status != STATUS_NORMAL:
        raise forbidden("账号已被禁用")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def get_current_admin(user: CurrentUser) -> User:
    if user.role != ROLE_ADMIN:
        raise forbidden("该操作仅管理员可用")
    return user


CurrentAdmin = Annotated[User, Depends(get_current_admin)]
