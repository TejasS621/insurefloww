"""Payment response schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PaymentInitiationResponse(BaseModel):
    """Checkout payload returned to the frontend."""

    model_config = ConfigDict(extra="forbid")

    payment_reference: str = Field(..., description="Unique payment reference returned by the provider backend.")
    payment_url: str = Field(..., description="Hosted mock payment URL that the frontend can redirect to.")
    amount: float = Field(..., ge=0, description="Amount payable by the customer.")
    currency: str = Field(..., min_length=3, max_length=3, description="Currency code for the payment.")
    available_payment_methods: list[str] = Field(
        default_factory=list,
        description="Payment methods displayed to the customer on the hosted payment page.",
    )
    status: str = Field(..., description="Current status for the hosted payment session.")

