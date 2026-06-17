"""
Handle quote routes for the main backend.

Args:
    None: This module defines customer quote-selection endpoints used after
    quote generation and before payment initiation.

Returns:
    None: Route handlers return structured quote responses under
    `/api/v1/quotes`.

Raises:
    HTTPException: Unexpected failures are normalized through the shared
    route guard before being returned to the caller.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from odmantic import AIOEngine

from backend.main_backend.commons.logger import get_logger
from backend.main_backend.core.apis.routes._mappers import to_quote_response
from backend.main_backend.core.apis.routes.dependencies import get_optional_user_id
from backend.main_backend.core.apis.schemas.requests.quote_request import (
    QuoteSelectRequest,
)
from backend.main_backend.core.apis.schemas.responses.common_response import APIResponse
from backend.main_backend.core.apis.schemas.responses.quote_response import (
    NormalizedQuoteResponse,
)
from backend.main_backend.core.database.database import get_database
from backend.main_backend.core.models.application_model import Application
from backend.main_backend.core.models.quote_model import Quote
from backend.main_backend.core.services.quote_service import quote_service
from backend.main_backend.core.services.service_exceptions import (
    AuthorizationServiceError,
    NotFoundServiceError,
    ServiceError,
)

quote_router = APIRouter(prefix="/api/v1/quotes", tags=["Quotes"])
logger = get_logger(__name__)


@quote_router.post("/select/{quote_id}", response_model=APIResponse[NormalizedQuoteResponse])
async def select_quote(
    quote_id: str,
    request_data: QuoteSelectRequest,
    engine: AIOEngine = Depends(get_database),
    user_id: str | None = Depends(get_optional_user_id),
) -> APIResponse[NormalizedQuoteResponse]:
    """
    Select a quote for a guest or authenticated customer journey.

    Args:
        quote_id: Provider quote identifier selected by the customer.
        request_data: Payload containing the selected add-on codes.
        engine: Active ODMantic database engine dependency.
        user_id: Optional authenticated customer identifier for ownership checks.

    Returns:
        APIResponse[NormalizedQuoteResponse]: Selected quote details after
        pricing totals have been propagated to the transaction.

    Raises:
        HTTPException: Re-raises domain validation errors or wraps unexpected
        failures as HTTP 500 responses through the route guard.
    """
    try:
        quote_record = await engine.find_one(Quote, Quote.provider_quote_id == quote_id)
        if quote_record is None:
            raise NotFoundServiceError("The requested quote could not be found.")

        application = await engine.find_one(
            Application,
            Application.transaction_reference == quote_record.transaction_reference,
        )
        if application is None:
            raise NotFoundServiceError("The application for the requested quote could not be found.")
        if application.user_id is None and user_id is not None:
            application.user_id = user_id
            application.updated_at = datetime.now(timezone.utc)
            await engine.save(application)
        elif (
            application.user_id is not None
            and user_id is not None
            and application.user_id != user_id
        ):
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
    except ServiceError:
        raise
    except Exception:
        logger.exception("Failed to select quote %s.", quote_id)
        raise
