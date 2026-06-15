"""Application submission request schemas."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator

from backend.main_backend.core.apis.schemas.shared import (
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

    @model_validator(mode="after")
    def validate_application_dependencies(self) -> "ApplicationCreateRequest":
        """Keep insurance-specific request fields consistent before service execution."""
        if self.coverage_details.insurance_type != self.insurance_type:
            raise ValueError("Coverage insurance type must match the application insurance type.")

        if self.insurance_type.value == "HEALTH" and self.health_details is None:
            raise ValueError("Health details are required for health insurance applications.")

        today = date.today()
        dob = self.personal_details.date_of_birth
        age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))

        if age < 0 or age > 120:
            raise ValueError("Applicant age must be between 0 and 120 years.")
        if self.insurance_type.value == "HEALTH" and not 18 <= age <= 65:
            raise ValueError("Health insurance requires age to be between 18 and 65 years.")
        if self.insurance_type.value == "LIFE" and not 18 <= age <= 70:
            raise ValueError("Life insurance requires age to be between 18 and 70 years.")
        if self.insurance_type.value == "VEHICLE" and age < 18:
            raise ValueError("Vehicle insurance requires the applicant to be at least 18 years old.")

        return self

