from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from odmantic import Field, Model
from pydantic import ConfigDict


class WebhookRetryStatus(str, Enum):
    PENDING = "PENDING"
    RETRYING = "RETRYING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"


class WebhookRetry(Model):
    event_type: str = Field(...)
    main_transaction_reference: str = Field(...)
    payload: dict[str, object] = Field(default_factory=dict)
    retry_count: int = Field(default=0, ge=0)
    next_retry_at: datetime | None = Field(default=None)
    status: WebhookRetryStatus = Field(default=WebhookRetryStatus.PENDING)
    last_error: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(collection="webhook_retries", extra="forbid")
