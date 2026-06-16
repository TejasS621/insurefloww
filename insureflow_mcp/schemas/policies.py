"""Request and response schemas for shared policy helpers."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from insureflow_mcp.schemas.common import FileMetadata


class GetPolicyInput(BaseModel):
    """Input accepted by the policy lookup helper."""

    model_config = ConfigDict(extra="forbid")

    policy_number: str = Field(..., description="Policy number to fetch from the main backend.")
    customer_access_token: str | None = Field(
        default=None,
        min_length=20,
        description=(
            "Optional customer JWT access token. "
            "If omitted, the MCP server will use the current stored customer session when available."
        ),
    )


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

    policy_number: str = Field(
        ...,
        description="Policy number whose PDF document should be downloaded.",
    )
    customer_access_token: str | None = Field(
        default=None,
        min_length=20,
        description=(
            "Optional customer JWT access token. "
            "If omitted, the MCP server will use the current stored customer session when available."
        ),
    )


class DownloadPolicyOutput(FileMetadata):
    """Downloaded policy file metadata returned to shared clients."""
