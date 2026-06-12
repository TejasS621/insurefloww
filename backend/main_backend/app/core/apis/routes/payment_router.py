"""Payment routes for the main backend."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from odmantic import AIOEngine

from backend.main_backend.app.core.apis.routes._mappers import to_payment_initiation_response
from backend.main_backend.app.core.apis.schemas.requests.payment_request import (
    PaymentInitiationRequest,
)
from backend.main_backend.app.core.apis.schemas.responses.common_response import APIResponse
from backend.main_backend.app.core.apis.schemas.responses.payment_response import PaymentInitiationResponse
from backend.main_backend.app.core.database.database import get_database
from backend.main_backend.app.core.models.application_model import Application
from backend.main_backend.app.core.models.transaction_model import Transaction
from backend.main_backend.app.core.services.payment_service import payment_service
from backend.main_backend.app.core.services.service_exceptions import (
    IntegrationServiceError,
    NotFoundServiceError,
)

payment_router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])


@payment_router.post("/initiate/{transaction_reference}", response_model=APIResponse[PaymentInitiationResponse])
async def initiate_payment(
    transaction_reference: str,
    request_data: PaymentInitiationRequest | None = None,
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[PaymentInitiationResponse]:
    """Create a provider-hosted mock payment session for the selected customer quote."""
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

    application = await engine.find_one(
        Application,
        Application.transaction_reference == transaction_reference,
    )
    if application is None:
        raise IntegrationServiceError(
            "Customer application context is missing for the supplied transaction reference."
        )

    provider_session = await payment_service.request_provider_hosted_payment_session(
        transaction_reference=transaction_reference,
        quote_reference=transaction.selected_quote_id,
        amount=transaction.final_amount,
        customer_full_name=(
            f"{application.personal_details.first_name} {application.personal_details.last_name}".strip()
        ),
        customer_email=application.personal_details.email,
        customer_mobile_number=application.personal_details.mobile_number,
        selected_payment_method=(
            request_data.selected_payment_method
            if request_data is not None
            else None
        ),
    )
    await payment_service.mark_payment_initiated(
        engine,
        transaction_reference=transaction_reference,
        provider_payment_reference=provider_session.payment_reference,
        checkout_metadata={
            "payment_url": provider_session.payment_url,
            "available_payment_methods": provider_session.available_payment_methods,
            "selected_payment_method": (
                request_data.selected_payment_method
                if request_data is not None
                else None
            ),
            "selected_addons": transaction.selected_addons,
        },
    )
    return APIResponse(
        message="Payment session created successfully.",
        data=to_payment_initiation_response(provider_session),
    )
