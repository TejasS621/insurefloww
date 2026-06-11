"""Provider payment response schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ProviderPaymentResponse(BaseModel):
    """Payment session payload returned to the main backend."""

    model_config = ConfigDict(extra="forbid")

    gateway: str
    razorpay_key_id: str | None = None
    razorpay_order_id: str
    provider_payment_reference: str
    amount: float = Field(..., ge=0)
    currency: str = Field(..., min_length=3, max_length=3)

