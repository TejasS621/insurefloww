"""Environment-backed configuration for the InsureFlow MCP server."""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPSettings(BaseSettings):
    """Runtime configuration for the thin MCP orchestration layer."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "InsureFlow MCP Server"
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    main_backend_url: str = Field(
        default="http://localhost:8000/api/v1",
        alias="MAIN_BACKEND_URL",
    )
    provider_backend_url: str = Field(
        default="http://localhost:8001/api/v1",
        alias="PROVIDER_BACKEND_URL",
    )

    customer_jwt_token: str | None = Field(default=None, alias="CUSTOMER_JWT_TOKEN")
    admin_jwt_token: str | None = Field(default=None, alias="ADMIN_JWT_TOKEN")
    jwt_secret_key: str | None = Field(default=None, alias="JWT_SECRET_KEY")

    broker_code: str = Field(default="MAIN_BACKEND", alias="BROKER_CODE")
    broker_api_key: str | None = Field(default=None, alias="BROKER_API_KEY")

    request_timeout_seconds: float = Field(default=15.0, alias="MCP_REQUEST_TIMEOUT_SECONDS")
    max_retries: int = Field(default=2, alias="MCP_MAX_RETRIES")
    retry_backoff_seconds: float = Field(default=0.5, alias="MCP_RETRY_BACKOFF_SECONDS")
    download_directory: str = Field(default="storage/mcp_downloads", alias="MCP_DOWNLOAD_DIRECTORY")


@lru_cache(maxsize=1)
def get_settings() -> MCPSettings:
    """Return a cached settings object for the current process."""

    return MCPSettings()
