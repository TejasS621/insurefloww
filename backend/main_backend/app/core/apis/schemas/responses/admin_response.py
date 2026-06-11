"""Admin response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class BrokerRegistryResponse(BaseModel):
    """Broker registry payload returned by admin broker APIs."""

    model_config = ConfigDict(extra="forbid")

    broker_code: str
    broker_name: str
    callback_url: str
    webhook_url: str
    status: str
    created_by_admin: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None

