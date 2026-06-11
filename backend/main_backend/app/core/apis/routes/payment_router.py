"""Payment routes for the main backend."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from odmantic import AIOEngine

from backend.main_backend.app.core.apis.routes._mappers import to_payment_initiation_response
from backend.main_backend.app.core.apis.schemas.responses.common_response import APIResponse
from backend.main_backend.app.core.apis.schemas.responses.payment_response import PaymentInitiationResponse
from backend.main_backend.app.core.database.database import get_database
from backend.main_backend.app.core.models.transaction_model import Transaction
from backend.main_backend.app.core.services.payment_service import payment_service
from backend.main_backend.app.core.services.service_exceptions import (
    IntegrationServiceError,
    NotFoundServiceError,
)
from backend.provider_backend.app.core.apis.schemas.requests.payment_request import (
    PaymentSessionCreateRequest,
)
from backend.provider_backend.app.core.models.provider_transaction_model import ProviderTransaction
from backend.provider_backend.app.core.services.payment_service import provider_payment_service

payment_router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])


@payment_router.post("/initiate/{transaction_reference}", response_model=APIResponse[PaymentInitiationResponse])
async def initiate_payment(
    transaction_reference: str,
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[PaymentInitiationResponse]:
    """Start the provider-backed payment flow for a quote-selected transaction."""
    transaction = await engine.find_one(
        Transaction,
        Transaction.transaction_reference == transaction_reference,
    )
    if transaction is None:
        raise NotFoundServiceError("Transaction not found for payment initiation.")
    if not transaction.selected_quote_id or transaction.final_amount is None:
        raise IntegrationServiceError(
            "A quote must be selected and priced before payment can be initiated."
        )

    provider_transaction = await engine.find_one(
        ProviderTransaction,
        ProviderTransaction.main_transaction_reference == transaction_reference,
    )
    if provider_transaction is None:
        raise IntegrationServiceError(
            "No provider transaction exists for the supplied main transaction reference."
        )

    provider_payment = await provider_payment_service.create_payment_session(
        engine,
        PaymentSessionCreateRequest(
            provider_transaction_reference=provider_transaction.provider_transaction_reference,
            main_transaction_reference=transaction_reference,
            provider_quote_id=transaction.selected_quote_id,
            selected_addons=transaction.selected_addons,
            amount=transaction.final_amount,
            currency="INR",
        ),
    )
    updated_transaction = await payment_service.mark_payment_initiated(
        engine,
        transaction_reference=transaction_reference,
        provider_payment_reference=provider_payment.payment_reference,
        checkout_metadata={
            "gateway_order_id": provider_payment.gateway_order_id,
            "provider_transaction_reference": provider_transaction.provider_transaction_reference,
            "selected_addons": transaction.selected_addons,
        },
    )
    return APIResponse(
        message="Payment session created successfully.",
        data=to_payment_initiation_response(
            updated_transaction,
            gateway=provider_payment.gateway_name.value,
            gateway_order_id=provider_payment.gateway_order_id or "",
            currency=provider_payment.currency,
        ),
    )
