"""Quote generation request schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

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

    @model_validator(mode="after")
    def validate_quote_dependencies(self) -> "ProviderQuoteCreateRequest":
        """Reject inconsistent quote payloads before pricing begins."""
        if self.coverage_details.insurance_type != self.insurance_type:
            raise ValueError("Coverage insurance type must match the quote insurance type.")
        if self.insurance_type.value == "HEALTH" and self.health_details is None:
            raise ValueError("Health details are required for health insurance quotes.")
        return self

