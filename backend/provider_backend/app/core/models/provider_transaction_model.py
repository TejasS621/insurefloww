from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from odmantic import Field, Model
from pydantic import ConfigDict

from .shared import InsuranceType


class ProviderTransactionStatus(str, Enum):
    QUOTE_REQUESTED = "QUOTE_REQUESTED"
    QUOTE_GENERATED = "QUOTE_GENERATED"
    PAYMENT_PENDING = "PAYMENT_PENDING"
    PAYMENT_SUCCESS = "PAYMENT_SUCCESS"
    PAYMENT_FAILED = "PAYMENT_FAILED"
    POLICY_ISSUED = "POLICY_ISSUED"
    FAILED = "FAILED"


class ProviderTransaction(Model):
    provider_transaction_reference: str = Field(..., unique=True)
    main_transaction_reference: str = Field(...)
    provider_code: str = Field(...)
    broker_code: str = Field(...)
    application_reference: str = Field(...)
    insurance_type: InsuranceType = Field(...)
    quote_reference: str | None = Field(default=None)
    payment_reference: str | None = Field(default=None)
    policy_reference: str | None = Field(default=None)
    gateway_order_id: str | None = Field(default=None)
    gateway_payment_id: str | None = Field(default=None)
    execution_status: ProviderTransactionStatus = Field(default=ProviderTransactionStatus.QUOTE_REQUESTED)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(collection="provider_transactions", extra="forbid")

