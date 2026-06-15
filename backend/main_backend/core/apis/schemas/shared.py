"""Shared API schema fragments for the main backend."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class Gender(str, Enum):
    """Supported applicant gender values."""

    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class InsuranceType(str, Enum):
    """Supported insurance lines."""

    HEALTH = "HEALTH"
    LIFE = "LIFE"
    VEHICLE = "VEHICLE"
    TRAVEL = "TRAVEL"
    HOME = "HOME"


class Relation(str, Enum):
    """Relationship values used for coverage grouping."""

    SELF = "SELF"
    SPOUSE = "SPOUSE"
    CHILD = "CHILD"
    PARENT = "PARENT"
    FAMILY = "FAMILY"


class PersonalDetailsSchema(BaseModel):
    """Applicant identity and contact details."""

    model_config = ConfigDict(extra="forbid")

    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    email: EmailStr
    mobile_number: str = Field(..., min_length=10, max_length=15)
    date_of_birth: date
    gender: Gender
    address_line_1: str = Field(..., min_length=3)
    address_line_2: str | None = None
    city: str = Field(..., min_length=2)
    state: str = Field(..., min_length=2)
    pincode: str = Field(..., min_length=4, max_length=10)
    gstin: str | None = None
    politically_exposed_person: bool = False

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def parse_date_of_birth(cls, value: object) -> object:
        """Accept both ISO and DD/MM/YYYY date strings from the frontend."""
        if isinstance(value, str):
            trimmed = value.strip()
            if "/" in trimmed:
                day, month, year = trimmed.split("/")
                return date(int(year), int(month), int(day))
        return value


class HealthDetailsSchema(BaseModel):
    """Health and underwriting-related applicant details."""

    model_config = ConfigDict(extra="forbid")

    height_cm: float | None = Field(default=None, ge=50, le=250)
    weight_kg: float | None = Field(default=None, ge=10, le=300)
    calculated_bmi: float | None = Field(default=None, ge=0, le=100)
    smoker: bool = False
    diabetes: bool = False
    blood_pressure: bool = False
    heart_ailments: bool = False
    pre_existing_disease: bool = False
    other_conditions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_height_weight_pair(self) -> "HealthDetailsSchema":
        """Ensure anthropometric fields arrive together for underwriting requests."""
        if (self.height_cm is None) != (self.weight_kg is None):
            raise ValueError("Height and weight must be provided together.")
        return self


class CoverageDetailsSchema(BaseModel):
    """Coverage selection details shared across flows."""

    model_config = ConfigDict(extra="forbid")

    insurance_type: InsuranceType
    coverage_amount: float = Field(..., gt=0)
    sum_insured: float | None = Field(default=None, gt=0)
    tenure_years: int | None = Field(default=None, ge=1)
    relation: Relation | None = None
    insured_members: int | None = Field(default=None, ge=1)
    pan_india_cover: bool = True


class TimelineStampSchema(BaseModel):
    """Shared timestamp metadata for API payloads."""

    model_config = ConfigDict(extra="forbid")

    created_at: datetime
    updated_at: datetime | None = None
