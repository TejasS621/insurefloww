"""Broker registry response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BrokerRegistryResponse(BaseModel):
    """Broker registry payload returned by provider broker APIs."""

    model_config = ConfigDict(extra="forbid")

    broker_code: str
    broker_name: str
    callback_url: str
    webhook_url: str
    status: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class BrokerCredentialResponse(BaseModel):
    """One-time credential payload returned during broker registration or rotation."""

    model_config = ConfigDict(extra="forbid")

    broker_code: str
    api_key: str
    message: str

