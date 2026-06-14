"""Entrypoint for the InsureFlow Model Context Protocol server."""

from __future__ import annotations

from insureflow_mcp.core.auth_session import AuthSessionStore
from insureflow_mcp.clients.main_backend_client import MainBackendClient
from insureflow_mcp.core.config import get_settings
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

try:
    from fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover - import guard for runtime setup only
    raise RuntimeError(
        "The fastmcp package is required to run the InsureFlow MCP server. "
        "Install the dependencies from mcp/requirements.txt first."
    ) from exc


def create_server() -> FastMCP:
    """Construct and register the InsureFlow MCP server."""

    settings = get_settings()
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
    return server


server = create_server()


if __name__ == "__main__":  # pragma: no cover - exercised in real runtime only
    server.run()


