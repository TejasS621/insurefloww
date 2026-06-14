"""Shared FastMCP server construction and runtime helpers."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from insureflow_mcp.clients.main_backend_client import MainBackendClient
from insureflow_mcp.core.auth_session import AuthSessionStore
from insureflow_mcp.core.config import MCPSettings, get_settings
from insureflow_mcp.core.logging import configure_logging
from insureflow_mcp.tools import (
    AuthTools,
    BrokerTools,
    PaymentTools,
    PolicyTools,
    QuoteTools,
    TicketTools,
    register_auth_tools,
    register_broker_tools,
    register_payment_tools,
    register_policy_tools,
    register_quote_tools,
    register_ticket_tools,
)


def create_server(settings: MCPSettings | None = None) -> FastMCP:
    """Construct and register the InsureFlow MCP server."""

    settings = settings or get_settings()
    configure_logging(settings.log_level)

    main_client = MainBackendClient(settings)
    auth_session = AuthSessionStore()

    server = FastMCP(
        name=settings.app_name,
        instructions=(
            "InsureFlow MCP exposes thin orchestration tools over the existing "
            "InsureFlow REST APIs. It validates inputs, forwards requests, "
            "normalizes outputs, and does not implement business logic."
        ),
    )

    register_auth_tools(server, AuthTools(main_client=main_client, auth_session=auth_session))
    register_quote_tools(server, QuoteTools(main_client=main_client))
    register_payment_tools(server, PaymentTools(main_client=main_client))
    register_policy_tools(server, PolicyTools(settings=settings, auth_session=auth_session, main_client=main_client))
    register_ticket_tools(server, TicketTools(auth_session=auth_session, main_client=main_client))
    register_broker_tools(server, BrokerTools(auth_session=auth_session, main_client=main_client))

    @server.custom_route(settings.health_path, methods=["GET"], include_in_schema=False)
    async def health_check(request: Request) -> Response:
        """Expose a simple health endpoint for remote deployments."""

        del request
        return JSONResponse(
            {
                "status": "ok",
                "service": settings.app_name,
                "transport": settings.transport,
            }
        )

    return server


def build_http_middleware(settings: MCPSettings) -> list[Middleware]:
    """Create HTTP middleware required by the remote MCP deployment."""

    return [
        Middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allow_origins or ["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ]


def run_server(
    *,
    server: FastMCP,
    settings: MCPSettings,
    default_transport: str = "stdio",
) -> None:
    """Run the shared MCP server with environment-driven transport selection."""

    transport = settings.transport or default_transport
    if transport == "stdio":
        server.run(transport="stdio")
        return

    server.run(
        transport=transport,
        host=settings.host,
        port=settings.port,
        path=settings.streamable_http_path,
        middleware=build_http_middleware(settings),
    )
