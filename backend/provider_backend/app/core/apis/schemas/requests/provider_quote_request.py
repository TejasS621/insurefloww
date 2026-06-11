"""Quote generation request schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from backend.provider_backend.app.core.apis.schemas.shared import (
    CoverageDetailsSchema,
    HealthDetailsSchema,
    InsuranceType,
    PersonalDetailsSchema,
)


class ProviderQuoteCreateRequest(BaseModel):
    """Generate provider-side quotes for an application."""

    model_config = ConfigDict(extra="forbid")

    main_transaction_reference: str = Field(..., min_length=3, max_length=100)
    application_reference: str = Field(..., min_length=3, max_length=100)
    provider_code: str = Field(..., min_length=2, max_length=50)
    broker_code: str = Field(..., min_length=2, max_length=50)
    insurance_type: InsuranceType
    personal_details: PersonalDetailsSchema
    health_details: HealthDetailsSchema | None = None
    coverage_details: CoverageDetailsSchema

