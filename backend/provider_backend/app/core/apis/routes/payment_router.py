"""Payment routes for the provider backend."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from odmantic import AIOEngine

from backend.provider_backend.app.core.apis.routes._mappers import to_provider_payment_response
from backend.provider_backend.app.core.apis.schemas.requests.payment_request import (
    PaymentSessionCreateRequest,
)
from backend.provider_backend.app.core.apis.schemas.responses.common_response import APIResponse
from backend.provider_backend.app.core.apis.schemas.responses.payment_response import (
    ProviderPaymentResponse,
)
from backend.provider_backend.app.core.database.database import get_database
from backend.provider_backend.app.core.services.payment_service import provider_payment_service

payment_router = APIRouter(prefix="/api/v1/provider/payments", tags=["Provider Payments"])


@payment_router.post("/create-session", response_model=APIResponse[ProviderPaymentResponse], status_code=status.HTTP_201_CREATED)
async def create_payment_session(
    request_data: PaymentSessionCreateRequest,
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[ProviderPaymentResponse]:
    """Create a provider-owned payment order or checkout session."""
    payment = await provider_payment_service.create_payment_session(engine, request_data)
    return APIResponse(
        message="Provider payment session created successfully.",
        data=to_provider_payment_response(payment),
    )

