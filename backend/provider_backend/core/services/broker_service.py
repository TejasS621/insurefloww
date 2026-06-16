"""Broker registry services for the provider backend."""

from __future__ import annotations

import hashlib
import secrets
from datetime import datetime, timezone

from odmantic import AIOEngine

from backend.provider_backend.core.apis.schemas.requests.provider_request import (
    BrokerRegistrationRequest,
    BrokerStatusUpdateRequest,
    KeyRotationRequest,
)
from backend.provider_backend.commons.config import settings
from backend.provider_backend.commons.logger import get_logger
from backend.provider_backend.core.models.broker_registry_model import (
    BrokerRegistry,
    BrokerStatus,
)

from .service_exceptions import ConflictServiceError, NotFoundServiceError

logger = get_logger(__name__)


class BrokerService:
    """Manage provider-side broker registry records and credentials."""

    async def ensure_integration_broker(self, engine: AIOEngine) -> BrokerRegistry:
        """Ensure the default local integration broker exists for backend-to-backend calls."""
        await self._backfill_legacy_broker_documents(engine)
        broker = await engine.find_one(
            BrokerRegistry,
            BrokerRegistry.broker_code == settings.integration_broker_code,
        )
        if broker is not None:
            expected_hash = self._hash_api_key(settings.integration_broker_api_key)
            if broker.api_key_hash != expected_hash:
                broker.api_key_hash = expected_hash
                broker.status = BrokerStatus.ACTIVE
                broker.updated_at = datetime.now(timezone.utc)
                await engine.save(broker)
                logger.info(
                    "Refreshed integration broker credentials for '%s'.",
                    settings.integration_broker_code,
                )
            return broker

        broker = BrokerRegistry(
            broker_code=settings.integration_broker_code,
            broker_name="Main Backend Integration",
            api_key_hash=self._hash_api_key(settings.integration_broker_api_key),
            company_name="InsureFlow Main Backend",
            supported_insurance_types=["HEALTH", "LIFE", "VEHICLE", "TRAVEL", "HOME"],
            active_regions=["PAN_INDIA"],
            partner_provider_codes=["DEMO_PROVIDER"],
            callback_url=settings.default_broker_callback_url,
            webhook_url=settings.default_broker_webhook_url,
            status=BrokerStatus.ACTIVE,
            created_by_admin="system",
        )
        await engine.save(broker)
        logger.info(
            "Created integration broker '%s' for backend synchronization.",
            settings.integration_broker_code,
        )
        return broker

    async def register_broker(
        self,
        engine: AIOEngine,
        request_data: BrokerRegistrationRequest,
    ) -> tuple[BrokerRegistry, str]:
        """Register a broker and return the one-time raw API key."""
        await self._backfill_legacy_broker_documents(engine)
        existing = await engine.find_one(
            BrokerRegistry,
            BrokerRegistry.broker_code == request_data.broker_code,
        )
        if existing is not None:
            raise ConflictServiceError("A broker with the given code already exists.")

        api_key = self._generate_api_key()
        callback_url = (
            str(request_data.callback_url)
            if request_data.callback_url is not None
            else settings.default_broker_callback_url
        )
        webhook_url = (
            str(request_data.webhook_url)
            if request_data.webhook_url is not None
            else settings.default_broker_webhook_url
        )
        broker = BrokerRegistry(
            broker_code=request_data.broker_code,
            broker_name=request_data.broker_name,
            company_name=request_data.company_name,
            license_number=request_data.license_number,
            registration_number=request_data.registration_number,
            contact_person_name=request_data.contact_person_name,
            contact_email=str(request_data.contact_email) if request_data.contact_email else None,
            contact_phone=request_data.contact_phone,
            supported_insurance_types=request_data.supported_insurance_types,
            active_regions=request_data.active_regions,
            partner_provider_codes=request_data.partner_provider_codes,
            notes=request_data.notes,
            api_key_hash=self._hash_api_key(api_key),
            callback_url=callback_url,
            webhook_url=webhook_url,
            status=BrokerStatus.ACTIVE,
            created_by_admin=request_data.created_by_admin,
        )
        await engine.save(broker)
        logger.info("Registered broker '%s'.", request_data.broker_code)
        return broker, api_key

    async def list_brokers(self, engine: AIOEngine) -> list[BrokerRegistry]:
        """Return all registered brokers."""
        await self._backfill_legacy_broker_documents(engine)
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
        logger.info("Updated broker '%s' to status '%s'.", broker_code, request_data.status.value)
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
        logger.info("Rotated API key for broker '%s'.", broker_code)
        return broker, api_key

    async def _get_broker(self, engine: AIOEngine, broker_code: str) -> BrokerRegistry:
        """Fetch a broker by broker code or raise a typed not-found error."""
        await self._backfill_legacy_broker_documents(engine)
        broker = await engine.find_one(BrokerRegistry, BrokerRegistry.broker_code == broker_code)
        if broker is None:
            raise NotFoundServiceError("The requested broker could not be found.")
        return broker

    async def _backfill_legacy_broker_documents(self, engine: AIOEngine) -> None:
        """Populate newly-added broker fields on older MongoDB documents."""
        collection = engine.get_collection(BrokerRegistry)
        await collection.update_many(
            {"supported_insurance_types": {"$exists": False}},
            {"$set": {"supported_insurance_types": []}},
        )
        await collection.update_many(
            {"active_regions": {"$exists": False}},
            {"$set": {"active_regions": []}},
        )
        await collection.update_many(
            {"partner_provider_codes": {"$exists": False}},
            {"$set": {"partner_provider_codes": []}},
        )
        await collection.update_many(
            {"company_name": {"$exists": False}},
            {"$set": {"company_name": None}},
        )
        await collection.update_many(
            {"license_number": {"$exists": False}},
            {"$set": {"license_number": None}},
        )
        await collection.update_many(
            {"registration_number": {"$exists": False}},
            {"$set": {"registration_number": None}},
        )
        await collection.update_many(
            {"contact_person_name": {"$exists": False}},
            {"$set": {"contact_person_name": None}},
        )
        await collection.update_many(
            {"contact_email": {"$exists": False}},
            {"$set": {"contact_email": None}},
        )
        await collection.update_many(
            {"contact_phone": {"$exists": False}},
            {"$set": {"contact_phone": None}},
        )
        await collection.update_many(
            {"notes": {"$exists": False}},
            {"$set": {"notes": None}},
        )

    @staticmethod
    def _generate_api_key() -> str:
        """Generate a broker API key suitable for one-time display."""
        return f"brk_live_{secrets.token_urlsafe(24)}"

    @staticmethod
    def _hash_api_key(api_key: str) -> str:
        """Hash a broker API key before persistence."""
        return hashlib.sha256(api_key.encode("utf-8")).hexdigest()


broker_service = BrokerService()

