"""Common schema fragments shared across MCP tools."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class PersonalDetailsInput(BaseModel):
    """Customer identity payload passed to the application generation tool."""

    model_config = ConfigDict(extra="forbid")

    first_name: str = Field(..., min_length=1, description="Customer first name.")
    last_name: str = Field(..., min_length=1, description="Customer last name.")
    email: EmailStr = Field(..., description="Customer email address.")
    mobile_number: str = Field(
        ...,
        min_length=10,
        max_length=15,
        description="Customer mobile number used for the application.",
    )
    date_of_birth: str = Field(
        ...,
        description="Date of birth in YYYY-MM-DD or DD/MM/YYYY format.",
    )
    gender: str = Field(..., description="Customer gender: MALE, FEMALE, or OTHER.")
    address_line_1: str = Field(
        ...,
        min_length=3,
        description="Primary street address for the customer.",
    )
    address_line_2: str | None = Field(
        default=None,
        description="Optional secondary address line such as apartment or landmark.",
    )
    city: str = Field(..., min_length=2, description="Customer city.")
    state: str = Field(..., min_length=2, description="Customer state.")
    pincode: str = Field(
        ...,
        min_length=4,
        max_length=10,
        description="Customer postal or PIN code.",
    )
    gstin: str | None = Field(
        default=None,
        description="Optional GSTIN if the customer wants to provide it.",
    )
    politically_exposed_person: bool = Field(
        default=False,
        description="Whether the customer is a politically exposed person.",
    )


class HealthDetailsInput(BaseModel):
    """Health underwriting input required for health insurance applications."""

    model_config = ConfigDict(extra="forbid")

    height_cm: float | None = Field(
        default=None,
        ge=50,
        le=250,
        description="Customer height in centimeters.",
    )
    weight_kg: float | None = Field(
        default=None,
        ge=10,
        le=300,
        description="Customer weight in kilograms.",
    )
    calculated_bmi: float | None = Field(
        default=None,
        ge=0,
        le=100,
        description="Optional BMI value if already calculated by the caller.",
    )
    smoker: bool = Field(default=False, description="Whether the customer is a smoker.")
    diabetes: bool = Field(default=False, description="Whether the customer has diabetes.")
    blood_pressure: bool = Field(
        default=False,
        description="Whether the customer has blood pressure history.",
    )
    heart_ailments: bool = Field(
        default=False,
        description="Whether the customer has heart-related ailments.",
    )
    pre_existing_disease: bool = Field(
        default=False,
        description="Whether the customer has any pre-existing disease.",
    )
    other_conditions: list[str] = Field(
        default_factory=list,
        description="Optional list of other medical conditions not covered by the boolean flags.",
    )


class CoverageDetailsInput(BaseModel):
    """Coverage details forwarded to the application endpoint."""

    model_config = ConfigDict(extra="forbid")

    insurance_type: str = Field(
        ...,
        description="Insurance type matching the top-level insurance_type field.",
    )
    coverage_amount: float = Field(
        ...,
        gt=0,
        description="Requested coverage amount for the policy.",
    )
    sum_insured: float | None = Field(
        default=None,
        gt=0,
        description="Optional sum insured amount if distinct from coverage amount.",
    )
    tenure_years: int | None = Field(
        default=None,
        ge=1,
        description="Requested policy tenure in years.",
    )
    relation: str | None = Field(
        default=None,
        description="Relation grouping such as SELF, SPOUSE, CHILD, PARENT, or FAMILY.",
    )
    insured_members: int | None = Field(
        default=None,
        ge=1,
        description="Number of insured members covered by the policy.",
    )
    pan_india_cover: bool = Field(
        default=True,
        description="Whether the requested coverage should apply across India.",
    )


class QuoteAddon(BaseModel):
    """Add-on returned inside quote payloads."""

    model_config = ConfigDict(extra="forbid")

    addon_code: str
    addon_name: str
    addon_price: float


class PremiumBreakdown(BaseModel):
    """Premium details shown after quote selection or payment initiation."""

    model_config = ConfigDict(extra="forbid")

    base_premium: float
    tax_amount: float
    addon_amount: float
    total_premium: float


class FileMetadata(BaseModel):
    """Metadata for a downloaded file returned by an MCP tool."""

    model_config = ConfigDict(extra="forbid")

    file_name: str
    local_file_path: str


def extract_api_data(payload: dict[str, Any]) -> Any:
    """Return the `data` field from a standard InsureFlow API response payload."""

    return payload.get("data")

