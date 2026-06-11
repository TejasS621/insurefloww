"""Payment creation request schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PaymentSessionCreateRequest(BaseModel):
    """Create a payment order or checkout session."""

    model_config = ConfigDict(extra="forbid")

    provider_transaction_reference: str = Field(..., min_length=3, max_length=100)
    main_transaction_reference: str = Field(..., min_length=3, max_length=100)
    provider_quote_id: str = Field(..., min_length=3, max_length=100)
    selected_addons: list[str] = Field(default_factory=list)
    amount: float = Field(..., gt=0)
    currency: str = Field(default="INR", min_length=3, max_length=3)

