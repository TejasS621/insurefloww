"""Request and response schemas for quote tools."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, model_validator

from mcp.schemas.common import CoverageDetailsInput, HealthDetailsInput, PersonalDetailsInput, PremiumBreakdown, QuoteAddon


class GenerateQuoteInput(BaseModel):
    """Input accepted by the quote-generation MCP tool."""

    model_config = ConfigDict(extra="forbid")

    insurance_type: str = Field(..., description="HEALTH, LIFE, VEHICLE, TRAVEL, or HOME.")
    guest_identifier: str | None = None
    personal_details: PersonalDetailsInput
    coverage_details: CoverageDetailsInput
    health_details: HealthDetailsInput | None = None
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=128)

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


class GetQuoteInput(BaseModel):
    """Input accepted by the quote-detail lookup tool."""

    model_config = ConfigDict(extra="forbid")

    quote_id: str


class GetQuoteOutput(BaseModel):
    """Detailed quote information returned from cached or authenticated lookup."""

    model_config = ConfigDict(extra="forbid")

    quote_id: str
    provider_name: str
    plan_code: str
    plan_name: str
    premium: PremiumBreakdown
    coverage_amount: float
    addons: list[QuoteAddon]
    status: str
    transaction_reference: str | None = None


class SelectQuoteInput(BaseModel):
    """Input accepted by the quote selection tool."""

    model_config = ConfigDict(extra="forbid")

    quote_id: str
    selected_addons: list[str] = Field(default_factory=list)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=128)


class SelectQuoteOutput(BaseModel):
    """Output returned after selecting a quote."""

    model_config = ConfigDict(extra="forbid")

    quote_id: str
    transaction_reference: str | None = None
    premium_breakdown: PremiumBreakdown
    payment_status: str | None = None
    selected_addons: list[str]
