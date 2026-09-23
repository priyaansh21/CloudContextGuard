"""
Application configuration for CloudContextGuard.

Settings are read from environment variables (optionally via a local .env
file) with sensible development defaults, so the backend runs out of the box
without any configuration. Filesystem locations always come from
``app.core.paths`` rather than being redefined here, keeping the project
portable across drives and folders.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.paths import DATABASE_PATH, PROJECT_ROOT


class Settings(BaseSettings):
    """Runtime configuration, overridable via environment variables or .env."""

    model_config = SettingsConfigDict(
        env_file=str(PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    APP_NAME: str = "CloudContextGuard"
    APP_ENV: str = "development"

    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000

    # Comma-separated list of allowed origins for the frontend dev server.
    CORS_ORIGINS: str = "http://127.0.0.1:5173,http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    @property
    def database_path(self) -> str:
        """Absolute, portable path to the SQLite database file."""
        return str(DATABASE_PATH)

    @property
    def database_url(self) -> str:
        return f"sqlite:///{DATABASE_PATH.as_posix()}"


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance shared across the application."""
    return Settings()
