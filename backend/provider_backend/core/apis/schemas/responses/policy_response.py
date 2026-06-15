"""Provider policy response schemas."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, ConfigDict, Field


class ProviderPolicyResponse(BaseModel):
    """Issued policy payload returned by provider policy APIs."""

    model_config = ConfigDict(extra="forbid")

    policy_number: str
    provider_transaction_reference: str
    main_transaction_reference: str
    policy_status: str
    coverage_amount: float = Field(..., ge=0)
    premium_amount: float = Field(..., ge=0)
    issue_date: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    policy_document_url: str | None = None

