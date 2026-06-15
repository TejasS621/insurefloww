"""Process-local authentication state for login-driven shared workflows."""

from __future__ import annotations

from dataclasses import dataclass

from insureflow_mcp.core.errors import AuthenticationRequiredError


@dataclass(slots=True)
class AuthSessionStore:
    """Keep the latest customer and admin bearer tokens in server memory.

    This shared helper is reused by integrations like the voice bot, even
    though the public MCP server no longer exposes login tools directly.
    """

    customer_token: str | None = None
    admin_token: str | None = None

    def set_customer_token(self, token: str) -> None:
        """Persist the latest customer bearer token for this process."""

        self.customer_token = token

    def set_admin_token(self, token: str) -> None:
        """Persist the latest admin bearer token for this process."""

        self.admin_token = token

    def get_customer_token(self) -> str:
        """Return the stored customer token or raise a typed auth error."""

        if not self.customer_token:
            raise AuthenticationRequiredError(
                "Customer authentication is required. Run request_customer_otp and verify_customer_otp first."
            )
        return self.customer_token

    def get_admin_token(self) -> str:
        """Return the stored admin token or raise a typed auth error."""

        if not self.admin_token:
            raise AuthenticationRequiredError(
                "Admin authentication is required. Run admin_login or admin_verify first."
            )
        return self.admin_token
