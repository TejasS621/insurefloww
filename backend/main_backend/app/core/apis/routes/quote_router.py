"""Quote routes for the main backend."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from odmantic import AIOEngine

from backend.main_backend.app.core.apis.routes._mappers import to_quote_response
from backend.main_backend.app.core.apis.schemas.requests.quote_request import QuoteSelectRequest
from backend.main_backend.app.core.apis.schemas.responses.common_response import APIResponse
from backend.main_backend.app.core.apis.schemas.responses.quote_response import NormalizedQuoteResponse
from backend.main_backend.app.core.database.database import get_database
from backend.main_backend.app.core.services.quote_service import quote_service

quote_router = APIRouter(prefix="/api/v1/quotes", tags=["Quotes"])


@quote_router.post("/select/{quote_id}", response_model=APIResponse[NormalizedQuoteResponse])
async def select_quote(
    quote_id: str,
    request_data: QuoteSelectRequest,
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[NormalizedQuoteResponse]:
    """Select a quote, store chosen add-ons, and update transaction pricing."""
    quote = await quote_service.select_quote(
        engine,
        quote_id=quote_id,
        selected_addons=request_data.selected_addons,
    )
    return APIResponse(
        message="Quote selected successfully.",
        data=to_quote_response(quote),
    )
