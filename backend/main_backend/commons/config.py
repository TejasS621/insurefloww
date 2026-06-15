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
    jwt_secret_key: str = Field(default="change-this-main-backend-jwt-secret")
    jwt_algorithm: str = Field(default="HS256")
    jwt_access_token_expire_minutes: int = Field(default=60, ge=5, le=1440)
    admin_email: str = Field(default="admin@insurefloww.com")
    admin_password: str = Field(default="Admin@12345")
    admin_otp_code: str = Field(default="123456")
    customer_otp_expiry_minutes: int = Field(default=10, ge=1, le=60)
    customer_otp_length: int = Field(default=6, ge=4, le=8)
    provider_payment_create_url: str = Field(
        default="http://127.0.0.1:8001/api/v1/payments/create"
    )
    provider_quote_generate_url: str = Field(
        default="http://127.0.0.1:8001/api/v1/quotes/generate"
    )
    provider_request_timeout_seconds: float = Field(default=10.0, gt=0)
    integration_broker_code: str = Field(default="MAINAPP")
    integration_broker_api_key: str = Field(default="mainapp_dev_api_key")
    integration_provider_code: str = Field(default="DEMO_PROVIDER")
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

