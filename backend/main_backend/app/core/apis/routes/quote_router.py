"""Quote routes for the main backend."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from odmantic import AIOEngine

from backend.main_backend.app.core.apis.routes._mappers import to_quote_response
from backend.main_backend.app.core.apis.routes.dependencies import get_current_user_id
from backend.main_backend.app.core.apis.schemas.requests.quote_request import QuoteSelectRequest
from backend.main_backend.app.core.apis.schemas.responses.common_response import APIResponse
from backend.main_backend.app.core.apis.schemas.responses.quote_response import NormalizedQuoteResponse
from backend.main_backend.app.core.database.database import get_database
from backend.main_backend.app.core.models.application_model import Application
from backend.main_backend.app.core.models.quote_model import Quote
from datetime import datetime, timezone

from backend.main_backend.app.core.services.service_exceptions import AuthorizationServiceError, NotFoundServiceError
from backend.main_backend.app.core.services.quote_service import quote_service

quote_router = APIRouter(prefix="/api/v1/quotes", tags=["Quotes"])


@quote_router.post("/select/{quote_id}", response_model=APIResponse[NormalizedQuoteResponse])
async def select_quote(
    quote_id: str,
    request_data: QuoteSelectRequest,
    engine: AIOEngine = Depends(get_database),
    user_id: str = Depends(get_current_user_id),
) -> APIResponse[NormalizedQuoteResponse]:
    """Select a quote for the authenticated customer and update pricing totals."""
    quote_record = await engine.find_one(Quote, Quote.provider_quote_id == quote_id)
    if quote_record is None:
        raise NotFoundServiceError("The requested quote could not be found.")

    application = await engine.find_one(
        Application,
        Application.transaction_reference == quote_record.transaction_reference,
    )
    if application is None:
        raise NotFoundServiceError("The application for the requested quote could not be found.")
    if application.user_id is None:
        application.user_id = user_id
        application.updated_at = datetime.now(timezone.utc)
        await engine.save(application)
    elif application.user_id != user_id:
        raise AuthorizationServiceError("You are not allowed to select this quote.")

    quote = await quote_service.select_quote(
        engine,
        quote_id=quote_id,
        selected_addons=request_data.selected_addons,
    )
    return APIResponse(
        message="Quote selected successfully.",
        data=to_quote_response(quote),
    )
