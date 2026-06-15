"""Shared fixtures for MCP tool tests."""

from __future__ import annotations

import pytest

from insureflow_mcp.clients.main_backend_client import MainBackendClient
from insureflow_mcp.core.config import MCPSettings


@pytest.fixture
def settings() -> MCPSettings:
    """Return a test settings object with a fixed main backend URL."""

    return MCPSettings(
        MAIN_BACKEND_URL="http://test-main/api/v1",
    )


@pytest.fixture
def main_client(settings: MCPSettings) -> MainBackendClient:
    """Return a main backend client bound to the test settings."""

    return MainBackendClient(settings)
