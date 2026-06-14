"""MCP payment tools implemented as thin adapters over InsureFlow APIs."""

from __future__ import annotations

from typing import Any

from mcp.clients.main_backend_client import MainBackendClient
from mcp.core.errors import BackendRequestError, MCPToolError
from mcp.core.results import ToolResult, error_result, success_result
from mcp.schemas.common import extract_api_data
from mcp.schemas.payments import (
    GetPaymentStatusInput,
    InitiatePaymentInput,
    InitiatePaymentOutput,
    PaymentStatusOutput,
)


class PaymentTools:
    """Payment-oriented orchestration helpers used by the MCP server."""

    def __init__(self, *, main_client: MainBackendClient) -> None:
        self.main_client = main_client

    async def initiate_payment(self, payload: InitiatePaymentInput) -> ToolResult[InitiatePaymentOutput]:
        """Create a hosted payment session through the main backend."""

        try:
            response = await self.main_client.initiate_payment(
                payload.transaction_reference,
                payload.model_dump(exclude={"transaction_reference"}, exclude_none=True),
            )
            data = extract_api_data(response)
            if not isinstance(data, dict):
                raise BackendRequestError("Main backend returned a malformed payment initiation response.")
            result = InitiatePaymentOutput(
                payment_reference=str(data.get("payment_reference")),
                payment_url=str(data.get("payment_url")),
                amount=float(data.get("amount", 0.0)),
                currency=str(data.get("currency", "INR")),
                available_payment_methods=[
                    str(method) for method in data.get("available_payment_methods", [])
                ],
                status=str(data.get("status", "UNKNOWN")),
            )
            return success_result("Payment session created successfully.", result)
        except MCPToolError as exc:
            return error_result(exc)

    async def get_payment_status(self, payload: GetPaymentStatusInput) -> ToolResult[PaymentStatusOutput]:
        """Return the current payment status for a transaction reference."""

        try:
            response = await self.main_client.get_payment_status(payload.transaction_reference)
            data = extract_api_data(response)
            if not isinstance(data, dict):
                raise BackendRequestError("Main backend returned a malformed payment status response.")
            result = PaymentStatusOutput(
                payment_status=str(data.get("payment_status", "UNKNOWN")),
                transaction_status=str(data.get("transaction_status", "UNKNOWN")),
                payment_reference=(
                    str(data["provider_payment_reference"])
                    if data.get("provider_payment_reference") is not None
                    else None
                ),
            )
            return success_result("Payment status fetched successfully.", result)
        except MCPToolError as exc:
            return error_result(exc)


def register_payment_tools(mcp_server: Any, tools: PaymentTools) -> None:
    """Register payment tool handlers on the running MCP server."""

    @mcp_server.tool(
        name="initiate_payment",
        description=(
            "Start the InsureFlow hosted payment flow for a selected transaction reference. "
            "This returns the payment URL and payment methods without performing the payment."
        ),
    )
    async def initiate_payment(payload: InitiatePaymentInput) -> dict[str, Any]:
        """Create a hosted payment session and return checkout metadata."""

        return (await tools.initiate_payment(payload)).model_dump(mode="json")

    @mcp_server.tool(
        name="get_payment_status",
        description="Check the current payment and transaction status for a transaction reference.",
    )
    async def get_payment_status(payload: GetPaymentStatusInput) -> dict[str, Any]:
        """Poll the current payment status for a transaction."""

        return (await tools.get_payment_status(payload)).model_dump(mode="json")

