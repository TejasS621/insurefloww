from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from odmantic import Field, Model
from pydantic import ConfigDict


class PolicyStatus(str, Enum):
    PENDING = "PENDING"
    ISSUED = "ISSUED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class Policy(Model):
    policy_number: str = Field(..., unique=True)
    provider_transaction_reference: str = Field(...)
    main_transaction_reference: str = Field(...)
    payment_reference: str = Field(...)
    provider_quote_id: str = Field(...)
    policy_status: PolicyStatus = Field(default=PolicyStatus.PENDING)
    coverage_amount: float = Field(..., ge=0)
    premium_amount: float = Field(..., ge=0)
    issue_date: datetime | None = Field(default=None)
    start_date: datetime | None = Field(default=None)
    end_date: datetime | None = Field(default=None)
    policy_pdf_path: str | None = Field(default=None)
    policy_document_url: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(collection="policies", extra="forbid")

