"""Provider backend REST client used by internal MCP compatibility helpers."""

from __future__ import annotations

from typing import Any

from mcp.clients.base import BaseBackendClient
from mcp.core.config import MCPSettings
from mcp.core.errors import ConfigurationError


class ProviderBackendClient(BaseBackendClient):
    """Typed REST client for provider-side broker and payment APIs."""

    def __init__(self, settings: MCPSettings) -> None:
        super().__init__(
            base_url=settings.provider_backend_url,
            settings=settings,
            client_name="provider backend",
        )
        self._broker_code = settings.broker_code
        self._broker_api_key = settings.broker_api_key

    async def generate_quotes(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Compatibility wrapper for direct provider quote generation."""

        return await self.request_json(
            "POST",
            "/provider/quotes/generate",
            json_body=payload,
            headers=self._broker_headers(),
        )

    async def create_payment_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Compatibility wrapper for direct provider payment session creation."""

        return await self.request_json(
            "POST",
            "/provider/payments/create",
            json_body=payload,
            headers=self._broker_headers(),
        )

    def _broker_headers(self) -> dict[str, str]:
        """Build broker integration headers or raise when credentials are missing."""

        if not self._broker_api_key:
            raise ConfigurationError(
                "BROKER_API_KEY must be configured for provider backend integration calls."
            )
        return {
            "X-Broker-Code": self._broker_code,
            "X-Broker-Api-Key": self._broker_api_key,
        }

