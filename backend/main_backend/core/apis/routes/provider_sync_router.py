"""
Handle provider synchronization webhook routes for the main backend.

Args:
    None: This module defines the broker-authenticated webhook endpoint used
    to receive payment and policy updates from the provider side.

Returns:
    None: Route handlers return structured provider-sync responses.

Raises:
    HTTPException: Route handlers re-raise handled controller errors and
    normalize unexpected failures through the shared route guard.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from odmantic import AIOEngine

from backend.main_backend.core.apis.routes._helpers import route_guard
from backend.main_backend.core.apis.routes._mappers import to_provider_sync_response
from backend.main_backend.core.apis.routes.dependencies import (
    get_authenticated_broker,
)
from backend.main_backend.core.apis.schemas.requests.provider_sync_request import (
    ProviderWebhookPayload,
)
from backend.main_backend.core.apis.schemas.responses.common_response import APIResponse
from backend.main_backend.core.apis.schemas.responses.provider_sync_response import (
    ProviderWebhookSyncResponse,
)
from backend.main_backend.core.database.database import get_database
from backend.main_backend.core.services.provider_sync_service import (
    provider_sync_service,
)

provider_sync_router = APIRouter(prefix="/api/v1/provider-sync", tags=["Provider Sync"])


@provider_sync_router.post("/webhook", response_model=APIResponse[ProviderWebhookSyncResponse])
@route_guard
async def receive_provider_sync(
    request_data: ProviderWebhookPayload,
    engine: AIOEngine = Depends(get_database),
    _: object = Depends(get_authenticated_broker),
) -> APIResponse[ProviderWebhookSyncResponse]:
    """
    Receive payment or policy updates from the provider backend.

    Args:
        request_data: Validated webhook payload supplied by the provider flow.
        engine: Active ODMantic database engine dependency.
        _: Authenticated broker dependency used to enforce trusted access.

    Returns:
        APIResponse[ProviderWebhookSyncResponse]: Processed webhook event
        summary after transaction and application updates.

    Raises:
        HTTPException: Re-raises domain validation errors or wraps unexpected
        failures as HTTP 500 responses through the route guard.
    """
    event = await provider_sync_service.process_provider_webhook(engine, request_data)
    return APIResponse(
        message="Provider webhook processed successfully.",
        data=to_provider_sync_response(event),
    )
