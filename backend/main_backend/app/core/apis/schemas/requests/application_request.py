"""Application submission request schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from backend.main_backend.app.core.apis.schemas.shared import (
    CoverageDetailsSchema,
    HealthDetailsSchema,
    InsuranceType,
    PersonalDetailsSchema,
)


class ApplicationCreateRequest(BaseModel):
    """Submit a new insurance application."""

    model_config = ConfigDict(extra="forbid")

    guest_identifier: str | None = None
    insurance_type: InsuranceType
    personal_details: PersonalDetailsSchema
    health_details: HealthDetailsSchema | None = None
    coverage_details: CoverageDetailsSchema
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=128)

