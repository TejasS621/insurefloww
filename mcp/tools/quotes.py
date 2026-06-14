"""MCP quote tools implemented as thin adapters over InsureFlow APIs."""

from __future__ import annotations

from typing import Any

from mcp.clients.main_backend_client import MainBackendClient
from mcp.core.config import MCPSettings
from mcp.core.errors import AuthenticationRequiredError, BackendRequestError, MCPToolError
from mcp.core.results import ToolResult, error_result, success_result
from mcp.schemas.common import PremiumBreakdown, QuoteAddon, extract_api_data
from mcp.schemas.quotes import (
    GenerateQuoteInput,
    GenerateQuoteOutput,
    GetQuoteInput,
    GetQuoteOutput,
    QuoteSummary,
    SelectQuoteInput,
    SelectQuoteOutput,
)


class QuoteTools:
    """Quote-oriented orchestration helpers used by the MCP server."""

    def __init__(self, *, settings: MCPSettings, main_client: MainBackendClient) -> None:
        self.settings = settings
        self.main_client = main_client

    async def generate_quote(self, payload: GenerateQuoteInput) -> ToolResult[GenerateQuoteOutput]:
        """Create an application and return the generated quote summary list."""

        try:
            response = await self.main_client.create_application(payload.model_dump(exclude_none=True))
            data = extract_api_data(response)
            if not isinstance(data, dict):
                raise BackendRequestError("Main backend returned a malformed application response.")

            quotes = data.get("quotes", [])
            quote_summaries = [
                QuoteSummary(
                    quote_id=str(quote.get("quote_id")),
                    provider_name=str(quote.get("provider_name")),
                    plan_name=str(quote.get("plan_name")),
                    premium_amount=float(quote.get("total_premium", 0.0)),
                    coverage_amount=float(quote.get("coverage_amount", 0.0)),
                    status=str(quote.get("quote_status", "UNKNOWN")),
                )
                for quote in quotes
                if isinstance(quote, dict)
            ]
            result = GenerateQuoteOutput(
                application_reference=str(data.get("application_reference")),
                transaction_reference=(
                    str(data["transaction_reference"])
                    if data.get("transaction_reference") is not None
                    else None
                ),
                application_status=str(data.get("application_status")),
                quote_ids=[quote.quote_id for quote in quote_summaries],
                provider_names=[quote.provider_name for quote in quote_summaries],
                premium_amounts=[quote.premium_amount for quote in quote_summaries],
                quote_summary=quote_summaries,
            )
            return success_result("Application created and quotes generated successfully.", result)
        except MCPToolError as exc:
            return error_result(exc)

    async def get_quote(self, payload: GetQuoteInput) -> ToolResult[GetQuoteOutput]:
        """Find a quote by scanning the authenticated customer's application list."""

        if not self.settings.customer_jwt_token:
            return error_result(
                AuthenticationRequiredError(
                    "get_quote requires CUSTOMER_JWT_TOKEN because the backend does not expose a public quote-detail endpoint."
                )
            )

        try:
            match = await self._find_quote_by_id(payload.quote_id)
            if match is None:
                raise BackendRequestError(
                    "The requested quote could not be found in the authenticated customer's applications.",
                    status_code=404,
                    code="resource_not_found",
                )
            transaction_reference, quote = match
            output = GetQuoteOutput(
                quote_id=str(quote.get("quote_id")),
                provider_name=str(quote.get("provider_name")),
                plan_code=str(quote.get("plan_code")),
                plan_name=str(quote.get("plan_name")),
                premium=PremiumBreakdown(
                    base_premium=float(quote.get("base_premium", 0.0)),
                    tax_amount=float(quote.get("tax_amount", 0.0)),
                    addon_amount=0.0,
                    total_premium=float(quote.get("total_premium", 0.0)),
                ),
                coverage_amount=float(quote.get("coverage_amount", 0.0)),
                addons=[
                    QuoteAddon(
                        addon_code=str(addon.get("addon_code")),
                        addon_name=str(addon.get("addon_name")),
                        addon_price=float(addon.get("addon_price", 0.0)),
                    )
                    for addon in quote.get("available_addons", [])
                    if isinstance(addon, dict)
                ],
                status=str(quote.get("quote_status", "UNKNOWN")),
                transaction_reference=transaction_reference,
            )
            return success_result("Quote fetched successfully.", output)
        except MCPToolError as exc:
            return error_result(exc)

    async def select_quote(self, payload: SelectQuoteInput) -> ToolResult[SelectQuoteOutput]:
        """Select a quote and return the premium breakdown for the next payment step."""

        try:
            response = await self.main_client.select_quote(
                payload.quote_id,
                payload.model_dump(exclude={"quote_id"}, exclude_none=True),
            )
            data = extract_api_data(response)
            if not isinstance(data, dict):
                raise BackendRequestError("Main backend returned a malformed quote selection response.")

            selected_addons = payload.selected_addons
            addon_amount = sum(
                float(addon.get("addon_price", 0.0))
                for addon in data.get("available_addons", [])
                if isinstance(addon, dict) and str(addon.get("addon_code")) in set(selected_addons)
            )
            transaction_reference = None
            payment_status = None
            if self.settings.customer_jwt_token:
                try:
                    match = await self._find_quote_by_id(payload.quote_id)
                    if match is not None:
                        transaction_reference, _ = match
                        payment_status = await self._safe_payment_status(transaction_reference)
                except MCPToolError:
                    transaction_reference = None
                    payment_status = None

            result = SelectQuoteOutput(
                quote_id=str(data.get("quote_id")),
                transaction_reference=transaction_reference,
                premium_breakdown=PremiumBreakdown(
                    base_premium=float(data.get("base_premium", 0.0)),
                    tax_amount=float(data.get("tax_amount", 0.0)),
                    addon_amount=addon_amount,
                    total_premium=float(data.get("total_premium", 0.0)) + addon_amount,
                ),
                payment_status=payment_status,
                selected_addons=selected_addons,
            )
            return success_result("Quote selected successfully.", result)
        except MCPToolError as exc:
            return error_result(exc)

    async def _find_quote_by_id(self, quote_id: str) -> tuple[str | None, dict[str, Any]] | None:
        """Search the authenticated customer's applications for a quote identifier."""

        applications_payload = await self.main_client.list_my_applications(self.settings.customer_jwt_token or "")
        applications = extract_api_data(applications_payload)
        if not isinstance(applications, list):
            raise BackendRequestError("Main backend returned a malformed applications list.")

        for application in applications:
            if not isinstance(application, dict):
                continue
            transaction_reference = (
                str(application["transaction_reference"])
                if application.get("transaction_reference") is not None
                else None
            )
            for quote in application.get("quotes", []):
                if isinstance(quote, dict) and str(quote.get("quote_id")) == quote_id:
                    return transaction_reference, quote
        return None

    async def _safe_payment_status(self, transaction_reference: str) -> str | None:
        """Fetch payment status when the transaction reference is known."""

        response = await self.main_client.get_payment_status(transaction_reference)
        data = extract_api_data(response)
        if isinstance(data, dict):
            return str(data.get("payment_status")) if data.get("payment_status") is not None else None
        return None


def register_quote_tools(mcp_server: Any, tools: QuoteTools) -> None:
    """Register quote tool handlers on the running MCP server."""

    @mcp_server.tool(
        name="generate_quote",
        description=(
            "Create a new insurance application in InsureFlow and return generated quotes. "
            "Use the exact application schema required by the main backend."
        ),
    )
    async def generate_quote(payload: GenerateQuoteInput) -> dict[str, Any]:
        """Create an application and return quote summaries for Claude."""

        return (await tools.generate_quote(payload)).model_dump(mode="json")

    @mcp_server.tool(
        name="get_quote",
        description=(
            "Find detailed quote information by quote ID. "
            "This tool requires CUSTOMER_JWT_TOKEN because the backend exposes quote details through customer applications."
        ),
    )
    async def get_quote(payload: GetQuoteInput) -> dict[str, Any]:
        """Return quote details using authenticated application lookup."""

        return (await tools.get_quote(payload)).model_dump(mode="json")

    @mcp_server.tool(
        name="select_quote",
        description=(
            "Select a quote and return the premium breakdown needed before payment initiation. "
            "This tool does not initiate payment by itself."
        ),
    )
    async def select_quote(payload: SelectQuoteInput) -> dict[str, Any]:
        """Select a quote and return MCP-friendly pricing output."""

        return (await tools.select_quote(payload)).model_dump(mode="json")
