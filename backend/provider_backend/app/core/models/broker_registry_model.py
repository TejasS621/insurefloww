from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from odmantic import Field, Model
from pydantic import ConfigDict


class BrokerStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class BrokerRegistry(Model):
    broker_code: str = Field(..., unique=True)
    broker_name: str = Field(..., min_length=2)
    api_key_hash: str = Field(...)
    callback_url: str = Field(...)
    webhook_url: str = Field(...)
    status: BrokerStatus = Field(default=BrokerStatus.ACTIVE)
    created_by_admin: str | None = Field(default=None)
    last_key_rotated_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(collection="broker_registry", extra="forbid")

