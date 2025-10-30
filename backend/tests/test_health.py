"""Health endpoint integration tests."""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_readiness_probe() -> None:
    async with AsyncClient(app=app, base_url="http://testserver") as client:
        response = await client.get("/health/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}



