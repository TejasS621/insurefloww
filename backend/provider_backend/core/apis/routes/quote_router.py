"""Quote routes for the provider backend."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from odmantic import AIOEngine

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

quote_router = APIRouter(prefix="/api/v1/provider/quotes", tags=["Provider Quotes"])


@quote_router.post("/generate", response_model=APIResponse[list[ProviderQuoteResponse]], status_code=status.HTTP_201_CREATED)
async def generate_quotes(
    request_data: ProviderQuoteCreateRequest,
    engine: AIOEngine = Depends(get_database),
    _: object = Depends(get_authenticated_broker),
) -> APIResponse[list[ProviderQuoteResponse]]:
    """Generate provider-side quotes for an authenticated broker integration."""
    quotes = await provider_quote_service.generate_quotes(engine, request_data)
    return APIResponse(
        message="Provider quotes generated successfully.",
        data=[to_provider_quote_response(quote) for quote in quotes],
    )

