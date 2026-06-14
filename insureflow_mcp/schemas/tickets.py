"""Request and response schemas for support ticket tools."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class CreateTicketInput(BaseModel):
    """Input accepted by the ticket-creation tool."""

    model_config = ConfigDict(extra="forbid")

    transaction_reference: str | None = None
    category: str = "GENERAL"
    priority: str = "MEDIUM"
    subject: str = Field(..., min_length=3, max_length=120)
    message: str = Field(..., min_length=5, max_length=4000)


class TicketOutput(BaseModel):
    """Ticket payload returned to the MCP client."""

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

