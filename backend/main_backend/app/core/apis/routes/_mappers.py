"""Response mapping helpers for main backend API routes."""

from __future__ import annotations

from backend.main_backend.app.core.apis.schemas.responses.admin_response import (
    BrokerRegistryResponse as AdminBrokerRegistryResponse,
)
from backend.main_backend.app.core.apis.schemas.responses.application_response import (
    ApplicationSummaryResponse,
)
from backend.main_backend.app.core.apis.schemas.responses.payment_response import (
    PaymentInitiationResponse,
)
from backend.main_backend.app.core.apis.schemas.responses.policy_response import (
    PolicySummaryResponse,
)
from backend.main_backend.app.core.apis.schemas.responses.provider_sync_response import (
    ProviderWebhookSyncResponse,
)
from backend.main_backend.app.core.apis.schemas.responses.quote_response import (
    NormalizedQuoteResponse,
    QuoteAddonResponse,
)
from backend.main_backend.app.core.apis.schemas.responses.ticket_response import (
    TicketResponse,
)
from backend.main_backend.app.core.apis.schemas.shared import (
    CoverageDetailsSchema,
    HealthDetailsSchema,
    PersonalDetailsSchema,
)
from backend.main_backend.app.core.models.application_model import Application
from backend.main_backend.app.core.models.quote_model import Quote
from backend.main_backend.app.core.models.ticket_model import Ticket
from backend.main_backend.app.core.models.transaction_model import Transaction
from backend.main_backend.app.core.models.webhook_event_model import WebhookEvent
from backend.provider_backend.app.core.models.broker_registry_model import BrokerRegistry
from backend.provider_backend.app.core.models.policy_model import Policy
from backend.main_backend.app.core.services.payment_service import ProviderHostedPaymentSession


def to_quote_response(quote: Quote) -> NormalizedQuoteResponse:
    """Convert a normalized quote model into an API response schema."""
    return NormalizedQuoteResponse(
        quote_id=quote.provider_quote_id,
        provider_name=quote.provider_name,
        plan_code=quote.plan_code,
        plan_name=quote.plan_name,
        base_premium=quote.base_premium,
        tax_amount=quote.tax_amount,
        total_premium=quote.total_premium,
        coverage_amount=quote.coverage_amount,
        available_addons=[
            QuoteAddonResponse(
                addon_code=str(addon.get("addon_code", "")),
                addon_name=str(addon.get("addon_name", "")),
                addon_price=float(addon.get("addon_price", 0.0)),
            )
            for addon in quote.available_addons
        ],
        quote_status=quote.quote_status.value,
        expires_at=quote.expires_at,
    )


def to_application_response(
    application: Application,
    *,
    quotes: list[Quote] | None = None,
) -> ApplicationSummaryResponse:
    """Convert an application aggregate into a frontend-friendly payload."""
    return ApplicationSummaryResponse(
        application_reference=application.application_reference,
        transaction_reference=application.transaction_reference,
        insurance_type=application.insurance_type.value,
        personal_details=PersonalDetailsSchema.model_validate(application.personal_details.model_dump()),
        health_details=(
            HealthDetailsSchema.model_validate(application.health_details.model_dump())
            if application.health_details
            else None
        ),
        coverage_details=CoverageDetailsSchema.model_validate(application.coverage_details.model_dump()),
        application_status=application.application_status.value,
        quotes=[to_quote_response(quote) for quote in quotes or []],
        created_at=application.created_at,
        updated_at=application.updated_at,
    )


def to_payment_initiation_response(
    session: ProviderHostedPaymentSession,
) -> PaymentInitiationResponse:
    """Build the frontend-facing hosted payment response returned by the main backend."""
    return PaymentInitiationResponse(
        payment_reference=session.payment_reference,
        payment_url=session.payment_url,
        amount=session.amount,
        currency=session.currency,
        available_payment_methods=session.available_payment_methods,
        status=session.status,
    )


def to_ticket_response(ticket: Ticket) -> TicketResponse:
    """Convert a ticket model into the public ticket schema."""
    return TicketResponse(
        ticket_reference=ticket.ticket_reference,
        transaction_reference=ticket.transaction_reference,
        category=ticket.category.value,
        priority=ticket.priority.value,
        status=ticket.status.value,
        subject=ticket.subject,
        message=ticket.message,
        admin_response=ticket.admin_response,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )


def to_provider_sync_response(event: WebhookEvent) -> ProviderWebhookSyncResponse:
    """Convert a stored webhook event into an acknowledgement payload."""
    return ProviderWebhookSyncResponse(
        event_type=event.event_type,
        transaction_reference=event.transaction_reference,
        processing_status=event.processing_status.value,
    )


def to_policy_summary_response(policy: Policy) -> PolicySummaryResponse:
    """Convert a provider-issued policy into the main backend policy view."""
    return PolicySummaryResponse(
        policy_number=policy.policy_number,
        transaction_reference=policy.main_transaction_reference,
        policy_status=policy.policy_status.value,
        coverage_amount=policy.coverage_amount,
        premium_amount=policy.premium_amount,
        issue_date=policy.issue_date,
        start_date=policy.start_date,
        end_date=policy.end_date,
        document_url=f"/api/v1/policies/{policy.policy_number}/view",
        created_at=policy.created_at,
    )


def to_admin_broker_response(broker: BrokerRegistry) -> AdminBrokerRegistryResponse:
    """Convert a provider broker record into the main admin response schema."""
    return AdminBrokerRegistryResponse(
        broker_code=broker.broker_code,
        broker_name=broker.broker_name,
        callback_url=broker.callback_url,
        webhook_url=broker.webhook_url,
        status=broker.status.value,
        created_by_admin=broker.created_by_admin,
        created_at=broker.created_at,
        updated_at=broker.updated_at,
    )
