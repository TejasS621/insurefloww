"""Configuration settings for the main backend service."""

from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the main backend."""

    model_config = SettingsConfigDict(
        env_prefix="MAIN_BACKEND_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "InsureFlow Main Backend"
    mongodb_url: str = Field(default="mongodb://localhost:27017/")
    database_name: str = Field(default="Insure_floww")
    server_host: str = Field(default="127.0.0.1")
    server_port: int = Field(default=8000, ge=1, le=65535)
    debug: bool = Field(default=True)


settings = Settings()

