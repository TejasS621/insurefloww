"""Request and response schemas for shared support ticket helpers."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CreateTicketInput(BaseModel):
    """Input accepted by the ticket-creation helper."""

    model_config = ConfigDict(extra="forbid")

    customer_access_token: str = Field(
        ...,
        min_length=20,
        description="Customer JWT access token required by the authenticated ticket endpoint.",
    )
    transaction_reference: str | None = Field(
        default=None,
        description="Optional transaction reference if the support ticket is tied to a policy journey.",
    )
    category: str = Field(
        default="GENERAL",
        description="Ticket category such as CLAIM, PAYMENT, POLICY, or GENERAL.",
    )
    priority: str = Field(
        default="MEDIUM",
        description="Ticket priority such as LOW, MEDIUM, or HIGH.",
    )
    subject: str = Field(
        ...,
        min_length=3,
        max_length=120,
        description="Short subject summarizing the support request.",
    )
    message: str = Field(
        ...,
        min_length=5,
        max_length=4000,
        description="Detailed customer message describing the support issue.",
    )


class TicketOutput(BaseModel):
    """Ticket payload returned to shared clients."""

    model_config = ConfigDict(extra="forbid")

    ticket_reference: str
    transaction_reference: str | None = None
    category: str
    priority: str
    status: str
    subject: str
    message: str
    admin_response: str | None = None
    created_at: str
    updated_at: str
