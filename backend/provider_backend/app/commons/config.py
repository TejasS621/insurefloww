"""Configuration settings for the provider backend service."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the provider backend."""

    model_config = SettingsConfigDict(
        env_prefix="PROVIDER_BACKEND_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "InsureFlow Provider Backend"
    mongodb_url: str = Field(default="mongodb://localhost:27017/")
    database_name: str = Field(default="Insure_floww")
    server_host: str = Field(default="127.0.0.1")
    server_port: int = Field(default=8001, ge=1, le=65535)
    debug: bool = Field(default=True)
    main_backend_sync_url: str = Field(default="http://127.0.0.1:8000/api/v1/provider-sync/webhook")
    sync_timeout_seconds: float = Field(default=10.0, gt=0)
    sync_max_retries: int = Field(default=5, ge=1, le=20)
    sync_retry_delay_seconds: int = Field(default=300, ge=5, le=86400)


settings = Settings()

