"""Webhook routes for the provider backend."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from odmantic import AIOEngine

from backend.provider_backend.core.apis.routes._helpers import route_guard
from backend.provider_backend.core.apis.schemas.requests.webhook_request import (
    PaymentSuccessWebhookRequest,
)
from backend.provider_backend.core.apis.schemas.responses.common_response import APIResponse
from backend.provider_backend.core.apis.schemas.responses.webhook_response import (
    WebhookAcknowledgementResponse,
)
from backend.provider_backend.core.database.database import get_database
from backend.provider_backend.core.services.webhook_service import webhook_service

webhook_router = APIRouter(prefix="/api/v1/webhooks", tags=["Provider Webhooks"])


@webhook_router.post("/payment-success", response_model=APIResponse[WebhookAcknowledgementResponse])
@route_guard
async def payment_success_webhook(
    request_data: PaymentSuccessWebhookRequest,
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[WebhookAcknowledgementResponse]:
    """Receive and validate payment success callbacks."""
    await webhook_service.handle_payment_success(engine, request_data)
    return APIResponse(
        message="Payment success webhook processed successfully.",
        data=WebhookAcknowledgementResponse(
            event_type="PAYMENT_SUCCESS",
            processing_status="PROCESSED",
        ),
    )
