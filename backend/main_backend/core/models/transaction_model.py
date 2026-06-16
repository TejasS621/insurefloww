"""Transaction and payment lifecycle models for the main backend."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from odmantic import Field, Model
from pydantic import ConfigDict

from .shared import ApplicationSnapshot


class TransactionStatus(str, Enum):
    APPLICATION_SUBMITTED = "APPLICATION_SUBMITTED"
    QUOTE_GENERATED = "QUOTE_GENERATED"
    QUOTE_SELECTED = "QUOTE_SELECTED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAYMENT_SUCCESS = "PAYMENT_SUCCESS"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    POLICY_ISSUED = "POLICY_ISSUED"
    EXPIRED = "EXPIRED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, Enum):
    NOT_INITIATED = "NOT_INITIATED"
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class PolicyStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    PENDING = "PENDING"
    ISSUED = "ISSUED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class Transaction(Model):
    transaction_reference: str = Field(..., unique=True)
    application_id: str = Field(...)
    insurance_details_id: str | None = Field(default=None)
    selected_quote_id: str | None = Field(default=None)
    selected_addons: list[str] = Field(default_factory=list)
    base_premium: float | None = Field(default=None, ge=0)
    addon_amount: float = Field(default=0.0, ge=0)
    final_amount: float | None = Field(default=None, ge=0)
    transaction_status: TransactionStatus = Field(default=TransactionStatus.APPLICATION_SUBMITTED)
    payment_status: PaymentStatus = Field(default=PaymentStatus.NOT_INITIATED)
    policy_status: PolicyStatus = Field(default=PolicyStatus.NOT_STARTED)
    provider_transaction_reference: str | None = Field(default=None)
    provider_payment_reference: str | None = Field(default=None)
    provider_policy_reference: str | None = Field(default=None)
    checkout_metadata: dict[str, object] = Field(default_factory=dict)
    application_snapshot: ApplicationSnapshot = Field(...)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(collection="transactions", extra="forbid")

