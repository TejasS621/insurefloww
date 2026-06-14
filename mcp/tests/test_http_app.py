"""HTTP app tests for remote MCP deployment behavior."""

from __future__ import annotations

from starlette.testclient import TestClient

from insureflow_mcp.core.config import MCPSettings
from insureflow_mcp.server import build_http_app, create_server


def _make_settings(**overrides: object) -> MCPSettings:
    """Create a settings object for HTTP app tests."""

    values = {
        "MAIN_BACKEND_URL": "http://test-main/api/v1",
        **overrides,
    }
    return MCPSettings(**values)


def test_health_endpoint_is_public() -> None:
    """The remote health route should stay public without API key auth."""

    settings = _make_settings(MCP_TRANSPORT="http", MCP_API_KEY="secret-key")
    app = build_http_app(server=create_server(settings=settings), settings=settings)

    with TestClient(app) as client:
        response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_remote_mcp_requires_api_key_when_enabled() -> None:
    """The MCP endpoint should require X-MCP-API-Key when configured."""

    settings = _make_settings(MCP_TRANSPORT="http", MCP_API_KEY="secret-key")
    app = build_http_app(server=create_server(settings=settings), settings=settings)

    with TestClient(app) as client:
        response = client.get("/mcp")

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "mcp_api_key_required"


def test_remote_mcp_allows_request_with_valid_api_key() -> None:
    """A valid MCP API key should allow the request to reach the MCP transport."""

    settings = _make_settings(MCP_TRANSPORT="http", MCP_API_KEY="secret-key")
    app = build_http_app(server=create_server(settings=settings), settings=settings)

    with TestClient(app) as client:
        response = client.get("/mcp", headers={"X-MCP-API-Key": "secret-key"})

    assert response.status_code != 401
