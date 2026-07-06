"""
Application settings.
"""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

from project_sentinel.config.defaults import (
    DEFAULT_HOST,
    DEFAULT_LOG_LEVEL,
    DEFAULT_OLLAMA_URL,
    DEFAULT_PORT,
)


class Settings(BaseSettings):
    """Application settings."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="SENTINEL_",
        extra="ignore",
    )

    host: str = DEFAULT_HOST

    port: int = DEFAULT_PORT

    log_level: str = DEFAULT_LOG_LEVEL

    ollama_url: str = DEFAULT_OLLAMA_URL

    github_token: str | None = Field(default=None)

    openai_api_key: str | None = Field(default=None)