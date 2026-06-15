from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from odmantic import Field, Model
from pydantic import ConfigDict


class GatewayName(str, Enum):
    RAZORPAY = "RAZORPAY"
    MOCK = "MOCK"


class PaymentStatus(str, Enum):
    CREATED = "CREATED"
    PENDING = "PENDING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class Payment(Model):
    payment_reference: str = Field(..., unique=True)
    provider_transaction_reference: str = Field(...)
    main_transaction_reference: str = Field(...)
    gateway_name: GatewayName = Field(default=GatewayName.RAZORPAY)
    gateway_order_id: str | None = Field(default=None)
    gateway_payment_id: str | None = Field(default=None)
    gateway_signature: str | None = Field(default=None)
    amount: float = Field(..., ge=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    payment_status: PaymentStatus = Field(default=PaymentStatus.CREATED)
    receipt_pdf_path: str | None = Field(default=None)
    receipt_document_url: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(collection="payments", extra="forbid")

