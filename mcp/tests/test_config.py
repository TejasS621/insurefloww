"""Unit tests for MCP server configuration defaults."""

from __future__ import annotations

from insureflow_mcp.core.config import MCPSettings


def test_remote_transport_defaults_are_available() -> None:
    """The settings object should expose stdio and remote transport options."""

    settings = MCPSettings()

    assert settings.transport == "stdio"
    assert settings.host == "0.0.0.0"
    assert settings.port == 8080
    assert settings.streamable_http_path == "/mcp"
    assert settings.health_path == "/health"
    assert settings.cors_allow_origins == ["*"]
