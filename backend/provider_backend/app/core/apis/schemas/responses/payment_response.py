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


class MockPaymentSessionResponse(BaseModel):
    """Frontend-ready payment session payload returned by the provider backend."""

    model_config = ConfigDict(extra="forbid")

    payment_reference: str = Field(..., description="Unique provider payment reference.")
    payment_url: str = Field(..., description="Hosted mock payment URL for redirect flow.")
    amount: float = Field(..., ge=0, description="Amount payable through the hosted payment page.")
    currency: str = Field(..., min_length=3, max_length=3, description="Currency code for checkout.")
    available_payment_methods: list[str] = Field(
        default_factory=list,
        description="Payment methods displayed to the customer on the hosted page.",
    )
    status: str = Field(..., description="Hosted payment session lifecycle status.")

