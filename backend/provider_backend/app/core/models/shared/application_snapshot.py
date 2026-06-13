from __future__ import annotations

from odmantic import EmbeddedModel, Field

from .coverage_details import CoverageDetails
from .health_details import HealthDetails
from .personal_details import PersonalDetails


class ApplicationSnapshot(EmbeddedModel):
    application_reference: str = Field(...)
    insurance_type: str = Field(...)
    personal_details: PersonalDetails = Field(...)
    health_details: HealthDetails = Field(default_factory=HealthDetails)
    coverage_details: CoverageDetails = Field(...)
