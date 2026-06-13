"""Application routes for the main backend."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from odmantic import AIOEngine

from backend.main_backend.app.core.apis.routes.dependencies import get_current_user_id, get_optional_user_id
from backend.main_backend.app.core.apis.routes._mappers import to_application_response
from backend.main_backend.app.core.apis.schemas.requests.application_request import ApplicationCreateRequest
from backend.main_backend.app.core.apis.schemas.responses.application_response import ApplicationSummaryResponse
from backend.main_backend.app.core.apis.schemas.responses.common_response import APIResponse
from backend.main_backend.app.core.database.database import get_database
from backend.main_backend.app.core.services.application_service import application_service
from backend.main_backend.app.core.services.quote_service import quote_service

application_router = APIRouter(prefix="/api/v1/applications", tags=["Applications"])


@application_router.post("", response_model=APIResponse[ApplicationSummaryResponse], status_code=status.HTTP_201_CREATED)
async def create_application(
    request_data: ApplicationCreateRequest,
    engine: AIOEngine = Depends(get_database),
    user_id: str | None = Depends(get_optional_user_id),
) -> APIResponse[ApplicationSummaryResponse]:
    """Create a new application or resume an existing active customer journey."""
    result = await application_service.create_application(
        engine,
        request_data,
        user_id=user_id,
    )
    if result.resumed:
        quotes = (
            await quote_service.list_quotes_for_transaction(engine, result.transaction.transaction_reference)
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
async def list_my_applications(
    engine: AIOEngine = Depends(get_database),
    user_id: str = Depends(get_current_user_id),
) -> APIResponse[list[ApplicationSummaryResponse]]:
    """List applications owned by the authenticated customer."""
    applications = await application_service.list_user_applications(engine, user_id=user_id)
    responses: list[ApplicationSummaryResponse] = []
    for application in applications:
        quotes = (
            await quote_service.list_quotes_for_transaction(engine, application.transaction_reference)
            if application.transaction_reference
            else []
        )
        responses.append(to_application_response(application, quotes=quotes))
    return APIResponse(
        message="Applications fetched successfully.",
        data=responses,
    )

