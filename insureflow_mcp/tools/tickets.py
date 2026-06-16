"""Ticket tool adapters exposed by the MCP server and reused by other integrations."""

from __future__ import annotations

from typing import Any

from insureflow_mcp.clients.main_backend_client import MainBackendClient
from insureflow_mcp.core.auth_session import AuthSessionStore
from insureflow_mcp.core.errors import (
    AuthenticationRequiredError,
    BackendRequestError,
    MCPToolError,
)
from insureflow_mcp.core.results import ToolResult, error_result, success_result
from insureflow_mcp.schemas.common import extract_api_data
from insureflow_mcp.schemas.tickets import CreateTicketInput, TicketOutput


class TicketTools:
    """Thin ticket adapters exposed by the MCP server."""

    def __init__(self, *, auth_session: AuthSessionStore, main_client: MainBackendClient) -> None:
        self.auth_session = auth_session
        self.main_client = main_client

    async def create_ticket(self, payload: CreateTicketInput) -> ToolResult[TicketOutput]:
        """Create a customer support ticket through the main backend."""

        try:
            response = await self.main_client.create_ticket(
                payload.model_dump(exclude={"customer_access_token"}, exclude_none=True),
                self._resolve_customer_token(payload.customer_access_token),
            )
            data = extract_api_data(response)
            if not isinstance(data, dict):
                raise BackendRequestError("Main backend returned a malformed ticket creation response.")
            result = TicketOutput(**self._ticket_payload(data))
            return success_result("Ticket created successfully.", result)
        except MCPToolError as exc:
            return error_result(exc)

    def _resolve_customer_token(self, explicit_token: str | None) -> str:
        """Return an explicit token when provided, otherwise use the stored customer session."""

        if explicit_token:
            return explicit_token
        try:
            return self.auth_session.get_customer_token()
        except AuthenticationRequiredError as exc:
            raise AuthenticationRequiredError(
                "Customer authentication is required before ticket tools can be used. "
                "Use a stored MCP customer session or provide a customer access token."
            ) from exc

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
            "Uses the current customer session when available, or accepts a customer JWT access token as a fallback."
        ),
    )
    async def create_ticket(payload: CreateTicketInput) -> dict[str, Any]:
        """Create a support ticket for the caller."""

        return (await tools.create_ticket(payload)).model_dump(mode="json")
