"""Support ticket response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TicketResponse(BaseModel):
    """Ticket payload returned to customers and admins."""

    model_config = ConfigDict(extra="forbid")

    ticket_reference: str
    transaction_reference: str | None = None
    category: str
    priority: str
    status: str
    subject: str
    message: str
    admin_response: str | None = None
    created_at: datetime
    updated_at: datetime

