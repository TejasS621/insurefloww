"""
Handle payment routes for the main backend.

Args:
    None: This module defines payment initiation, status lookup, and receipt
    download endpoints for guest and authenticated customer flows.

Returns:
    None: Route handlers return structured payment responses or receipt files
    under the `/api/v1/payments` router.

Raises:
    HTTPException: Unexpected failures are normalized through the shared
    route guard before being returned to the caller.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from odmantic import AIOEngine

from backend.main_backend.commons.logger import get_logger
from backend.main_backend.core.apis.routes._helpers import route_guard
from backend.main_backend.core.apis.routes._mappers import (
    to_payment_initiation_response,
)
from backend.main_backend.core.apis.routes.dependencies import (
    get_current_user_id,
    get_optional_user_id,
)
from backend.main_backend.core.apis.schemas.requests.payment_request import (
    PaymentInitiationRequest,
)
from backend.main_backend.core.apis.schemas.responses.common_response import APIResponse
from backend.main_backend.core.apis.schemas.responses.payment_response import (
    PaymentInitiationResponse,
    PaymentStatusResponse,
)
from backend.main_backend.core.database.database import get_database
from backend.main_backend.core.models.application_model import Application
from backend.main_backend.core.models.transaction_model import Transaction
from backend.main_backend.core.services.payment_service import payment_service
from backend.main_backend.core.services.service_exceptions import (
    AuthorizationServiceError,
    IntegrationServiceError,
    NotFoundServiceError,
    ServiceError,
)
from backend.provider_backend.core.models.payment_model import Payment

payment_router = APIRouter(prefix="/api/v1/payments", tags=["Payments"])
logger = get_logger(__name__)


@payment_router.post(
    "/initiate/{transaction_reference}",
    response_model=APIResponse[PaymentInitiationResponse],
)
@route_guard
async def initiate_payment(
    transaction_reference: str,
    request_data: PaymentInitiationRequest | None = None,
    engine: AIOEngine = Depends(get_database),
    user_id: str | None = Depends(get_optional_user_id),
) -> APIResponse[PaymentInitiationResponse]:
    """
    Create a provider-hosted mock payment session for a customer transaction.

    Args:
        transaction_reference: Main transaction reference selected for payment.
        request_data: Optional payload containing the preferred payment method.
        engine: Active ODMantic database engine dependency.
        user_id: Optional authenticated customer identifier for ownership checks.

    Returns:
        APIResponse[PaymentInitiationResponse]: Hosted payment session details
        returned by the provider-facing payment orchestration.

    Raises:
        HTTPException: Re-raises domain validation errors or wraps unexpected
        failures as HTTP 500 responses through the route guard.
    """
    try:
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
        if application.user_id is None and user_id is not None:
            application.user_id = user_id
            application.updated_at = datetime.now(timezone.utc)
            await engine.save(application)
        elif (
            application.user_id is not None
            and user_id is not None
            and application.user_id != user_id
        ):
            raise AuthorizationServiceError(
                "You are not allowed to initiate payment for this transaction."
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
                request_data.selected_payment_method if request_data is not None else None
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
                    request_data.selected_payment_method if request_data is not None else None
                ),
                "selected_addons": transaction.selected_addons,
            },
        )
        return APIResponse(
            message="Payment session created successfully.",
            data=to_payment_initiation_response(provider_session),
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception("Failed to initiate payment for %s.", transaction_reference)
        raise


@payment_router.get(
    "/status/{transaction_reference}",
    response_model=APIResponse[PaymentStatusResponse],
)
@route_guard
async def get_payment_status(
    transaction_reference: str,
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[PaymentStatusResponse]:
    """
    Return the payment and transaction status for a customer transaction.

    Args:
        transaction_reference: Main transaction reference being polled.
        engine: Active ODMantic database engine dependency.

    Returns:
        APIResponse[PaymentStatusResponse]: Current payment state and linked
        transaction state for frontend polling flows.

    Raises:
        HTTPException: Re-raises domain validation errors or wraps unexpected
        failures as HTTP 500 responses through the route guard.
    """
    try:
        transaction = await engine.find_one(
            Transaction,
            Transaction.transaction_reference == transaction_reference,
        )
        if transaction is None:
            raise NotFoundServiceError("Transaction not found for payment status lookup.")

        return APIResponse(
            message="Payment status fetched successfully.",
            data=PaymentStatusResponse(
                payment_status=transaction.payment_status.value,
                transaction_status=transaction.transaction_status.value,
                provider_payment_reference=transaction.provider_payment_reference,
            ),
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception("Failed to fetch payment status for %s.", transaction_reference)
        raise


@payment_router.get("/receipt/{payment_reference}", response_class=FileResponse)
@route_guard
async def download_payment_receipt(
    payment_reference: str,
    engine: AIOEngine = Depends(get_database),
    user_id: str = Depends(get_current_user_id),
) -> FileResponse:
    """
    Download a payment receipt for an authenticated customer-owned payment.

    Args:
        payment_reference: Provider payment reference used to locate the receipt.
        engine: Active ODMantic database engine dependency.
        user_id: Authenticated customer identifier used for access control.

    Returns:
        FileResponse: PDF receipt file streamed to the client.

    Raises:
        HTTPException: Re-raises domain validation errors or wraps unexpected
        failures as HTTP 500 responses through the route guard.
    """
    try:
        payment = await engine.find_one(Payment, Payment.payment_reference == payment_reference)
        if payment is None:
            raise NotFoundServiceError("The requested payment receipt could not be found.")

        application = await engine.find_one(
            Application,
            Application.transaction_reference == payment.main_transaction_reference,
        )
        if application is None:
            raise NotFoundServiceError("The application for the requested payment could not be found.")
        if application.user_id is None:
            application.user_id = user_id
            application.updated_at = datetime.now(timezone.utc)
            await engine.save(application)
        elif application.user_id != user_id:
            raise AuthorizationServiceError("You are not allowed to access this payment receipt.")

        if not payment.receipt_pdf_path:
            raise NotFoundServiceError("The requested payment receipt is not available.")

        document_path = Path(payment.receipt_pdf_path)
        if not document_path.exists():
            raise NotFoundServiceError("The requested payment receipt file is missing.")

        return FileResponse(
            path=document_path,
            media_type="application/pdf",
            filename=f"{payment.payment_reference}-receipt.pdf",
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception("Failed to download payment receipt %s.", payment_reference)
        raise
