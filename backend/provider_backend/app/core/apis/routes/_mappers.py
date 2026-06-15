"""Response mapping helpers for provider backend API routes."""

from __future__ import annotations

from backend.provider_backend.app.core.apis.schemas.responses.payment_response import (
    MockPaymentSessionResponse,
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
from backend.provider_backend.app.core.apis.schemas.responses.sync_response import (
    ProviderSyncStatusResponse,
    RetryProcessingResponse,
)
from backend.provider_backend.app.core.models.broker_registry_model import BrokerRegistry
from backend.provider_backend.app.core.models.payment_model import Payment
from backend.provider_backend.app.core.models.policy_model import Policy
from backend.provider_backend.app.core.models.provider_quote_model import ProviderQuote
from backend.provider_backend.app.core.models.webhook_retry_model import WebhookRetry
from backend.provider_backend.app.core.services.provider_sync_service import (
    RetryProcessingResult,
)
from backend.provider_backend.app.core.services.payment_service import (
    MockPaymentSessionResult,
)


def _to_date(value: object) -> object:
    """Convert stored datetimes to plain dates for API responses."""
    return value.date() if hasattr(value, "date") else value


def _normalize_addon_payload(addon: object) -> ProviderQuoteAddonResponse:
    """Normalize stored add-on payloads into the public quote add-on response schema."""
    if isinstance(addon, ProviderQuoteAddonResponse):
        return addon
    if isinstance(addon, dict):
        return ProviderQuoteAddonResponse(
            addon_code=str(addon.get("addon_code", "")),
            addon_name=str(addon.get("addon_name", "")),
            addon_price=float(addon.get("addon_price", 0.0)),
        )
    return ProviderQuoteAddonResponse(
        addon_code="UNKNOWN",
        addon_name=str(addon),
        addon_price=0.0,
    )


def to_broker_response(broker: BrokerRegistry) -> BrokerRegistryResponse:
    """Convert a broker registry record into its API response schema."""
    return BrokerRegistryResponse(
        broker_code=broker.broker_code,
        broker_name=broker.broker_name,
        company_name=broker.company_name,
        license_number=broker.license_number,
        registration_number=broker.registration_number,
        contact_person_name=broker.contact_person_name,
        contact_email=broker.contact_email,
        contact_phone=broker.contact_phone,
        supported_insurance_types=broker.supported_insurance_types,
        active_regions=broker.active_regions,
        partner_provider_codes=broker.partner_provider_codes,
        notes=broker.notes,
        callback_url=broker.callback_url,
        webhook_url=broker.webhook_url,
        status=broker.status.value,
        created_at=broker.created_at,
        updated_at=broker.updated_at,
    )


def to_provider_quote_response(quote: ProviderQuote) -> ProviderQuoteResponse:
    """Convert a provider quote model into the public provider quote payload."""
    status_value = quote.status.value if hasattr(quote.status, "value") else str(quote.status)
    risk_category_value = (
        quote.risk_category.value if hasattr(quote.risk_category, "value") else str(quote.risk_category)
    ) if quote.risk_category else None
    return ProviderQuoteResponse(
        provider_quote_id=quote.provider_quote_id,
        provider_transaction_reference=quote.provider_transaction_reference,
        provider_name="Demo Provider",
        plan_code=quote.plan_code,
        plan_name=quote.plan_code.split(":", 1)[1] if ":" in quote.plan_code else quote.plan_code,
        base_premium=quote.base_premium,
        tax_amount=quote.tax_amount,
        total_premium=quote.total_premium,
        coverage_amount=quote.coverage_amount,
        risk_score=quote.risk_score,
        risk_category=risk_category_value,
        available_addons=[_normalize_addon_payload(addon) for addon in quote.available_addons],
        status=status_value,
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


def to_mock_payment_session_response(
    session: MockPaymentSessionResult,
) -> MockPaymentSessionResponse:
    """Convert a mock hosted-payment session into the frontend-facing response schema."""
    return MockPaymentSessionResponse(
        payment_reference=session.payment.payment_reference,
        payment_url=session.payment_url,
        amount=session.payment.amount,
        currency=session.payment.currency,
        available_payment_methods=session.available_payment_methods,
        status=session.status,
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
        issue_date=_to_date(policy.issue_date),
        start_date=_to_date(policy.start_date),
        end_date=_to_date(policy.end_date),
        policy_document_url=f"/api/v1/provider/policies/{policy.policy_number}/document",
    )


def to_sync_status_response(record: WebhookRetry) -> ProviderSyncStatusResponse:
    """Convert a webhook retry record into the provider sync response schema."""
    return ProviderSyncStatusResponse(
        event_type=record.event_type,
        main_transaction_reference=record.main_transaction_reference,
        status=record.status.value,
        retry_count=record.retry_count,
        next_retry_at=record.next_retry_at,
        last_error=record.last_error,
        updated_at=record.updated_at,
    )


def to_retry_processing_response(result: RetryProcessingResult) -> RetryProcessingResponse:
    """Convert a retry-processing result into the API summary schema."""
    return RetryProcessingResponse(
        processed_count=result.processed_count,
        success_count=result.success_count,
        failed_count=result.failed_count,
        records=[to_sync_status_response(record) for record in result.records],
    )
