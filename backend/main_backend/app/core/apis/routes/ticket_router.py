"""Support ticket routes for the main backend."""

from __future__ import annotations

from fastapi import APIRouter, status

from backend.main_backend.app.core.apis.routes._helpers import raise_not_implemented
from backend.main_backend.app.core.apis.schemas.requests.ticket_request import TicketCreateRequest
from backend.main_backend.app.core.apis.schemas.responses.common_response import APIResponse
from backend.main_backend.app.core.apis.schemas.responses.ticket_response import TicketResponse

ticket_router = APIRouter(prefix="/api/v1/tickets", tags=["Tickets"])


@ticket_router.post("", response_model=APIResponse[TicketResponse], status_code=status.HTTP_201_CREATED)
async def create_ticket(_: TicketCreateRequest) -> APIResponse[TicketResponse]:
    """Create a new customer support ticket."""
    raise_not_implemented("Ticket creation")


@ticket_router.get("/me", response_model=APIResponse[list[TicketResponse]])
async def list_my_tickets() -> APIResponse[list[TicketResponse]]:
    """List tickets raised by the authenticated customer."""
    raise_not_implemented("List customer tickets")

