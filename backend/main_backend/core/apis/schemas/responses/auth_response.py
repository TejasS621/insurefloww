"""Authentication response schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class OTPDispatchResponse(BaseModel):
    """Payload returned when an OTP is dispatched."""

    model_config = ConfigDict(extra="forbid")

    mobile_number: str
    expires_in_seconds: int


class TokenData(BaseModel):
    """Token payload returned after successful authentication."""

    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    user_role: str


class AuthTokenResponse(BaseModel):
    """Authentication success response payload."""

    model_config = ConfigDict(extra="forbid")

    user_id: str | None = None
    token: TokenData

