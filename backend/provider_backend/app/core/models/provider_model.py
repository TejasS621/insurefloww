from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from odmantic import Field, Model
from pydantic import ConfigDict


class ProviderStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class Provider(Model):
    provider_code: str = Field(..., unique=True)
    provider_name: str = Field(..., min_length=2)
    contact_email: str = Field(...)
    contact_phone: str = Field(..., min_length=10, max_length=15)
    webhook_url: str = Field(...)
    status: ProviderStatus = Field(default=ProviderStatus.ACTIVE)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(collection="providers", extra="forbid")

