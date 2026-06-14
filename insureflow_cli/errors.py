"""CLI-local exceptions and backend error wrappers."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CLIError(Exception):
    """Base error raised by CLI operations for clean user-facing messages."""

    message: str

    def __str__(self) -> str:
        """Return the user-facing error message."""

        return self.message


@dataclass(slots=True)
class BackendRequestError(CLIError):
    """Raised when the backend request fails or returns an invalid response."""

    status_code: int | None = None
    retryable: bool = False
    code: str = "backend_request_error"


class AuthenticationRequiredError(CLIError):
    """Raised when a command needs a stored customer or admin session token."""
