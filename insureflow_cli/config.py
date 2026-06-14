"""Environment-backed settings for the InsureFlow CLI."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class CLISettings(BaseSettings):
    """Runtime configuration used by the Typer CLI and HTTP client."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "InsureFlow CLI"
    main_backend_url: str = Field(
        default="http://localhost:8000/api/v1",
        alias="INSUREFLOW_CLI_MAIN_BACKEND_URL",
    )
    request_timeout_seconds: float = Field(default=15.0, alias="INSUREFLOW_CLI_REQUEST_TIMEOUT_SECONDS")
    max_retries: int = Field(default=2, alias="INSUREFLOW_CLI_MAX_RETRIES")
    retry_backoff_seconds: float = Field(default=0.5, alias="INSUREFLOW_CLI_RETRY_BACKOFF_SECONDS")
    session_file: Path = Field(default=Path("storage/cli/session.json"), alias="INSUREFLOW_CLI_SESSION_FILE")
    download_directory: Path = Field(
        default=Path("storage/cli/downloads"),
        alias="INSUREFLOW_CLI_DOWNLOAD_DIRECTORY",
    )


@lru_cache(maxsize=1)
def get_settings() -> CLISettings:
    """Return cached CLI settings for the current process."""

    return CLISettings()
