"""Broker registry routes for the provider backend."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from odmantic import AIOEngine

from backend.provider_backend.app.core.apis.routes._mappers import to_broker_response
from backend.provider_backend.app.core.apis.routes.dependencies import get_current_provider_admin_principal
from backend.provider_backend.app.core.apis.schemas.requests.provider_request import (
    BrokerRegistrationRequest,
    BrokerStatusUpdateRequest,
    KeyRotationRequest,
)
from backend.provider_backend.app.core.apis.schemas.responses.common_response import APIResponse
from backend.provider_backend.app.core.apis.schemas.responses.provider_response import (
    BrokerCredentialResponse,
    BrokerRegistryResponse,
)
from backend.provider_backend.app.core.database.database import get_database
from backend.provider_backend.app.core.services.broker_service import broker_service

provider_router = APIRouter(prefix="/api/v1/provider/brokers", tags=["Brokers"])


@provider_router.post("/register", response_model=APIResponse[BrokerCredentialResponse], status_code=status.HTTP_201_CREATED)
async def register_broker(
    request_data: BrokerRegistrationRequest,
    engine: AIOEngine = Depends(get_database),
    _: object = Depends(get_current_provider_admin_principal),
) -> APIResponse[BrokerCredentialResponse]:
    """Register a broker and return one-time credentials."""
    broker, api_key = await broker_service.register_broker(engine, request_data)
    return APIResponse(
        message="Broker registered successfully.",
        data=BrokerCredentialResponse(
            broker_code=broker.broker_code,
            api_key=api_key,
            message="Store this API key securely. It will not be shown again.",
        ),
    )


@provider_router.get("", response_model=APIResponse[list[BrokerRegistryResponse]])
async def list_brokers(
    engine: AIOEngine = Depends(get_database),
    _: object = Depends(get_current_provider_admin_principal),
) -> APIResponse[list[BrokerRegistryResponse]]:
    """List brokers known to the provider backend."""
    brokers = await broker_service.list_brokers(engine)
    return APIResponse(
        message="Brokers fetched successfully.",
        data=[to_broker_response(broker) for broker in brokers],
    )


@provider_router.patch("/{broker_code}/status", response_model=APIResponse[BrokerRegistryResponse])
async def update_broker_status(
    broker_code: str,
    request_data: BrokerStatusUpdateRequest,
    engine: AIOEngine = Depends(get_database),
    _: object = Depends(get_current_provider_admin_principal),
) -> APIResponse[BrokerRegistryResponse]:
    """Update broker activation state."""
    broker = await broker_service.update_broker_status(
        engine,
        broker_code=broker_code,
        request_data=request_data,
    )
    return APIResponse(
        message="Broker status updated successfully.",
        data=to_broker_response(broker),
    )


@provider_router.put("/{broker_code}/rotate-key", response_model=APIResponse[BrokerCredentialResponse])
async def rotate_broker_key(
    broker_code: str,
    request_data: KeyRotationRequest,
    engine: AIOEngine = Depends(get_database),
    _: object = Depends(get_current_provider_admin_principal),
) -> APIResponse[BrokerCredentialResponse]:
    """Rotate a broker API key and return the new one-time credential."""
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
