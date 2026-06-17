"""Reusable async HTTP client primitives with retries and timeouts."""

from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import Any

import httpx

from insureflow_mcp.core.config import MCPSettings
from insureflow_mcp.core.errors import BackendRequestError

logger = logging.getLogger(__name__)


class BaseBackendClient:
    """Thin async HTTP wrapper used by main and provider backend clients."""

    def __init__(self, *, base_url: str, settings: MCPSettings, client_name: str) -> None:
        self.base_url = base_url.rstrip("/")
        self.settings = settings
        self.client_name = client_name

    async def request_json(
        self,
        method: str,
        path: str,
        *,
        headers: dict[str, str] | None = None,
        json_body: dict[str, Any] | None = None,
        params: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Send a JSON request with retry and user-friendly error translation."""

        response = await self._request(
            method,
            path,
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
        """Download a file response from a backend into a local destination path."""

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
        """Execute an HTTP request with bounded retries for transient failures."""

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
                logger.warning(
                    "timeout from %s method=%s path=%s attempt=%s",
                    self.client_name,
                    method,
                    path,
                    attempt,
                )
                if attempt <= self.settings.max_retries:
                    await asyncio.sleep(self.settings.retry_backoff_seconds * attempt)
                    continue
                raise BackendRequestError(
                    f"{self.client_name} timed out while processing the request.",
                    retryable=True,
                ) from exc
            except httpx.HTTPError as exc:
                last_error = exc
                logger.warning(
                    "transport error from %s method=%s path=%s attempt=%s",
                    self.client_name,
                    method,
                    path,
                    attempt,
                )
                if attempt <= self.settings.max_retries:
                    await asyncio.sleep(self.settings.retry_backoff_seconds * attempt)
                    continue
                raise BackendRequestError(
                    f"Unable to reach {self.client_name}. Please verify that the backend is running.",
                    retryable=True,
                ) from exc

            if response.status_code >= 500 and attempt <= self.settings.max_retries:
                logger.warning(
                    "retrying %s server error method=%s path=%s status=%s attempt=%s",
                    self.client_name,
                    method,
                    path,
                    response.status_code,
                    attempt,
                )
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
        """Translate a backend error response into a user-friendly MCP error."""

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
                    if response.status_code == 422 and detail.get("loc") and detail.get("msg"):
                        location = ".".join(
                            str(item) for item in detail.get("loc", []) if str(item) != "body"
                        )
                        field_label = location or "request"
                        message = f"{field_label}: {detail['msg']}"
                    else:
                        message = str(detail["detail"])
                elif response.status_code == 422 and isinstance(detail, dict) and detail.get("msg"):
                    location = ".".join(
                        str(item) for item in detail.get("loc", []) if str(item) != "body"
                    )
                    field_label = location or "request"
                    message = f"{field_label}: {detail['msg']}"

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
            message,
            status_code=response.status_code,
            retryable=response.status_code >= 500,
            code=code,
        )
