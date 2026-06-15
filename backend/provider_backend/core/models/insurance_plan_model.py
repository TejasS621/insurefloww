from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from odmantic import Field, Model
from pydantic import ConfigDict

from .shared import InsuranceType


class InsurancePlanStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class InsurancePlan(Model):
    plan_code: str = Field(..., unique=True)
    provider_code: str = Field(...)
    insurance_type: InsuranceType = Field(...)
    plan_name: str = Field(..., min_length=2)
    coverage_options: list[float] = Field(default_factory=list)
    base_premium_rules: dict[str, object] = Field(default_factory=dict)
    benefits: list[str] = Field(default_factory=list)
    status: InsurancePlanStatus = Field(default=InsurancePlanStatus.ACTIVE)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(collection="insurance_plans", extra="forbid")

