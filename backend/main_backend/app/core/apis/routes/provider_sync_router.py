"""Provider sync webhook routes for the main backend."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from odmantic import AIOEngine

from backend.main_backend.app.core.apis.routes._mappers import to_provider_sync_response
from backend.main_backend.app.core.apis.routes.dependencies import get_authenticated_broker
from backend.main_backend.app.core.apis.schemas.requests.provider_sync_request import ProviderWebhookPayload
from backend.main_backend.app.core.apis.schemas.responses.common_response import APIResponse
from backend.main_backend.app.core.apis.schemas.responses.provider_sync_response import ProviderWebhookSyncResponse
from backend.main_backend.app.core.database.database import get_database
from backend.main_backend.app.core.services.provider_sync_service import provider_sync_service

provider_sync_router = APIRouter(prefix="/api/v1/provider-sync", tags=["Provider Sync"])


@provider_sync_router.post("/webhook", response_model=APIResponse[ProviderWebhookSyncResponse])
async def receive_provider_sync(
    request_data: ProviderWebhookPayload,
    engine: AIOEngine = Depends(get_database),
    _: object = Depends(get_authenticated_broker),
) -> APIResponse[ProviderWebhookSyncResponse]:
    """Receive payment or policy updates from the provider backend."""
    event = await provider_sync_service.process_provider_webhook(engine, request_data)
    return APIResponse(
        message="Provider webhook processed successfully.",
        data=to_provider_sync_response(event),
    )

