"""Payment services for the provider backend."""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, timezone

from odmantic import AIOEngine

from backend.provider_backend.app.core.apis.schemas.requests.payment_request import (
    MockPaymentCreateRequest,
    PaymentSessionCreateRequest,
)
from backend.provider_backend.app.commons.config import settings
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


@dataclass(slots=True)
class MockPaymentSessionResult:
    """Frontend-ready hosted payment session details."""

    payment: Payment
    payment_url: str
    available_payment_methods: list[str]
    status: str


class ProviderPaymentService:
    """Create and update provider-owned payment records."""

    AVAILABLE_PAYMENT_METHODS = ["UPI", "CARD", "NETBANKING", "WALLET"]

    async def create_payment_session(
        self,
        engine: AIOEngine,
        request_data: PaymentSessionCreateRequest,
    ) -> Payment:
        """Create a provider-side payment session and update transaction state."""
        payment, _, _ = await self._create_payment_record(
            engine,
            provider_transaction_reference=request_data.provider_transaction_reference,
            main_transaction_reference=request_data.main_transaction_reference,
            provider_quote_id=request_data.provider_quote_id,
            amount=request_data.amount,
            currency=request_data.currency,
        )
        return payment

    async def create_mock_payment_session(
        self,
        engine: AIOEngine,
        request_data: MockPaymentCreateRequest,
    ) -> MockPaymentSessionResult:
        """Create a mock hosted payment session that the frontend can redirect to."""
        provider_transaction = await engine.find_one(
            ProviderTransaction,
            ProviderTransaction.main_transaction_reference == request_data.transaction_reference,
        )
        if provider_transaction is None:
            raise NotFoundServiceError("Provider transaction not found for payment creation.")

        payment, _, _ = await self._create_payment_record(
            engine,
            provider_transaction_reference=provider_transaction.provider_transaction_reference,
            main_transaction_reference=request_data.transaction_reference,
            provider_quote_id=request_data.quote_reference,
            amount=request_data.amount,
            currency=request_data.currency,
        )
        payment_url = self._build_mock_payment_url(payment.payment_reference)
        return MockPaymentSessionResult(
            payment=payment,
            payment_url=payment_url,
            available_payment_methods=self.AVAILABLE_PAYMENT_METHODS.copy(),
            status="PAYMENT_INITIATED",
        )

    async def get_payment_by_reference(
        self,
        engine: AIOEngine,
        *,
        payment_reference: str,
    ) -> Payment | None:
        """Fetch a provider payment record by its external reference."""
        return await engine.find_one(Payment, Payment.payment_reference == payment_reference)

    async def _create_payment_record(
        self,
        engine: AIOEngine,
        *,
        provider_transaction_reference: str,
        main_transaction_reference: str,
        provider_quote_id: str,
        amount: float,
        currency: str,
    ) -> tuple[Payment, ProviderTransaction, ProviderQuote]:
        """Create a provider payment record and mark related quote and transaction as pending."""
        provider_transaction = await engine.find_one(
            ProviderTransaction,
            ProviderTransaction.provider_transaction_reference == provider_transaction_reference,
        )
        if provider_transaction is None:
            raise NotFoundServiceError("Provider transaction not found for payment session creation.")

        quote = await engine.find_one(
            ProviderQuote,
            ProviderQuote.provider_quote_id == provider_quote_id,
        )
        if quote is None:
            raise NotFoundServiceError("Provider quote not found for payment session creation.")
        if quote.main_transaction_reference != main_transaction_reference:
            raise ConflictServiceError(
                "The selected quote does not belong to the supplied transaction reference."
            )

        payment = Payment(
            payment_reference=self._generate_reference("PAY"),
            provider_transaction_reference=provider_transaction_reference,
            main_transaction_reference=main_transaction_reference,
            gateway_name=GatewayName.RAZORPAY,
            gateway_order_id=self._generate_reference("ORD"),
            amount=amount,
            currency=currency,
            payment_status=PaymentStatus.PENDING,
        )
        await engine.save(payment)

        provider_transaction.payment_reference = payment.payment_reference
        provider_transaction.quote_reference = provider_quote_id
        provider_transaction.gateway_order_id = payment.gateway_order_id
        provider_transaction.execution_status = ProviderTransactionStatus.PAYMENT_PENDING
        provider_transaction.updated_at = datetime.now(timezone.utc)
        await engine.save(provider_transaction)

        quote.status = ProviderQuoteStatus.PAYMENT_PENDING
        await engine.save(quote)
        return payment, provider_transaction, quote

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

    @staticmethod
    def _build_mock_payment_url(payment_reference: str) -> str:
        """Build the mock hosted-payment URL returned to the frontend."""
        return f"{settings.mock_payment_base_url.rstrip('/')}/{payment_reference}"


provider_payment_service = ProviderPaymentService()

