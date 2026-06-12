"""Incoming webhook processing for the provider backend."""

from __future__ import annotations

from odmantic import AIOEngine

from backend.provider_backend.app.core.apis.schemas.requests.webhook_request import (
    PaymentSuccessWebhookRequest,
)
from backend.provider_backend.app.core.models.payment_model import Payment
from backend.provider_backend.app.core.models.policy_model import Policy

from .payment_service import provider_payment_service
from .policy_service import provider_policy_service
from .provider_sync_service import provider_sync_service


class WebhookService:
    """Coordinate provider-side payment webhook handling."""

    async def handle_payment_success(
        self,
        engine: AIOEngine,
        request_data: PaymentSuccessWebhookRequest,
    ) -> tuple[Payment, Policy]:
        """Apply a successful payment callback, issue a policy, and sync it upstream."""
        payment = await provider_payment_service.mark_payment_success(
            engine,
            gateway_order_id=request_data.gateway_order_id,
            gateway_payment_id=request_data.gateway_payment_id,
            gateway_signature=request_data.gateway_signature,
        )
        policy = await provider_policy_service.issue_policy_for_payment(
            engine,
            payment_reference=payment.payment_reference,
        )
        await provider_sync_service.dispatch_policy_issued_for_payment(
            engine,
            payment_reference=payment.payment_reference,
        )
        return payment, policy


webhook_service = WebhookService()

