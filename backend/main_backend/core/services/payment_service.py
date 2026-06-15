"""Payment status orchestration for the main backend."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

import httpx
from odmantic import AIOEngine

from backend.main_backend.commons.config import settings
from backend.main_backend.core.models.transaction_model import (
    PaymentStatus,
    PolicyStatus,
    Transaction,
    TransactionStatus,
)

from .service_exceptions import ConflictServiceError, IntegrationServiceError, NotFoundServiceError


@dataclass(slots=True)
class ProviderHostedPaymentSession:
    """Frontend-facing hosted payment session returned by the provider backend."""

    payment_reference: str
    payment_url: str
    amount: float
    currency: str
    available_payment_methods: list[str]
    status: str


class PaymentService:
    """Manage payment state transitions on the main transaction ledger."""

    async def request_provider_hosted_payment_session(
        self,
        *,
        transaction_reference: str,
        quote_reference: str,
        amount: float,
        customer_full_name: str,
        customer_email: str,
        customer_mobile_number: str,
        selected_payment_method: str | None = None,
    ) -> ProviderHostedPaymentSession:
        """Request a hosted mock payment session from the provider backend."""
        payload = {
            "transaction_reference": transaction_reference,
            "quote_reference": quote_reference,
            "amount": amount,
            "currency": "INR",
            "customer": {
                "full_name": customer_full_name,
                "email": customer_email,
                "mobile_number": customer_mobile_number,
            },
            "selected_payment_method": selected_payment_method,
        }

        try:
            async with httpx.AsyncClient(timeout=settings.provider_request_timeout_seconds) as client:
                response = await client.post(
                    settings.provider_payment_create_url,
                    json=payload,
                    headers={
                        "X-Broker-Code": settings.integration_broker_code,
                        "X-Broker-Api-Key": settings.integration_broker_api_key,
                    },
                )
        except httpx.HTTPError as exc:
            raise IntegrationServiceError(
                "Unable to reach the provider backend to create a payment session."
            ) from exc

        if response.status_code >= 400:
            try:
                response_payload = response.json()
            except ValueError:
                response_payload = {}
            provider_message = response_payload.get(
                "message",
                "Provider backend rejected the payment session request.",
            )
            raise IntegrationServiceError(provider_message)

        try:
            response_payload = response.json()
        except ValueError as exc:
            raise IntegrationServiceError(
                "Provider backend returned an invalid payment session response."
            ) from exc

        session_data = response_payload.get("data")
        if not isinstance(session_data, dict):
            raise IntegrationServiceError(
                "Provider backend returned a malformed payment session payload."
            )
        payment_reference = str(session_data.get("payment_reference", ""))
        payment_url = str(session_data.get("payment_url", ""))
        if not payment_reference or not payment_url:
            raise IntegrationServiceError(
                "Provider backend returned an incomplete payment session payload."
            )

        return ProviderHostedPaymentSession(
            payment_reference=payment_reference,
            payment_url=payment_url,
            amount=float(session_data.get("amount", amount)),
            currency=str(session_data.get("currency", "INR")),
            available_payment_methods=[
                str(method) for method in session_data.get("available_payment_methods", [])
            ],
            status=str(session_data.get("status", "PAYMENT_INITIATED")),
        )

    async def mark_payment_initiated(
        self,
        engine: AIOEngine,
        *,
        transaction_reference: str,
        provider_payment_reference: str,
        checkout_metadata: dict[str, object],
    ) -> Transaction:
        """Move a transaction into a payment-pending state."""
        transaction = await engine.find_one(
            Transaction,
            Transaction.transaction_reference == transaction_reference,
        )
        if transaction is None:
            raise NotFoundServiceError("Transaction not found for payment initiation.")
        if not transaction.selected_quote_id:
            raise ConflictServiceError("A quote must be selected before payment is initiated.")

        transaction.provider_payment_reference = provider_payment_reference
        transaction.checkout_metadata = checkout_metadata
        transaction.payment_status = PaymentStatus.PENDING
        transaction.transaction_status = TransactionStatus.PAYMENT_PENDING
        transaction.updated_at = datetime.now(timezone.utc)
        await engine.save(transaction)
        return transaction

    async def mark_payment_result(
        self,
        engine: AIOEngine,
        *,
        transaction_reference: str,
        payment_succeeded: bool,
        provider_payment_reference: str | None = None,
        provider_policy_reference: str | None = None,
    ) -> Transaction:
        """Apply a provider-originated payment result to a transaction."""
        transaction = await engine.find_one(
            Transaction,
            Transaction.transaction_reference == transaction_reference,
        )
        if transaction is None:
            raise NotFoundServiceError("Transaction not found for payment update.")

        transaction.provider_payment_reference = (
            provider_payment_reference or transaction.provider_payment_reference
        )

        if payment_succeeded:
            transaction.payment_status = PaymentStatus.SUCCESS
            transaction.transaction_status = TransactionStatus.PAYMENT_SUCCESS
            if provider_policy_reference:
                transaction.provider_policy_reference = provider_policy_reference
                transaction.policy_status = PolicyStatus.ISSUED
                transaction.transaction_status = TransactionStatus.POLICY_ISSUED
        else:
            transaction.payment_status = PaymentStatus.FAILED
            transaction.transaction_status = TransactionStatus.PAYMENT_FAILED
            transaction.policy_status = PolicyStatus.FAILED

        transaction.updated_at = datetime.now(timezone.utc)
        await engine.save(transaction)
        return transaction


payment_service = PaymentService()

