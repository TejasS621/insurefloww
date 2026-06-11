"""Provider sync webhook routes for the main backend."""

from __future__ import annotations

from fastapi import APIRouter

from backend.main_backend.app.core.apis.routes._helpers import raise_not_implemented
from backend.main_backend.app.core.apis.schemas.requests.provider_sync_request import ProviderWebhookPayload
from backend.main_backend.app.core.apis.schemas.responses.common_response import APIResponse
from backend.main_backend.app.core.apis.schemas.responses.provider_sync_response import ProviderWebhookSyncResponse

provider_sync_router = APIRouter(prefix="/api/v1/provider-sync", tags=["Provider Sync"])


@provider_sync_router.post("/webhook", response_model=APIResponse[ProviderWebhookSyncResponse])
async def receive_provider_sync(
    _: ProviderWebhookPayload,
) -> APIResponse[ProviderWebhookSyncResponse]:
    """Receive payment or policy updates from the provider backend."""
    raise_not_implemented("Provider sync webhook processing")

