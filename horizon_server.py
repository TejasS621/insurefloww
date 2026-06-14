"""Prefect Horizon entrypoint for the InsureFlow remote MCP server."""

from __future__ import annotations

from insureflow_mcp.core.config import get_settings
from insureflow_mcp.server import create_server

settings = get_settings()
server = create_server(settings=settings)

