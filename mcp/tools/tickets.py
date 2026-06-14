"""MCP support ticket tools implemented as thin adapters over InsureFlow APIs."""

from __future__ import annotations

from typing import Any

from mcp.clients.main_backend_client import MainBackendClient
from mcp.core.config import MCPSettings
from mcp.core.errors import AuthenticationRequiredError, BackendRequestError, MCPToolError
from mcp.core.results import ToolResult, error_result, success_result
from mcp.schemas.common import extract_api_data
from mcp.schemas.tickets import (
    CreateTicketInput,
    GetTicketStatusInput,
    TicketOutput,
    TicketStatusOutput,
)


class TicketTools:
    """Support-ticket orchestration helpers used by the MCP server."""

    def __init__(self, *, settings: MCPSettings, main_client: MainBackendClient) -> None:
        self.settings = settings
        self.main_client = main_client

    async def create_ticket(self, payload: CreateTicketInput) -> ToolResult[TicketOutput]:
        """Create a customer support ticket through the main backend."""

        if not self.settings.customer_jwt_token:
            return error_result(
                AuthenticationRequiredError("create_ticket requires CUSTOMER_JWT_TOKEN to create customer tickets.")
            )

        try:
            response = await self.main_client.create_ticket(
                payload.model_dump(exclude_none=True),
                self.settings.customer_jwt_token,
            )
            data = extract_api_data(response)
            if not isinstance(data, dict):
                raise BackendRequestError("Main backend returned a malformed ticket creation response.")
            result = TicketOutput(**self._ticket_payload(data))
            return success_result("Ticket created successfully.", result)
        except MCPToolError as exc:
            return error_result(exc)

    async def get_ticket_status(self, payload: GetTicketStatusInput) -> ToolResult[TicketStatusOutput]:
        """Find a ticket by searching the authenticated customer's ticket list."""

        if not self.settings.customer_jwt_token:
            return error_result(
                AuthenticationRequiredError(
                    "get_ticket_status requires CUSTOMER_JWT_TOKEN because the backend exposes ticket details through the customer ticket list."
                )
            )

        try:
            tickets_payload = await self.main_client.list_my_tickets(self.settings.customer_jwt_token)
            tickets = extract_api_data(tickets_payload)
            if not isinstance(tickets, list):
                raise BackendRequestError("Main backend returned a malformed ticket list response.")
            for ticket in tickets:
                if isinstance(ticket, dict) and str(ticket.get("ticket_reference")) == payload.ticket_id:
                    result = TicketStatusOutput(
                        ticket_reference=str(ticket.get("ticket_reference")),
                        status=str(ticket.get("status", "UNKNOWN")),
                        assigned_to=None,
                        last_updated=str(ticket.get("updated_at")),
                    )
                    return success_result("Ticket status fetched successfully.", result)
            raise BackendRequestError(
                "The requested ticket could not be found in the authenticated customer's tickets.",
                status_code=404,
                code="resource_not_found",
            )
        except MCPToolError as exc:
            return error_result(exc)

    @staticmethod
    def _ticket_payload(data: dict[str, Any]) -> dict[str, Any]:
        """Normalize a ticket response payload into the MCP ticket schema."""

        return {
            "ticket_reference": str(data.get("ticket_reference")),
            "transaction_reference": (
                str(data["transaction_reference"]) if data.get("transaction_reference") is not None else None
            ),
            "category": str(data.get("category", "GENERAL")),
            "priority": str(data.get("priority", "MEDIUM")),
            "status": str(data.get("status", "UNKNOWN")),
            "subject": str(data.get("subject", "")),
            "message": str(data.get("message", "")),
            "admin_response": (
                str(data["admin_response"]) if data.get("admin_response") is not None else None
            ),
            "created_at": str(data.get("created_at")),
            "updated_at": str(data.get("updated_at")),
        }


def register_ticket_tools(mcp_server: Any, tools: TicketTools) -> None:
    """Register ticket tool handlers on the running MCP server."""

    @mcp_server.tool(
        name="create_ticket",
        description="Create a customer support ticket using the authenticated customer token.",
    )
    async def create_ticket(payload: CreateTicketInput) -> dict[str, Any]:
        """Create a support ticket for Claude-driven workflows."""

        return (await tools.create_ticket(payload)).model_dump(mode="json")

    @mcp_server.tool(
        name="get_ticket_status",
        description=(
            "Find a customer ticket by ticket reference using the authenticated customer ticket list. "
            "Use this when you need the latest ticket status."
        ),
    )
    async def get_ticket_status(payload: GetTicketStatusInput) -> dict[str, Any]:
        """Return the current status of a customer support ticket."""

        return (await tools.get_ticket_status(payload)).model_dump(mode="json")

