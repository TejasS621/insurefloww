"""Process-local authentication state for customer login-driven shared workflows."""

from __future__ import annotations

from dataclasses import dataclass

from insureflow_mcp.core.errors import AuthenticationRequiredError


@dataclass(slots=True)
class AuthSessionStore:
    """Keep the latest customer bearer token in server memory.

    This shared helper is reused by integrations like the voice bot, even
    though the public MCP server no longer exposes login tools directly.
    """

    customer_token: str | None = None

    def set_customer_token(self, token: str) -> None:
        """Persist the latest customer bearer token for this process."""

        self.customer_token = token

    def get_customer_token(self) -> str:
        """Return the stored customer token or raise a typed auth error."""

        if not self.customer_token:
            raise AuthenticationRequiredError(
                "Customer authentication is required. Run request_customer_otp and verify_customer_otp first."
            )
        return self.customer_token
