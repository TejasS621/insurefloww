"""Unit tests for MCP server configuration defaults."""

from __future__ import annotations

import pytest

from insureflow_mcp.core.config import MCPSettings


def test_remote_transport_defaults_are_available(monkeypatch: pytest.MonkeyPatch) -> None:
    """The settings object should expose stdio defaults when no env override exists."""

    monkeypatch.delenv("MCP_TRANSPORT", raising=False)

    settings = MCPSettings()

    assert settings.transport == "stdio"
    assert settings.host == "0.0.0.0"
    assert settings.port == 8080
    assert settings.streamable_http_path == "/mcp"
    assert settings.health_path == "/health"
    assert settings.cors_allow_origins == ["*"]
    assert settings.api_key is None


def test_transport_can_be_overridden_to_http(monkeypatch: pytest.MonkeyPatch) -> None:
    """The MCP transport should resolve to HTTP when the env override is set."""

    monkeypatch.setenv("MCP_TRANSPORT", "http")

    settings = MCPSettings()

    assert settings.transport == "http"
