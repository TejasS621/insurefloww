"""Admin routes for the main backend."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, status
from odmantic import AIOEngine

from backend.main_backend.app.core.apis.routes._mappers import (
    to_admin_application_response,
    to_admin_broker_response,
    to_admin_policy_response,
    to_admin_ticket_response,
    to_audit_log_response,
    to_dashboard_statistics_response,
    to_status_count_response,
    to_underwriting_review_response,
)
from backend.main_backend.app.core.apis.routes.dependencies import (
    get_current_admin_actor,
    get_optional_admin_email,
)
from backend.main_backend.app.core.apis.schemas.requests.admin_request import (
    ApplicationReviewRequest,
    BrokerKeyRotationRequest,
    BrokerRegistrationRequest,
    BrokerStatusUpdateRequest,
    PolicyStatusUpdateRequest,
    TicketAssignmentRequest,
    TicketStatusUpdateRequest,
    UnderwritingReviewRequest,
)
from backend.main_backend.app.core.apis.schemas.responses.admin_response import (
    AdminApplicationResponse,
    AdminPolicyResponse,
    AdminTicketResponse,
    AuditLogResponse,
    BrokerRegistryResponse,
    DashboardStatisticsResponse,
    UnderwritingReviewResponse,
)
from backend.main_backend.app.core.apis.schemas.responses.common_response import APIResponse
from backend.main_backend.app.core.database.database import get_database
from backend.main_backend.app.core.services.admin_workflow_service import admin_workflow_service
from backend.provider_backend.app.core.apis.schemas.requests.provider_request import (
    BrokerRegistrationRequest as ProviderBrokerRegistrationRequest,
    BrokerStatusUpdateRequest as ProviderBrokerStatusUpdateRequest,
    KeyRotationRequest as ProviderKeyRotationRequest,
)
from backend.provider_backend.app.core.services.broker_service import broker_service

admin_router = APIRouter(prefix="/api/v1/admin", tags=["Admin"])


@admin_router.post("/brokers", response_model=APIResponse[BrokerRegistryResponse], status_code=status.HTTP_201_CREATED)
async def register_broker(
    request_data: BrokerRegistrationRequest,
    engine: AIOEngine = Depends(get_database),
    admin_email: str | None = Depends(get_optional_admin_email),
) -> APIResponse[BrokerRegistryResponse]:
    """Register a broker through the admin orchestration API."""
    broker, _ = await broker_service.register_broker(
        engine,
        ProviderBrokerRegistrationRequest(
            broker_name=request_data.broker_name,
            broker_code=request_data.broker_code,
            callback_url=request_data.callback_url,
            webhook_url=request_data.webhook_url,
            created_by_admin=admin_email,
        ),
    )
    return APIResponse(
        message="Broker registered successfully.",
        data=to_admin_broker_response(broker),
    )


@admin_router.get("/brokers", response_model=APIResponse[list[BrokerRegistryResponse]])
async def list_brokers(
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[list[BrokerRegistryResponse]]:
    """List registered brokers."""
    brokers = await broker_service.list_brokers(engine)
    return APIResponse(
        message="Brokers fetched successfully.",
        data=[to_admin_broker_response(broker) for broker in brokers],
    )


@admin_router.patch("/brokers/{broker_code}/status", response_model=APIResponse[BrokerRegistryResponse])
async def update_broker_status(
    broker_code: str,
    request_data: BrokerStatusUpdateRequest,
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[BrokerRegistryResponse]:
    """Update the lifecycle status of a broker."""
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


@admin_router.put("/brokers/{broker_code}/rotate-key", response_model=APIResponse[BrokerRegistryResponse])
async def rotate_broker_key(
    broker_code: str,
    request_data: BrokerKeyRotationRequest,
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[BrokerRegistryResponse]:
    """Rotate broker credentials through the admin API."""
    broker, _ = await broker_service.rotate_broker_key(
        engine,
        broker_code=broker_code,
        request_data=ProviderKeyRotationRequest(
            rotated_by=request_data.initiated_by,
            reason=request_data.reason,
        ),
    )
    return APIResponse(
        message="Broker key rotated successfully.",
        data=to_admin_broker_response(broker),
    )


@admin_router.get("/tickets", response_model=APIResponse[list[AdminTicketResponse]])
async def list_tickets(
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[list[AdminTicketResponse]]:
    """List all customer support tickets for administrative review."""
    tickets = await admin_workflow_service.list_tickets(engine)
    return APIResponse(
        message="Admin tickets fetched successfully.",
        data=[to_admin_ticket_response(ticket) for ticket in tickets],
    )


@admin_router.patch("/tickets/{ticket_reference}/assignment", response_model=APIResponse[AdminTicketResponse])
async def assign_ticket(
    ticket_reference: str,
    request_data: TicketAssignmentRequest,
    engine: AIOEngine = Depends(get_database),
    actor_id: str = Depends(get_current_admin_actor),
) -> APIResponse[AdminTicketResponse]:
    """Assign a support ticket to an admin owner and persist an audit log."""
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


@admin_router.patch("/tickets/{ticket_reference}/status", response_model=APIResponse[AdminTicketResponse])
async def update_ticket_status(
    ticket_reference: str,
    request_data: TicketStatusUpdateRequest,
    engine: AIOEngine = Depends(get_database),
    actor_id: str = Depends(get_current_admin_actor),
) -> APIResponse[AdminTicketResponse]:
    """Update a support ticket status and optional admin response."""
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


@admin_router.get("/applications", response_model=APIResponse[list[AdminApplicationResponse]])
async def list_applications(
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[list[AdminApplicationResponse]]:
    """List all insurance applications for administrative review."""
    applications = await admin_workflow_service.list_applications(engine)
    return APIResponse(
        message="Admin applications fetched successfully.",
        data=[to_admin_application_response(application) for application in applications],
    )


@admin_router.patch("/applications/{application_reference}/review", response_model=APIResponse[AdminApplicationResponse])
async def review_application(
    application_reference: str,
    request_data: ApplicationReviewRequest,
    engine: AIOEngine = Depends(get_database),
    actor_id: str = Depends(get_current_admin_actor),
) -> APIResponse[AdminApplicationResponse]:
    """Review an application and apply an approve, reject, or cancel decision."""
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


@admin_router.get("/underwriting/reviews", response_model=APIResponse[list[UnderwritingReviewResponse]])
async def list_underwriting_reviews(
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[list[UnderwritingReviewResponse]]:
    """List applications that require or merit manual underwriting review."""
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


@admin_router.patch("/underwriting/reviews/{application_reference}", response_model=APIResponse[AdminApplicationResponse])
async def process_underwriting_review(
    application_reference: str,
    request_data: UnderwritingReviewRequest,
    engine: AIOEngine = Depends(get_database),
    actor_id: str = Depends(get_current_admin_actor),
) -> APIResponse[AdminApplicationResponse]:
    """Apply a manual underwriting decision to an application in the review queue."""
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


@admin_router.get("/policies", response_model=APIResponse[list[AdminPolicyResponse]])
async def list_policies(
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[list[AdminPolicyResponse]]:
    """List all issued policies for administrative management."""
    policies = await admin_workflow_service.list_policies(engine)
    return APIResponse(
        message="Admin policies fetched successfully.",
        data=[to_admin_policy_response(policy) for policy in policies],
    )


@admin_router.patch("/policies/{policy_number}/status", response_model=APIResponse[AdminPolicyResponse])
async def update_policy_status(
    policy_number: str,
    request_data: PolicyStatusUpdateRequest,
    engine: AIOEngine = Depends(get_database),
    actor_id: str = Depends(get_current_admin_actor),
) -> APIResponse[AdminPolicyResponse]:
    """Update a policy lifecycle state and reflect the change in linked transaction records."""
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


@admin_router.get("/dashboard", response_model=APIResponse[DashboardStatisticsResponse])
async def get_dashboard(
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[DashboardStatisticsResponse]:
    """Return high-level dashboard metrics for admin operational monitoring."""
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


@admin_router.get("/audit-logs", response_model=APIResponse[list[AuditLogResponse]])
async def list_audit_logs(
    limit: int = Query(default=100, ge=1, le=500),
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[list[AuditLogResponse]]:
    """List the newest audit log records captured for admin workflow actions."""
    logs = await admin_workflow_service.list_audit_logs(engine, limit=limit)
    return APIResponse(
        message="Audit logs fetched successfully.",
        data=[to_audit_log_response(log) for log in logs],
    )
