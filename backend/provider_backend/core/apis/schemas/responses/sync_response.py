"""Provider synchronization response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ProviderSyncStatusResponse(BaseModel):
    """Synchronization status payload returned by provider sync APIs."""

    model_config = ConfigDict(extra="forbid")

    event_type: str
    main_transaction_reference: str
    status: str
    retry_count: int
    next_retry_at: datetime | None = None
    last_error: str | None = None
    updated_at: datetime


class RetryProcessingResponse(BaseModel):
    """Summary payload returned after processing due retry records."""

    model_config = ConfigDict(extra="forbid")

    processed_count: int
    success_count: int
    failed_count: int
    records: list[ProviderSyncStatusResponse]
