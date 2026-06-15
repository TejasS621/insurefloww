"""Application response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from backend.main_backend.core.apis.schemas.responses.quote_response import NormalizedQuoteResponse
from backend.main_backend.core.apis.schemas.shared import CoverageDetailsSchema, HealthDetailsSchema, PersonalDetailsSchema


class ApplicationSummaryResponse(BaseModel):
    """Application summary returned to the frontend."""

    model_config = ConfigDict(extra="forbid")

    application_reference: str
    transaction_reference: str | None = None
    insurance_type: str
    personal_details: PersonalDetailsSchema
    health_details: HealthDetailsSchema | None = None
    coverage_details: CoverageDetailsSchema
    application_status: str
    quotes: list[NormalizedQuoteResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
