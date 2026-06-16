"""Normalized quote persistence models for the main backend."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from odmantic import Field, Model
from pydantic import ConfigDict


class QuoteStatus(str, Enum):
    ACTIVE = "ACTIVE"
    SELECTED = "SELECTED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"


class Quote(Model):
    transaction_reference: str = Field(...)
    transaction_id: str = Field(...)
    provider_quote_id: str = Field(..., unique=True)
    provider_name: str = Field(...)
    plan_code: str = Field(...)
    plan_name: str = Field(...)
    base_premium: float = Field(..., ge=0)
    tax_amount: float = Field(default=0.0, ge=0)
    total_premium: float = Field(..., ge=0)
    coverage_amount: float = Field(..., ge=0)
    available_addons: list[dict[str, object]] = Field(default_factory=list)
    quote_status: QuoteStatus = Field(default=QuoteStatus.ACTIVE)
    expires_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(collection="quotes", extra="forbid")

