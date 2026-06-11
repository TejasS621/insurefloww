"""Broker registry services for the provider backend."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone

from odmantic import AIOEngine

from backend.provider_backend.app.core.apis.schemas.requests.provider_request import (
    BrokerRegistrationRequest,
    BrokerStatusUpdateRequest,
    KeyRotationRequest,
)
from backend.provider_backend.app.core.models.broker_registry_model import (
    BrokerRegistry,
    BrokerStatus,
)

from .service_exceptions import ConflictServiceError, NotFoundServiceError


class BrokerService:
    """Manage provider-side broker registry records and credentials."""

    async def register_broker(
        self,
        engine: AIOEngine,
        request_data: BrokerRegistrationRequest,
    ) -> tuple[BrokerRegistry, str]:
        """Register a broker and return the one-time raw API key."""
        existing = await engine.find_one(
            BrokerRegistry,
            BrokerRegistry.broker_code == request_data.broker_code,
        )
        if existing is not None:
            raise ConflictServiceError("A broker with the given code already exists.")

        api_key = self._generate_api_key()
        broker = BrokerRegistry(
            broker_code=request_data.broker_code,
            broker_name=request_data.broker_name,
            api_key_hash=self._hash_api_key(api_key),
            callback_url=str(request_data.callback_url),
            webhook_url=str(request_data.webhook_url),
            status=BrokerStatus.ACTIVE,
            created_by_admin=request_data.created_by_admin,
        )
        await engine.save(broker)
        return broker, api_key

    async def list_brokers(self, engine: AIOEngine) -> list[BrokerRegistry]:
        """Return all registered brokers."""
        return await engine.find(BrokerRegistry)

    async def update_broker_status(
        self,
        engine: AIOEngine,
        *,
        broker_code: str,
        request_data: BrokerStatusUpdateRequest,
    ) -> BrokerRegistry:
        """Change the lifecycle status of a broker."""
        broker = await self._get_broker(engine, broker_code)
        broker.status = BrokerStatus(request_data.status.value)
        broker.updated_at = datetime.now(timezone.utc)
        await engine.save(broker)
        return broker

    async def rotate_broker_key(
        self,
        engine: AIOEngine,
        *,
        broker_code: str,
        request_data: KeyRotationRequest,
    ) -> tuple[BrokerRegistry, str]:
        """Rotate a broker's API key and return the new raw credential once."""
        _ = request_data
        broker = await self._get_broker(engine, broker_code)
        api_key = self._generate_api_key()
        broker.api_key_hash = self._hash_api_key(api_key)
        broker.last_key_rotated_at = datetime.now(timezone.utc)
        broker.updated_at = datetime.now(timezone.utc)
        await engine.save(broker)
        return broker, api_key

    async def _get_broker(self, engine: AIOEngine, broker_code: str) -> BrokerRegistry:
        """Fetch a broker by broker code or raise a typed not-found error."""
        broker = await engine.find_one(BrokerRegistry, BrokerRegistry.broker_code == broker_code)
        if broker is None:
            raise NotFoundServiceError("The requested broker could not be found.")
        return broker

    @staticmethod
    def _generate_api_key() -> str:
        """Generate a broker API key suitable for one-time display."""
        return f"brk_live_{secrets.token_urlsafe(24)}"

    @staticmethod
    def _hash_api_key(api_key: str) -> str:
        """Hash a broker API key before persistence."""
        return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


broker_service = BrokerService()

