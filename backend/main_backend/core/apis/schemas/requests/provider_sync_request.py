"""Provider sync webhook request schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ProviderWebhookPayload(BaseModel):
    """Payload received from the provider backend sync webhook."""

    model_config = ConfigDict(extra="forbid")

    event_type: str = Field(..., min_length=3, max_length=100)
    transaction_reference: str = Field(..., min_length=3, max_length=100)
    provider_payment_reference: str | None = None
    provider_policy_reference: str | None = None
    payload: dict[str, object] = Field(default_factory=dict)

