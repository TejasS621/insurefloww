"""Provider sync response schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ProviderWebhookSyncResponse(BaseModel):
    """Acknowledgement returned for provider sync webhooks."""

    model_config = ConfigDict(extra="forbid")

    event_type: str
    transaction_reference: str
    processing_status: str
