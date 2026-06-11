"""Payment services for the provider backend."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone

from odmantic import AIOEngine

from backend.provider_backend.app.core.apis.schemas.requests.payment_request import (
    PaymentSessionCreateRequest,
)
from backend.provider_backend.app.core.models.payment_model import (
    GatewayName,
    Payment,
    PaymentStatus,
)
from backend.provider_backend.app.core.models.provider_quote_model import ProviderQuote, ProviderQuoteStatus
from backend.provider_backend.app.core.models.provider_transaction_model import (
    ProviderTransaction,
    ProviderTransactionStatus,
)

from .service_exceptions import ConflictServiceError, NotFoundServiceError


class ProviderPaymentService:
    """Create and update provider-owned payment records."""

    async def create_payment_session(
        self,
        engine: AIOEngine,
        request_data: PaymentSessionCreateRequest,
    ) -> Payment:
        """Create a provider-side payment session and update transaction state."""
        provider_transaction = await engine.find_one(
            ProviderTransaction,
            ProviderTransaction.provider_transaction_reference
            == request_data.provider_transaction_reference,
        )
        if provider_transaction is None:
            raise NotFoundServiceError("Provider transaction not found for payment session creation.")

        quote = await engine.find_one(
            ProviderQuote,
            ProviderQuote.provider_quote_id == request_data.provider_quote_id,
        )
        if quote is None:
            raise NotFoundServiceError("Provider quote not found for payment session creation.")

        payment = Payment(
            payment_reference=self._generate_reference("PAY"),
            provider_transaction_reference=request_data.provider_transaction_reference,
            main_transaction_reference=request_data.main_transaction_reference,
            gateway_name=GatewayName.RAZORPAY,
            gateway_order_id=self._generate_reference("ORD"),
            amount=request_data.amount,
            currency=request_data.currency,
            payment_status=PaymentStatus.PENDING,
        )
        await engine.save(payment)

        provider_transaction.payment_reference = payment.payment_reference
        provider_transaction.quote_reference = request_data.provider_quote_id
        provider_transaction.gateway_order_id = payment.gateway_order_id
        provider_transaction.execution_status = ProviderTransactionStatus.PAYMENT_PENDING
        provider_transaction.updated_at = datetime.now(timezone.utc)
        await engine.save(provider_transaction)

        quote.status = ProviderQuoteStatus.PAYMENT_PENDING
        await engine.save(quote)
        return payment

    async def mark_payment_success(
        self,
        engine: AIOEngine,
        *,
        gateway_order_id: str,
        gateway_payment_id: str,
        gateway_signature: str,
    ) -> Payment:
        """Mark a payment as successful from an incoming webhook."""
        payment = await engine.find_one(Payment, Payment.gateway_order_id == gateway_order_id)
        if payment is None:
            raise NotFoundServiceError("Payment not found for the supplied gateway order identifier.")

        payment.gateway_payment_id = gateway_payment_id
        payment.gateway_signature = gateway_signature
        payment.payment_status = PaymentStatus.SUCCESS
        payment.updated_at = datetime.now(timezone.utc)
        await engine.save(payment)

        provider_transaction = await engine.find_one(
            ProviderTransaction,
            ProviderTransaction.provider_transaction_reference == payment.provider_transaction_reference,
        )
        if provider_transaction is None:
            raise ConflictServiceError("Provider transaction is missing for the successful payment.")

        provider_transaction.gateway_payment_id = gateway_payment_id
        provider_transaction.execution_status = ProviderTransactionStatus.PAYMENT_SUCCESS
        provider_transaction.updated_at = datetime.now(timezone.utc)
        await engine.save(provider_transaction)
        return payment

    @staticmethod
    def _generate_reference(prefix: str) -> str:
        """Generate a provider-side payment or order reference."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        return f"{prefix}-{timestamp}-{secrets.token_hex(3).upper()}"


provider_payment_service = ProviderPaymentService()

