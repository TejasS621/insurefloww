"""Application routes for the main backend."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from odmantic import AIOEngine

from backend.main_backend.app.core.apis.routes.dependencies import get_optional_user_id
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
    quotes = (
        await quote_service.list_quotes_for_transaction(engine, result.transaction.transaction_reference)
        if result.transaction.transaction_reference
        else []
    )
    return APIResponse(
        message=(
            "Active application journey resumed successfully."
            if result.resumed
            else "Application created successfully."
        ),
        data=to_application_response(result.application, quotes=quotes),
    )

