"""Webhook routes for the provider backend."""

from __future__ import annotations

from fastapi import APIRouter

from backend.provider_backend.app.core.apis.routes._helpers import raise_not_implemented
from backend.provider_backend.app.core.apis.schemas.requests.webhook_request import (
    PaymentSuccessWebhookRequest,
)
from backend.provider_backend.app.core.apis.schemas.responses.common_response import APIResponse
from backend.provider_backend.app.core.apis.schemas.responses.webhook_response import (
    WebhookAcknowledgementResponse,
)

webhook_router = APIRouter(prefix="/api/v1/provider/webhooks", tags=["Provider Webhooks"])


@webhook_router.post("/payment-success", response_model=APIResponse[WebhookAcknowledgementResponse])
async def payment_success_webhook(
    _: PaymentSuccessWebhookRequest,
) -> APIResponse[WebhookAcknowledgementResponse]:
    """Receive and validate payment success callbacks."""
    raise_not_implemented("Provider payment success webhook")
