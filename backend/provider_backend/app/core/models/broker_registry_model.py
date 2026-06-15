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
    company_name: str | None = Field(default=None)
    license_number: str | None = Field(default=None)
    registration_number: str | None = Field(default=None)
    contact_person_name: str | None = Field(default=None)
    contact_email: str | None = Field(default=None)
    contact_phone: str | None = Field(default=None)
    supported_insurance_types: list[str] = Field(default_factory=list)
    active_regions: list[str] = Field(default_factory=list)
    partner_provider_codes: list[str] = Field(default_factory=list)
    notes: str | None = Field(default=None)
    api_key_hash: str = Field(...)
    callback_url: str = Field(...)
    webhook_url: str = Field(...)
    status: BrokerStatus = Field(default=BrokerStatus.ACTIVE)
    created_by_admin: str | None = Field(default=None)
    last_key_rotated_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(collection="broker_registry", extra="forbid")

