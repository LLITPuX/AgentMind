"""Application configuration management using Pydantic settings."""

from __future__ import annotations

from functools import lru_cache
from typing import List
from pydantic import field_validator

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Centralised configuration container."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", env_nested_delimiter="__")

    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    log_level: str = Field(default="info", alias="LOG_LEVEL")

    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="agentmind", alias="POSTGRES_DB")
    postgres_user: str = Field(default="agentmind", alias="POSTGRES_USER")
    postgres_password: str = Field(default="change_me", alias="POSTGRES_PASSWORD")

    redis_host: str = Field(default="localhost", alias="REDIS_HOST")
    redis_port: int = Field(default=6379, alias="REDIS_PORT")
    redis_db: int = Field(default=0, alias="REDIS_DB")
    redis_password: str | None = Field(default=None, alias="REDIS_PASSWORD")

    # FalkorDB (Redis protocol)
    falkordb_host: str = Field(default="falkordb", alias="FALKORDB_HOST")
    falkordb_port: int = Field(default=6379, alias="FALKORDB_PORT")
    falkordb_password: str | None = Field(default=None, alias="FALKORDB_PASSWORD")
    falkordb_graph: str = Field(default="agentmind", alias="FALKORDB_GRAPH")

    cors_allow_origins: str = Field(default="http://localhost:5173", alias="CORS_ALLOW_ORIGINS")

    # LLM / Agent
    google_api_key: str | None = Field(default=None, alias="GOOGLE_API_KEY")
    gemini_chat_model: str = Field(default="gemini-1.5-flash", alias="GEMINI_CHAT_MODEL")
    gemini_analysis_model: str = Field(default="gemini-1.5-flash", alias="GEMINI_ANALYSIS_MODEL")

    @property
    def cors_allow_origins_list(self) -> List[str]:
        raw = (self.cors_allow_origins or "").strip()
        if not raw:
            return []
        if raw.startswith("[") and raw.endswith("]"):
            import json

            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [str(item).strip() for item in parsed if str(item).strip()]
            except Exception:
                pass
        return [s.strip() for s in raw.split(",") if s.strip()]

    @property
    def sqlalchemy_database_uri(self) -> str:
        """Build SQLAlchemy async connection string."""

        return (
            "postgresql+asyncpg://"
            f"{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def falkordb_url(self) -> str:
        """Build FalkorDB connection URL (Redis protocol)."""

        auth = f":{self.falkordb_password}@" if self.falkordb_password else ""
        return f"redis://{auth}{self.falkordb_host}:{self.falkordb_port}/0"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached settings instance."""

    return Settings()  # type: ignore[call-arg]


settings = get_settings()

