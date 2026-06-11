"""Response mapping helpers for provider backend API routes."""

from __future__ import annotations

from backend.provider_backend.app.core.apis.schemas.responses.payment_response import (
    ProviderPaymentResponse,
)
from backend.provider_backend.app.core.apis.schemas.responses.policy_response import (
    ProviderPolicyResponse,
)
from backend.provider_backend.app.core.apis.schemas.responses.provider_quote_response import (
    ProviderQuoteAddonResponse,
    ProviderQuoteResponse,
)
from backend.provider_backend.app.core.apis.schemas.responses.provider_response import (
    BrokerRegistryResponse,
)
from backend.provider_backend.app.core.models.broker_registry_model import BrokerRegistry
from backend.provider_backend.app.core.models.payment_model import Payment
from backend.provider_backend.app.core.models.policy_model import Policy
from backend.provider_backend.app.core.models.provider_quote_model import ProviderQuote


def to_broker_response(broker: BrokerRegistry) -> BrokerRegistryResponse:
    """Convert a broker registry record into its API response schema."""
    return BrokerRegistryResponse(
        broker_code=broker.broker_code,
        broker_name=broker.broker_name,
        callback_url=broker.callback_url,
        webhook_url=broker.webhook_url,
        status=broker.status.value,
        created_at=broker.created_at,
        updated_at=broker.updated_at,
    )


def to_provider_quote_response(quote: ProviderQuote) -> ProviderQuoteResponse:
    """Convert a provider quote model into the public provider quote payload."""
    return ProviderQuoteResponse(
        provider_quote_id=quote.provider_quote_id,
        provider_transaction_reference=quote.provider_transaction_reference,
        plan_code=quote.plan_code,
        base_premium=quote.base_premium,
        tax_amount=quote.tax_amount,
        total_premium=quote.total_premium,
        coverage_amount=quote.coverage_amount,
        risk_score=quote.risk_score,
        risk_category=quote.risk_category.value if quote.risk_category else None,
        available_addons=[
            ProviderQuoteAddonResponse(
                addon_code=str(addon.get("addon_code", "")),
                addon_name=str(addon.get("addon_name", "")),
                addon_price=float(addon.get("addon_price", 0.0)),
            )
            for addon in quote.available_addons
        ],
        status=quote.status.value,
        expires_at=quote.expires_at,
    )


def to_provider_payment_response(payment: Payment) -> ProviderPaymentResponse:
    """Convert a provider payment record into the session response schema."""
    return ProviderPaymentResponse(
        gateway=payment.gateway_name.value,
        razorpay_key_id="rzp_test_insurefloww",
        razorpay_order_id=payment.gateway_order_id or "",
        provider_payment_reference=payment.payment_reference,
        amount=payment.amount,
        currency=payment.currency,
    )


def to_provider_policy_response(policy: Policy) -> ProviderPolicyResponse:
    """Convert a provider-issued policy model into the API response schema."""
    return ProviderPolicyResponse(
        policy_number=policy.policy_number,
        provider_transaction_reference=policy.provider_transaction_reference,
        main_transaction_reference=policy.main_transaction_reference,
        policy_status=policy.policy_status.value,
        coverage_amount=policy.coverage_amount,
        premium_amount=policy.premium_amount,
        issue_date=policy.issue_date,
        start_date=policy.start_date,
        end_date=policy.end_date,
        policy_document_url=policy.policy_document_url,
    )
