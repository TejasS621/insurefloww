"""Provider synchronization request schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class ProviderSyncDispatchRequest(BaseModel):
    """Request a provider-to-main synchronization for a payment reference."""

    model_config = ConfigDict(extra="forbid")

    payment_reference: str = Field(..., min_length=3, max_length=100)


class RetryProcessingRequest(BaseModel):
    """Request processing of due provider sync retry records."""

    model_config = ConfigDict(extra="forbid")

    limit: int = Field(default=20, ge=1, le=100)
