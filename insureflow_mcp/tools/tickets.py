"""Ticket tool adapters exposed by the MCP server and reused by other integrations."""

from __future__ import annotations

from typing import Any

from insureflow_mcp.clients.main_backend_client import MainBackendClient
from insureflow_mcp.core.errors import BackendRequestError, MCPToolError
from insureflow_mcp.core.results import ToolResult, error_result, success_result
from insureflow_mcp.schemas.common import extract_api_data
from insureflow_mcp.schemas.tickets import CreateTicketInput, TicketOutput


class TicketTools:
    """Thin ticket adapters exposed by the MCP server."""

    def __init__(self, *, main_client: MainBackendClient) -> None:
        self.main_client = main_client

    async def create_ticket(self, payload: CreateTicketInput) -> ToolResult[TicketOutput]:
        """Create a customer support ticket through the main backend."""

        try:
            response = await self.main_client.create_ticket(
                payload.model_dump(exclude={"customer_access_token"}, exclude_none=True),
                payload.customer_access_token,
            )
            data = extract_api_data(response)
            if not isinstance(data, dict):
                raise BackendRequestError("Main backend returned a malformed ticket creation response.")
            result = TicketOutput(**self._ticket_payload(data))
            return success_result("Ticket created successfully.", result)
        except MCPToolError as exc:
            return error_result(exc)

    @staticmethod
    def _ticket_payload(data: dict[str, Any]) -> dict[str, Any]:
        """Normalize a ticket response payload into the shared ticket schema."""

        return {
            "ticket_reference": str(data.get("ticket_reference")),
            "transaction_reference": str(data["transaction_reference"]) if data.get("transaction_reference") is not None else None,
            "category": str(data.get("category", "GENERAL")),
            "priority": str(data.get("priority", "MEDIUM")),
            "status": str(data.get("status", "UNKNOWN")),
            "subject": str(data.get("subject", "")),
            "message": str(data.get("message", "")),
            "admin_response": str(data["admin_response"]) if data.get("admin_response") is not None else None,
            "created_at": str(data.get("created_at")),
            "updated_at": str(data.get("updated_at")),
        }


def register_ticket_tools(mcp_server: Any, tools: TicketTools) -> None:
    """Register ticket helpers on the active MCP server."""

    @mcp_server.tool(
        name="create_ticket",
        description=(
            "Create a customer support ticket. "
            "Requires a customer JWT access token because the backend ticket route is authenticated."
        ),
    )
    async def create_ticket(payload: CreateTicketInput) -> dict[str, Any]:
        """Create a support ticket for the caller."""

        return (await tools.create_ticket(payload)).model_dump(mode="json")
