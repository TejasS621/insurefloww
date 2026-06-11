"""Admin routes for the main backend."""

from __future__ import annotations

from fastapi import APIRouter, status

from backend.main_backend.app.core.apis.routes._helpers import raise_not_implemented
from backend.main_backend.app.core.apis.schemas.requests.admin_request import (
    BrokerKeyRotationRequest,
    BrokerRegistrationRequest,
    BrokerStatusUpdateRequest,
)
from backend.main_backend.app.core.apis.schemas.responses.admin_response import BrokerRegistryResponse
from backend.main_backend.app.core.apis.schemas.responses.common_response import APIResponse

admin_router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@admin_router.post("/brokers", response_model=APIResponse[BrokerRegistryResponse], status_code=status.HTTP_201_CREATED)
async def register_broker(_: BrokerRegistrationRequest) -> APIResponse[BrokerRegistryResponse]:
    """Register a broker through the admin orchestration API."""
    raise_not_implemented("Admin broker registration")


@admin_router.get("/brokers", response_model=APIResponse[list[BrokerRegistryResponse]])
async def list_brokers() -> APIResponse[list[BrokerRegistryResponse]]:
    """List registered brokers."""
    raise_not_implemented("List brokers")


@admin_router.patch("/brokers/{broker_code}/status", response_model=APIResponse[BrokerRegistryResponse])
async def update_broker_status(
    broker_code: str, _: BrokerStatusUpdateRequest
) -> APIResponse[BrokerRegistryResponse]:
    """Update the lifecycle status of a broker."""
    raise_not_implemented("Broker status update")


@admin_router.put("/brokers/{broker_code}/rotate-key", response_model=APIResponse[BrokerRegistryResponse])
async def rotate_broker_key(
    broker_code: str, _: BrokerKeyRotationRequest
) -> APIResponse[BrokerRegistryResponse]:
    """Rotate broker credentials through the admin API."""
    raise_not_implemented("Broker key rotation")
