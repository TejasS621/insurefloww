"""
Handle broker registry routes for the provider backend.

Args:
    None: This module defines provider-admin broker registration, listing,
    status update, and key-rotation endpoints.

Returns:
    None: Route handlers return structured broker registry or credential
    responses under the `/api/v1/brokers` router.

Raises:
    HTTPException: Unexpected failures are normalized through the shared
    route guard before being returned to the caller.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from odmantic import AIOEngine

from backend.provider_backend.commons.logger import get_logger
from backend.provider_backend.core.apis.routes._helpers import route_guard
from backend.provider_backend.core.apis.routes._mappers import to_broker_response
from backend.provider_backend.core.apis.routes.dependencies import (
    get_current_provider_admin_principal,
)
from backend.provider_backend.core.apis.schemas.requests.provider_request import (
    BrokerRegistrationRequest,
    BrokerStatusUpdateRequest,
    KeyRotationRequest,
)
from backend.provider_backend.core.apis.schemas.responses.common_response import APIResponse
from backend.provider_backend.core.apis.schemas.responses.provider_response import (
    BrokerCredentialResponse,
    BrokerRegistryResponse,
)
from backend.provider_backend.core.database.database import get_database
from backend.provider_backend.core.services.broker_service import broker_service
from backend.provider_backend.core.services.service_exceptions import ServiceError

provider_router = APIRouter(prefix="/api/v1/brokers", tags=["Brokers"])
logger = get_logger(__name__)


@provider_router.post(
    "/register",
    response_model=APIResponse[BrokerCredentialResponse],
    status_code=status.HTTP_201_CREATED,
)
@route_guard
async def register_broker(
    request_data: BrokerRegistrationRequest,
    engine: AIOEngine = Depends(get_database),
    _: object = Depends(get_current_provider_admin_principal),
) -> APIResponse[BrokerCredentialResponse]:
    """
    Register a broker and return the one-time API credential payload.

    Args:
        request_data: Validated broker registration payload.
        engine: Active ODMantic database engine dependency.
        _: Authenticated provider-admin dependency used for access control.

    Returns:
        APIResponse[BrokerCredentialResponse]: Created broker identity and
        one-time API key that must be stored by the caller.

    Raises:
        HTTPException: Re-raises domain validation errors or wraps unexpected
        failures as HTTP 500 responses through the route guard.
    """
    try:
        broker, api_key = await broker_service.register_broker(engine, request_data)
        return APIResponse(
            message="Broker registered successfully.",
            data=BrokerCredentialResponse(
                broker_code=broker.broker_code,
                api_key=api_key,
                message="Store this API key securely. It will not be shown again.",
            ),
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception("Failed to register broker %s.", request_data.broker_code)
        raise


@provider_router.get("", response_model=APIResponse[list[BrokerRegistryResponse]])
@route_guard
async def list_brokers(
    engine: AIOEngine = Depends(get_database),
    _: object = Depends(get_current_provider_admin_principal),
) -> APIResponse[list[BrokerRegistryResponse]]:
    """
    List broker registry records available to the provider admin console.

    Args:
        engine: Active ODMantic database engine dependency.
        _: Authenticated provider-admin dependency used for access control.

    Returns:
        APIResponse[list[BrokerRegistryResponse]]: Provider-known broker
        registry records.

    Raises:
        HTTPException: Re-raises domain validation errors or wraps unexpected
        failures as HTTP 500 responses through the route guard.
    """
    try:
        brokers = await broker_service.list_brokers(engine)
        return APIResponse(
            message="Brokers fetched successfully.",
            data=[to_broker_response(broker) for broker in brokers],
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception("Failed to list provider brokers.")
        raise


@provider_router.patch(
    "/{broker_code}/status",
    response_model=APIResponse[BrokerRegistryResponse],
)
@route_guard
async def update_broker_status(
    broker_code: str,
    request_data: BrokerStatusUpdateRequest,
    engine: AIOEngine = Depends(get_database),
    _: object = Depends(get_current_provider_admin_principal),
) -> APIResponse[BrokerRegistryResponse]:
    """
    Update the lifecycle status of a registered broker.

    Args:
        broker_code: Broker code whose status should be updated.
        request_data: Validated status-change payload.
        engine: Active ODMantic database engine dependency.
        _: Authenticated provider-admin dependency used for access control.

    Returns:
        APIResponse[BrokerRegistryResponse]: Updated broker registry record.

    Raises:
        HTTPException: Re-raises domain validation errors or wraps unexpected
        failures as HTTP 500 responses through the route guard.
    """
    try:
        broker = await broker_service.update_broker_status(
            engine,
            broker_code=broker_code,
            request_data=request_data,
        )
        return APIResponse(
            message="Broker status updated successfully.",
            data=to_broker_response(broker),
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception("Failed to update broker status for %s.", broker_code)
        raise


@provider_router.put(
    "/{broker_code}/rotate-key",
    response_model=APIResponse[BrokerCredentialResponse],
)
@route_guard
async def rotate_broker_key(
    broker_code: str,
    request_data: KeyRotationRequest,
    engine: AIOEngine = Depends(get_database),
    _: object = Depends(get_current_provider_admin_principal),
) -> APIResponse[BrokerCredentialResponse]:
    """
    Rotate a broker API key and return the new one-time credential payload.

    Args:
        broker_code: Broker code whose key should be rotated.
        request_data: Validated rotation payload.
        engine: Active ODMantic database engine dependency.
        _: Authenticated provider-admin dependency used for access control.

    Returns:
        APIResponse[BrokerCredentialResponse]: Broker code and the rotated
        one-time API key.

    Raises:
        HTTPException: Re-raises domain validation errors or wraps unexpected
        failures as HTTP 500 responses through the route guard.
    """
    try:
        broker, api_key = await broker_service.rotate_broker_key(
            engine,
            broker_code=broker_code,
            request_data=request_data,
        )
        return APIResponse(
            message="Broker key rotated successfully.",
            data=BrokerCredentialResponse(
                broker_code=broker.broker_code,
                api_key=api_key,
                message="Store this rotated API key securely. It will not be shown again.",
            ),
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception("Failed to rotate broker key for %s.", broker_code)
        raise
