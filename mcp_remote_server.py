"""Remote-friendly entrypoint for the InsureFlow MCP server."""

from __future__ import annotations

from insureflow_mcp.core.config import get_settings
from insureflow_mcp.server import create_server, run_server

settings = get_settings()
server = create_server(settings=settings)


if __name__ == "__main__":  # pragma: no cover - exercised in real runtime only
    run_server(server=server, settings=settings, default_transport="http")
