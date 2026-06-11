"""Policy issuance services for the provider backend."""

from __future__ import annotations

import secrets
from datetime import date, datetime, timedelta, timezone

from odmantic import AIOEngine

from backend.provider_backend.app.core.models.payment_model import Payment, PaymentStatus
from backend.provider_backend.app.core.models.policy_model import Policy, PolicyStatus
from backend.provider_backend.app.core.models.provider_quote_model import ProviderQuote
from backend.provider_backend.app.core.models.provider_transaction_model import (
    ProviderTransaction,
    ProviderTransactionStatus,
)

from .service_exceptions import ConflictServiceError, NotFoundServiceError


class ProviderPolicyService:
    """Issue provider-side policies after successful payment confirmation."""

    async def issue_policy_for_payment(
        self,
        engine: AIOEngine,
        *,
        payment_reference: str,
    ) -> Policy:
        """Issue a policy for a successful payment if one does not already exist."""
        existing_policy = await engine.find_one(
            Policy,
            Policy.payment_reference == payment_reference,
        )
        if existing_policy is not None:
            return existing_policy

        payment = await engine.find_one(Payment, Payment.payment_reference == payment_reference)
        if payment is None:
            raise NotFoundServiceError("Payment not found for policy issuance.")
        if payment.payment_status != PaymentStatus.SUCCESS:
            raise ConflictServiceError("Policy issuance requires a successful payment.")

        provider_transaction = await engine.find_one(
            ProviderTransaction,
            ProviderTransaction.provider_transaction_reference == payment.provider_transaction_reference,
        )
        if provider_transaction is None:
            raise NotFoundServiceError("Provider transaction not found for policy issuance.")
        if not provider_transaction.quote_reference:
            raise ConflictServiceError("Provider transaction is missing an associated quote reference.")

        quote = await engine.find_one(
            ProviderQuote,
            ProviderQuote.provider_quote_id == provider_transaction.quote_reference,
        )
        if quote is None:
            raise NotFoundServiceError("Provider quote not found for policy issuance.")

        today = date.today()
        policy = Policy(
            policy_number=self._generate_policy_number(),
            provider_transaction_reference=provider_transaction.provider_transaction_reference,
            main_transaction_reference=provider_transaction.main_transaction_reference,
            payment_reference=payment.payment_reference,
            provider_quote_id=quote.provider_quote_id,
            policy_status=PolicyStatus.ISSUED,
            coverage_amount=quote.coverage_amount,
            premium_amount=quote.total_premium,
            issue_date=today,
            start_date=today,
            end_date=today + timedelta(days=365),
        )
        await engine.save(policy)

        provider_transaction.policy_reference = policy.policy_number
        provider_transaction.execution_status = ProviderTransactionStatus.POLICY_ISSUED
        provider_transaction.updated_at = datetime.now(timezone.utc)
        await engine.save(provider_transaction)
        return policy

    async def get_policy_by_number(
        self,
        engine: AIOEngine,
        *,
        policy_number: str,
    ) -> Policy | None:
        """Fetch a provider-issued policy by its external number."""
        return await engine.find_one(Policy, Policy.policy_number == policy_number)

    @staticmethod
    def _generate_policy_number() -> str:
        """Generate a unique policy number."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        return f"POL-{timestamp}-{secrets.token_hex(4).upper()}"


provider_policy_service = ProviderPolicyService()

