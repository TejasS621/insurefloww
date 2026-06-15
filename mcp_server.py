"""Entrypoint for the InsureFlow Model Context Protocol server."""

from __future__ import annotations

from insureflow_mcp.core.config import get_settings
from insureflow_mcp.server import create_server as build_server, run_server

try:
    from fastmcp import FastMCP
except ImportError as exc:  # pragma: no cover - import guard for runtime setup only
    raise RuntimeError(
        "The fastmcp package is required to run the InsureFlow MCP server. "
        "Install the dependencies from insureflow_mcp/requirements.txt first."
    ) from exc


def create_server() -> FastMCP:
    """Construct and register the InsureFlow MCP server."""

    return build_server(settings=get_settings())


server = create_server()


if __name__ == "__main__":  # pragma: no cover - exercised in real runtime only
    run_server(server=server, settings=get_settings(), default_transport="stdio")


