from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from odmantic import Field, Model
from pydantic import ConfigDict

from .shared import CoverageDetails, HealthDetails, InsuranceType, PersonalDetails


class ApplicationStatus(str, Enum):
    APPLICATION_SUBMITTED = "APPLICATION_SUBMITTED"
    QUOTE_GENERATED = "QUOTE_GENERATED"
    QUOTE_SELECTED = "QUOTE_SELECTED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    POLICY_ISSUED = "POLICY_ISSUED"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class Application(Model):
    application_reference: str = Field(..., unique=True)
    user_id: str | None = Field(default=None)
    guest_identifier: str | None = Field(default=None)
    transaction_id: str | None = Field(default=None)
    transaction_reference: str | None = Field(default=None)
    insurance_type: InsuranceType = Field(...)
    personal_details: PersonalDetails = Field(...)
    health_details: HealthDetails | None = Field(default=None)
    coverage_details: CoverageDetails = Field(...)
    application_status: ApplicationStatus = Field(default=ApplicationStatus.APPLICATION_SUBMITTED)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(collection="applications", extra="forbid")
