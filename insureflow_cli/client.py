"""Async REST client used by the InsureFlow Typer CLI."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import httpx

from insureflow_cli.config import CLISettings
from insureflow_cli.errors import AuthenticationRequiredError, BackendRequestError


class CLIBackendClient:
    """Thin HTTP client that wraps the existing main backend routes."""

    def __init__(self, settings: CLISettings) -> None:
        self.settings = settings
        self.base_url = settings.main_backend_url.rstrip("/")
        self.client_name = "main backend"

    async def request_customer_otp(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Start the customer OTP login flow."""

        return await self.request_json("POST", "/auth/login/otp", json_body=payload)

    async def verify_customer_otp(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Verify a customer OTP and receive an access token."""

        return await self.request_json("POST", "/auth/login/verify", json_body=payload)

    async def admin_login(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Validate admin credentials and receive the current admin login payload."""

        return await self.request_json("POST", "/auth/admin/login", json_body=payload)

    async def admin_verify(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Verify the admin OTP flow and receive an access token."""

        return await self.request_json("POST", "/auth/admin/login/verify", json_body=payload)

    async def create_application(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Create an application and trigger quote generation."""

        return await self.request_json("POST", "/applications", json_body=payload)

    async def select_quote(self, quote_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Select a quote and update downstream pricing."""

        return await self.request_json("POST", f"/quotes/select/{quote_id}", json_body=payload)

    async def initiate_payment(self, transaction_reference: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        """Create a hosted payment session for a selected transaction."""

        return await self.request_json(
            "POST",
            f"/payments/initiate/{transaction_reference}",
            json_body=payload or {},
        )

    async def get_payment_status(self, transaction_reference: str) -> dict[str, Any]:
        """Poll the current payment status for a transaction."""

        return await self.request_json("GET", f"/payments/status/{transaction_reference}")

    async def list_policies(self, token: str) -> dict[str, Any]:
        """List customer policies using the authenticated customer token."""

        return await self.request_json("GET", "/policies/me", headers=self._bearer_headers(token))

    async def get_policy(self, policy_number: str, token: str) -> dict[str, Any]:
        """Fetch one customer policy by policy number."""

        return await self.request_json("GET", f"/policies/{policy_number}", headers=self._bearer_headers(token))

    async def download_policy(self, policy_number: str, *, token: str, destination: Path) -> Path:
        """Download a policy file to the requested local destination path."""

        return await self.download_file(
            f"/policies/{policy_number}/download",
            destination=destination,
            headers=self._bearer_headers(token),
        )

    async def create_ticket(self, payload: dict[str, Any], token: str) -> dict[str, Any]:
        """Create a support ticket for the authenticated customer."""

        return await self.request_json(
            "POST",
            "/tickets",
            headers=self._bearer_headers(token),
            json_body=payload,
        )

    async def list_tickets(self, token: str) -> dict[str, Any]:
        """List tickets for the authenticated customer."""

        return await self.request_json("GET", "/tickets/me", headers=self._bearer_headers(token))

    async def list_brokers(self, token: str) -> dict[str, Any]:
        """List broker registry records for the authenticated admin."""

        return await self.request_json("GET", "/admin/brokers", headers=self._bearer_headers(token))

    async def register_broker(self, payload: dict[str, Any], token: str) -> dict[str, Any]:
        """Register a broker through the admin API."""

        return await self.request_json(
            "POST",
            "/admin/brokers",
            headers=self._bearer_headers(token),
            json_body=payload,
        )

    async def update_broker_status(self, broker_code: str, payload: dict[str, Any], token: str) -> dict[str, Any]:
        """Update a broker lifecycle status through the admin API."""

        return await self.request_json(
            "PATCH",
            f"/admin/brokers/{broker_code}/status",
            headers=self._bearer_headers(token),
            json_body=payload,
        )

    async def rotate_broker_key(self, broker_code: str, payload: dict[str, Any], token: str) -> dict[str, Any]:
        """Rotate broker credentials through the admin API."""

        return await self.request_json(
            "PUT",
            f"/admin/brokers/{broker_code}/rotate-key",
            headers=self._bearer_headers(token),
            json_body=payload,
        )

    async def request_json(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send a JSON request and parse the response body."""

        response = await self._request(
            method=method,
            path=path,
            headers=headers,
            json_body=json_body,
            params=params,
        )
        try:
            return response.json()
        except json.JSONDecodeError as exc:
            raise BackendRequestError(
                f"{self.client_name} returned a malformed JSON response.",
                status_code=response.status_code,
            ) from exc

    async def download_file(
        self,
        path: str,
        *,
        destination: Path,
        headers: dict[str, str] | None = None,
    ) -> Path:
        """Download a file response into a local path."""

        response = await self._request("GET", path, headers=headers)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(response.content)
        return destination

    async def _request(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> httpx.Response:
        """Execute an HTTP request with timeout, retry, and clean error translation."""

        url = f"{self.base_url}{path}"
        last_error: Exception | None = None

        for attempt in range(1, self.settings.max_retries + 2):
            try:
                async with httpx.AsyncClient(timeout=self.settings.request_timeout_seconds) as client:
                    response = await client.request(
                        method=method,
                        url=url,
                        headers=headers,
                        json=json_body,
                        params=params,
                    )
            except httpx.TimeoutException as exc:
                last_error = exc
                if attempt <= self.settings.max_retries:
                    await asyncio.sleep(self.settings.retry_backoff_seconds * attempt)
                    continue
                raise BackendRequestError(
                    f"{self.client_name} timed out while processing the request.",
                    retryable=True,
                ) from exc
            except httpx.HTTPError as exc:
                last_error = exc
                if attempt <= self.settings.max_retries:
                    await asyncio.sleep(self.settings.retry_backoff_seconds * attempt)
                    continue
                raise BackendRequestError(
                    f"Unable to reach {self.client_name}. Please verify that the backend is running.",
                    retryable=True,
                ) from exc

            if response.status_code >= 500 and attempt <= self.settings.max_retries:
                await asyncio.sleep(self.settings.retry_backoff_seconds * attempt)
                continue

            if response.status_code >= 400:
                raise self._build_backend_error(response)

            return response

        raise BackendRequestError(
            f"{self.client_name} request failed unexpectedly.",
            retryable=last_error is not None,
        )

    def _build_backend_error(self, response: httpx.Response) -> BackendRequestError:
        """Translate a backend error response into a clean CLI error."""

        message = f"{self.client_name} request failed."
        try:
            payload = response.json()
        except json.JSONDecodeError:
            payload = None

        if isinstance(payload, dict):
            message = str(payload.get("message") or message)
            errors = payload.get("errors")
            if isinstance(errors, list) and errors:
                detail = errors[0]
                if isinstance(detail, dict) and detail.get("detail"):
                    message = str(detail["detail"])

        code = "backend_request_error"
        if response.status_code == 401:
            code = "authentication_failed"
        elif response.status_code == 403:
            code = "authorization_failed"
        elif response.status_code == 404:
            code = "resource_not_found"
        elif response.status_code == 422:
            code = "validation_failed"

        return BackendRequestError(
            message=message,
            status_code=response.status_code,
            retryable=response.status_code >= 500,
            code=code,
        )

    @staticmethod
    def _bearer_headers(token: str | None) -> dict[str, str]:
        """Build bearer authorization headers or raise when the token is missing."""

        if not token:
            raise AuthenticationRequiredError("This command requires a stored bearer token.")
        return {"Authorization": f"Bearer {token}"}
