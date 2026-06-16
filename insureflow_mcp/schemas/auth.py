"""Request and response schemas for customer authentication helpers."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class RequestCustomerOTPInput(BaseModel):
    """Input accepted by the customer OTP-dispatch helper."""

    model_config = ConfigDict(extra="forbid")

    mobile_number: str = Field(..., min_length=10, max_length=15)


class VerifyCustomerOTPInput(BaseModel):
    """Input accepted by the customer OTP-verification helper."""

    model_config = ConfigDict(extra="forbid")

    mobile_number: str = Field(..., min_length=10, max_length=15)
    otp_code: str = Field(..., min_length=4, max_length=8)


class OTPDispatchOutput(BaseModel):
    """OTP-dispatch payload returned from the main backend."""

    model_config = ConfigDict(extra="forbid")

    mobile_number: str
    expires_in_seconds: int


class TokenPayloadOutput(BaseModel):
    """Normalized access-token payload returned after successful login."""

    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: str
    expires_in_seconds: int
    user_role: str


class AuthTokenOutput(BaseModel):
    """Authentication result returned by the customer OTP verification helper."""

    model_config = ConfigDict(extra="forbid")

    user_id: str | None = None
    token: TokenPayloadOutput
