"""Provider quote response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProviderQuoteAddonResponse(BaseModel):
    """Provider-side add-on option included in quote payloads."""

    model_config = ConfigDict(extra="forbid")

    addon_code: str
    addon_name: str
    addon_price: float = Field(..., ge=0)


class ProviderQuoteResponse(BaseModel):
    """Provider-generated quote response payload."""

    model_config = ConfigDict(extra="forbid")

    provider_quote_id: str
    provider_transaction_reference: str
    provider_name: str
    plan_code: str
    plan_name: str
    base_premium: float = Field(..., ge=0)
    tax_amount: float = Field(..., ge=0)
    total_premium: float = Field(..., ge=0)
    coverage_amount: float = Field(..., ge=0)
    risk_score: float | None = Field(default=None, ge=0)
    risk_category: str | None = None
    available_addons: list[ProviderQuoteAddonResponse] = Field(default_factory=list)
    status: str
    expires_at: datetime | None = None

