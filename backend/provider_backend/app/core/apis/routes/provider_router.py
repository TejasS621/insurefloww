"""Broker registry routes for the provider backend."""

from __future__ import annotations

from fastapi import APIRouter, status

from backend.provider_backend.app.core.apis.routes._helpers import raise_not_implemented
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

provider_router = APIRouter(prefix="/api/v1/provider/brokers", tags=["Brokers"])


@provider_router.post("/register", response_model=APIResponse[BrokerCredentialResponse], status_code=status.HTTP_201_CREATED)
async def register_broker(
    _: BrokerRegistrationRequest,
) -> APIResponse[BrokerCredentialResponse]:
    """Register a broker and return one-time credentials."""
    raise_not_implemented("Provider broker registration")


@provider_router.get("", response_model=APIResponse[list[BrokerRegistryResponse]])
async def list_brokers() -> APIResponse[list[BrokerRegistryResponse]]:
    """List brokers known to the provider backend."""
    raise_not_implemented("Provider broker listing")


@provider_router.patch("/{broker_code}/status", response_model=APIResponse[BrokerRegistryResponse])
async def update_broker_status(
    broker_code: str, _: BrokerStatusUpdateRequest
) -> APIResponse[BrokerRegistryResponse]:
    """Update broker activation state."""
    raise_not_implemented("Provider broker status update")


@provider_router.put("/{broker_code}/rotate-key", response_model=APIResponse[BrokerCredentialResponse])
async def rotate_broker_key(
    broker_code: str, _: KeyRotationRequest
) -> APIResponse[BrokerCredentialResponse]:
    """Rotate a broker API key and return the new one-time credential."""
    raise_not_implemented("Provider broker key rotation")
