"""Payment initiation request schemas for the main backend."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class PaymentInitiationRequest(BaseModel):
    """Create a customer-facing payment session for a selected quote."""

    model_config = ConfigDict(extra="forbid")

    selected_payment_method: str | None = Field(
        default=None,
        min_length=3,
        max_length=30,
        description="Optional payment method preselected by the frontend.",
    )
