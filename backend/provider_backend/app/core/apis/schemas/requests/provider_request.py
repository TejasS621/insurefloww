"""Provider broker-management request schemas."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class BrokerStatus(str, Enum):
    """Broker states managed by the provider backend."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class BrokerRegistrationRequest(BaseModel):
    """Register a new broker with generated credentials."""

    model_config = ConfigDict(extra="forbid")

    broker_name: str = Field(..., min_length=2, max_length=120)
    broker_code: str = Field(..., min_length=2, max_length=50)
    callback_url: HttpUrl
    webhook_url: HttpUrl
    created_by_admin: str | None = Field(default=None, max_length=120)


class BrokerStatusUpdateRequest(BaseModel):
    """Update a broker lifecycle status."""

    model_config = ConfigDict(extra="forbid")

    status: BrokerStatus
    reason: str | None = Field(default=None, max_length=500)


class KeyRotationRequest(BaseModel):
    """Request broker API key rotation."""

    model_config = ConfigDict(extra="forbid")

    rotated_by: str | None = Field(default=None, max_length=120)
    reason: str | None = Field(default=None, max_length=500)

