"""Broker registry response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class BrokerRegistryResponse(BaseModel):
    """Broker registry payload returned by provider broker APIs."""

    model_config = ConfigDict(extra="forbid")

    broker_code: str
    broker_name: str
    company_name: str | None = None
    license_number: str | None = None
    registration_number: str | None = None
    contact_person_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    supported_insurance_types: list[str] = Field(default_factory=list)
    active_regions: list[str] = Field(default_factory=list)
    partner_provider_codes: list[str] = Field(default_factory=list)
    notes: str | None = None
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

