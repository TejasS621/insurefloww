"""Payment status orchestration for the main backend."""

from __future__ import annotations

from datetime import datetime, timezone

from odmantic import AIOEngine

from backend.main_backend.app.core.models.transaction_model import (
    PaymentStatus,
    PolicyStatus,
    Transaction,
    TransactionStatus,
)

from .service_exceptions import ConflictServiceError, NotFoundServiceError


class PaymentService:
    """Manage payment state transitions on the main transaction ledger."""

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

