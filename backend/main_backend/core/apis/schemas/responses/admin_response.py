"""Admin response schemas."""

from __future__ import annotations

from datetime import date, datetime

from pydantic import BaseModel, ConfigDict, Field


class BrokerRegistryResponse(BaseModel):
    """Broker registry payload returned by admin broker APIs."""

    model_config = ConfigDict(extra="forbid")

    broker_code: str
    broker_name: str
    company_name: str | None = None
    license_number: str | None = None
    registration_number: str | None = None
    contact_person_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    supported_insurance_types: list[str] = Field(default_factory=list)
    active_regions: list[str] = Field(default_factory=list)
    partner_provider_codes: list[str] = Field(default_factory=list)
    notes: str | None = None
    status: str
    created_by_admin: str | None = None
    api_key: str | None = None
    last_key_rotated_at: datetime | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None


class ProviderRegistryResponse(BaseModel):
    """Provider registry payload returned by admin provider APIs."""

    model_config = ConfigDict(extra="forbid")

    provider_code: str
    provider_name: str
    company_name: str | None = None
    contact_email: str
    contact_phone: str
    supported_insurance_types: list[str] = Field(default_factory=list)
    supported_regions: list[str] = Field(default_factory=list)
    serviceable_products: list[str] = Field(default_factory=list)
    notes: str | None = None
    status: str
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


class AdminTransactionResponse(BaseModel):
    """Transaction payload returned by admin transaction inspection APIs."""

    model_config = ConfigDict(extra="forbid")

    transaction_reference: str
    customer_name: str
    insurance_type: str
    amount: float = Field(..., ge=0)
    status: str
    payment_status: str
    policy_status: str
    user_id: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    date: str | None = None


class AdminTransactionDetailResponse(AdminTransactionResponse):
    """Detailed transaction payload returned for admin side drawers."""

    application_reference: str | None = None
    selected_quote_id: str | None = None
    selected_addons: list[str] = Field(default_factory=list)
    base_premium: float | None = Field(default=None, ge=0)
    addon_amount: float = Field(default=0, ge=0)
    final_amount: float | None = Field(default=None, ge=0)
    provider_transaction_reference: str | None = None
    provider_payment_reference: str | None = None
    provider_policy_reference: str | None = None


class AdminPaymentResponse(BaseModel):
    """Payment payload returned by admin payment monitoring APIs."""

    model_config = ConfigDict(extra="forbid")

    payment_reference: str
    transaction_reference: str
    gateway: str
    amount: float = Field(..., ge=0)
    currency: str
    status: str
    provider_transaction_reference: str | None = None
    created_at: datetime | None = None
    updated_at: datetime | None = None
    date: str | None = None


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

