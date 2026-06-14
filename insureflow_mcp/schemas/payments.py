"""Request and response schemas for payment tools."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class GetPaymentStatusInput(BaseModel):
    """Input accepted by the payment-status tool."""

    model_config = ConfigDict(extra="forbid")

    transaction_reference: str


class PaymentStatusOutput(BaseModel):
    """Payment status payload returned to the MCP client."""

    model_config = ConfigDict(extra="forbid")

    payment_status: str
    transaction_status: str
    payment_reference: str | None = None


class InitiatePaymentInput(BaseModel):
    """Input accepted by the payment-initiation tool."""

    model_config = ConfigDict(extra="forbid")

    transaction_reference: str
    selected_payment_method: str | None = Field(default=None, min_length=3, max_length=30)


class InitiatePaymentOutput(BaseModel):
    """Hosted payment session returned to the MCP client."""

    model_config = ConfigDict(extra="forbid")

    payment_reference: str
    payment_url: str
    amount: float
    currency: str
    available_payment_methods: list[str]
    status: str

