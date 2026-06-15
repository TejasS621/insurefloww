"""Provider-to-main synchronization services for the provider backend."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import httpx
from odmantic import AIOEngine

from backend.provider_backend.commons.config import settings
from backend.provider_backend.core.models.payment_model import Payment, PaymentStatus
from backend.provider_backend.core.models.policy_model import Policy, PolicyStatus
from backend.provider_backend.core.models.webhook_retry_model import (
    WebhookRetry,
    WebhookRetryStatus,
)

from .service_exceptions import ConflictServiceError, NotFoundServiceError


@dataclass(slots=True)
class RetryProcessingResult:
    """Structured result returned after processing due retry records."""

    processed_count: int
    success_count: int
    failed_count: int
    records: list[WebhookRetry]


class ProviderSyncService:
    """Dispatch provider events back to the main backend and track retries."""

    async def dispatch_payment_success(
        self,
        engine: AIOEngine,
        *,
        payment_reference: str,
    ) -> WebhookRetry:
        """Dispatch a payment-success synchronization event to the main backend."""
        payment = await engine.find_one(Payment, Payment.payment_reference == payment_reference)
        if payment is None:
            raise NotFoundServiceError("Payment not found for provider synchronization.")
        if payment.payment_status != PaymentStatus.SUCCESS:
            raise ConflictServiceError(
                "Provider synchronization requires a successful payment record."
            )

        payload = {
            "event_type": "PAYMENT_SUCCESS",
            "transaction_reference": payment.main_transaction_reference,
            "provider_payment_reference": payment.payment_reference,
            "provider_policy_reference": None,
            "payload": {
                "payment_reference": payment.payment_reference,
                "gateway_payment_id": payment.gateway_payment_id,
                "payment_status": payment.payment_status.value,
            },
        }
        return await self._dispatch_payload(
            engine,
            event_type="PAYMENT_SUCCESS",
            main_transaction_reference=payment.main_transaction_reference,
            payload=payload,
        )

    async def dispatch_policy_issued_for_payment(
        self,
        engine: AIOEngine,
        *,
        payment_reference: str,
    ) -> WebhookRetry:
        """Dispatch a policy-issued synchronization event for a successful payment."""
        payment = await engine.find_one(Payment, Payment.payment_reference == payment_reference)
        if payment is None:
            raise NotFoundServiceError("Payment not found for provider synchronization.")
        if payment.payment_status != PaymentStatus.SUCCESS:
            raise ConflictServiceError(
                "Provider synchronization requires a successful payment record."
            )

        policy = await engine.find_one(Policy, Policy.payment_reference == payment_reference)
        if policy is None:
            raise NotFoundServiceError("Policy not found for provider synchronization.")
        if policy.policy_status != PolicyStatus.ISSUED:
            raise ConflictServiceError("Only issued policies can be synchronized to the main backend.")

        payload = self._build_policy_issued_payload(payment=payment, policy=policy)
        return await self._dispatch_payload(
            engine,
            event_type="POLICY_ISSUED",
            main_transaction_reference=policy.main_transaction_reference,
            payload=payload,
        )

    async def process_due_retries(
        self,
        engine: AIOEngine,
        *,
        limit: int = 20,
    ) -> RetryProcessingResult:
        """Process retry records that are due for another synchronization attempt."""
        now = datetime.now(timezone.utc)
        records = await engine.find(WebhookRetry)
        due_records = [
            record
            for record in sorted(records, key=lambda item: item.updated_at)
            if record.status in {WebhookRetryStatus.PENDING, WebhookRetryStatus.RETRYING}
            and (record.next_retry_at is None or record.next_retry_at <= now)
        ][:limit]

        processed_records: list[WebhookRetry] = []
        success_count = 0
        failed_count = 0

        for record in due_records:
            processed = await self._dispatch_payload(
                engine,
                event_type=record.event_type,
                main_transaction_reference=record.main_transaction_reference,
                payload=record.payload,
                existing_record=record,
            )
            processed_records.append(processed)
            if processed.status == WebhookRetryStatus.SUCCESS:
                success_count += 1
            else:
                failed_count += 1

        return RetryProcessingResult(
            processed_count=len(processed_records),
            success_count=success_count,
            failed_count=failed_count,
            records=processed_records,
        )

    async def list_retry_records(self, engine: AIOEngine) -> list[WebhookRetry]:
        """Return all synchronization retry records ordered by most recent first."""
        records = await engine.find(WebhookRetry)
        return sorted(records, key=lambda item: item.updated_at, reverse=True)

    async def _dispatch_payload(
        self,
        engine: AIOEngine,
        *,
        event_type: str,
        main_transaction_reference: str,
        payload: dict[str, object],
        existing_record: WebhookRetry | None = None,
    ) -> WebhookRetry:
        """Dispatch a synchronization payload and persist retry state."""
        record = existing_record or await self._get_or_create_retry_record(
            engine,
            event_type=event_type,
            main_transaction_reference=main_transaction_reference,
            payload=payload,
        )

        try:
            async with httpx.AsyncClient(timeout=settings.sync_timeout_seconds) as client:
                response = await client.post(
                    settings.main_backend_sync_url,
                    json=payload,
                    headers={
                        "X-Broker-Code": settings.integration_broker_code,
                        "X-Broker-Api-Key": settings.integration_broker_api_key,
                    },
                )
                response.raise_for_status()
        except httpx.HTTPError as exc:
            await self._mark_retry_failure(engine, record, str(exc))
            return record

        record.status = WebhookRetryStatus.SUCCESS
        record.last_error = None
        record.next_retry_at = None
        record.updated_at = datetime.now(timezone.utc)
        await engine.save(record)
        return record

    async def _get_or_create_retry_record(
        self,
        engine: AIOEngine,
        *,
        event_type: str,
        main_transaction_reference: str,
        payload: dict[str, object],
    ) -> WebhookRetry:
        """Fetch or create a retry record for a sync event."""
        records = await engine.find(
            WebhookRetry,
            (WebhookRetry.event_type == event_type)
            & (WebhookRetry.main_transaction_reference == main_transaction_reference),
        )
        if records:
            record = max(records, key=lambda item: item.updated_at)
            record.payload = payload
            record.updated_at = datetime.now(timezone.utc)
            await engine.save(record)
            return record

        record = WebhookRetry(
            event_type=event_type,
            main_transaction_reference=main_transaction_reference,
            payload=payload,
        )
        await engine.save(record)
        return record

    async def _mark_retry_failure(
        self,
        engine: AIOEngine,
        record: WebhookRetry,
        error_message: str,
    ) -> None:
        """Persist a failed synchronization attempt and schedule the next retry."""
        record.retry_count += 1
        record.status = (
            WebhookRetryStatus.FAILED
            if record.retry_count >= settings.sync_max_retries
            else WebhookRetryStatus.RETRYING
        )
        record.last_error = error_message
        record.next_retry_at = (
            None
            if record.status == WebhookRetryStatus.FAILED
            else datetime.now(timezone.utc) + timedelta(seconds=settings.sync_retry_delay_seconds)
        )
        record.updated_at = datetime.now(timezone.utc)
        await engine.save(record)

    @staticmethod
    def _build_policy_issued_payload(
        *,
        payment: Payment,
        policy: Policy,
    ) -> dict[str, object]:
        """Build the outbound main-backend synchronization payload."""
        return {
            "event_type": "POLICY_ISSUED",
            "transaction_reference": policy.main_transaction_reference,
            "provider_payment_reference": payment.payment_reference,
            "provider_policy_reference": policy.policy_number,
            "payload": {
                "payment_reference": payment.payment_reference,
                "gateway_payment_id": payment.gateway_payment_id,
                "policy_number": policy.policy_number,
                "policy_status": policy.policy_status.value,
                "coverage_amount": policy.coverage_amount,
                "premium_amount": policy.premium_amount,
            },
        }


provider_sync_service = ProviderSyncService()
