"""Provider admin authentication response schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ProviderAuthResponse(BaseModel):
    """Authentication payload returned to provider admins."""

    model_config = ConfigDict(extra="forbid")

    access_token: str
    token_type: str = "bearer"
    expires_in_seconds: int

