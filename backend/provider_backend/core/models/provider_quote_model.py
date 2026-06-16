"""Provider quote persistence models used during pricing workflows."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from odmantic import Field, Model
from pydantic import ConfigDict

from .shared import ApplicationSnapshot


class ProviderQuoteStatus(str, Enum):
    GENERATED = "GENERATED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAYMENT_SUCCESS = "PAYMENT_SUCCESS"
    POLICY_GENERATED = "POLICY_GENERATED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"


class RiskCategory(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class ProviderQuote(Model):
    provider_transaction_reference: str = Field(...)
    main_transaction_reference: str = Field(...)
    provider_quote_id: str = Field(..., unique=True)
    plan_code: str = Field(...)
    base_premium: float = Field(..., ge=0)
    tax_amount: float = Field(default=0.0, ge=0)
    total_premium: float = Field(..., ge=0)
    coverage_amount: float = Field(..., ge=0)
    risk_score: float | None = Field(default=None, ge=0)
    risk_category: RiskCategory | None = Field(default=None)
    available_addons: list[dict[str, object]] = Field(default_factory=list)
    application_snapshot: ApplicationSnapshot = Field(...)
    status: ProviderQuoteStatus = Field(default=ProviderQuoteStatus.GENERATED)
    expires_at: datetime | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(collection="provider_quotes", extra="forbid")

