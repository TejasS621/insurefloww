"""Support ticket services for the main backend."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone

from odmantic import AIOEngine

from backend.main_backend.core.apis.schemas.requests.ticket_request import TicketCreateRequest
from backend.main_backend.core.models.ticket_model import Ticket

from .service_exceptions import ValidationServiceError


class TicketService:
    """Create and retrieve support tickets."""

    async def create_ticket(
        self,
        engine: AIOEngine,
        *,
        user_id: str,
        request_data: TicketCreateRequest,
    ) -> Ticket:
        """Persist a customer support ticket."""
        if not user_id.strip():
            raise ValidationServiceError("A valid user identifier is required to create a ticket.")

        ticket = Ticket(
            ticket_reference=self._generate_ticket_reference(),
            user_id=user_id,
            transaction_reference=request_data.transaction_reference,
            category=request_data.category.value,
            priority=request_data.priority.value,
            subject=request_data.subject,
            message=request_data.message,
        )
        await engine.save(ticket)
        return ticket

    async def list_user_tickets(
        self,
        engine: AIOEngine,
        *,
        user_id: str,
    ) -> list[Ticket]:
        """Return all tickets owned by a user."""
        if not user_id.strip():
            raise ValidationServiceError("A valid user identifier is required.")
        return await engine.find(Ticket, Ticket.user_id == user_id)

    @staticmethod
    def _generate_ticket_reference() -> str:
        """Generate a ticket reference value suitable for customer support flows."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        random_part = secrets.token_hex(3).upper()
        return f"TKT-{timestamp}-{random_part}"


ticket_service = TicketService()

