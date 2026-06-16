"""
Handle admin routes for the main backend.

Args:
    None: This module defines the admin router covering broker management,
    provider management, tickets, underwriting, policies, transactions,
    payments, dashboard statistics, and audit-log workflows.

Returns:
    None: Route handlers return structured admin responses under `/api/v1/admin`.

Raises:
    HTTPException: Route handlers re-raise handled controller errors and
    normalize unexpected failures through the shared route guard.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from odmantic import AIOEngine

from backend.main_backend.commons.logger import get_logger
from backend.main_backend.core.apis.routes._helpers import route_guard
from backend.main_backend.core.apis.routes._mappers import (
    to_admin_application_response,
    to_admin_broker_response,
    to_admin_payment_response,
    to_admin_policy_response,
    to_admin_provider_response,
    to_admin_ticket_response,
    to_admin_transaction_detail_response,
    to_admin_transaction_response,
    to_audit_log_response,
    to_dashboard_statistics_response,
    to_status_count_response,
    to_underwriting_review_response,
)
from backend.main_backend.core.apis.routes.dependencies import get_current_admin_actor
from backend.main_backend.core.apis.schemas.requests.admin_request import (
    ApplicationReviewRequest,
    BrokerKeyRotationRequest,
    BrokerRegistrationRequest,
    BrokerStatusUpdateRequest,
    PolicyStatusUpdateRequest,
    ProviderRegistrationRequest,
    ProviderStatusUpdateRequest,
    TicketAssignmentRequest,
    TicketStatusUpdateRequest,
    UnderwritingReviewRequest,
)
from backend.main_backend.core.apis.schemas.responses.admin_response import (
    AdminApplicationResponse,
    AdminPaymentResponse,
    AdminPolicyResponse,
    AdminTicketResponse,
    AdminTransactionDetailResponse,
    AdminTransactionResponse,
    AuditLogResponse,
    BrokerRegistryResponse,
    DashboardStatisticsResponse,
    ProviderRegistryResponse,
    UnderwritingReviewResponse,
)
from backend.main_backend.core.apis.schemas.responses.common_response import APIResponse
from backend.main_backend.core.database.database import get_database
from backend.main_backend.core.models.application_model import Application
from backend.main_backend.core.services.admin_workflow_service import (
    admin_workflow_service,
)
from backend.main_backend.core.services.service_exceptions import ServiceError
from backend.provider_backend.core.apis.schemas.requests.provider_request import (
    BrokerRegistrationRequest as ProviderBrokerRegistrationRequest,
)
from backend.provider_backend.core.apis.schemas.requests.provider_request import (
    BrokerStatusUpdateRequest as ProviderBrokerStatusUpdateRequest,
)
from backend.provider_backend.core.apis.schemas.requests.provider_request import (
    KeyRotationRequest as ProviderKeyRotationRequest,
)
from backend.provider_backend.core.services.broker_service import broker_service

admin_router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])
logger = get_logger(__name__)


@admin_router.post(
    "/brokers",
    response_model=APIResponse[BrokerRegistryResponse],
    status_code=status.HTTP_201_CREATED,
)
@route_guard
async def register_broker(
    request_data: BrokerRegistrationRequest,
    engine: AIOEngine = Depends(get_database),
    actor_id: str = Depends(get_current_admin_actor),
) -> APIResponse[BrokerRegistryResponse]:
    """
    Register a broker through the admin orchestration API.

    Args:
        request_data: Validated broker-registration payload from the admin UI.
        engine: Active ODMantic database engine dependency.
        actor_id: Authenticated admin identifier used for audit ownership.

    Returns:
        APIResponse[BrokerRegistryResponse]: Newly registered broker details,
        including the one-time API key reveal payload.

    Raises:
        HTTPException: Re-raises controller validation errors or wraps
        unexpected exceptions as HTTP 500 responses.
    """
    try:
        broker, api_key = await broker_service.register_broker(
            engine,
            ProviderBrokerRegistrationRequest(
                broker_name=request_data.broker_name,
                broker_code=request_data.broker_code,
                company_name=request_data.company_name,
                license_number=request_data.license_number,
                registration_number=request_data.registration_number,
                contact_person_name=request_data.contact_person_name,
                contact_email=request_data.contact_email,
                contact_phone=request_data.contact_phone,
                supported_insurance_types=request_data.supported_insurance_types,
                active_regions=request_data.active_regions,
                partner_provider_codes=request_data.partner_provider_codes,
                notes=request_data.notes,
                created_by_admin=actor_id,
            ),
        )
        return APIResponse(
            message="Broker registered successfully.",
            data=to_admin_broker_response(broker).model_copy(update={"api_key": api_key}),
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception(
            "Failed to register broker '%s'.",
            request_data.broker_code,
        )
        raise


@admin_router.get("/brokers", response_model=APIResponse[list[BrokerRegistryResponse]])
@route_guard
async def list_brokers(
    engine: AIOEngine = Depends(get_database),
    _: str = Depends(get_current_admin_actor),
) -> APIResponse[list[BrokerRegistryResponse]]:
    """
    List all registered brokers for the admin console.

    Args:
        engine: Active ODMantic database engine dependency.
        _: Authenticated admin dependency enforcing admin-only access.

    Returns:
        APIResponse[list[BrokerRegistryResponse]]: Registered broker records
        formatted for admin views.

    Raises:
        HTTPException: Re-raises controller validation errors or wraps
        unexpected exceptions as HTTP 500 responses.
    """
    try:
        brokers = await broker_service.list_brokers(engine)
        return APIResponse(
            message="Brokers fetched successfully.",
            data=[to_admin_broker_response(broker) for broker in brokers],
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception("Failed to list brokers for the admin console.")
        raise


@admin_router.post(
    "/providers",
    response_model=APIResponse[ProviderRegistryResponse],
    status_code=status.HTTP_201_CREATED,
)
@route_guard
async def register_provider(
    request_data: ProviderRegistrationRequest,
    engine: AIOEngine = Depends(get_database),
    actor_id: str = Depends(get_current_admin_actor),
) -> APIResponse[ProviderRegistryResponse]:
    """
    Register a provider through the admin orchestration API.

    Args:
        request_data: Validated provider-registration payload from the admin UI.
        engine: Active ODMantic database engine dependency.
        actor_id: Authenticated admin identifier used for audit ownership.

    Returns:
        APIResponse[ProviderRegistryResponse]: Newly registered provider details.

    Raises:
        HTTPException: Re-raises controller validation errors or wraps
        unexpected exceptions as HTTP 500 responses.
    """
    try:
        provider = await admin_workflow_service.register_provider(
            engine,
            request_data=request_data,
            actor_id=actor_id,
        )
        return APIResponse(
            message="Provider registered successfully.",
            data=to_admin_provider_response(provider),
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception(
            "Failed to register provider '%s'.",
            request_data.provider_code,
        )
        raise


@admin_router.get("/providers", response_model=APIResponse[list[ProviderRegistryResponse]])
@route_guard
async def list_providers(
    engine: AIOEngine = Depends(get_database),
    _: str = Depends(get_current_admin_actor),
) -> APIResponse[list[ProviderRegistryResponse]]:
    """
    List all registered providers for the admin console.

    Args:
        engine: Active ODMantic database engine dependency.
        _: Authenticated admin dependency enforcing admin-only access.

    Returns:
        APIResponse[list[ProviderRegistryResponse]]: Registered provider records.

    Raises:
        HTTPException: Re-raises controller validation errors or wraps
        unexpected exceptions as HTTP 500 responses.
    """
    try:
        providers = await admin_workflow_service.list_providers(engine)
        return APIResponse(
            message="Providers fetched successfully.",
            data=[to_admin_provider_response(provider) for provider in providers],
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception("Failed to list providers for the admin console.")
        raise


@admin_router.patch(
    "/providers/{provider_code}/status",
    response_model=APIResponse[ProviderRegistryResponse],
)
@route_guard
async def update_provider_status(
    provider_code: str,
    request_data: ProviderStatusUpdateRequest,
    engine: AIOEngine = Depends(get_database),
    actor_id: str = Depends(get_current_admin_actor),
) -> APIResponse[ProviderRegistryResponse]:
    """
    Update the lifecycle status of a provider.

    Args:
        provider_code: Provider code identifying the target provider record.
        request_data: Validated status-update payload from the admin UI.
        engine: Active ODMantic database engine dependency.
        actor_id: Authenticated admin identifier used for audit ownership.

    Returns:
        APIResponse[ProviderRegistryResponse]: Updated provider registry record.

    Raises:
        HTTPException: Re-raises controller validation errors or wraps
        unexpected exceptions as HTTP 500 responses.
    """
    try:
        provider = await admin_workflow_service.update_provider_status(
            engine,
            provider_code=provider_code,
            request_data=request_data,
            actor_id=actor_id,
        )
        return APIResponse(
            message="Provider status updated successfully.",
            data=to_admin_provider_response(provider),
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception(
            "Failed to update provider status for '%s'.",
            provider_code,
        )
        raise


@admin_router.patch(
    "/brokers/{broker_code}/status",
    response_model=APIResponse[BrokerRegistryResponse],
)
@route_guard
async def update_broker_status(
    broker_code: str,
    request_data: BrokerStatusUpdateRequest,
    engine: AIOEngine = Depends(get_database),
    _: str = Depends(get_current_admin_actor),
) -> APIResponse[BrokerRegistryResponse]:
    """
    Update the lifecycle status of a broker.

    Args:
        broker_code: Broker code identifying the target broker record.
        request_data: Validated status-update payload from the admin UI.
        engine: Active ODMantic database engine dependency.
        _: Authenticated admin dependency enforcing admin-only access.

    Returns:
        APIResponse[BrokerRegistryResponse]: Updated broker registry record.

    Raises:
        HTTPException: Re-raises controller validation errors or wraps
        unexpected exceptions as HTTP 500 responses.
    """
    try:
        broker = await broker_service.update_broker_status(
            engine,
            broker_code=broker_code,
            request_data=ProviderBrokerStatusUpdateRequest(
                status=request_data.status.value,
                reason=request_data.reason,
            ),
        )
        return APIResponse(
            message="Broker status updated successfully.",
            data=to_admin_broker_response(broker),
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception(
            "Failed to update broker status for '%s'.",
            broker_code,
        )
        raise


@admin_router.put(
    "/brokers/{broker_code}/rotate-key",
    response_model=APIResponse[BrokerRegistryResponse],
)
@route_guard
async def rotate_broker_key(
    broker_code: str,
    request_data: BrokerKeyRotationRequest,
    engine: AIOEngine = Depends(get_database),
    actor_id: str = Depends(get_current_admin_actor),
) -> APIResponse[BrokerRegistryResponse]:
    """
    Rotate broker credentials through the admin API.

    Args:
        broker_code: Broker code identifying the target broker record.
        request_data: Validated key-rotation payload from the admin UI.
        engine: Active ODMantic database engine dependency.
        actor_id: Authenticated admin identifier used as the fallback actor.

    Returns:
        APIResponse[BrokerRegistryResponse]: Updated broker details with the
        one-time replacement API key reveal payload.

    Raises:
        HTTPException: Re-raises controller validation errors or wraps
        unexpected exceptions as HTTP 500 responses.
    """
    try:
        broker, api_key = await broker_service.rotate_broker_key(
            engine,
            broker_code=broker_code,
            request_data=ProviderKeyRotationRequest(
                rotated_by=request_data.initiated_by or actor_id,
                reason=request_data.reason,
            ),
        )
        return APIResponse(
            message="Broker key rotated successfully.",
            data=to_admin_broker_response(broker).model_copy(update={"api_key": api_key}),
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception(
            "Failed to rotate broker key for '%s'.",
            broker_code,
        )
        raise


@admin_router.get("/tickets", response_model=APIResponse[list[AdminTicketResponse]])
@route_guard
async def list_tickets(
    engine: AIOEngine = Depends(get_database),
    _: str = Depends(get_current_admin_actor),
) -> APIResponse[list[AdminTicketResponse]]:
    """
    List all customer support tickets for administrative review.

    Args:
        engine: Active ODMantic database engine dependency.
        _: Authenticated admin dependency enforcing admin-only access.

    Returns:
        APIResponse[list[AdminTicketResponse]]: Ticket records formatted for
        the admin ticket board.

    Raises:
        HTTPException: Re-raises controller validation errors or wraps
        unexpected exceptions as HTTP 500 responses.
    """
    try:
        tickets = await admin_workflow_service.list_tickets(engine)
        return APIResponse(
            message="Admin tickets fetched successfully.",
            data=[to_admin_ticket_response(ticket) for ticket in tickets],
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception("Failed to list admin tickets.")
        raise


@admin_router.get(
    "/tickets/{ticket_reference}",
    response_model=APIResponse[AdminTicketResponse],
)
@route_guard
async def get_ticket_detail(
    ticket_reference: str,
    engine: AIOEngine = Depends(get_database),
    _: str = Depends(get_current_admin_actor),
) -> APIResponse[AdminTicketResponse]:
    """
    Return one admin ticket detail record for the drawer workflow.

    Args:
        ticket_reference: Ticket reference identifying the target support ticket.
        engine: Active ODMantic database engine dependency.
        _: Authenticated admin dependency enforcing admin-only access.

    Returns:
        APIResponse[AdminTicketResponse]: Detailed ticket record for the admin drawer.

    Raises:
        HTTPException: Re-raises controller validation errors or wraps
        unexpected exceptions as HTTP 500 responses.
    """
    try:
        ticket = await admin_workflow_service.get_ticket_detail(
            engine,
            ticket_reference=ticket_reference,
        )
        return APIResponse(
            message="Admin ticket detail fetched successfully.",
            data=to_admin_ticket_response(ticket),
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception(
            "Failed to fetch admin ticket detail for '%s'.",
            ticket_reference,
        )
        raise


@admin_router.patch(
    "/tickets/{ticket_reference}/assignment",
    response_model=APIResponse[AdminTicketResponse],
)
@route_guard
async def assign_ticket(
    ticket_reference: str,
    request_data: TicketAssignmentRequest,
    engine: AIOEngine = Depends(get_database),
    actor_id: str = Depends(get_current_admin_actor),
) -> APIResponse[AdminTicketResponse]:
    """
    Assign a support ticket to an admin owner and persist an audit log.

    Args:
        ticket_reference: Ticket reference identifying the target support ticket.
        request_data: Validated assignment payload from the admin UI.
        engine: Active ODMantic database engine dependency.
        actor_id: Authenticated admin identifier used for audit ownership.

    Returns:
        APIResponse[AdminTicketResponse]: Updated assigned ticket record.

    Raises:
        HTTPException: Re-raises controller validation errors or wraps
        unexpected exceptions as HTTP 500 responses.
    """
    try:
        ticket = await admin_workflow_service.assign_ticket(
            engine,
            ticket_reference=ticket_reference,
            request_data=request_data,
            actor_id=actor_id,
        )
        return APIResponse(
            message="Ticket assigned successfully.",
            data=to_admin_ticket_response(ticket),
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception(
            "Failed to assign ticket '%s'.",
            ticket_reference,
        )
        raise


@admin_router.patch(
    "/tickets/{ticket_reference}/status",
    response_model=APIResponse[AdminTicketResponse],
)
@route_guard
async def update_ticket_status(
    ticket_reference: str,
    request_data: TicketStatusUpdateRequest,
    engine: AIOEngine = Depends(get_database),
    actor_id: str = Depends(get_current_admin_actor),
) -> APIResponse[AdminTicketResponse]:
    """
    Update a support ticket status and optional admin response.

    Args:
        ticket_reference: Ticket reference identifying the target support ticket.
        request_data: Validated status-update payload from the admin UI.
        engine: Active ODMantic database engine dependency.
        actor_id: Authenticated admin identifier used for audit ownership.

    Returns:
        APIResponse[AdminTicketResponse]: Updated ticket record.

    Raises:
        HTTPException: Re-raises controller validation errors or wraps
        unexpected exceptions as HTTP 500 responses.
    """
    try:
        ticket = await admin_workflow_service.update_ticket_status(
            engine,
            ticket_reference=ticket_reference,
            request_data=request_data,
            actor_id=actor_id,
        )
        return APIResponse(
            message="Ticket status updated successfully.",
            data=to_admin_ticket_response(ticket),
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception(
            "Failed to update ticket status for '%s'.",
            ticket_reference,
        )
        raise


@admin_router.get(
    "/applications",
    response_model=APIResponse[list[AdminApplicationResponse]],
)
@route_guard
async def list_applications(
    engine: AIOEngine = Depends(get_database),
    _: str = Depends(get_current_admin_actor),
) -> APIResponse[list[AdminApplicationResponse]]:
    """
    List all insurance applications for administrative review.

    Args:
        engine: Active ODMantic database engine dependency.
        _: Authenticated admin dependency enforcing admin-only access.

    Returns:
        APIResponse[list[AdminApplicationResponse]]: Application records
        formatted for administrative review.

    Raises:
        HTTPException: Re-raises controller validation errors or wraps
        unexpected exceptions as HTTP 500 responses.
    """
    try:
        applications = await admin_workflow_service.list_applications(engine)
        return APIResponse(
            message="Admin applications fetched successfully.",
            data=[to_admin_application_response(application) for application in applications],
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception("Failed to list admin applications.")
        raise


@admin_router.patch(
    "/applications/{application_reference}/review",
    response_model=APIResponse[AdminApplicationResponse],
)
@route_guard
async def review_application(
    application_reference: str,
    request_data: ApplicationReviewRequest,
    engine: AIOEngine = Depends(get_database),
    actor_id: str = Depends(get_current_admin_actor),
) -> APIResponse[AdminApplicationResponse]:
    """
    Review an application and apply an approve, reject, or cancel decision.

    Args:
        application_reference: Application reference identifying the target application.
        request_data: Validated review-decision payload from the admin UI.
        engine: Active ODMantic database engine dependency.
        actor_id: Authenticated admin identifier used for audit ownership.

    Returns:
        APIResponse[AdminApplicationResponse]: Updated application review result.

    Raises:
        HTTPException: Re-raises controller validation errors or wraps
        unexpected exceptions as HTTP 500 responses.
    """
    try:
        application = await admin_workflow_service.review_application(
            engine,
            application_reference=application_reference,
            request_data=request_data,
            actor_id=actor_id,
        )
        return APIResponse(
            message="Application review completed successfully.",
            data=to_admin_application_response(application),
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception(
            "Failed to review application '%s'.",
            application_reference,
        )
        raise


@admin_router.get(
    "/underwriting/reviews",
    response_model=APIResponse[list[UnderwritingReviewResponse]],
)
@route_guard
async def list_underwriting_reviews(
    engine: AIOEngine = Depends(get_database),
    _: str = Depends(get_current_admin_actor),
) -> APIResponse[list[UnderwritingReviewResponse]]:
    """
    List applications that require or merit manual underwriting review.

    Args:
        engine: Active ODMantic database engine dependency.
        _: Authenticated admin dependency enforcing admin-only access.

    Returns:
        APIResponse[list[UnderwritingReviewResponse]]: Underwriting review queue
        entries enriched with risk information.

    Raises:
        HTTPException: Re-raises controller validation errors or wraps
        unexpected exceptions as HTTP 500 responses.
    """
    try:
        review_items = await admin_workflow_service.list_underwriting_reviews(engine)
        return APIResponse(
            message="Underwriting review queue fetched successfully.",
            data=[
                to_underwriting_review_response(
                    item.application,
                    risk_flags=item.risk_flags,
                    highest_quote_risk_category=item.highest_quote_risk_category,
                )
                for item in review_items
            ],
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception("Failed to list underwriting review queue items.")
        raise


@admin_router.patch(
    "/underwriting/reviews/{application_reference}",
    response_model=APIResponse[AdminApplicationResponse],
)
@route_guard
async def process_underwriting_review(
    application_reference: str,
    request_data: UnderwritingReviewRequest,
    engine: AIOEngine = Depends(get_database),
    actor_id: str = Depends(get_current_admin_actor),
) -> APIResponse[AdminApplicationResponse]:
    """
    Apply a manual underwriting decision to an application in the review queue.

    Args:
        application_reference: Application reference identifying the target application.
        request_data: Validated underwriting decision payload from the admin UI.
        engine: Active ODMantic database engine dependency.
        actor_id: Authenticated admin identifier used for audit ownership.

    Returns:
        APIResponse[AdminApplicationResponse]: Updated application after
        underwriting review is completed.

    Raises:
        HTTPException: Re-raises controller validation errors or wraps
        unexpected exceptions as HTTP 500 responses.
    """
    try:
        application = await admin_workflow_service.process_underwriting_review(
            engine,
            application_reference=application_reference,
            request_data=request_data,
            actor_id=actor_id,
        )
        return APIResponse(
            message="Underwriting review completed successfully.",
            data=to_admin_application_response(application),
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception(
            "Failed to process underwriting review for '%s'.",
            application_reference,
        )
        raise


@admin_router.get("/policies", response_model=APIResponse[list[AdminPolicyResponse]])
@route_guard
async def list_policies(
    engine: AIOEngine = Depends(get_database),
    _: str = Depends(get_current_admin_actor),
) -> APIResponse[list[AdminPolicyResponse]]:
    """
    List all issued policies for administrative management.

    Args:
        engine: Active ODMantic database engine dependency.
        _: Authenticated admin dependency enforcing admin-only access.

    Returns:
        APIResponse[list[AdminPolicyResponse]]: Policy records formatted for admin views.

    Raises:
        HTTPException: Re-raises controller validation errors or wraps
        unexpected exceptions as HTTP 500 responses.
    """
    try:
        policies = await admin_workflow_service.list_policies(engine)
        return APIResponse(
            message="Admin policies fetched successfully.",
            data=[to_admin_policy_response(policy) for policy in policies],
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception("Failed to list admin policies.")
        raise


@admin_router.get(
    "/transactions",
    response_model=APIResponse[list[AdminTransactionResponse]],
)
@route_guard
async def list_transactions(
    status: str = Query(default="ALL"),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    engine: AIOEngine = Depends(get_database),
    _: str = Depends(get_current_admin_actor),
) -> APIResponse[list[AdminTransactionResponse]]:
    """
    List admin-visible transaction records with filtering and pagination.

    Args:
        status: Transaction status filter value from the admin UI.
        search: Optional search term for transaction, type, or customer lookup.
        page: Page number for paginated admin results.
        limit: Maximum number of records returned per page.
        engine: Active ODMantic database engine dependency.
        _: Authenticated admin dependency enforcing admin-only access.

    Returns:
        APIResponse[list[AdminTransactionResponse]]: Filtered and paginated
        transaction records formatted for the admin console.

    Raises:
        HTTPException: Re-raises controller validation errors or wraps
        unexpected exceptions as HTTP 500 responses.
    """
    try:
        transactions = await admin_workflow_service.list_transactions(engine)
        applications = await admin_workflow_service.list_applications(engine)
        application_by_reference = {
            application.transaction_reference: application
            for application in applications
            if application.transaction_reference
        }
        filtered = [
            transaction
            for transaction in transactions
            if admin_workflow_service.match_transaction_status_filter(transaction, status)
        ]
        if search:
            needle = search.strip().lower()
            filtered = [
                transaction
                for transaction in filtered
                if needle in transaction.transaction_reference.lower()
                or needle in transaction.application_snapshot.insurance_type.lower()
                or needle
                in (
                    f"{transaction.application_snapshot.personal_details.first_name} "
                    f"{transaction.application_snapshot.personal_details.last_name}"
                )
                .strip()
                .lower()
            ]
        start = (page - 1) * limit
        paged = filtered[start : start + limit]
        return APIResponse(
            message="Admin transactions fetched successfully.",
            data=[
                to_admin_transaction_response(
                    transaction,
                    application=application_by_reference.get(transaction.transaction_reference),
                )
                for transaction in paged
            ],
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception(
            "Failed to list admin transactions with status '%s' and page %s.",
            status,
            page,
        )
        raise


@admin_router.get(
    "/transactions/{transaction_reference}",
    response_model=APIResponse[AdminTransactionDetailResponse],
)
@route_guard
async def get_transaction_detail(
    transaction_reference: str,
    engine: AIOEngine = Depends(get_database),
    _: str = Depends(get_current_admin_actor),
) -> APIResponse[AdminTransactionDetailResponse]:
    """
    Return one transaction detail payload for the admin drawer.

    Args:
        transaction_reference: Transaction reference identifying the target record.
        engine: Active ODMantic database engine dependency.
        _: Authenticated admin dependency enforcing admin-only access.

    Returns:
        APIResponse[AdminTransactionDetailResponse]: Detailed transaction payload
        for the admin side drawer.

    Raises:
        HTTPException: Re-raises controller validation errors or wraps
        unexpected exceptions as HTTP 500 responses.
    """
    try:
        transaction = await admin_workflow_service.get_transaction_detail(
            engine,
            transaction_reference=transaction_reference,
        )
        application = (
            await engine.find_one(
                Application,
                Application.application_reference
                == transaction.application_snapshot.application_reference,
            )
            if transaction.application_snapshot.application_reference
            else None
        )
        return APIResponse(
            message="Admin transaction detail fetched successfully.",
            data=to_admin_transaction_detail_response(transaction, application=application),
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception(
            "Failed to fetch admin transaction detail for '%s'.",
            transaction_reference,
        )
        raise


@admin_router.get("/payments", response_model=APIResponse[list[AdminPaymentResponse]])
@route_guard
async def list_payments(
    status: str = Query(default="ALL"),
    search: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=10, ge=1, le=100),
    engine: AIOEngine = Depends(get_database),
    _: str = Depends(get_current_admin_actor),
) -> APIResponse[list[AdminPaymentResponse]]:
    """
    List admin-visible payment records with filtering and pagination.

    Args:
        status: Payment status filter value from the admin UI.
        search: Optional search term for payment reference or gateway lookup.
        page: Page number for paginated admin results.
        limit: Maximum number of records returned per page.
        engine: Active ODMantic database engine dependency.
        _: Authenticated admin dependency enforcing admin-only access.

    Returns:
        APIResponse[list[AdminPaymentResponse]]: Filtered and paginated payment
        records formatted for the admin console.

    Raises:
        HTTPException: Re-raises controller validation errors or wraps
        unexpected exceptions as HTTP 500 responses.
    """
    try:
        payments = await admin_workflow_service.list_payments(engine)
        filtered = [
            payment
            for payment in payments
            if admin_workflow_service.match_payment_status_filter(payment, status)
        ]
        if search:
            needle = search.strip().lower()
            filtered = [
                payment
                for payment in filtered
                if needle in payment.payment_reference.lower()
                or needle in payment.main_transaction_reference.lower()
                or needle in payment.gateway_name.value.lower()
            ]
        start = (page - 1) * limit
        paged = filtered[start : start + limit]
        return APIResponse(
            message="Admin payments fetched successfully.",
            data=[to_admin_payment_response(payment) for payment in paged],
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception(
            "Failed to list admin payments with status '%s' and page %s.",
            status,
            page,
        )
        raise


@admin_router.patch(
    "/policies/{policy_number}/status",
    response_model=APIResponse[AdminPolicyResponse],
)
@route_guard
async def update_policy_status(
    policy_number: str,
    request_data: PolicyStatusUpdateRequest,
    engine: AIOEngine = Depends(get_database),
    actor_id: str = Depends(get_current_admin_actor),
) -> APIResponse[AdminPolicyResponse]:
    """
    Update a policy lifecycle state and reflect it in linked transaction records.

    Args:
        policy_number: Policy number identifying the target policy record.
        request_data: Validated status-update payload from the admin UI.
        engine: Active ODMantic database engine dependency.
        actor_id: Authenticated admin identifier used for audit ownership.

    Returns:
        APIResponse[AdminPolicyResponse]: Updated policy record after the change.

    Raises:
        HTTPException: Re-raises controller validation errors or wraps
        unexpected exceptions as HTTP 500 responses.
    """
    try:
        policy = await admin_workflow_service.update_policy_status(
            engine,
            policy_number=policy_number,
            request_data=request_data,
            actor_id=actor_id,
        )
        return APIResponse(
            message="Policy status updated successfully.",
            data=to_admin_policy_response(policy),
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception(
            "Failed to update policy status for '%s'.",
            policy_number,
        )
        raise


@admin_router.get(
    "/dashboard",
    response_model=APIResponse[DashboardStatisticsResponse],
)
@route_guard
async def get_dashboard(
    engine: AIOEngine = Depends(get_database),
    _: str = Depends(get_current_admin_actor),
) -> APIResponse[DashboardStatisticsResponse]:
    """
    Return high-level dashboard metrics for admin operational monitoring.

    Args:
        engine: Active ODMantic database engine dependency.
        _: Authenticated admin dependency enforcing admin-only access.

    Returns:
        APIResponse[DashboardStatisticsResponse]: Aggregated dashboard metrics
        and status breakdowns for the admin console.

    Raises:
        HTTPException: Re-raises controller validation errors or wraps
        unexpected exceptions as HTTP 500 responses.
    """
    try:
        stats = await admin_workflow_service.get_dashboard_statistics(engine)
        return APIResponse(
            message="Admin dashboard statistics fetched successfully.",
            data=to_dashboard_statistics_response(
                total_applications=stats.total_applications,
                total_tickets=stats.total_tickets,
                total_policies=stats.total_policies,
                total_brokers=stats.total_brokers,
                total_audit_logs=stats.total_audit_logs,
                pending_underwriting_reviews=stats.pending_underwriting_reviews,
                application_status_breakdown=[
                    to_status_count_response(status_name, count)
                    for status_name, count in stats.application_status_breakdown
                ],
                ticket_status_breakdown=[
                    to_status_count_response(status_name, count)
                    for status_name, count in stats.ticket_status_breakdown
                ],
                policy_status_breakdown=[
                    to_status_count_response(status_name, count)
                    for status_name, count in stats.policy_status_breakdown
                ],
                broker_status_breakdown=[
                    to_status_count_response(status_name, count)
                    for status_name, count in stats.broker_status_breakdown
                ],
            ),
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception("Failed to fetch admin dashboard statistics.")
        raise


@admin_router.get("/audit-logs", response_model=APIResponse[list[AuditLogResponse]])
@route_guard
async def list_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    engine: AIOEngine = Depends(get_database),
    _: str = Depends(get_current_admin_actor),
) -> APIResponse[list[AuditLogResponse]]:
    """
    List the newest audit-log records captured for admin workflow actions.

    Args:
        limit: Maximum number of audit-log records returned to the admin UI.
        engine: Active ODMantic database engine dependency.
        _: Authenticated admin dependency enforcing admin-only access.

    Returns:
        APIResponse[list[AuditLogResponse]]: Recent audit-log records formatted
        for admin review.

    Raises:
        HTTPException: Re-raises controller validation errors or wraps
        unexpected exceptions as HTTP 500 responses.
    """
    try:
        logs = await admin_workflow_service.list_audit_logs(engine, limit=limit)
        return APIResponse(
            message="Audit logs fetched successfully.",
            data=[to_audit_log_response(log) for log in logs],
        )
    except ServiceError:
        raise
    except Exception:
        logger.exception(
            "Failed to list admin audit logs with limit %s.",
            limit,
        )
        raise
