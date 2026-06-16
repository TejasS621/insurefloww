"""MCP quote tools implemented as thin adapters over InsureFlow APIs."""

from __future__ import annotations

from typing import Any

from insureflow_mcp.clients.main_backend_client import MainBackendClient
from insureflow_mcp.core.errors import BackendRequestError, MCPToolError
from insureflow_mcp.core.results import ToolResult, error_result, success_result
from insureflow_mcp.schemas.common import QuoteAddon, extract_api_data
from insureflow_mcp.schemas.quotes import (
    GenerateQuoteInput,
    GenerateQuoteOutput,
    QuoteSummary,
    SelectQuoteInput,
    SelectQuoteOutput,
)


class QuoteTools:
    """Quote-oriented orchestration helpers used by the MCP server."""

    def __init__(self, *, main_client: MainBackendClient) -> None:
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

    async def select_quote(self, payload: SelectQuoteInput) -> ToolResult[SelectQuoteOutput]:
        """Select a quote and return the direct backend quote payload."""

        try:
            response = await self.main_client.select_quote(
                payload.quote_id,
                payload.model_dump(exclude={"quote_id"}, exclude_none=True),
            )
            data = extract_api_data(response)
            if not isinstance(data, dict):
                raise BackendRequestError("Main backend returned a malformed quote selection response.")

            result = SelectQuoteOutput(
                quote_id=str(data.get("quote_id")),
                provider_name=str(data.get("provider_name")),
                plan_code=str(data.get("plan_code")),
                plan_name=str(data.get("plan_name")),
                base_premium=float(data.get("base_premium", 0.0)),
                tax_amount=float(data.get("tax_amount", 0.0)),
                total_premium=float(data.get("total_premium", 0.0)),
                coverage_amount=float(data.get("coverage_amount", 0.0)),
                available_addons=[
                    QuoteAddon(
                        addon_code=str(addon.get("addon_code")),
                        addon_name=str(addon.get("addon_name")),
                        addon_price=float(addon.get("addon_price", 0.0)),
                    )
                    for addon in data.get("available_addons", [])
                    if isinstance(addon, dict)
                ],
                quote_status=str(data.get("quote_status", "UNKNOWN")),
                expires_at=str(data["expires_at"]) if data.get("expires_at") is not None else None,
            )
            return success_result("Quote selected successfully.", result)
        except MCPToolError as exc:
            return error_result(exc)


def register_quote_tools(mcp_server: Any, tools: QuoteTools) -> None:
    """Register quote tool handlers on the running MCP server."""

    @mcp_server.tool(
        name="generate_quote",
        description=(
            "Create a full InsureFlow application and return generated quotes. "
            "Collect complete customer identity, mobile number, email, date of birth, gender, "
            "address, coverage preferences, and for HEALTH insurance also collect height, weight, "
            "smoker status, diabetes, blood pressure history, heart ailments, pre-existing disease, "
            "and any other medical conditions before calling this tool."
        ),
    )
    async def generate_quote(payload: GenerateQuoteInput) -> dict[str, Any]:
        """Create an application and return quote summaries for Claude."""

        return (await tools.generate_quote(payload)).model_dump(mode="json")

    @mcp_server.tool(
        name="select_quote",
        description=(
            "Select a quote via POST /api/v1/quotes/select/{quote_id} "
            "and return the direct normalized quote payload."
        ),
    )
    async def select_quote(payload: SelectQuoteInput) -> dict[str, Any]:
        """Select a quote and return MCP-friendly pricing output."""

        return (await tools.select_quote(payload)).model_dump(mode="json")
