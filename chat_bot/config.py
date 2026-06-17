"""Environment-backed configuration for the InsureFlow chatbot service."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class ChatBotSettings(BaseSettings):
    """Runtime settings used by the chatbot API service and session layer."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = Field(default="InsureFlow Chat Bot", alias="CHAT_BOT_APP_NAME")
    log_level: str = Field(default="INFO", alias="CHAT_BOT_LOG_LEVEL")
    host: str = Field(default="127.0.0.1", alias="CHAT_BOT_HOST")
    port: int = Field(default=8090, alias="CHAT_BOT_PORT")
    debug: bool = Field(default=True, alias="CHAT_BOT_DEBUG")
    session_ttl_minutes: int = Field(default=120, ge=10, le=1440, alias="CHAT_BOT_SESSION_TTL_MINUTES")
    environment: Literal["local", "production"] = Field(default="local", alias="CHAT_BOT_ENVIRONMENT")
    cors_allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            "http://127.0.0.1:5174",
            "http://localhost:5174",
        ],
        alias="CHAT_BOT_CORS_ALLOWED_ORIGINS",
    )


@lru_cache(maxsize=1)
def get_chat_bot_settings() -> ChatBotSettings:
    """Return a cached chatbot settings object for the current process."""

    return ChatBotSettings()
