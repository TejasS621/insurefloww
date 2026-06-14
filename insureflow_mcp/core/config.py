"""Environment-backed configuration for the InsureFlow MCP server."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

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
    transport: Literal["stdio", "http", "sse", "streamable-http"] = Field(
        default="stdio",
        alias="MCP_TRANSPORT",
    )
    host: str = Field(default="0.0.0.0", alias="MCP_HOST")
    port: int = Field(default=8080, alias="MCP_PORT")
    streamable_http_path: str = Field(default="/mcp", alias="MCP_HTTP_PATH")
    health_path: str = Field(default="/health", alias="MCP_HEALTH_PATH")
    cors_allow_origins: list[str] = Field(default_factory=lambda: ["*"], alias="MCP_CORS_ALLOW_ORIGINS")
    api_key: str | None = Field(default=None, alias="MCP_API_KEY")

    main_backend_url: str = Field(
        default="http://localhost:8000/api/v1",
        alias="MAIN_BACKEND_URL",
    )
    request_timeout_seconds: float = Field(default=15.0, alias="MCP_REQUEST_TIMEOUT_SECONDS")
    max_retries: int = Field(default=2, alias="MCP_MAX_RETRIES")
    retry_backoff_seconds: float = Field(default=0.5, alias="MCP_RETRY_BACKOFF_SECONDS")
    download_directory: str = Field(default="storage/mcp_downloads", alias="MCP_DOWNLOAD_DIRECTORY")


@lru_cache(maxsize=1)
def get_settings() -> MCPSettings:
    """Return a cached settings object for the current process."""

    return MCPSettings()
