"""
Handle support-ticket routes for the main backend.

Args:
    None: This module defines customer ticket-creation and ticket-listing
    endpoints under the versioned ticket router.

Returns:
    None: Route handlers return structured support-ticket responses.

Raises:
    HTTPException: Route handlers re-raise handled controller errors and
    normalize unexpected failures through the shared route guard.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from odmantic import AIOEngine

from backend.main_backend.core.apis.routes._helpers import route_guard
from backend.main_backend.core.apis.routes._mappers import to_ticket_response
from backend.main_backend.core.apis.routes.dependencies import get_current_user_id
from backend.main_backend.core.apis.schemas.requests.ticket_request import (
    TicketCreateRequest,
)
from backend.main_backend.core.apis.schemas.responses.common_response import APIResponse
from backend.main_backend.core.apis.schemas.responses.ticket_response import (
    TicketResponse,
)
from backend.main_backend.core.database.database import get_database
from backend.main_backend.core.services.ticket_service import ticket_service

ticket_router = APIRouter(prefix="/api/v1/tickets", tags=["Tickets"])


@ticket_router.post(
    "",
    response_model=APIResponse[TicketResponse],
    status_code=status.HTTP_201_CREATED,
)
@route_guard
async def create_ticket(
    request_data: TicketCreateRequest,
    engine: AIOEngine = Depends(get_database),
    user_id: str = Depends(get_current_user_id),
) -> APIResponse[TicketResponse]:
    """
    Create a new customer support ticket.

    Args:
        request_data: Validated support-ticket payload from TicketCreateRequest.
        engine: Active ODMantic database engine dependency.
        user_id: Authenticated customer identifier used as the ticket owner.

    Returns:
        APIResponse[TicketResponse]: Newly created support-ticket response.

    Raises:
        HTTPException: Re-raises domain validation errors or wraps unexpected
        failures as HTTP 500 responses through the route guard.
    """
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
@route_guard
async def list_my_tickets(
    engine: AIOEngine = Depends(get_database),
    user_id: str = Depends(get_current_user_id),
) -> APIResponse[list[TicketResponse]]:
    """
    List support tickets created by the authenticated customer.

    Args:
        engine: Active ODMantic database engine dependency.
        user_id: Authenticated customer identifier used for ownership lookup.

    Returns:
        APIResponse[list[TicketResponse]]: Support tickets owned by the user.

    Raises:
        HTTPException: Re-raises domain validation errors or wraps unexpected
        failures as HTTP 500 responses through the route guard.
    """
    tickets = await ticket_service.list_user_tickets(engine, user_id=user_id)
    return APIResponse(
        message="Tickets fetched successfully.",
        data=[to_ticket_response(ticket) for ticket in tickets],
    )
