"""
Handle customer application routes for the main backend.

Args:
    None: This module defines the router and handlers for application
    creation and customer application lookup.

Returns:
    None: Route handlers return structured API responses for application
    workflows under `/api/v1/applications`.

Raises:
    HTTPException: Route handlers re-raise handled controller errors and
    normalize unexpected failures through the shared route guard.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from odmantic import AIOEngine

from backend.main_backend.core.apis.routes._helpers import route_guard
from backend.main_backend.core.apis.routes._mappers import to_application_response
from backend.main_backend.core.apis.routes.dependencies import (
    get_current_user_id,
    get_optional_user_id,
)
from backend.main_backend.core.apis.schemas.requests.application_request import (
    ApplicationCreateRequest,
)
from backend.main_backend.core.apis.schemas.responses.application_response import (
    ApplicationSummaryResponse,
)
from backend.main_backend.core.apis.schemas.responses.common_response import APIResponse
from backend.main_backend.core.database.database import get_database
from backend.main_backend.core.services.application_service import application_service
from backend.main_backend.core.services.quote_service import quote_service

application_router = APIRouter(prefix="/api/v1/applications", tags=["Applications"])


@application_router.post(
    "",
    response_model=APIResponse[ApplicationSummaryResponse],
    status_code=status.HTTP_201_CREATED,
)
@route_guard
async def create_application(
    request_data: ApplicationCreateRequest,
    engine: AIOEngine = Depends(get_database),
    user_id: str | None = Depends(get_optional_user_id),
) -> APIResponse[ApplicationSummaryResponse]:
    """
    Create a new customer application or resume an active application journey.

    Args:
        request_data: Validated application payload from ApplicationCreateRequest.
        engine: Active ODMantic database engine dependency.
        user_id: Optional authenticated customer identifier for linking records.

    Returns:
        APIResponse[ApplicationSummaryResponse]: Created or resumed application
        details along with the generated quotes for the journey.

    Raises:
        HTTPException: Re-raises controller validation errors or wraps
        unexpected exceptions as HTTP 500 responses through the route guard.
    """
    result = await application_service.create_application(
        engine,
        request_data,
        user_id=user_id,
    )
    if result.resumed:
        quotes = (
            await quote_service.list_quotes_for_transaction(
                engine, result.transaction.transaction_reference
            )
            if result.transaction.transaction_reference
            else []
        )
        if not quotes:
            quotes = await quote_service.request_and_store_quotes_for_application(
                engine,
                application=result.application,
                transaction=result.transaction,
                request_data=request_data,
            )
    else:
        quotes = await quote_service.request_and_store_quotes_for_application(
            engine,
            application=result.application,
            transaction=result.transaction,
            request_data=request_data,
        )
    return APIResponse(
        message=(
            "Active application journey resumed successfully."
            if result.resumed
            else "Application created successfully."
        ),
        data=to_application_response(result.application, quotes=quotes),
    )


@application_router.get("/me", response_model=APIResponse[list[ApplicationSummaryResponse]])
@route_guard
async def list_my_applications(
    engine: AIOEngine = Depends(get_database),
    user_id: str = Depends(get_current_user_id),
) -> APIResponse[list[ApplicationSummaryResponse]]:
    """
    List all applications owned by the authenticated customer.

    Args:
        engine: Active ODMantic database engine dependency.
        user_id: Authenticated customer identifier resolved from JWT context.

    Returns:
        APIResponse[list[ApplicationSummaryResponse]]: Application summaries
        enriched with quotes for the authenticated user.

    Raises:
        HTTPException: Re-raises controller validation errors or wraps
        unexpected exceptions as HTTP 500 responses through the route guard.
    """
    applications = await application_service.list_user_applications(
        engine, user_id=user_id
    )
    responses: list[ApplicationSummaryResponse] = []
    for application in applications:
        quotes = (
            await quote_service.list_quotes_for_transaction(
                engine, application.transaction_reference
            )
            if application.transaction_reference
            else []
        )
        responses.append(to_application_response(application, quotes=quotes))
    return APIResponse(
        message="Applications fetched successfully.",
        data=responses,
    )
