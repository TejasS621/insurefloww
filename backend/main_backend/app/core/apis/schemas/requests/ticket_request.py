"""Support ticket request schemas."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class TicketCategory(str, Enum):
    """Ticket categories exposed via the public API."""

    GENERAL = "GENERAL"
    QUOTE = "QUOTE"
    PAYMENT = "PAYMENT"
    POLICY = "POLICY"
    TECHNICAL = "TECHNICAL"


class TicketPriority(str, Enum):
    """Priority levels for ticket creation."""

    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class TicketCreateRequest(BaseModel):
    """Create a new customer support ticket."""

    model_config = ConfigDict(extra="forbid")

    transaction_reference: str | None = None
    category: TicketCategory = TicketCategory.GENERAL
    priority: TicketPriority = TicketPriority.MEDIUM
    subject: str = Field(..., min_length=3, max_length=120)
    message: str = Field(..., min_length=5, max_length=4000)

