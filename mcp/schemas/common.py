"""Common schema fragments shared across MCP tools."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class PersonalDetailsInput(BaseModel):
    """Customer identity payload passed to the application generation tool."""

    model_config = ConfigDict(extra="forbid")

    first_name: str = Field(..., min_length=1)
    last_name: str = Field(..., min_length=1)
    email: EmailStr
    mobile_number: str = Field(..., min_length=10, max_length=15)
    date_of_birth: str = Field(..., description="Date of birth in ISO or DD/MM/YYYY format.")
    gender: str = Field(..., description="MALE, FEMALE, or OTHER.")
    address_line_1: str = Field(..., min_length=3)
    address_line_2: str | None = None
    city: str = Field(..., min_length=2)
    state: str = Field(..., min_length=2)
    pincode: str = Field(..., min_length=4, max_length=10)
    gstin: str | None = None
    politically_exposed_person: bool = False


class HealthDetailsInput(BaseModel):
    """Health underwriting input required for health insurance applications."""

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


class CoverageDetailsInput(BaseModel):
    """Coverage details forwarded to the application endpoint."""

    model_config = ConfigDict(extra="forbid")

    insurance_type: str
    coverage_amount: float = Field(..., gt=0)
    sum_insured: float | None = Field(default=None, gt=0)
    tenure_years: int | None = Field(default=None, ge=1)
    relation: str | None = None
    insured_members: int | None = Field(default=None, ge=1)
    pan_india_cover: bool = True


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

