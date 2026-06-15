"""Shared FastMCP server construction and runtime helpers."""

from __future__ import annotations

from typing import Any

from fastmcp import FastMCP
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from insureflow_mcp.clients.main_backend_client import MainBackendClient
from insureflow_mcp.core.config import MCPSettings, get_settings
from insureflow_mcp.core.logging import configure_logging
from insureflow_mcp.tools import (
    PaymentTools,
    QuoteTools,
    register_payment_tools,
    register_quote_tools,
)


class MCPAPIKeyMiddleware(BaseHTTPMiddleware):
    """Protect remote MCP endpoints with an optional shared API key."""

    def __init__(self, app: Any, *, settings: MCPSettings) -> None:
        super().__init__(app)
        self.settings = settings

    async def dispatch(self, request: Request, call_next: Any) -> Response:
        """Require `X-MCP-API-Key` for non-health HTTP requests when configured."""

        if request.method == "OPTIONS":
            return await call_next(request)

        if request.url.path == self.settings.health_path:
            return await call_next(request)

        configured_key = self.settings.api_key
        if not configured_key:
            return await call_next(request)

        provided_key = request.headers.get("X-MCP-API-Key")
        if provided_key != configured_key:
            return JSONResponse(
                {
                    "success": False,
                    "message": "Missing or invalid MCP API key.",
                    "error": {
                        "code": "mcp_api_key_required",
                        "detail": "Provide a valid X-MCP-API-Key header for remote MCP access.",
                        "status_code": 401,
                        "retryable": False,
                    },
                },
                status_code=401,
            )

        return await call_next(request)


def create_server(settings: MCPSettings | None = None) -> FastMCP:
    """Construct and register the InsureFlow MCP server."""

    settings = settings or get_settings()
    configure_logging(settings.log_level)

    main_client = MainBackendClient(settings)

    server = FastMCP(
        name=settings.app_name,
        instructions=(
            "InsureFlow MCP exposes thin orchestration tools over the existing "
            "InsureFlow REST APIs. It validates inputs, forwards requests, "
            "normalizes outputs, and does not implement business logic."
        ),
    )

    register_quote_tools(server, QuoteTools(main_client=main_client))
    register_payment_tools(server, PaymentTools(main_client=main_client))

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
        Middleware(MCPAPIKeyMiddleware, settings=settings),
        Middleware(
            CORSMiddleware,
            allow_origins=settings.cors_allow_origins or ["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    ]


def build_http_app(*, server: FastMCP, settings: MCPSettings) -> Any:
    """Build the Starlette HTTP app for remote MCP usage and tests."""

    return server.http_app(
        path=settings.streamable_http_path,
        transport="http",
        middleware=build_http_middleware(settings),
    )


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
