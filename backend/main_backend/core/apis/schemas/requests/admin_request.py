"""Admin request schemas for broker and operations workflows."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class BrokerStatus(str, Enum):
    """Broker lifecycle states exposed to admin APIs."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class BrokerRegistrationRequest(BaseModel):
    """Register a broker through the admin API."""

    model_config = ConfigDict(extra="forbid")

    broker_name: str = Field(..., min_length=2, max_length=120)
    broker_code: str = Field(..., min_length=2, max_length=50)
    company_name: str | None = Field(default=None, min_length=2, max_length=160)
    license_number: str | None = Field(default=None, max_length=80)
    registration_number: str | None = Field(default=None, max_length=80)
    contact_person_name: str | None = Field(default=None, min_length=2, max_length=120)
    contact_email: EmailStr | None = None
    contact_phone: str | None = Field(default=None, min_length=10, max_length=15)
    supported_insurance_types: list[str] = Field(default_factory=list)
    active_regions: list[str] = Field(default_factory=list)
    partner_provider_codes: list[str] = Field(default_factory=list)
    notes: str | None = Field(default=None, max_length=1000)


class BrokerStatusUpdateRequest(BaseModel):
    """Change the status of an existing broker."""

    model_config = ConfigDict(extra="forbid")

    status: BrokerStatus
    reason: str | None = Field(default=None, max_length=500)


class BrokerKeyRotationRequest(BaseModel):
    """Trigger API key rotation for a broker."""

    model_config = ConfigDict(extra="forbid")

    initiated_by: str | None = Field(default=None, max_length=120)
    reason: str | None = Field(default=None, max_length=500)


class ProviderStatus(str, Enum):
    """Provider lifecycle states exposed to admin APIs."""

    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    SUSPENDED = "SUSPENDED"


class ProviderRegistrationRequest(BaseModel):
    """Register a provider through the admin API."""

    model_config = ConfigDict(extra="forbid")

    provider_name: str = Field(..., min_length=2, max_length=120)
    provider_code: str = Field(..., min_length=2, max_length=50)
    company_name: str | None = Field(default=None, min_length=2, max_length=160)
    contact_email: EmailStr
    contact_phone: str = Field(..., min_length=10, max_length=15)
    supported_insurance_types: list[str] = Field(default_factory=list)
    supported_regions: list[str] = Field(default_factory=list)
    serviceable_products: list[str] = Field(default_factory=list)
    notes: str | None = Field(default=None, max_length=1000)


class ProviderStatusUpdateRequest(BaseModel):
    """Change the status of an existing provider."""

    model_config = ConfigDict(extra="forbid")

    status: ProviderStatus
    reason: str | None = Field(default=None, max_length=500)


class TicketStatusValue(str, Enum):
    """Ticket statuses that an admin can assign."""

    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class TicketAssignmentRequest(BaseModel):
    """Assign a support ticket to an admin owner."""

    model_config = ConfigDict(extra="forbid")

    assigned_admin_id: str = Field(
        ...,
        min_length=2,
        max_length=120,
        description="Admin identifier that will own the ticket.",
    )
    assignment_note: str | None = Field(
        default=None,
        max_length=500,
        description="Optional internal note captured during ticket assignment.",
    )


class TicketStatusUpdateRequest(BaseModel):
    """Update the lifecycle state of a support ticket."""

    model_config = ConfigDict(extra="forbid")

    status: TicketStatusValue = Field(..., description="New status assigned to the ticket.")
    admin_response: str | None = Field(
        default=None,
        max_length=4000,
        description="Optional customer-facing response from the admin team.",
    )


class ApplicationReviewDecision(str, Enum):
    """High-level decisions available during application review."""

    APPROVE = "APPROVE"
    REJECT = "REJECT"
    CANCEL = "CANCEL"


class ApplicationReviewRequest(BaseModel):
    """Review a customer application and update its status."""

    model_config = ConfigDict(extra="forbid")

    decision: ApplicationReviewDecision = Field(..., description="Admin decision for the application.")
    reason: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional explanation captured in audit logs.",
    )


class UnderwritingDecision(str, Enum):
    """Manual underwriting decisions available to admin reviewers."""

    APPROVE = "APPROVE"
    REJECT = "REJECT"


class UnderwritingReviewRequest(BaseModel):
    """Apply a manual underwriting decision to a queued application."""

    model_config = ConfigDict(extra="forbid")

    decision: UnderwritingDecision = Field(..., description="Manual underwriting outcome.")
    notes: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional reviewer notes recorded in the audit log.",
    )


class PolicyAdminStatus(str, Enum):
    """Policy statuses that can be applied through admin management flows."""

    ISSUED = "ISSUED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class PolicyStatusUpdateRequest(BaseModel):
    """Update a policy lifecycle state through the admin API."""

    model_config = ConfigDict(extra="forbid")

    status: PolicyAdminStatus = Field(..., description="New policy status applied by the admin team.")
    reason: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional explanation captured in audit logs.",
    )

