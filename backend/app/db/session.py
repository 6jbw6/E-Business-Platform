"""数据库会话与引擎。"""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from backend.app.core.config import settings
from backend.app.db.base import Base

engine = create_engine(
    settings.sqlalchemy_uri,
    pool_pre_ping=True,
    # MySQL 默认 wait_timeout 8 小时，回收更早可避免拿到已断开的连接
    pool_recycle=3600,
    pool_size=10,
    max_overflow=20,
    echo=settings.debug,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    """FastAPI 依赖：每个请求一个会话，异常回滚，结束关闭。"""
    db = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


__all__ = ["Base", "SessionLocal", "engine", "get_db"]
