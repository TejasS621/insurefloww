"""Provider-to-main synchronization routes for the provider backend."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from odmantic import AIOEngine

from backend.provider_backend.core.apis.routes._mappers import (
    to_retry_processing_response,
    to_sync_status_response,
)
from backend.provider_backend.core.apis.routes.dependencies import get_current_provider_admin_principal
from backend.provider_backend.core.apis.schemas.requests.sync_request import (
    ProviderSyncDispatchRequest,
    RetryProcessingRequest,
)
from backend.provider_backend.core.apis.schemas.responses.common_response import APIResponse
from backend.provider_backend.core.apis.schemas.responses.sync_response import (
    ProviderSyncStatusResponse,
    RetryProcessingResponse,
)
from backend.provider_backend.core.database.database import get_database
from backend.provider_backend.core.services.provider_sync_service import (
    provider_sync_service,
)

sync_router = APIRouter(prefix="/api/v1/provider/sync", tags=["Provider Sync"])


@sync_router.post(
    "/dispatch",
    response_model=APIResponse[ProviderSyncStatusResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
async def dispatch_provider_sync(
    request_data: ProviderSyncDispatchRequest,
    engine: AIOEngine = Depends(get_database),
    _: object = Depends(get_current_provider_admin_principal),
) -> APIResponse[ProviderSyncStatusResponse]:
    """Dispatch a provider synchronization event for a processed payment."""
    retry_record = await provider_sync_service.dispatch_policy_issued_for_payment(
        engine,
        payment_reference=request_data.payment_reference,
    )
    return APIResponse(
        message="Provider synchronization dispatch attempted.",
        data=to_sync_status_response(retry_record),
    )


@sync_router.post(
    "/retries/process",
    response_model=APIResponse[RetryProcessingResponse],
)
async def process_due_retries(
    request_data: RetryProcessingRequest,
    engine: AIOEngine = Depends(get_database),
    _: object = Depends(get_current_provider_admin_principal),
) -> APIResponse[RetryProcessingResponse]:
    """Process queued provider synchronization retries that are due."""
    result = await provider_sync_service.process_due_retries(
        engine,
        limit=request_data.limit,
    )
    return APIResponse(
        message="Due provider synchronization retries processed.",
        data=to_retry_processing_response(result),
    )


@sync_router.get(
    "/retries",
    response_model=APIResponse[list[ProviderSyncStatusResponse]],
)
async def list_sync_retries(
    engine: AIOEngine = Depends(get_database),
    _: object = Depends(get_current_provider_admin_principal),
) -> APIResponse[list[ProviderSyncStatusResponse]]:
    """List all provider synchronization retry records."""
    records = await provider_sync_service.list_retry_records(engine)
    return APIResponse(
        message="Provider synchronization retry records fetched successfully.",
        data=[to_sync_status_response(record) for record in records],
    )
