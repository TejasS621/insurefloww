"""Admin workflow services for ticketing, reviews, dashboards, policies, and audit logs."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone

from odmantic import AIOEngine

from backend.main_backend.app.core.apis.schemas.requests.admin_request import (
    ApplicationReviewDecision,
    ApplicationReviewRequest,
    PolicyAdminStatus,
    PolicyStatusUpdateRequest,
    TicketAssignmentRequest,
    TicketStatusUpdateRequest,
    UnderwritingDecision,
    UnderwritingReviewRequest,
)
from backend.main_backend.app.core.models.application_model import (
    Application,
    ApplicationStatus,
)
from backend.main_backend.app.core.models.audit_log_model import AuditAction, AuditLog
from backend.main_backend.app.core.models.quote_model import Quote
from backend.main_backend.app.core.models.ticket_model import Ticket, TicketStatus
from backend.main_backend.app.core.models.transaction_model import (
    PaymentStatus as MainPaymentStatus,
    PolicyStatus as MainPolicyStatus,
    Transaction,
    TransactionStatus,
)
from backend.provider_backend.app.core.models.broker_registry_model import BrokerRegistry
from backend.provider_backend.app.core.models.payment_model import (
    Payment as ProviderPayment,
    PaymentStatus as ProviderPaymentStatus,
)
from backend.provider_backend.app.core.models.policy_model import (
    Policy,
    PolicyStatus as ProviderPolicyStatus,
)
from backend.provider_backend.app.core.models.provider_quote_model import (
    ProviderQuote,
    RiskCategory,
)

from .service_exceptions import NotFoundServiceError


@dataclass(slots=True)
class UnderwritingReviewItem:
    """Application and risk details returned by underwriting review queues."""

    application: Application
    risk_flags: list[str]
    highest_quote_risk_category: str | None


@dataclass(slots=True)
class DashboardStatistics:
    """Aggregated counts and breakdowns for the admin dashboard."""

    total_applications: int
    total_tickets: int
    total_policies: int
    total_brokers: int
    total_audit_logs: int
    pending_underwriting_reviews: int
    application_status_breakdown: list[tuple[str, int]]
    ticket_status_breakdown: list[tuple[str, int]]
    policy_status_breakdown: list[tuple[str, int]]
    broker_status_breakdown: list[tuple[str, int]]


class AdminWorkflowService:
    """Coordinate admin-specific workflows across the main and provider data models."""

    async def list_tickets(self, engine: AIOEngine) -> list[Ticket]:
        """Return all tickets ordered from newest to oldest."""
        tickets = await engine.find(Ticket)
        return sorted(tickets, key=lambda item: item.updated_at, reverse=True)

    async def get_ticket_detail(self, engine: AIOEngine, *, ticket_reference: str) -> Ticket:
        """Return one ticket for the admin drawer view."""
        return await self._get_ticket(engine, ticket_reference)

    async def assign_ticket(
        self,
        engine: AIOEngine,
        *,
        ticket_reference: str,
        request_data: TicketAssignmentRequest,
        actor_id: str,
    ) -> Ticket:
        """Assign a support ticket to an admin and write an audit record."""
        ticket = await self._get_ticket(engine, ticket_reference)
        old_state = self._serialize_ticket(ticket)
        ticket.assigned_admin_id = request_data.assigned_admin_id
        ticket.updated_at = datetime.now(timezone.utc)
        await engine.save(ticket)
        await self._create_audit_log(
            engine,
            actor_id=actor_id,
            action=AuditAction.UPDATE,
            entity_type="ticket_assignment",
            entity_id=ticket.ticket_reference,
            transaction_reference=ticket.transaction_reference,
            old_state=old_state,
            new_state={
                **self._serialize_ticket(ticket),
                "assignment_note": request_data.assignment_note,
            },
        )
        return ticket

    async def update_ticket_status(
        self,
        engine: AIOEngine,
        *,
        ticket_reference: str,
        request_data: TicketStatusUpdateRequest,
        actor_id: str,
    ) -> Ticket:
        """Update a ticket status, optional admin response, and audit the change."""
        ticket = await self._get_ticket(engine, ticket_reference)
        old_state = self._serialize_ticket(ticket)
        ticket.status = TicketStatus(request_data.status.value)
        if request_data.admin_response is not None:
            ticket.admin_response = request_data.admin_response
        ticket.updated_at = datetime.now(timezone.utc)
        await engine.save(ticket)
        await self._create_audit_log(
            engine,
            actor_id=actor_id,
            action=AuditAction.STATUS_CHANGE,
            entity_type="ticket",
            entity_id=ticket.ticket_reference,
            transaction_reference=ticket.transaction_reference,
            old_state=old_state,
            new_state=self._serialize_ticket(ticket),
        )
        return ticket

    async def list_applications(self, engine: AIOEngine) -> list[Application]:
        """Return all applications ordered from newest to oldest."""
        applications = await engine.find(Application)
        return sorted(applications, key=lambda item: item.updated_at, reverse=True)

    async def review_application(
        self,
        engine: AIOEngine,
        *,
        application_reference: str,
        request_data: ApplicationReviewRequest,
        actor_id: str,
    ) -> Application:
        """Apply an admin review decision to an application and linked transaction."""
        application = await self._get_application(engine, application_reference)
        transaction = await self._get_transaction_for_application(engine, application)
        old_state = self._serialize_application(application)

        if request_data.decision == ApplicationReviewDecision.APPROVE:
            new_status = self._approved_application_status(application)
            application.application_status = new_status
            if transaction is not None:
                transaction.transaction_status = self._transaction_status_for_application(new_status)
        elif request_data.decision == ApplicationReviewDecision.REJECT:
            application.application_status = ApplicationStatus.REJECTED
            if transaction is not None:
                transaction.transaction_status = TransactionStatus.REJECTED
        else:
            application.application_status = ApplicationStatus.CANCELLED
            if transaction is not None:
                transaction.transaction_status = TransactionStatus.CANCELLED

        application.updated_at = datetime.now(timezone.utc)
        await engine.save(application)
        if transaction is not None:
            transaction.updated_at = datetime.now(timezone.utc)
            await engine.save(transaction)

        await self._create_audit_log(
            engine,
            actor_id=actor_id,
            action=AuditAction.STATUS_CHANGE,
            entity_type="application_review",
            entity_id=application.application_reference,
            transaction_reference=application.transaction_reference,
            old_state=old_state,
            new_state={
                **self._serialize_application(application),
                "reason": request_data.reason,
            },
        )
        return application

    async def list_underwriting_reviews(self, engine: AIOEngine) -> list[UnderwritingReviewItem]:
        """Return applications that merit manual underwriting attention."""
        applications = await self.list_applications(engine)
        review_items: list[UnderwritingReviewItem] = []
        for application in applications:
            if application.application_status not in {
                ApplicationStatus.APPLICATION_SUBMITTED,
                ApplicationStatus.QUOTE_GENERATED,
                ApplicationStatus.QUOTE_SELECTED,
            }:
                continue
            risk_flags = self._extract_risk_flags(application)
            highest_quote_risk_category = await self._get_highest_quote_risk_category(
                engine,
                transaction_reference=application.transaction_reference,
            )
            if not risk_flags and highest_quote_risk_category is None:
                continue
            review_items.append(
                UnderwritingReviewItem(
                    application=application,
                    risk_flags=risk_flags,
                    highest_quote_risk_category=highest_quote_risk_category,
                )
            )
        return review_items

    async def process_underwriting_review(
        self,
        engine: AIOEngine,
        *,
        application_reference: str,
        request_data: UnderwritingReviewRequest,
        actor_id: str,
    ) -> Application:
        """Apply a manual underwriting decision and audit the outcome."""
        application = await self._get_application(engine, application_reference)
        transaction = await self._get_transaction_for_application(engine, application)
        old_state = self._serialize_application(application)

        if request_data.decision == UnderwritingDecision.APPROVE:
            new_status = self._approved_application_status(application)
            application.application_status = new_status
            if transaction is not None:
                transaction.transaction_status = self._transaction_status_for_application(new_status)
        else:
            application.application_status = ApplicationStatus.REJECTED
            if transaction is not None:
                transaction.transaction_status = TransactionStatus.REJECTED

        application.updated_at = datetime.now(timezone.utc)
        await engine.save(application)
        if transaction is not None:
            transaction.updated_at = datetime.now(timezone.utc)
            await engine.save(transaction)

        await self._create_audit_log(
            engine,
            actor_id=actor_id,
            action=AuditAction.STATUS_CHANGE,
            entity_type="underwriting_review",
            entity_id=application.application_reference,
            transaction_reference=application.transaction_reference,
            old_state=old_state,
            new_state={
                **self._serialize_application(application),
                "decision": request_data.decision.value,
                "notes": request_data.notes,
            },
        )
        return application

    async def list_policies(self, engine: AIOEngine) -> list[Policy]:
        """Return all issued policies ordered from newest to oldest."""
        policies = await engine.find(Policy)
        return sorted(policies, key=lambda item: item.updated_at, reverse=True)

    async def list_transactions(self, engine: AIOEngine) -> list[Transaction]:
        """Return all transactions ordered from newest to oldest."""
        transactions = await engine.find(Transaction)
        return sorted(transactions, key=lambda item: item.updated_at, reverse=True)

    async def get_transaction_detail(
        self,
        engine: AIOEngine,
        *,
        transaction_reference: str,
    ) -> Transaction:
        """Return one transaction for the admin drawer view."""
        transaction = await engine.find_one(
            Transaction,
            Transaction.transaction_reference == transaction_reference,
        )
        if transaction is None:
            raise NotFoundServiceError("The requested transaction could not be found.")
        return transaction

    async def list_payments(self, engine: AIOEngine) -> list[ProviderPayment]:
        """Return all provider payments ordered from newest to oldest."""
        payments = await engine.find(ProviderPayment)
        return sorted(payments, key=lambda item: item.updated_at, reverse=True)

    async def update_policy_status(
        self,
        engine: AIOEngine,
        *,
        policy_number: str,
        request_data: PolicyStatusUpdateRequest,
        actor_id: str,
    ) -> Policy:
        """Update a policy status and reflect related state on the main transaction."""
        policy = await engine.find_one(Policy, Policy.policy_number == policy_number)
        if policy is None:
            raise NotFoundServiceError("The requested policy could not be found.")

        old_state = self._serialize_policy(policy)
        policy.policy_status = ProviderPolicyStatus(request_data.status.value)
        policy.updated_at = datetime.now(timezone.utc)
        await engine.save(policy)

        transaction = await engine.find_one(
            Transaction,
            Transaction.transaction_reference == policy.main_transaction_reference,
        )
        if transaction is not None:
            if request_data.status == PolicyAdminStatus.CANCELLED:
                transaction.policy_status = MainPolicyStatus.CANCELLED
                transaction.transaction_status = TransactionStatus.CANCELLED
            elif request_data.status == PolicyAdminStatus.EXPIRED:
                transaction.transaction_status = TransactionStatus.EXPIRED
            elif request_data.status == PolicyAdminStatus.ISSUED:
                transaction.policy_status = MainPolicyStatus.ISSUED
                transaction.transaction_status = TransactionStatus.POLICY_ISSUED
            transaction.updated_at = datetime.now(timezone.utc)
            await engine.save(transaction)

        await self._create_audit_log(
            engine,
            actor_id=actor_id,
            action=AuditAction.STATUS_CHANGE,
            entity_type="policy",
            entity_id=policy.policy_number,
            transaction_reference=policy.main_transaction_reference,
            old_state=old_state,
            new_state={
                **self._serialize_policy(policy),
                "reason": request_data.reason,
            },
        )
        return policy

    async def get_dashboard_statistics(self, engine: AIOEngine) -> DashboardStatistics:
        """Aggregate high-level counters and status breakdowns for the admin dashboard."""
        applications = await engine.find(Application)
        tickets = await engine.find(Ticket)
        policies = await engine.find(Policy)
        brokers = await engine.find(BrokerRegistry)
        audit_logs = await engine.find(AuditLog)
        underwriting_reviews = await self.list_underwriting_reviews(engine)

        return DashboardStatistics(
            total_applications=len(applications),
            total_tickets=len(tickets),
            total_policies=len(policies),
            total_brokers=len(brokers),
            total_audit_logs=len(audit_logs),
            pending_underwriting_reviews=len(underwriting_reviews),
            application_status_breakdown=self._counter_to_pairs(
                Counter(application.application_status.value for application in applications)
            ),
            ticket_status_breakdown=self._counter_to_pairs(
                Counter(ticket.status.value for ticket in tickets)
            ),
            policy_status_breakdown=self._counter_to_pairs(
                Counter(policy.policy_status.value for policy in policies)
            ),
            broker_status_breakdown=self._counter_to_pairs(
                Counter(broker.status.value for broker in brokers)
            ),
        )

    @staticmethod
    def match_transaction_status_filter(transaction: Transaction, status: str) -> bool:
        """Return whether a transaction matches the admin status filter."""
        normalized = status.strip().upper()
        if normalized in {"", "ALL"}:
            return True
        if normalized == "SUCCESS":
            return (
                transaction.payment_status.value == "SUCCESS"
                or transaction.transaction_status in {TransactionStatus.PAYMENT_SUCCESS, TransactionStatus.POLICY_ISSUED}
            )
        if normalized == "FAILED":
            return (
                transaction.payment_status.value == "FAILED"
                or transaction.transaction_status == TransactionStatus.PAYMENT_FAILED
            )
        if normalized == "PENDING":
            return transaction.payment_status in {
                MainPaymentStatus.NOT_INITIATED,
                MainPaymentStatus.PENDING,
            } or transaction.transaction_status in {
                TransactionStatus.APPLICATION_SUBMITTED,
                TransactionStatus.QUOTE_GENERATED,
                TransactionStatus.QUOTE_SELECTED,
                TransactionStatus.PAYMENT_PENDING,
            }
        return transaction.transaction_status.value == normalized or transaction.payment_status.value == normalized

    @staticmethod
    def match_payment_status_filter(payment: ProviderPayment, status: str) -> bool:
        """Return whether a payment matches the admin status filter."""
        normalized = status.strip().upper()
        if normalized in {"", "ALL"}:
            return True
        if normalized == "PENDING":
            return payment.payment_status in {ProviderPaymentStatus.CREATED, ProviderPaymentStatus.PENDING}
        return payment.payment_status.value == normalized

    async def list_audit_logs(self, engine: AIOEngine, *, limit: int = 100) -> list[AuditLog]:
        """Return the newest audit log records up to the supplied limit."""
        logs = await engine.find(AuditLog)
        return sorted(logs, key=lambda item: item.created_at, reverse=True)[:limit]

    async def _get_ticket(self, engine: AIOEngine, ticket_reference: str) -> Ticket:
        """Fetch a ticket by reference or raise a typed not-found error."""
        ticket = await engine.find_one(Ticket, Ticket.ticket_reference == ticket_reference)
        if ticket is None:
            raise NotFoundServiceError("The requested ticket could not be found.")
        return ticket

    async def _get_application(self, engine: AIOEngine, application_reference: str) -> Application:
        """Fetch an application by reference or raise a typed not-found error."""
        application = await engine.find_one(
            Application,
            Application.application_reference == application_reference,
        )
        if application is None:
            raise NotFoundServiceError("The requested application could not be found.")
        return application

    async def _get_transaction_for_application(
        self,
        engine: AIOEngine,
        application: Application,
    ) -> Transaction | None:
        """Fetch the linked main transaction for an application when it exists."""
        if not application.transaction_reference:
            return None
        return await engine.find_one(
            Transaction,
            Transaction.transaction_reference == application.transaction_reference,
        )

    async def _get_highest_quote_risk_category(
        self,
        engine: AIOEngine,
        *,
        transaction_reference: str | None,
    ) -> str | None:
        """Return the highest available provider quote risk category for a transaction."""
        if transaction_reference is None:
            return None
        provider_quotes = await engine.find(
            ProviderQuote,
            ProviderQuote.main_transaction_reference == transaction_reference,
        )
        categories = {
            quote.risk_category.value
            for quote in provider_quotes
            if quote.risk_category is not None
        }
        if RiskCategory.HIGH.value in categories:
            return RiskCategory.HIGH.value
        if RiskCategory.MEDIUM.value in categories:
            return RiskCategory.MEDIUM.value
        if RiskCategory.LOW.value in categories:
            return RiskCategory.LOW.value
        return None

    async def _create_audit_log(
        self,
        engine: AIOEngine,
        *,
        actor_id: str,
        action: AuditAction,
        entity_type: str,
        entity_id: str,
        transaction_reference: str | None,
        old_state: dict[str, object] | None,
        new_state: dict[str, object] | None,
    ) -> AuditLog:
        """Persist an audit log entry for a mutating admin operation."""
        audit_log = AuditLog(
            actor_id=actor_id,
            actor_role="ADMIN",
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            transaction_reference=transaction_reference,
            old_state=old_state,
            new_state=new_state,
        )
        await engine.save(audit_log)
        return audit_log

    @staticmethod
    def _approved_application_status(application: Application) -> ApplicationStatus:
        """Return the best next status for an application after admin approval."""
        if application.application_status == ApplicationStatus.APPLICATION_SUBMITTED:
            return ApplicationStatus.QUOTE_GENERATED
        return application.application_status

    @staticmethod
    def _transaction_status_for_application(status: ApplicationStatus) -> TransactionStatus:
        """Map an application status into the nearest main transaction status."""
        return TransactionStatus(status.value)

    @staticmethod
    def _extract_risk_flags(application: Application) -> list[str]:
        """Extract simple risk flags from health-related application details."""
        if application.health_details is None:
            return []
        flags: list[str] = []
        if application.health_details.smoker:
            flags.append("SMOKER")
        if application.health_details.diabetes:
            flags.append("DIABETES")
        if application.health_details.blood_pressure:
            flags.append("BLOOD_PRESSURE")
        if application.health_details.heart_ailments:
            flags.append("HEART_AILMENTS")
        if application.health_details.pre_existing_disease:
            flags.append("PRE_EXISTING_DISEASE")
        if application.health_details.other_conditions:
            flags.extend(
                item.strip()
                for item in application.health_details.other_conditions.split(",")
                if item.strip()
            )
        return flags

    @staticmethod
    def _counter_to_pairs(counter: Counter[str]) -> list[tuple[str, int]]:
        """Convert a counter into a sorted list of status-count pairs."""
        return sorted(counter.items(), key=lambda item: item[0])

    @staticmethod
    def _serialize_ticket(ticket: Ticket) -> dict[str, object]:
        """Serialize a ticket into a small audit-friendly state snapshot."""
        return {
            "status": ticket.status.value,
            "assigned_admin_id": ticket.assigned_admin_id,
            "admin_response": ticket.admin_response,
        }

    @staticmethod
    def _serialize_application(application: Application) -> dict[str, object]:
        """Serialize an application into a small audit-friendly state snapshot."""
        return {
            "application_status": application.application_status.value,
            "transaction_reference": application.transaction_reference,
        }

    @staticmethod
    def _serialize_policy(policy: Policy) -> dict[str, object]:
        """Serialize a policy into a small audit-friendly state snapshot."""
        return {
            "policy_status": policy.policy_status.value,
            "document_url": policy.policy_document_url,
        }


admin_workflow_service = AdminWorkflowService()
