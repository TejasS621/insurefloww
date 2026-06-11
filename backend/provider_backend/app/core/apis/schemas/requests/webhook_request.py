"""Webhook request schemas for the provider backend."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PaymentSuccessWebhookRequest(BaseModel):
    """Payment gateway success callback payload."""

    model_config = ConfigDict(extra="forbid")

    gateway_order_id: str = Field(..., min_length=3, max_length=100)
    gateway_payment_id: str = Field(..., min_length=3, max_length=100)
    gateway_signature: str = Field(..., min_length=8, max_length=500)
    payload: dict[str, object] = Field(default_factory=dict)

