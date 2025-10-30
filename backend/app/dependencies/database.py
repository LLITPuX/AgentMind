"""Database dependency injection helpers."""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncGenerator, Callable

from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import async_session_factory, engine


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async SQLAlchemy session for request scope."""

    async with async_session_factory() as session:  # pragma: no branch
        yield session


@asynccontextmanager
async def lifespan(app) -> AsyncGenerator[None, None]:  # type: ignore[no-untyped-def]
    """Manage application lifespan resources (database, caches, etc.)."""

    try:
        yield
    finally:
        await engine.dispose()



