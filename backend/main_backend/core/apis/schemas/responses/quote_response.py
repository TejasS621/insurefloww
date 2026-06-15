"""Quote response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class QuoteAddonResponse(BaseModel):
    """Add-on option returned with a quote."""

    model_config = ConfigDict(extra="forbid")

    addon_code: str
    addon_name: str
    addon_price: float = Field(..., ge=0)


class NormalizedQuoteResponse(BaseModel):
    """Frontend-friendly normalized quote representation."""

    model_config = ConfigDict(extra="forbid")

    quote_id: str
    provider_name: str
    plan_code: str
    plan_name: str
    base_premium: float = Field(..., ge=0)
    tax_amount: float = Field(..., ge=0)
    total_premium: float = Field(..., ge=0)
    coverage_amount: float = Field(..., ge=0)
    available_addons: list[QuoteAddonResponse] = Field(default_factory=list)
    quote_status: str
    expires_at: datetime | None = None

