"""Shared fixtures for MCP tool tests."""

from __future__ import annotations

import pytest

from insureflow_mcp.core.auth_session import AuthSessionStore
from insureflow_mcp.clients.main_backend_client import MainBackendClient
from insureflow_mcp.core.config import MCPSettings


@pytest.fixture
def settings() -> MCPSettings:
    """Return a test settings object with fixed URLs and tokens."""

    return MCPSettings(
        MAIN_BACKEND_URL="http://test-main/api/v1",
    )


@pytest.fixture
def main_client(settings: MCPSettings) -> MainBackendClient:
    """Return a main backend client bound to the test settings."""

    return MainBackendClient(settings)


@pytest.fixture
def auth_session() -> AuthSessionStore:
    """Return a mutable in-memory auth session for MCP tool tests."""

    return AuthSessionStore(customer_token="customer-token", admin_token="admin-token")
