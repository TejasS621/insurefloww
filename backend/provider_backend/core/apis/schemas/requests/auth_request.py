"""Provider admin authentication request schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class ProviderAdminLoginRequest(BaseModel):
    """Authenticate a provider admin user."""

    model_config = ConfigDict(extra="forbid")

    email: EmailStr
    password: str = Field(..., min_length=8)

