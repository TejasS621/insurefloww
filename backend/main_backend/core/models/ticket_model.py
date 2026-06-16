"""Support ticket persistence models for customer service workflows."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from odmantic import Field, Model
from pydantic import ConfigDict


class TicketCategory(str, Enum):
    GENERAL = "GENERAL"
    QUOTE = "QUOTE"
    PAYMENT = "PAYMENT"
    POLICY = "POLICY"
    TECHNICAL = "TECHNICAL"


class TicketPriority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TicketStatus(str, Enum):
    OPEN = "OPEN"
    IN_PROGRESS = "IN_PROGRESS"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"


class Ticket(Model):
    ticket_reference: str = Field(..., unique=True)
    user_id: str = Field(...)
    transaction_reference: str | None = Field(default=None)
    category: TicketCategory = Field(default=TicketCategory.GENERAL)
    priority: TicketPriority = Field(default=TicketPriority.MEDIUM)
    status: TicketStatus = Field(default=TicketStatus.OPEN)
    subject: str = Field(..., min_length=3)
    message: str = Field(..., min_length=3)
    assigned_admin_id: str | None = Field(default=None)
    admin_response: str | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(collection="tickets", extra="forbid")

