from __future__ import annotations

from datetime import datetime, timedelta, timezone
from enum import Enum

from odmantic import Field, Model
from pydantic import ConfigDict


class UserRole(str, Enum):
    CUSTOMER = "CUSTOMER"
    ADMIN = "ADMIN"


class OTPPurpose(str, Enum):
    LOGIN = "LOGIN"
    REGISTER = "REGISTER"
    ADMIN_2FA = "ADMIN_2FA"


class User(Model):
    full_name: str = Field(..., min_length=2)
    email: str | None = Field(default=None, unique=True)
    mobile_number: str | None = Field(default=None, unique=True)
    password_hash: str | None = Field(default=None)
    user_role: UserRole = Field(default=UserRole.CUSTOMER)
    is_verified: bool = Field(default=False)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(collection="users", extra="forbid")


class OTPToken(Model):
    mobile_number: str = Field(..., min_length=10, max_length=15)
    otp_code_hash: str = Field(...)
    purpose: OTPPurpose = Field(...)
    is_used: bool = Field(default=False)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc) + timedelta(minutes=10)
    )

    model_config = ConfigDict(collection="otp_tokens", extra="forbid")

