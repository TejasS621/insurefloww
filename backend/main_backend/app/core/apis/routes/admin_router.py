"""Admin routes for the main backend."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from odmantic import AIOEngine

from backend.main_backend.app.core.apis.routes._mappers import to_admin_broker_response
from backend.main_backend.app.core.apis.routes.dependencies import get_optional_admin_email
from backend.main_backend.app.core.apis.schemas.requests.admin_request import (
    BrokerKeyRotationRequest,
    BrokerRegistrationRequest,
    BrokerStatusUpdateRequest,
)
from backend.main_backend.app.core.apis.schemas.responses.admin_response import BrokerRegistryResponse
from backend.main_backend.app.core.apis.schemas.responses.common_response import APIResponse
from backend.main_backend.app.core.database.database import get_database
from backend.provider_backend.app.core.apis.schemas.requests.provider_request import (
    BrokerRegistrationRequest as ProviderBrokerRegistrationRequest,
    BrokerStatusUpdateRequest as ProviderBrokerStatusUpdateRequest,
    KeyRotationRequest as ProviderKeyRotationRequest,
)
from backend.provider_backend.app.core.services.broker_service import broker_service

admin_router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@admin_router.post("/brokers", response_model=APIResponse[BrokerRegistryResponse], status_code=status.HTTP_201_CREATED)
async def register_broker(
    request_data: BrokerRegistrationRequest,
    engine: AIOEngine = Depends(get_database),
    admin_email: str | None = Depends(get_optional_admin_email),
) -> APIResponse[BrokerRegistryResponse]:
    """Register a broker through the admin orchestration API."""
    broker, _ = await broker_service.register_broker(
        engine,
        ProviderBrokerRegistrationRequest(
            broker_name=request_data.broker_name,
            broker_code=request_data.broker_code,
            callback_url=request_data.callback_url,
            webhook_url=request_data.webhook_url,
            created_by_admin=admin_email,
        ),
    )
    return APIResponse(
        message="Broker registered successfully.",
        data=to_admin_broker_response(broker),
    )


@admin_router.get("/brokers", response_model=APIResponse[list[BrokerRegistryResponse]])
async def list_brokers(
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[list[BrokerRegistryResponse]]:
    """List registered brokers."""
    brokers = await broker_service.list_brokers(engine)
    return APIResponse(
        message="Brokers fetched successfully.",
        data=[to_admin_broker_response(broker) for broker in brokers],
    )


@admin_router.patch("/brokers/{broker_code}/status", response_model=APIResponse[BrokerRegistryResponse])
async def update_broker_status(
    broker_code: str,
    request_data: BrokerStatusUpdateRequest,
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[BrokerRegistryResponse]:
    """Update the lifecycle status of a broker."""
    broker = await broker_service.update_broker_status(
        engine,
        broker_code=broker_code,
        request_data=ProviderBrokerStatusUpdateRequest(
            status=request_data.status.value,
            reason=request_data.reason,
        ),
    )
    return APIResponse(
        message="Broker status updated successfully.",
        data=to_admin_broker_response(broker),
    )


@admin_router.put("/brokers/{broker_code}/rotate-key", response_model=APIResponse[BrokerRegistryResponse])
async def rotate_broker_key(
    broker_code: str,
    request_data: BrokerKeyRotationRequest,
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[BrokerRegistryResponse]:
    """Rotate broker credentials through the admin API."""
    broker, _ = await broker_service.rotate_broker_key(
        engine,
        broker_code=broker_code,
        request_data=ProviderKeyRotationRequest(
            rotated_by=request_data.initiated_by,
            reason=request_data.reason,
        ),
    )
    return APIResponse(
        message="Broker key rotated successfully.",
        data=to_admin_broker_response(broker),
    )
