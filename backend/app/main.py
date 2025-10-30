"""FastAPI application entrypoint for AgentMind backend."""

from __future__ import annotations

import logging
from typing import AsyncGenerator

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router as api_router
from .core.config import settings
from .dependencies.database import lifespan

logger = logging.getLogger(__name__)


def create_application() -> FastAPI:
    """Instantiate and configure the FastAPI application."""

    app = FastAPI(
        title="AgentMind API",
        version="0.1.0",
        lifespan=lifespan,
        openapi_url="/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api")

    return app


app = create_application()


@app.get("/health/ready", tags=["health"], summary="Readiness probe")
async def readiness_probe() -> dict[str, str]:
    """Simple endpoint to signal readiness to orchestrators."""

    return {"status": "ok"}

