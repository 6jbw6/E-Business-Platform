"""密码散列与 JWT 令牌。"""

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
import jwt

from backend.app.core.config import settings

_BCRYPT_MAX_INPUT_BYTES = 72


def hash_password(plain: str) -> str:
    password = plain.encode("utf-8")[:_BCRYPT_MAX_INPUT_BYTES]
    return bcrypt.hashpw(password, bcrypt.gensalt()).decode("ascii")


def verify_password(plain: str, hashed: str) -> bool:
    if not hashed:
        return False
    password = plain.encode("utf-8")[:_BCRYPT_MAX_INPUT_BYTES]
    try:
        return bcrypt.checkpw(password, hashed.encode("ascii"))
    except ValueError:
        return False


def create_access_token(subject: int | str, *, role: str, expires_minutes: int | None = None) -> str:
    now = datetime.now(timezone.utc)
    minutes = expires_minutes or settings.jwt_expire_minutes
    payload: dict[str, Any] = {
        "sub": str(subject),
        "role": role,
        "iat": int(now.timestamp()),
        "exp": now + timedelta(minutes=minutes),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> dict[str, Any]:
    """校验签名与有效期，失败时抛 jwt 原生异常，由 deps 统一转成 401。"""
    return jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
