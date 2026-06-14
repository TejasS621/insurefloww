"""MCP broker tools implemented as thin adapters over InsureFlow admin APIs."""

from __future__ import annotations

from typing import Any

from mcp.clients.main_backend_client import MainBackendClient
from mcp.core.config import MCPSettings
from mcp.core.errors import AuthenticationRequiredError, BackendRequestError, MCPToolError
from mcp.core.results import ToolResult, error_result, success_result
from mcp.schemas.brokers import (
    BrokerSummaryOutput,
    ListBrokersInput,
    RegisterBrokerInput,
    RegisterBrokerOutput,
)
from mcp.schemas.common import extract_api_data


class BrokerTools:
    """Admin broker orchestration helpers used by the MCP server."""

    def __init__(self, *, settings: MCPSettings, main_client: MainBackendClient) -> None:
        self.settings = settings
        self.main_client = main_client

    async def list_brokers(self, payload: ListBrokersInput) -> ToolResult[list[BrokerSummaryOutput]]:
        """List brokers from the admin API and optionally filter active records."""

        if not self.settings.admin_jwt_token:
            return error_result(
                AuthenticationRequiredError("list_brokers requires ADMIN_JWT_TOKEN to access admin broker data.")
            )

        try:
            response = await self.main_client.list_brokers(self.settings.admin_jwt_token)
            data = extract_api_data(response)
            if not isinstance(data, list):
                raise BackendRequestError("Main backend returned a malformed broker list response.")

            brokers = [
                BrokerSummaryOutput(
                    broker_code=str(item.get("broker_code")),
                    broker_name=str(item.get("broker_name")),
                    status=str(item.get("status", "UNKNOWN")),
                    callback_url=str(item.get("callback_url")),
                    webhook_url=str(item.get("webhook_url")),
                )
                for item in data
                if isinstance(item, dict)
            ]
            if payload.active_only:
                brokers = [broker for broker in brokers if broker.status.upper() == "ACTIVE"]
            return success_result("Brokers fetched successfully.", brokers)
        except MCPToolError as exc:
            return error_result(exc)

    async def register_broker(self, payload: RegisterBrokerInput) -> ToolResult[RegisterBrokerOutput]:
        """Register a broker through the authenticated main admin API."""

        if not self.settings.admin_jwt_token:
            return error_result(
                AuthenticationRequiredError("register_broker requires ADMIN_JWT_TOKEN to register brokers.")
            )

        try:
            response = await self.main_client.register_broker(
                payload.model_dump(mode="json"),
                self.settings.admin_jwt_token,
            )
            data = extract_api_data(response)
            if not isinstance(data, dict):
                raise BackendRequestError("Main backend returned a malformed broker registration response.")
            result = RegisterBrokerOutput(
                broker_code=str(data.get("broker_code")),
                api_key=(str(data["api_key"]) if data.get("api_key") is not None else None),
                created_at=(str(data["created_at"]) if data.get("created_at") is not None else None),
                status=str(data.get("status", "ACTIVE")),
            )
            return success_result("Broker registered successfully.", result)
        except MCPToolError as exc:
            return error_result(exc)


def register_broker_tools(mcp_server: Any, tools: BrokerTools) -> None:
    """Register broker tool handlers on the running MCP server."""

    @mcp_server.tool(
        name="list_brokers",
        description="Admin-only tool that lists broker registry records from the InsureFlow admin API.",
    )
    async def list_brokers(payload: ListBrokersInput) -> dict[str, Any]:
        """List broker records for Claude."""

        return (await tools.list_brokers(payload)).model_dump(mode="json")

    @mcp_server.tool(
        name="register_broker",
        description=(
            "Admin-only tool that registers a new broker using the InsureFlow admin API. "
            "The broker_code must be supplied because the backend requires it."
        ),
    )
    async def register_broker(payload: RegisterBrokerInput) -> dict[str, Any]:
        """Register a broker and return the one-time API key."""

        return (await tools.register_broker(payload)).model_dump(mode="json")

