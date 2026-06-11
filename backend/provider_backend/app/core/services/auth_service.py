"""Authentication service helpers for the provider backend."""

from __future__ import annotations

from odmantic import AIOEngine

from .service_exceptions import IntegrationServiceError


class ProviderAuthService:
    """Encapsulate provider-admin authentication workflows."""

    async def authenticate_provider_admin(
        self,
        _: AIOEngine,
        *,
        email: str,
        password: str,
    ) -> None:
        """Validate provider-admin credentials.

        This workflow intentionally remains explicit rather than silently
        succeeding because the branch does not yet contain provider-admin
        persistence or password-hashing infrastructure.
        """
        _ = (email, password)
        raise IntegrationServiceError(
            "Provider admin authentication is not available until provider-admin persistence is implemented."
        )


provider_auth_service = ProviderAuthService()

