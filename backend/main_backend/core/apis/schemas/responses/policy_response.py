"""Policy response schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class PolicySummaryResponse(BaseModel):
    """Policy summary returned to customers."""

    model_config = ConfigDict(extra="forbid")

    policy_number: str
    transaction_reference: str
    policy_status: str
    coverage_amount: float = Field(..., ge=0)
    premium_amount: float = Field(..., ge=0)
    issue_date: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    document_url: str | None = None
    created_at: datetime | None = None

