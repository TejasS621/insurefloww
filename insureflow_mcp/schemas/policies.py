"""Request and response schemas for shared policy helpers."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from insureflow_mcp.schemas.common import FileMetadata


class GetPolicyInput(BaseModel):
    """Input accepted by the policy lookup helper."""

    model_config = ConfigDict(extra="forbid")

    policy_number: str


class PolicyOutput(BaseModel):
    """Policy details returned to shared clients."""

    model_config = ConfigDict(extra="forbid")

    policy_number: str
    transaction_reference: str
    policy_status: str
    coverage_amount: float
    premium_amount: float
    issue_date: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    policy_document_url: str | None = None


class DownloadPolicyInput(BaseModel):
    """Input accepted by the policy-download helper."""

    model_config = ConfigDict(extra="forbid")

    policy_number: str


class DownloadPolicyOutput(FileMetadata):
    """Downloaded policy file metadata returned to shared clients."""
