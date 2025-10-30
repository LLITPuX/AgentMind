"""Database engine and session factories."""

from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from ..core.config import settings

engine = create_async_engine(
    settings.sqlalchemy_database_uri,
    echo=False,
    future=True,
    pool_size=5,
    max_overflow=10,
    pool_timeout=30,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)



