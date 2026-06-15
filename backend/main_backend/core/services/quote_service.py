"""Quote orchestration services for the main backend."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import datetime, timezone

import httpx
from odmantic import AIOEngine

from backend.main_backend.commons.config import settings
from backend.main_backend.core.apis.schemas.requests.application_request import (
    ApplicationCreateRequest,
)
from backend.main_backend.core.models.application_model import (
    Application,
    ApplicationStatus,
)
from backend.main_backend.core.models.quote_model import Quote, QuoteStatus
from backend.main_backend.core.models.transaction_model import Transaction, TransactionStatus

from .service_exceptions import ConflictServiceError, IntegrationServiceError, NotFoundServiceError


class QuoteService:
    """Store normalized quotes and manage quote selection."""

    async def request_and_store_quotes_for_application(
        self,
        engine: AIOEngine,
        *,
        application: Application,
        transaction: Transaction,
        request_data: ApplicationCreateRequest,
    ) -> list[Quote]:
        """Request provider quotes for a freshly-created application and persist them locally."""
        payload = {
            "main_transaction_reference": transaction.transaction_reference,
            "application_reference": application.application_reference,
            "provider_code": settings.integration_provider_code,
            "broker_code": settings.integration_broker_code,
            "insurance_type": request_data.insurance_type.value,
            "personal_details": request_data.personal_details.model_dump(
                mode="json",
                exclude_none=True,
            ),
            "health_details": (
                request_data.health_details.model_dump(mode="json", exclude_none=True)
                if request_data.health_details
                else None
            ),
            "coverage_details": request_data.coverage_details.model_dump(
                mode="json",
                exclude_none=True,
            ),
        }

        try:
            async with httpx.AsyncClient(timeout=settings.provider_request_timeout_seconds) as client:
                response = await client.post(
                    settings.provider_quote_generate_url,
                    json=payload,
                    headers={
                        "X-Broker-Code": settings.integration_broker_code,
                        "X-Broker-Api-Key": settings.integration_broker_api_key,
                    },
                )
        except httpx.HTTPError as exc:
            raise IntegrationServiceError(
                "Unable to reach the provider backend to generate quotes."
            ) from exc

        if response.status_code >= 400:
            try:
                response_payload = response.json()
            except ValueError:
                response_payload = {}
            provider_message = response_payload.get(
                "message",
                "Provider backend rejected the quote generation request.",
            )
            raise IntegrationServiceError(provider_message)

        try:
            response_payload = response.json()
        except ValueError as exc:
            raise IntegrationServiceError(
                "Provider backend returned an invalid quote generation response."
            ) from exc

        quote_payloads = response_payload.get("data")
        if not isinstance(quote_payloads, list):
            raise IntegrationServiceError(
                "Provider backend returned a malformed quote response payload."
            )

        stored_quotes = await self.store_provider_quotes(
            engine,
            transaction_id=str(transaction.id),
            transaction_reference=transaction.transaction_reference,
            provider_quotes=quote_payloads,
        )
        transaction.transaction_status = TransactionStatus.QUOTE_GENERATED
        transaction.updated_at = datetime.now(timezone.utc)
        await engine.save(transaction)

        application.application_status = ApplicationStatus.QUOTE_GENERATED
        application.updated_at = datetime.now(timezone.utc)
        await engine.save(application)
        return stored_quotes

    async def list_quotes_for_transaction(
        self,
        engine: AIOEngine,
        transaction_reference: str,
    ) -> list[Quote]:
        """Return all normalized quotes tied to a transaction."""
        return await engine.find(
            Quote,
            Quote.transaction_reference == transaction_reference,
        )

    async def store_provider_quotes(
        self,
        engine: AIOEngine,
        *,
        transaction_id: str,
        transaction_reference: str,
        provider_quotes: Iterable[Mapping[str, object]],
    ) -> list[Quote]:
        """Persist normalized quote projections from provider quote payloads."""
        stored_quotes: list[Quote] = []
        for payload in provider_quotes:
            provider_quote_id = str(payload.get("provider_quote_id") or payload.get("quote_id") or "")
            if not provider_quote_id:
                raise ConflictServiceError("Provider quote payload is missing a quote identifier.")

            quote = Quote(
                transaction_reference=transaction_reference,
                transaction_id=transaction_id,
                provider_quote_id=provider_quote_id,
                provider_name=str(payload.get("provider_name", "Provider")),
                plan_code=str(payload.get("plan_code", "")),
                plan_name=str(payload.get("plan_name", "Unnamed Plan")),
                base_premium=float(payload.get("base_premium", 0.0)),
                tax_amount=float(payload.get("tax_amount", 0.0)),
                total_premium=float(payload.get("total_premium", payload.get("base_premium", 0.0))),
                coverage_amount=float(payload.get("coverage_amount", 0.0)),
                available_addons=list(payload.get("available_addons", [])),
                quote_status=QuoteStatus.ACTIVE,
                expires_at=payload.get("expires_at"),
            )
            await engine.save(quote)
            stored_quotes.append(quote)
        return stored_quotes

    async def select_quote(
        self,
        engine: AIOEngine,
        *,
        quote_id: str,
        selected_addons: list[str],
    ) -> Quote:
        """Mark a quote as selected and propagate pricing to the transaction."""
        quote = await engine.find_one(Quote, Quote.provider_quote_id == quote_id)
        if quote is None:
            raise NotFoundServiceError("The requested quote could not be found.")

        transaction = await engine.find_one(
            Transaction,
            Transaction.transaction_reference == quote.transaction_reference,
        )
        if transaction is None:
            raise NotFoundServiceError("The transaction for the selected quote could not be found.")

        addon_amount = self._calculate_addon_amount(quote.available_addons, selected_addons)
        transaction.selected_quote_id = quote.provider_quote_id
        transaction.selected_addons = selected_addons
        transaction.base_premium = quote.base_premium
        transaction.addon_amount = addon_amount
        transaction.final_amount = quote.total_premium + addon_amount
        transaction.transaction_status = TransactionStatus.QUOTE_SELECTED
        transaction.updated_at = datetime.now(timezone.utc)
        await engine.save(transaction)

        quote.quote_status = QuoteStatus.SELECTED
        await engine.save(quote)

        application = await engine.find_one(Application, Application.transaction_reference == quote.transaction_reference)
        if application is not None:
            application.application_status = ApplicationStatus.QUOTE_SELECTED
            application.updated_at = datetime.now(timezone.utc)
            await engine.save(application)

        return quote

    @staticmethod
    def _calculate_addon_amount(
        available_addons: list[dict[str, object]],
        selected_addons: list[str],
    ) -> float:
        """Calculate the total price for selected add-ons."""
        selected_codes = set(selected_addons)
        amount = 0.0
        for addon in available_addons:
            addon_code = str(addon.get("addon_code", ""))
            if addon_code in selected_codes:
                amount += float(addon.get("addon_price", 0.0))
        return amount


quote_service = QuoteService()

