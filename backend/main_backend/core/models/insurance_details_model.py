"""Insurance detail persistence models linked to customer transactions."""

from __future__ import annotations

from datetime import datetime, timezone

from odmantic import Field, Model
from pydantic import ConfigDict

from .shared import CoverageDetails, HealthDetails, InsuranceType


class InsuranceDetails(Model):
    transaction_reference: str = Field(..., unique=True)
    insurance_type: InsuranceType = Field(...)
    coverage_amount: float = Field(..., gt=0)
    tenure: int | None = Field(default=None, ge=1)
    sum_insured: float | None = Field(default=None, gt=0)
    insured_members: int | None = Field(default=None, ge=1)
    health_details: HealthDetails = Field(default_factory=HealthDetails)
    vehicle_details: dict[str, object] | None = Field(default=None)
    travel_details: dict[str, object] | None = Field(default=None)
    home_details: dict[str, object] | None = Field(default=None)
    life_details: dict[str, object] | None = Field(default=None)
    coverage_details: CoverageDetails = Field(...)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(collection="insurance_details", extra="forbid")
