"""Payment response schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PaymentInitiationResponse(BaseModel):
    """Checkout payload returned to the frontend."""

    model_config = ConfigDict(extra="forbid")

    gateway: str
    provider_payment_reference: str
    gateway_order_id: str
    amount: float = Field(..., ge=0)
    currency: str = Field(..., min_length=3, max_length=3)
    metadata: dict[str, object] = Field(default_factory=dict)

