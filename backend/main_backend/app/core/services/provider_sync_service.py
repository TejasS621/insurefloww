"""Provider sync webhook processing for the main backend."""

from __future__ import annotations

from datetime import datetime, timezone

from odmantic import AIOEngine

from backend.main_backend.app.core.apis.schemas.requests.provider_sync_request import (
    ProviderWebhookPayload,
)
from backend.main_backend.app.core.models.transaction_model import (
    PaymentStatus,
    PolicyStatus,
    Transaction,
    TransactionStatus,
)
from backend.main_backend.app.core.models.webhook_event_model import (
    WebhookEvent,
    WebhookEventStatus,
)

from .service_exceptions import NotFoundServiceError


class ProviderSyncService:
    """Process provider-originated payment and policy updates."""

    async def process_provider_webhook(
        self,
        engine: AIOEngine,
        payload: ProviderWebhookPayload,
    ) -> WebhookEvent:
        """Persist a webhook event and apply supported transaction state changes."""
        event = WebhookEvent(
            event_type=payload.event_type,
            transaction_reference=payload.transaction_reference,
            provider_payment_reference=payload.provider_payment_reference,
            provider_policy_reference=payload.provider_policy_reference,
            payload=payload.payload,
            processing_status=WebhookEventStatus.RECEIVED,
        )
        await engine.save(event)

        transaction = await engine.find_one(
            Transaction,
            Transaction.transaction_reference == payload.transaction_reference,
        )
        if transaction is None:
            event.processing_status = WebhookEventStatus.FAILED
            event.processed_at = datetime.now(timezone.utc)
            await engine.save(event)
            raise NotFoundServiceError("The webhook references an unknown transaction.")

        self._apply_transaction_update(transaction, payload)
        transaction.updated_at = datetime.now(timezone.utc)
        await engine.save(transaction)

        event.processing_status = WebhookEventStatus.PROCESSED
        event.processed_at = datetime.now(timezone.utc)
        await engine.save(event)
        return event

    @staticmethod
    def _apply_transaction_update(
        transaction: Transaction,
        payload: ProviderWebhookPayload,
    ) -> None:
        """Map webhook semantics into transaction state transitions."""
        event_type = payload.event_type.upper()

        transaction.provider_payment_reference = (
            payload.provider_payment_reference or transaction.provider_payment_reference
        )
        transaction.provider_policy_reference = (
            payload.provider_policy_reference or transaction.provider_policy_reference
        )

        if event_type == "PAYMENT_SUCCESS":
            transaction.payment_status = PaymentStatus.SUCCESS
            transaction.transaction_status = TransactionStatus.PAYMENT_SUCCESS
        elif event_type == "PAYMENT_FAILED":
            transaction.payment_status = PaymentStatus.FAILED
            transaction.policy_status = PolicyStatus.FAILED
            transaction.transaction_status = TransactionStatus.PAYMENT_FAILED
        elif event_type in {"POLICY_ISSUED", "POLICY_GENERATED"}:
            transaction.payment_status = PaymentStatus.SUCCESS
            transaction.policy_status = PolicyStatus.ISSUED
            transaction.transaction_status = TransactionStatus.POLICY_ISSUED


provider_sync_service = ProviderSyncService()

