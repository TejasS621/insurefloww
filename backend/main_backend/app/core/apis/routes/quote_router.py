"""Quote routes for the main backend."""

from __future__ import annotations

from fastapi import APIRouter

from backend.main_backend.app.core.apis.routes._helpers import raise_not_implemented
from backend.main_backend.app.core.apis.schemas.requests.quote_request import QuoteSelectRequest
from backend.main_backend.app.core.apis.schemas.responses.common_response import APIResponse
from backend.main_backend.app.core.apis.schemas.responses.quote_response import NormalizedQuoteResponse

quote_router = APIRouter(prefix="/api/v1/quotes", tags=["Quotes"])


@quote_router.post("/select/{quote_id}", response_model=APIResponse[NormalizedQuoteResponse])
async def select_quote(quote_id: str, _: QuoteSelectRequest) -> APIResponse[NormalizedQuoteResponse]:
    """Select a quote and persist add-on choices."""
    raise_not_implemented("Quote selection")
