"""Quote routes for the provider backend."""

from __future__ import annotations

from fastapi import APIRouter, status

from backend.provider_backend.app.core.apis.routes._helpers import raise_not_implemented
from backend.provider_backend.app.core.apis.schemas.requests.provider_quote_request import (
    ProviderQuoteCreateRequest,
)
from backend.provider_backend.app.core.apis.schemas.responses.common_response import APIResponse
from backend.provider_backend.app.core.apis.schemas.responses.provider_quote_response import (
    ProviderQuoteResponse,
)

quote_router = APIRouter(prefix="/api/v1/provider/quotes", tags=["Provider Quotes"])


@quote_router.post("/generate", response_model=APIResponse[list[ProviderQuoteResponse]], status_code=status.HTTP_201_CREATED)
async def generate_quotes(
    _: ProviderQuoteCreateRequest,
) -> APIResponse[list[ProviderQuoteResponse]]:
    """Generate provider-side quotes for an application."""
    raise_not_implemented("Provider quote generation")

