"""
Handle provider-to-main synchronization routes for the provider backend.

Args:
    None: This module defines provider-admin endpoints for dispatching sync
    events and processing or listing retry records.

Returns:
    None: Route handlers return structured synchronization status responses
    under the `/api/v1/sync` router.

Raises:
    HTTPException: Unexpected failures are normalized through the shared
    route guard before being returned to the caller.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from odmantic import AIOEngine

from backend.provider_backend.commons.logger import get_logger
from backend.provider_backend.core.apis.routes._helpers import route_guard
from backend.provider_backend.core.apis.routes._mappers import (
    to_retry_processing_response,
    to_sync_status_response,
)
from backend.provider_backend.core.apis.routes.dependencies import (
    get_current_provider_admin_principal,
)
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
from backend.provider_backend.core.services.service_exceptions import ServiceError

sync_router = APIRouter(prefix="/api/v1/sync", tags=["Provider Sync"])
logger = get_logger(__name__)


@sync_router.post(
    "/dispatch",
    response_model=APIResponse[ProviderSyncStatusResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
@route_guard
async def dispatch_provider_sync(
    request_data: ProviderSyncDispatchRequest,
    engine: AIOEngine = Depends(get_database),
    _: object = Depends(get_current_provider_admin_principal),
) -> APIResponse[ProviderSyncStatusResponse]:
    """
    Dispatch a provider synchronization event for a processed payment.

    Args:
        request_data: Validated dispatch payload containing a payment reference.
        engine: Active ODMantic database engine dependency.
        _: Authenticated provider-admin dependency used for access control.

    Returns:
        APIResponse[ProviderSyncStatusResponse]: Sync dispatch result and the
        persisted retry-tracking state.

    Raises:
        HTTPException: Re-raises domain validation errors or wraps unexpected
        failures as HTTP 500 responses through the route guard.
    """
    try:
        retry_record = await provider_sync_service.dispatch_policy_issued_for_payment(
            engine,
            payment_reference=request_data.payment_reference,
        )
        return APIResponse(
            message="Provider synchronization dispatch attempted.",
            data=to_sync_status_response(retry_record),
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception(
            "Failed to dispatch provider sync for payment %s.",
            request_data.payment_reference,
        )
        raise


@sync_router.post(
    "/retries/process",
    response_model=APIResponse[RetryProcessingResponse],
)
@route_guard
async def process_due_retries(
    request_data: RetryProcessingRequest,
    engine: AIOEngine = Depends(get_database),
    _: object = Depends(get_current_provider_admin_principal),
) -> APIResponse[RetryProcessingResponse]:
    """
    Process queued provider synchronization retries that are due.

    Args:
        request_data: Validated retry-processing payload containing the limit.
        engine: Active ODMantic database engine dependency.
        _: Authenticated provider-admin dependency used for access control.

    Returns:
        APIResponse[RetryProcessingResponse]: Retry-processing summary after
        the due queue has been evaluated.

    Raises:
        HTTPException: Re-raises domain validation errors or wraps unexpected
        failures as HTTP 500 responses through the route guard.
    """
    try:
        result = await provider_sync_service.process_due_retries(
            engine,
            limit=request_data.limit,
        )
        return APIResponse(
            message="Due provider synchronization retries processed.",
            data=to_retry_processing_response(result),
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception("Failed to process due provider sync retries.")
        raise


@sync_router.get(
    "/retries",
    response_model=APIResponse[list[ProviderSyncStatusResponse]],
)
@route_guard
async def list_sync_retries(
    engine: AIOEngine = Depends(get_database),
    _: object = Depends(get_current_provider_admin_principal),
) -> APIResponse[list[ProviderSyncStatusResponse]]:
    """
    List provider synchronization retry records for administrative review.

    Args:
        engine: Active ODMantic database engine dependency.
        _: Authenticated provider-admin dependency used for access control.

    Returns:
        APIResponse[list[ProviderSyncStatusResponse]]: Persisted retry records
        currently known to the provider backend.

    Raises:
        HTTPException: Re-raises domain validation errors or wraps unexpected
        failures as HTTP 500 responses through the route guard.
    """
    try:
        records = await provider_sync_service.list_retry_records(engine)
        return APIResponse(
            message="Provider synchronization retry records fetched successfully.",
            data=[to_sync_status_response(record) for record in records],
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception("Failed to list provider sync retries.")
        raise
