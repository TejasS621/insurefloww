"""Typed MCP-layer exceptions and error translation helpers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class MCPToolError(Exception):
    """Base exception used to convert integration failures into tool results."""

    code: str
    message: str
    status_code: int | None = None
    retryable: bool = False

    def __str__(self) -> str:
        """Return the user-facing error message."""

        return self.message


class AuthenticationRequiredError(MCPToolError):
    """Raised when the tool requires a JWT token that is not configured."""

    def __init__(self, message: str) -> None:
        super().__init__(
            code="authentication_required",
            message=message,
            status_code=401,
            retryable=False,
        )


class ConfigurationError(MCPToolError):
    """Raised when required MCP environment variables are missing."""

    def __init__(self, message: str) -> None:
        super().__init__(
            code="configuration_error",
            message=message,
            status_code=None,
            retryable=False,
        )


class BackendRequestError(MCPToolError):
    """Raised when a backend cannot be reached or returns a fatal response."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int | None = None,
        retryable: bool = False,
        code: str = "backend_request_error",
    ) -> None:
        super().__init__(
            code=code,
            message=message,
            status_code=status_code,
            retryable=retryable,
        )

