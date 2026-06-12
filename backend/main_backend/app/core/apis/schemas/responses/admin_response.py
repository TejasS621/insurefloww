"""Admin response schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class BrokerRegistryResponse(BaseModel):
    """Broker registry payload returned by admin broker APIs."""

    model_config = ConfigDict(extra="forbid")

    broker_code: str
    broker_name: str
    callback_url: str
    webhook_url: str
    status: str
    created_by_admin: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AdminTicketResponse(BaseModel):
    """Support ticket payload returned by admin ticket workflows."""

    model_config = ConfigDict(extra="forbid")

    ticket_reference: str
    user_id: str
    transaction_reference: str | None = None
    category: str
    priority: str
    status: str
    subject: str
    message: str
    assigned_admin_id: str | None = None
    admin_response: str | None = None
    created_at: datetime
    updated_at: datetime


class AdminApplicationResponse(BaseModel):
    """Application payload returned by admin application workflows."""

    model_config = ConfigDict(extra="forbid")

    application_reference: str
    user_id: str | None = None
    transaction_reference: str | None = None
    insurance_type: str
    application_status: str
    applicant_name: str
    email: str
    mobile_number: str
    created_at: datetime
    updated_at: datetime


class UnderwritingReviewResponse(BaseModel):
    """Admin view of an application awaiting or undergoing underwriting review."""

    model_config = ConfigDict(extra="forbid")

    application_reference: str
    transaction_reference: str | None = None
    insurance_type: str
    application_status: str
    risk_flags: list[str] = Field(default_factory=list)
    highest_quote_risk_category: str | None = None
    created_at: datetime
    updated_at: datetime


class AdminPolicyResponse(BaseModel):
    """Policy payload returned by admin policy management workflows."""

    model_config = ConfigDict(extra="forbid")

    policy_number: str
    transaction_reference: str
    payment_reference: str
    policy_status: str
    coverage_amount: float = Field(..., ge=0)
    premium_amount: float = Field(..., ge=0)
    issue_date: date | None = None
    start_date: date | None = None
    end_date: date | None = None
    document_url: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class StatusCountResponse(BaseModel):
    """Count grouped by status for dashboard statistics."""

    model_config = ConfigDict(extra="forbid")

    status: str
    count: int = Field(..., ge=0)


class DashboardStatisticsResponse(BaseModel):
    """High-level metrics returned by the admin dashboard endpoint."""

    model_config = ConfigDict(extra="forbid")

    total_applications: int = Field(..., ge=0)
    total_tickets: int = Field(..., ge=0)
    total_policies: int = Field(..., ge=0)
    total_brokers: int = Field(..., ge=0)
    total_audit_logs: int = Field(..., ge=0)
    pending_underwriting_reviews: int = Field(..., ge=0)
    application_status_breakdown: list[StatusCountResponse] = Field(default_factory=list)
    ticket_status_breakdown: list[StatusCountResponse] = Field(default_factory=list)
    policy_status_breakdown: list[StatusCountResponse] = Field(default_factory=list)
    broker_status_breakdown: list[StatusCountResponse] = Field(default_factory=list)


class AuditLogResponse(BaseModel):
    """Audit-log payload returned by admin audit inspection workflows."""

    model_config = ConfigDict(extra="forbid")

    actor_id: str | None = None
    actor_role: str | None = None
    action: str
    entity_type: str
    entity_id: str
    transaction_reference: str | None = None
    old_state: dict[str, object] | None = None
    new_state: dict[str, object] | None = None
    created_at: datetime

