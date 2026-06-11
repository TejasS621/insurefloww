"""Authentication request schemas for the main backend."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class OTPLoginRequest(BaseModel):
    """Request an OTP for customer login."""

    model_config = ConfigDict(extra="forbid")

    mobile_number: str = Field(..., min_length=10, max_length=15)


class OTPVerifyRequest(BaseModel):
    """Verify an OTP for customer login."""

    model_config = ConfigDict(extra="forbid")

    mobile_number: str = Field(..., min_length=10, max_length=15)
    otp_code: str = Field(..., min_length=4, max_length=8)


class AdminLoginRequest(BaseModel):
    """Start the admin login flow."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(..., min_length=8)


class AdminVerifyRequest(BaseModel):
    """Verify the admin second-factor OTP."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    otp_code: str = Field(..., min_length=4, max_length=8)

