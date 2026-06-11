"""Admin request schemas for broker operations."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class BrokerStatus(str, Enum):
    """Broker lifecycle states exposed to admin APIs."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class BrokerRegistrationRequest(BaseModel):
    """Register a broker through the admin API."""

    model_config = ConfigDict(extra="forbid")

    broker_name: str = Field(..., min_length=2, max_length=120)
    broker_code: str = Field(..., min_length=2, max_length=50)
    callback_url: HttpUrl
    webhook_url: HttpUrl


class BrokerStatusUpdateRequest(BaseModel):
    """Change the status of an existing broker."""

    model_config = ConfigDict(extra="forbid")

    status: BrokerStatus
    reason: str | None = Field(default=None, max_length=500)


class BrokerKeyRotationRequest(BaseModel):
    """Trigger API key rotation for a broker."""

    model_config = ConfigDict(extra="forbid")

    initiated_by: str | None = Field(default=None, max_length=120)
    reason: str | None = Field(default=None, max_length=500)

