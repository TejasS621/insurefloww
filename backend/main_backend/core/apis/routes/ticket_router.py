"""Support ticket routes for the main backend."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from odmantic import AIOEngine

from backend.main_backend.core.apis.routes._mappers import to_ticket_response
from backend.main_backend.core.apis.routes.dependencies import get_current_user_id
from backend.main_backend.core.apis.schemas.requests.ticket_request import TicketCreateRequest
from backend.main_backend.core.apis.schemas.responses.common_response import APIResponse
from backend.main_backend.core.apis.schemas.responses.ticket_response import TicketResponse
from backend.main_backend.core.database.database import get_database
from backend.main_backend.core.services.ticket_service import ticket_service

ticket_router = APIRouter(prefix="/api/v1/tickets", tags=["Tickets"])


@ticket_router.post("", response_model=APIResponse[TicketResponse], status_code=status.HTTP_201_CREATED)
async def create_ticket(
    request_data: TicketCreateRequest,
    engine: AIOEngine = Depends(get_database),
    user_id: str = Depends(get_current_user_id),
) -> APIResponse[TicketResponse]:
    """Create a new customer support ticket for the supplied user context."""
    ticket = await ticket_service.create_ticket(
        engine,
        user_id=user_id,
        request_data=request_data,
    )
    return APIResponse(
        message="Ticket created successfully.",
        data=to_ticket_response(ticket),
    )


@ticket_router.get("/me", response_model=APIResponse[list[TicketResponse]])
async def list_my_tickets(
    engine: AIOEngine = Depends(get_database),
    user_id: str = Depends(get_current_user_id),
) -> APIResponse[list[TicketResponse]]:
    """List support tickets raised by the supplied user context."""
    tickets = await ticket_service.list_user_tickets(engine, user_id=user_id)
    return APIResponse(
        message="Tickets fetched successfully.",
        data=[to_ticket_response(ticket) for ticket in tickets],
    )

