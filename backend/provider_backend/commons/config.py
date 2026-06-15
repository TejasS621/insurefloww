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
    jwt_secret_key: str = Field(default="change-this-provider-backend-jwt-secret")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=60, ge=5, le=1440)
    provider_admin_email: str = Field(default="provider-admin@insurefloww.com")
    provider_admin_password: str = Field(default="Provider@12345")
    mock_payment_base_url: str = Field(default="http://localhost:8001/mock-razorpay/pay")
    main_backend_sync_url: str = Field(default="http://127.0.0.1:8000/api/v1/provider-sync/webhook")
    sync_timeout_seconds: float = Field(default=10.0, gt=0)
    sync_max_retries: int = Field(default=5, ge=1, le=20)
    sync_retry_delay_seconds: int = Field(default=300, ge=5, le=86400)
    integration_broker_code: str = Field(default="MAINAPP")
    integration_broker_api_key: str = Field(default="mainapp_dev_api_key")
    default_broker_callback_url: str = Field(
        default="http://127.0.0.1:8000/api/v1/provider-sync/webhook"
    )
    default_broker_webhook_url: str = Field(
        default="http://127.0.0.1:8001/api/v1/provider/webhook"
    )
    default_provider_webhook_url: str = Field(
        default="http://127.0.0.1:8001/api/v1/provider/webhook"
    )
    cors_allowed_origins: list[str] = Field(
        default_factory=lambda: [
            "http://127.0.0.1:5173",
            "http://127.0.0.1:5174",
            "http://localhost:5173",
            "http://localhost:5174",
        ]
    )
    cors_allowed_origin_regex: str = Field(
        default=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$"
    )


settings = Settings()

