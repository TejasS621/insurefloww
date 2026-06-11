"""Payment routes for the main backend."""

from __future__ import annotations

from fastapi import APIRouter

from backend.main_backend.app.core.apis.routes._helpers import raise_not_implemented
from backend.main_backend.app.core.apis.schemas.responses.common_response import APIResponse
from backend.main_backend.app.core.apis.schemas.responses.payment_response import PaymentInitiationResponse

payment_router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])


@payment_router.post("/initiate/{transaction_reference}", response_model=APIResponse[PaymentInitiationResponse])
async def initiate_payment(transaction_reference: str) -> APIResponse[PaymentInitiationResponse]:
    """Start the provider-backed payment flow for a transaction."""
    raise_not_implemented("Payment initiation")
