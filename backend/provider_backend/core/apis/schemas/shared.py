"""Shared API schema fragments for the provider backend."""

from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator, model_validator


class InsuranceType(str, Enum):
    """Supported insurance lines on the provider side."""

    HEALTH = "HEALTH"
    LIFE = "LIFE"
    VEHICLE = "VEHICLE"
    TRAVEL = "TRAVEL"
    HOME = "HOME"


class Gender(str, Enum):
    """Supported applicant gender values on the provider side."""

    MALE = "MALE"
    FEMALE = "FEMALE"
    OTHER = "OTHER"


class Relation(str, Enum):
    """Relationship values used for coverage grouping."""

    SELF = "SELF"
    SPOUSE = "SPOUSE"
    CHILD = "CHILD"
    PARENT = "PARENT"
    FAMILY = "FAMILY"


class PersonalDetailsSchema(BaseModel):
    """Applicant identity details used during underwriting."""

    model_config = ConfigDict(extra="forbid")

    first_name: str = Field(..., min_length=1, description="Applicant first name.")
    last_name: str = Field(..., min_length=1, description="Applicant last name.")
    email: EmailStr = Field(..., description="Applicant email address.")
    mobile_number: str = Field(
        ..., min_length=10, max_length=15, description="Applicant mobile number."
    )
    date_of_birth: date = Field(..., description="Applicant date of birth.")
    gender: Gender = Field(..., description="Applicant gender.")
    address_line_1: str = Field(..., min_length=3, description="Primary address line.")
    address_line_2: str | None = Field(default=None, description="Secondary address line.")
    city: str = Field(..., min_length=2, description="Applicant city.")
    state: str = Field(..., min_length=2, description="Applicant state.")
    pincode: str = Field(..., min_length=4, max_length=10, description="Postal code.")
    gstin: str | None = Field(default=None, description="Optional GST identification number.")
    politically_exposed_person: bool = Field(
        default=False,
        description="Indicates whether the applicant is a politically exposed person.",
    )

    @field_validator("date_of_birth", mode="before")
    @classmethod
    def parse_date_of_birth(cls, value: object) -> object:
        """Accept both ISO and DD/MM/YYYY date strings from broker-facing flows."""
        if isinstance(value, str):
            trimmed = value.strip()
            if "/" in trimmed:
                day, month, year = trimmed.split("/")
                return date(int(year), int(month), int(day))
        return value


class HealthDetailsSchema(BaseModel):
    """Health details used for underwriting and pricing."""

    model_config = ConfigDict(extra="forbid")

    height_cm: float | None = Field(default=None, ge=50, le=250, description="Applicant height in centimeters.")
    weight_kg: float | None = Field(default=None, ge=10, le=300, description="Applicant weight in kilograms.")
    calculated_bmi: float | None = Field(default=None, ge=0, le=100, description="Optional BMI calculated by the caller.")
    smoker: bool = Field(default=False, description="Whether the applicant is a smoker.")
    diabetes: bool = Field(default=False, description="Whether the applicant has diabetes.")
    blood_pressure: bool = Field(default=False, description="Whether the applicant has blood-pressure history.")
    heart_ailments: bool = Field(default=False, description="Whether the applicant has heart-related ailments.")
    pre_existing_disease: bool = Field(default=False, description="Whether the applicant has any pre-existing disease.")
    other_conditions: list[str] = Field(default_factory=list, description="Additional declared health conditions.")

    @model_validator(mode="after")
    def validate_height_weight_pair(self) -> "HealthDetailsSchema":
        """Ensure height and weight stay paired for pricing requests."""
        if (self.height_cm is None) != (self.weight_kg is None):
            raise ValueError("Height and weight must be provided together.")
        return self


class CoverageDetailsSchema(BaseModel):
    """Coverage information needed to price a quote."""

    model_config = ConfigDict(extra="forbid")

    insurance_type: InsuranceType = Field(..., description="Insurance line requested from the provider.")
    coverage_amount: float = Field(..., gt=0, description="Requested coverage amount.")
    sum_insured: float | None = Field(default=None, gt=0, description="Optional sum-insured amount for applicable products.")
    tenure_years: int | None = Field(default=None, ge=1, description="Policy tenure in years.")
    relation: Relation | None = Field(default=None, description="Coverage relation grouping for the insured party.")
    insured_members: int | None = Field(default=None, ge=1, description="Number of insured members for family coverage.")
    pan_india_cover: bool = Field(default=True, description="Whether the requested plan should support PAN India coverage.")

