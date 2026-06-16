"""
Implement customer application lifecycle services for the main backend.

Args:
    None: This module defines the service layer responsible for application
    creation, journey resumption, and application retrieval.

Returns:
    None: Service methods return ODMantic models and typed service results
    used by the route layer.

Raises:
    ServiceError: Validation and conflict errors are raised from the service
    layer when application workflow rules are violated.
"""

from __future__ import annotations

import secrets
from dataclasses import dataclass
from datetime import datetime, time, timezone

from odmantic import AIOEngine

from backend.main_backend.commons.logger import get_logger
from backend.main_backend.core.apis.schemas.requests.application_request import (
    ApplicationCreateRequest,
)
from backend.main_backend.core.models.application_model import (
    Application,
    ApplicationStatus,
)
from backend.main_backend.core.models.insurance_details_model import InsuranceDetails
from backend.main_backend.core.models.shared import (
    ApplicationSnapshot,
    CoverageDetails,
    HealthDetails,
    InsuranceType as ModelInsuranceType,
    PersonalDetails,
)
from backend.main_backend.core.models.transaction_model import (
    Transaction,
    TransactionStatus,
)

from .service_exceptions import ConflictServiceError

logger = get_logger(__name__)


@dataclass(slots=True)
class ApplicationServiceResult:
    """Result payload returned after creating or resuming a journey."""

    resumed: bool
    application: Application
    transaction: Transaction
    insurance_details: InsuranceDetails | None


class ApplicationService:
    """
    Create, resume, and retrieve customer insurance applications.

    Args:
        None: Service state is derived from method inputs and database calls.

    Returns:
        None: Instance methods return typed application workflow results.

    Raises:
        ServiceError: Domain-specific service exceptions are raised when
        application workflow rules fail validation.
    """

    ACTIVE_STATUSES = {
        TransactionStatus.APPLICATION_SUBMITTED,
        TransactionStatus.QUOTE_GENERATED,
        TransactionStatus.QUOTE_SELECTED,
        TransactionStatus.PAYMENT_PENDING,
    }

    async def find_active_journey(
        self,
        engine: AIOEngine,
        *,
        mobile_number: str,
        insurance_type: str,
    ) -> tuple[Application | None, Transaction | None]:
        """
        Find an active transaction for a mobile number and insurance type.

        Args:
            engine: Active ODMantic database engine dependency.
            mobile_number: Customer mobile number used to match journeys.
            insurance_type: Insurance type used to scope the search.

        Returns:
            tuple[Application | None, Transaction | None]: Matching active
            application and transaction, or `(None, None)` if not found.

        Raises:
            ConflictServiceError: Propagates if downstream validation fails.
        """
        applications = await engine.find(
            Application,
            Application.insurance_type == ModelInsuranceType(insurance_type),
        )
        for application in sorted(
            applications, key=lambda item: item.created_at, reverse=True
        ):
            if application.personal_details.mobile_number != mobile_number:
                continue
            if not application.transaction_reference:
                continue
            transaction = await engine.find_one(
                Transaction,
                Transaction.transaction_reference == application.transaction_reference,
            )
            if transaction and transaction.transaction_status in self.ACTIVE_STATUSES:
                return application, transaction
        return None, None

    async def create_application(
        self,
        engine: AIOEngine,
        request_data: ApplicationCreateRequest,
        *,
        user_id: str | None = None,
    ) -> ApplicationServiceResult:
        """
        Create a new application or resume an active customer journey.

        Args:
            engine: Active ODMantic database engine dependency.
            request_data: Validated application payload from ApplicationCreateRequest.
            user_id: Optional authenticated customer identifier for ownership.

        Returns:
            ApplicationServiceResult: Persisted application, transaction, and
            insurance detail records for the customer journey.

        Raises:
            ConflictServiceError: Raised when a workflow rule prevents the
            application from being created or resumed safely.
        """
        existing_application, existing_transaction = await self.find_active_journey(
            engine,
            mobile_number=request_data.personal_details.mobile_number,
            insurance_type=request_data.insurance_type.value,
        )
        if existing_application and existing_transaction:
            logger.info(
                "Resuming active journey '%s' for mobile '%s' and insurance type '%s'.",
                existing_application.application_reference,
                request_data.personal_details.mobile_number,
                request_data.insurance_type.value,
            )
            insurance_details = await self._get_insurance_details(
                engine, existing_transaction
            )
            return ApplicationServiceResult(
                resumed=True,
                application=existing_application,
                transaction=existing_transaction,
                insurance_details=insurance_details,
            )

        application_reference = self._generate_reference(
            "APP", request_data.insurance_type.value
        )
        transaction_reference = self._generate_reference(
            "TXN", request_data.insurance_type.value
        )
        logger.info(
            "Creating new application '%s' with transaction '%s' for insurance type '%s'.",
            application_reference,
            transaction_reference,
            request_data.insurance_type.value,
        )

        personal_payload = request_data.personal_details.model_dump()
        personal_payload["date_of_birth"] = datetime.combine(
            request_data.personal_details.date_of_birth,
            time.min,
            tzinfo=timezone.utc,
        )
        personal_details = PersonalDetails(**personal_payload)
        health_details = (
            HealthDetails(
                **{
                    **request_data.health_details.model_dump(
                        exclude={"other_conditions"}
                    ),
                    "other_conditions": ", ".join(
                        request_data.health_details.other_conditions
                    )
                    if request_data.health_details.other_conditions
                    else None,
                }
            )
            if request_data.health_details
            else HealthDetails()
        )
        coverage_details = CoverageDetails(
            **request_data.coverage_details.model_dump()
        )

        application = Application(
            application_reference=application_reference,
            user_id=user_id,
            guest_identifier=request_data.guest_identifier,
            transaction_reference=transaction_reference,
            insurance_type=ModelInsuranceType(request_data.insurance_type.value),
            personal_details=personal_details,
            health_details=health_details,
            coverage_details=coverage_details,
            application_status=ApplicationStatus.APPLICATION_SUBMITTED,
        )
        await engine.save(application)

        insurance_details = InsuranceDetails(
            transaction_reference=transaction_reference,
            insurance_type=ModelInsuranceType(request_data.insurance_type.value),
            coverage_amount=request_data.coverage_details.coverage_amount,
            tenure=request_data.coverage_details.tenure_years,
            sum_insured=request_data.coverage_details.sum_insured,
            insured_members=request_data.coverage_details.insured_members,
            health_details=health_details,
            coverage_details=coverage_details,
        )
        await engine.save(insurance_details)

        transaction = Transaction(
            transaction_reference=transaction_reference,
            application_id=str(application.id),
            insurance_details_id=str(insurance_details.id),
            transaction_status=TransactionStatus.APPLICATION_SUBMITTED,
            application_snapshot=ApplicationSnapshot(
                application_reference=application_reference,
                insurance_type=request_data.insurance_type.value,
                personal_details=personal_details,
                health_details=health_details,
                coverage_details=coverage_details,
            ),
        )
        await engine.save(transaction)

        application.transaction_id = str(transaction.id)
        application.updated_at = datetime.now(timezone.utc)
        await engine.save(application)

        return ApplicationServiceResult(
            resumed=False,
            application=application,
            transaction=transaction,
            insurance_details=insurance_details,
        )

    async def get_application_by_reference(
        self,
        engine: AIOEngine,
        application_reference: str,
    ) -> Application | None:
        """
        Fetch a single application by its external reference.

        Args:
            engine: Active ODMantic database engine dependency.
            application_reference: Human-readable application reference value.

        Returns:
            Application | None: Matching application record if one exists.

        Raises:
            ConflictServiceError: Propagates if a database workflow rule fails.
        """
        return await engine.find_one(
            Application,
            Application.application_reference == application_reference,
        )

    async def list_user_applications(
        self,
        engine: AIOEngine,
        *,
        user_id: str,
    ) -> list[Application]:
        """
        List applications owned by a specific customer identifier.

        Args:
            engine: Active ODMantic database engine dependency.
            user_id: Authenticated user identifier used for ownership lookup.

        Returns:
            list[Application]: All applications owned by the supplied user.

        Raises:
            ConflictServiceError: Raised when the provided user identifier is invalid.
        """
        if not user_id.strip():
            raise ConflictServiceError("A valid user identifier is required.")
        return await engine.find(Application, Application.user_id == user_id)

    async def _get_insurance_details(
        self,
        engine: AIOEngine,
        transaction: Transaction,
    ) -> InsuranceDetails | None:
        """
        Fetch insurance details associated with a transaction.

        Args:
            engine: Active ODMantic database engine dependency.
            transaction: Transaction whose insurance details should be loaded.

        Returns:
            InsuranceDetails | None: Matching insurance details record if present.

        Raises:
            ConflictServiceError: Propagates if downstream validation fails.
        """
        if not transaction.insurance_details_id:
            return None
        records = await engine.find(
            InsuranceDetails,
            InsuranceDetails.transaction_reference == transaction.transaction_reference,
        )
        return records[0] if records else None

    @staticmethod
    def _generate_reference(prefix: str, insurance_type: str) -> str:
        """
        Generate a human-readable external reference value.

        Args:
            prefix: Reference prefix such as `APP` or `TXN`.
            insurance_type: Insurance type used to embed context in the ID.

        Returns:
            str: Generated reference value suitable for external use.

        Raises:
            ValueError: Propagates if invalid reference inputs are supplied.
        """
        date_part = datetime.now(timezone.utc).strftime("%Y%m%d")
        random_part = secrets.token_hex(3).upper()
        return f"{prefix}-{insurance_type[:3].upper()}-{date_part}-{random_part}"


application_service = ApplicationService()
