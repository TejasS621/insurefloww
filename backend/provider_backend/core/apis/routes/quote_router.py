"""
Handle quote routes for the provider backend.

Args:
    None: This module defines broker-authenticated quote generation endpoints
    used by the main backend integration and provider-side testing flows.

Returns:
    None: Route handlers return structured quote responses under the
    `/api/v1/quotes` router.

Raises:
    HTTPException: Unexpected failures are normalized through the shared
    route guard before being returned to the caller.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from odmantic import AIOEngine

from backend.provider_backend.commons.logger import get_logger
from backend.provider_backend.core.apis.routes._mappers import to_provider_quote_response
from backend.provider_backend.core.apis.routes.dependencies import get_authenticated_broker
from backend.provider_backend.core.apis.schemas.requests.provider_quote_request import (
    ProviderQuoteCreateRequest,
)
from backend.provider_backend.core.apis.schemas.responses.common_response import APIResponse
from backend.provider_backend.core.apis.schemas.responses.provider_quote_response import (
    ProviderQuoteResponse,
)
from backend.provider_backend.core.database.database import get_database
from backend.provider_backend.core.services.quote_service import provider_quote_service
from backend.provider_backend.core.services.service_exceptions import ServiceError

quote_router = APIRouter(prefix="/api/v1/quotes", tags=["Provider Quotes"])
logger = get_logger(__name__)


@quote_router.post(
    "/generate",
    response_model=APIResponse[list[ProviderQuoteResponse]],
    status_code=status.HTTP_201_CREATED,
)
async def generate_quotes(
    request_data: ProviderQuoteCreateRequest,
    engine: AIOEngine = Depends(get_database),
    _: object = Depends(get_authenticated_broker),
) -> APIResponse[list[ProviderQuoteResponse]]:
    """
    Generate provider-side quotes for a broker-authenticated integration call.

    Args:
        request_data: Validated quote-generation payload supplied by the broker.
        engine: Active ODMantic database engine dependency.
        _: Authenticated broker dependency used to enforce trusted access.

    Returns:
        APIResponse[list[ProviderQuoteResponse]]: Provider quote options
        generated for the submitted application context.

    Raises:
        HTTPException: Re-raises domain validation errors or wraps unexpected
        failures as HTTP 500 responses through the route guard.
    """
    try:
        quotes = await provider_quote_service.generate_quotes(engine, request_data)
        return APIResponse(
            message="Provider quotes generated successfully.",
            data=[to_provider_quote_response(quote) for quote in quotes],
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception("Failed to generate provider quotes.")
        raise
