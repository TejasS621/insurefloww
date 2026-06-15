"""
Implement provider-side quote generation services for the provider backend.

Args:
    None: This module defines the service layer responsible for creating
    provider transactions and generating quote records.

Returns:
    None: Service methods return persisted provider quote records used by the
    provider API and synchronization flows.

Raises:
    ServiceError: Validation and integration errors are raised when quote
    generation cannot be completed safely.
"""

from __future__ import annotations

import secrets
from datetime import datetime, time, timedelta, timezone

from odmantic import AIOEngine

from backend.provider_backend.core.apis.schemas.requests.provider_quote_request import (
    ProviderQuoteCreateRequest,
)
from backend.provider_backend.core.models.addon_model import AddOn, AddOnStatus
from backend.provider_backend.core.models.insurance_plan_model import (
    InsurancePlan,
    InsurancePlanStatus,
)
from backend.provider_backend.core.models.provider_quote_model import (
    ProviderQuote,
    ProviderQuoteStatus,
)
from backend.provider_backend.core.models.provider_transaction_model import (
    ProviderTransaction,
    ProviderTransactionStatus,
)
from backend.provider_backend.core.models.shared import (
    ApplicationSnapshot,
    CoverageDetails,
    HealthDetails,
    InsuranceType as ModelInsuranceType,
    PersonalDetails,
)

from .premium_engine import premium_engine
from .risk_engine import risk_engine


class ProviderQuoteService:
    """
    Generate provider-side quotes and maintain provider transaction state.

    Args:
        None: Service state is derived from method inputs and database calls.

    Returns:
        None: Instance methods return provider quote workflow results.

    Raises:
        ServiceError: Domain-specific service exceptions are raised when
        provider quote generation fails validation.
    """

    async def generate_quotes(
        self,
        engine: AIOEngine,
        request_data: ProviderQuoteCreateRequest,
    ) -> list[ProviderQuote]:
        """
        Generate one or more provider quotes for an incoming quote request.

        Args:
            engine: Active ODMantic database engine dependency.
            request_data: Validated provider quote request payload.

        Returns:
            list[ProviderQuote]: Persisted provider quote records generated for
            the supplied application and provider context.

        Raises:
            ServiceError: Propagates when provider quote generation or
            persistence cannot be completed safely.
        """
        insurance_type = ModelInsuranceType(request_data.insurance_type.value)
        provider_transaction = await self._get_or_create_provider_transaction(
            engine, request_data
        )
        active_plans = await engine.find(
            InsurancePlan,
            (InsurancePlan.provider_code == request_data.provider_code)
            & (InsurancePlan.insurance_type == insurance_type)
            & (InsurancePlan.status == InsurancePlanStatus.ACTIVE),
        )
        plans = active_plans or self._build_fallback_plans(request_data)

        addons = await engine.find(
            AddOn,
            (AddOn.provider_code == request_data.provider_code)
            & (AddOn.insurance_type == insurance_type)
            & (AddOn.status == AddOnStatus.ACTIVE),
        )
        addon_payload = [
            {
                "addon_code": addon.addon_code,
                "addon_name": addon.addon_name,
                "addon_price": addon.addon_price,
            }
            for addon in addons
        ]

        snapshot = ApplicationSnapshot(
            application_reference=request_data.application_reference,
            insurance_type=request_data.insurance_type.value,
            personal_details=PersonalDetails(
                **{
                    **request_data.personal_details.model_dump(),
                    "date_of_birth": datetime.combine(
                        request_data.personal_details.date_of_birth,
                        time.min,
                        tzinfo=timezone.utc,
                    ),
                }
            ),
            health_details=(
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
            ),
            coverage_details=CoverageDetails(**request_data.coverage_details.model_dump()),
        )

        risk_assessment = risk_engine.assess(
            date_of_birth=request_data.personal_details.date_of_birth,
            health_details=request_data.health_details,
        )

        stored_quotes: list[ProviderQuote] = []
        for index, plan in enumerate(plans, start=1):
            plan_code = getattr(
                plan, "plan_code", f"{request_data.insurance_type.value}-PLAN-{index}"
            )
            plan_name = getattr(
                plan, "plan_name", f"{request_data.insurance_type.value.title()} Plan {index}"
            )
            plan_multiplier = 1.0 + ((index - 1) * 0.12)
            premium = premium_engine.calculate(
                insurance_type=insurance_type,
                coverage_amount=request_data.coverage_details.coverage_amount,
                risk_category=risk_assessment.risk_category,
                plan_multiplier=plan_multiplier,
            )

            quote = ProviderQuote(
                provider_transaction_reference=provider_transaction.provider_transaction_reference,
                main_transaction_reference=request_data.main_transaction_reference,
                provider_quote_id=self._generate_reference("PQT"),
                plan_code=f"{plan_code}:{plan_name}",
                base_premium=premium.base_premium,
                tax_amount=premium.tax_amount,
                total_premium=premium.total_premium,
                coverage_amount=request_data.coverage_details.coverage_amount,
                risk_score=risk_assessment.risk_score,
                risk_category=risk_assessment.risk_category,
                available_addons=addon_payload,
                application_snapshot=snapshot,
                status=ProviderQuoteStatus.GENERATED,
                expires_at=datetime.now(timezone.utc) + timedelta(minutes=30),
            )
            await engine.save(quote)
            stored_quotes.append(quote)

        provider_transaction.execution_status = (
            ProviderTransactionStatus.QUOTE_GENERATED
        )
        provider_transaction.quote_reference = (
            stored_quotes[0].provider_quote_id if stored_quotes else None
        )
        provider_transaction.updated_at = datetime.now(timezone.utc)
        await engine.save(provider_transaction)
        return stored_quotes

    async def _get_or_create_provider_transaction(
        self,
        engine: AIOEngine,
        request_data: ProviderQuoteCreateRequest,
    ) -> ProviderTransaction:
        """
        Fetch or create the provider transaction linked to a main transaction.

        Args:
            engine: Active ODMantic database engine dependency.
            request_data: Validated provider quote request payload.

        Returns:
            ProviderTransaction: Existing or newly created provider transaction.

        Raises:
            ServiceError: Propagates if provider transaction persistence fails.
        """
        provider_transaction = await engine.find_one(
            ProviderTransaction,
            ProviderTransaction.main_transaction_reference
            == request_data.main_transaction_reference,
        )
        if provider_transaction is not None:
            return provider_transaction

        provider_transaction = ProviderTransaction(
            provider_transaction_reference=self._generate_reference("PTX"),
            main_transaction_reference=request_data.main_transaction_reference,
            provider_code=request_data.provider_code,
            broker_code=request_data.broker_code,
            application_reference=request_data.application_reference,
            insurance_type=ModelInsuranceType(request_data.insurance_type.value),
        )
        await engine.save(provider_transaction)
        return provider_transaction

    @staticmethod
    def _build_fallback_plans(
        request_data: ProviderQuoteCreateRequest,
    ) -> list[InsurancePlan]:
        """
        Create in-memory fallback plans when catalog data is unavailable.

        Args:
            request_data: Validated provider quote request payload.

        Returns:
            list[InsurancePlan]: In-memory fallback plan definitions.

        Raises:
            ValueError: Propagates if request values cannot build valid plans.
        """
        return [
            InsurancePlan(
                plan_code=f"{request_data.insurance_type.value}-BASIC",
                provider_code=request_data.provider_code,
                insurance_type=ModelInsuranceType(request_data.insurance_type.value),
                plan_name=f"{request_data.insurance_type.value.title()} Basic",
                coverage_options=[request_data.coverage_details.coverage_amount],
            ),
            InsurancePlan(
                plan_code=f"{request_data.insurance_type.value}-PLUS",
                provider_code=request_data.provider_code,
                insurance_type=ModelInsuranceType(request_data.insurance_type.value),
                plan_name=f"{request_data.insurance_type.value.title()} Plus",
                coverage_options=[request_data.coverage_details.coverage_amount],
            ),
            InsurancePlan(
                plan_code=f"{request_data.insurance_type.value}-MAX",
                provider_code=request_data.provider_code,
                insurance_type=ModelInsuranceType(request_data.insurance_type.value),
                plan_name=f"{request_data.insurance_type.value.title()} Max",
                coverage_options=[request_data.coverage_details.coverage_amount],
            ),
        ]

    @staticmethod
    def _generate_reference(prefix: str) -> str:
        """
        Generate a provider-facing external reference value.

        Args:
            prefix: Reference prefix such as `PQT` or `PTX`.

        Returns:
            str: Generated provider reference value.

        Raises:
            ValueError: Propagates if invalid reference input is supplied.
        """
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        return f"{prefix}-{timestamp}-{secrets.token_hex(3).upper()}"


provider_quote_service = ProviderQuoteService()
