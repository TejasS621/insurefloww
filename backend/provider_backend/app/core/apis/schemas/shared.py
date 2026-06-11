"""Shared API schema fragments for the provider backend."""

from __future__ import annotations

from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class InsuranceType(str, Enum):
    """Supported insurance lines on the provider side."""

    HEALTH = "HEALTH"
    LIFE = "LIFE"
    VEHICLE = "VEHICLE"
    TRAVEL = "TRAVEL"
    HOME = "HOME"


class PersonalDetailsSchema(BaseModel):
    """Applicant identity details used during underwriting."""

    model_config = ConfigDict(extra="forbid")

    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    email: EmailStr
    mobile_number: str = Field(..., min_length=10, max_length=15)
    date_of_birth: date
    address_line_1: str = Field(..., min_length=3)
    city: str = Field(..., min_length=2)
    state: str = Field(..., min_length=2)
    pincode: str = Field(..., min_length=4, max_length=10)


class HealthDetailsSchema(BaseModel):
    """Health details used for underwriting and pricing."""

    model_config = ConfigDict(extra="forbid")

    height_cm: float | None = Field(default=None, ge=0)
    weight_kg: float | None = Field(default=None, ge=0)
    smoker: bool = False
    diabetes: bool = False
    blood_pressure: bool = False
    heart_ailments: bool = False
    pre_existing_disease: bool = False
    other_conditions: list[str] = Field(default_factory=list)


class CoverageDetailsSchema(BaseModel):
    """Coverage information needed to price a quote."""

    model_config = ConfigDict(extra="forbid")

    insurance_type: InsuranceType
    coverage_amount: float = Field(..., gt=0)
    sum_insured: float | None = Field(default=None, gt=0)
    tenure_years: int | None = Field(default=None, ge=1)
    insured_members: int | None = Field(default=None, ge=1)

