"""FalkorDB async client and helpers (Redis protocol)."""

from __future__ import annotations

from typing import AsyncGenerator

import redis.asyncio as redis

from ..core.config import settings

_pool: redis.ConnectionPool | None = None


def _get_pool() -> redis.ConnectionPool:
    global _pool
    if _pool is None:
        _pool = redis.ConnectionPool.from_url(
            settings.falkordb_url,
            max_connections=32,
            decode_responses=True,
            health_check_interval=30,
            socket_timeout=5,
            socket_connect_timeout=5,
            retry_on_timeout=True,
        )
    return _pool


async def get_falkordb() -> AsyncGenerator[redis.Redis, None]:
    client = redis.Redis(connection_pool=_get_pool())
    try:
        yield client
    finally:
        await client.aclose()


async def graph_query(
    client: redis.Redis, graph_name: str, cypher: str, params: dict | None = None
):
    args: list[str] = [graph_name, cypher]
    if params:
        args.append("PARAMS")
        for key, value in params.items():
            args.extend([key, str(value)])
    return await client.execute_command("GRAPH.QUERY", *args)



