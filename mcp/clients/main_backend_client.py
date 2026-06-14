"""Main backend REST client used by customer and admin MCP tools."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.clients.base import BaseBackendClient
from mcp.core.config import MCPSettings
from mcp.core.errors import AuthenticationRequiredError


class MainBackendClient(BaseBackendClient):
    """Typed REST client for the customer-facing InsureFlow backend."""

    def __init__(self, settings: MCPSettings) -> None:
        super().__init__(
            base_url=settings.main_backend_url,
            settings=settings,
            client_name="main backend",
        )

    async def create_application(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create an application and trigger quote generation."""

        return await self.request_json("POST", "/applications", json_body=payload)

    async def list_my_applications(self, token: str) -> dict[str, Any]:
        """List customer applications using a customer JWT."""

        return await self.request_json("GET", "/applications/me", headers=self._bearer_headers(token))

    async def select_quote(self, quote_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Select a quote and update downstream pricing."""

        return await self.request_json(
            "POST",
            f"/quotes/select/{quote_id}",
            json_body=payload,
        )

    async def initiate_payment(
        self,
        transaction_reference: str,
        payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Start the hosted payment flow for a selected quote."""

        return await self.request_json(
            "POST",
            f"/payments/initiate/{transaction_reference}",
            json_body=payload or {},
        )

    async def get_payment_status(self, transaction_reference: str) -> dict[str, Any]:
        """Poll the payment status for a transaction."""

        return await self.request_json("GET", f"/payments/status/{transaction_reference}")

    async def get_policy(self, policy_number: str, token: str) -> dict[str, Any]:
        """Fetch a policy summary for an authenticated customer."""

        return await self.request_json(
            "GET",
            f"/policies/{policy_number}",
            headers=self._bearer_headers(token),
        )

    async def download_policy(self, policy_number: str, *, token: str, destination: Path) -> Path:
        """Download a policy PDF for an authenticated customer."""

        return await self.download_file(
            f"/policies/{policy_number}/download",
            destination=destination,
            headers=self._bearer_headers(token),
        )

    async def create_ticket(self, payload: dict[str, Any], token: str) -> dict[str, Any]:
        """Create a support ticket for an authenticated customer."""

        return await self.request_json(
            "POST",
            "/tickets",
            json_body=payload,
            headers=self._bearer_headers(token),
        )

    async def list_my_tickets(self, token: str) -> dict[str, Any]:
        """List support tickets for an authenticated customer."""

        return await self.request_json("GET", "/tickets/me", headers=self._bearer_headers(token))

    async def list_brokers(self, token: str) -> dict[str, Any]:
        """List brokers via the admin API."""

        return await self.request_json("GET", "/admin/brokers", headers=self._bearer_headers(token))

    async def register_broker(self, payload: dict[str, Any], token: str) -> dict[str, Any]:
        """Register a broker through the main backend admin API."""

        return await self.request_json(
            "POST",
            "/admin/brokers",
            json_body=payload,
            headers=self._bearer_headers(token),
        )

    @staticmethod
    def _bearer_headers(token: str | None) -> dict[str, str]:
        """Build bearer authorization headers or raise when no token is available."""

        if not token:
            raise AuthenticationRequiredError(
                "This tool requires a customer or admin JWT token to be configured."
            )
        return {"Authorization": f"Bearer {token}"}

