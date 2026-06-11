"""Payment routes for the provider backend."""

from __future__ import annotations

from fastapi import APIRouter, status

from backend.provider_backend.app.core.apis.routes._helpers import raise_not_implemented
from backend.provider_backend.app.core.apis.schemas.requests.payment_request import (
    PaymentSessionCreateRequest,
)
from backend.provider_backend.app.core.apis.schemas.responses.common_response import APIResponse
from backend.provider_backend.app.core.apis.schemas.responses.payment_response import (
    ProviderPaymentResponse,
)

payment_router = APIRouter(prefix="/api/v1/provider/payments", tags=["Provider Payments"])


@payment_router.post("/create-session", response_model=APIResponse[ProviderPaymentResponse], status_code=status.HTTP_201_CREATED)
async def create_payment_session(
    _: PaymentSessionCreateRequest,
) -> APIResponse[ProviderPaymentResponse]:
    """Create a provider-owned payment order or checkout session."""
    raise_not_implemented("Provider payment session creation")

