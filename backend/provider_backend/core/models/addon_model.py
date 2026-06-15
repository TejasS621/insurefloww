from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from odmantic import Field, Model
from pydantic import ConfigDict

from .shared import InsuranceType


class AddOnStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"


class AddOn(Model):
    addon_code: str = Field(..., unique=True)
    provider_code: str = Field(...)
    insurance_type: InsuranceType = Field(...)
    addon_name: str = Field(..., min_length=2)
    addon_description: str | None = Field(default=None)
    addon_price: float = Field(..., ge=0)
    status: AddOnStatus = Field(default=AddOnStatus.ACTIVE)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(collection="addons", extra="forbid")

