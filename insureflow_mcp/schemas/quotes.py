"""Request and response schemas for quote tools."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from insureflow_mcp.schemas.common import CoverageDetailsInput, HealthDetailsInput, PersonalDetailsInput, QuoteAddon


class GenerateQuoteInput(BaseModel):
    """Input accepted by the quote-generation MCP tool."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "description": (
                "Use this tool to create a complete insurance application and generate quotes. "
                "For HEALTH insurance, collect full customer identity details, contact details, "
                "address, coverage preferences, and detailed health underwriting inputs before calling."
            )
        },
    )

    insurance_type: str = Field(
        ...,
        description=(
            "Insurance type for the application. Use HEALTH, LIFE, VEHICLE, TRAVEL, or HOME."
        ),
    )
    guest_identifier: str | None = Field(
        default=None,
        description="Optional guest identifier if the caller already tracks anonymous users.",
    )
    personal_details: PersonalDetailsInput = Field(
        ...,
        description="Full customer identity, contact, and address details for the application.",
    )
    coverage_details: CoverageDetailsInput = Field(
        ...,
        description="Coverage preferences such as amount, tenure, relation, and insured members.",
    )
    health_details: HealthDetailsInput | None = Field(
        default=None,
        description=(
            "Health underwriting details required when insurance_type is HEALTH. "
            "Ask about height, weight, smoker status, diabetes, blood pressure history, "
            "heart ailments, pre-existing disease, and any other medical conditions."
        ),
    )
    idempotency_key: str | None = Field(
        default=None,
        min_length=8,
        max_length=128,
        description="Optional idempotency key to prevent accidental duplicate application creation.",
    )

    @model_validator(mode="after")
    def ensure_health_details_for_health(self) -> "GenerateQuoteInput":
        """Require health details when a health policy quote is requested."""

        if self.insurance_type.upper() == "HEALTH" and self.health_details is None:
            raise ValueError("health_details are required when insurance_type is HEALTH.")
        if self.coverage_details.insurance_type.upper() != self.insurance_type.upper():
            raise ValueError("coverage_details.insurance_type must match insurance_type.")
        return self


class QuoteSummary(BaseModel):
    """Condensed quote information returned to Claude."""

    model_config = ConfigDict(extra="forbid")

    quote_id: str
    provider_name: str
    plan_name: str
    premium_amount: float
    coverage_amount: float
    status: str


class GenerateQuoteOutput(BaseModel):
    """Tool output returned after application creation and quote generation."""

    model_config = ConfigDict(extra="forbid")

    application_reference: str
    transaction_reference: str | None = None
    application_status: str
    quote_ids: list[str]
    provider_names: list[str]
    premium_amounts: list[float]
    quote_summary: list[QuoteSummary]


class SelectQuoteInput(BaseModel):
    """Input accepted by the quote selection tool."""

    model_config = ConfigDict(extra="forbid")

    quote_id: str
    selected_addons: list[str] = Field(default_factory=list)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=128)


class SelectQuoteOutput(BaseModel):
    """Direct quote payload returned after selecting a quote."""

    model_config = ConfigDict(extra="forbid")

    quote_id: str
    provider_name: str
    plan_code: str
    plan_name: str
    base_premium: float
    tax_amount: float
    total_premium: float
    coverage_amount: float
    available_addons: list[QuoteAddon]
    quote_status: str
    expires_at: str | None = None
