"""
Handle webhook routes for the provider backend.

Args:
    None: This module defines external callback endpoints used to receive
    simulated or downstream payment success notifications.

Returns:
    None: Route handlers return structured webhook acknowledgement responses
    under the `/api/v1/webhooks` router.

Raises:
    HTTPException: Unexpected failures are normalized through the shared
    route guard before being returned to the caller.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from odmantic import AIOEngine

from backend.provider_backend.commons.logger import get_logger
from backend.provider_backend.core.apis.routes._helpers import route_guard
from backend.provider_backend.core.apis.schemas.requests.webhook_request import (
    PaymentSuccessWebhookRequest,
)
from backend.provider_backend.core.apis.schemas.responses.common_response import APIResponse
from backend.provider_backend.core.apis.schemas.responses.webhook_response import (
    WebhookAcknowledgementResponse,
)
from backend.provider_backend.core.database.database import get_database
from backend.provider_backend.core.services.service_exceptions import ServiceError
from backend.provider_backend.core.services.webhook_service import webhook_service

webhook_router = APIRouter(prefix="/api/v1/webhooks", tags=["Provider Webhooks"])
logger = get_logger(__name__)


@webhook_router.post(
    "/payment-success",
    response_model=APIResponse[WebhookAcknowledgementResponse],
)
@route_guard
async def payment_success_webhook(
    request_data: PaymentSuccessWebhookRequest,
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[WebhookAcknowledgementResponse]:
    """
    Receive and process a payment success callback for provider-side state updates.

    Args:
        request_data: Validated webhook callback payload from the payment flow.
        engine: Active ODMantic database engine dependency.

    Returns:
        APIResponse[WebhookAcknowledgementResponse]: Webhook acknowledgement
        confirming the event type and processing outcome.

    Raises:
        HTTPException: Re-raises domain validation errors or wraps unexpected
        failures as HTTP 500 responses through the route guard.
    """
    try:
        await webhook_service.handle_payment_success(engine, request_data)
        return APIResponse(
            message="Payment success webhook processed successfully.",
            data=WebhookAcknowledgementResponse(
                event_type="PAYMENT_SUCCESS",
                processing_status="PROCESSED",
            ),
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception("Failed to process provider payment-success webhook.")
        raise
