from __future__ import annotations

from collections.abc import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from .config import get_settings


class Base(DeclarativeBase):
    pass


def make_engine(url: str | None = None):
    target = url or get_settings().database_url
    args = {"check_same_thread": False} if target.startswith("sqlite") else {}
    return create_engine(target, pool_pre_ping=True, connect_args=args)


engine = make_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
