from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from odmantic import Field, Model
from pydantic import ConfigDict


class WebhookEventStatus(str, Enum):
    RECEIVED = "RECEIVED"
    PROCESSING = "PROCESSING"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class WebhookEvent(Model):
    event_type: str = Field(...)
    transaction_reference: str = Field(...)
    provider_payment_reference: str | None = Field(default=None)
    provider_policy_reference: str | None = Field(default=None)
    payload: dict[str, object] = Field(default_factory=dict)
    processing_status: WebhookEventStatus = Field(default=WebhookEventStatus.RECEIVED)
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    processed_at: datetime | None = Field(default=None)

    model_config = ConfigDict(collection="webhook_events", extra="forbid")
