"""Authentication service helpers for the provider backend."""

from __future__ import annotations

from odmantic import AIOEngine

from backend.provider_backend.commons.config import settings
from backend.provider_backend.commons.logger import get_logger

from .service_exceptions import AuthenticationServiceError

logger = get_logger(__name__)


class ProviderAuthService:
    """Encapsulate provider-admin authentication workflows."""

    async def authenticate_provider_admin(
        self,
        engine: AIOEngine,
        *,
        email: str,
        password: str,
    ) -> str:
        """Validate configured provider-admin credentials and return the identity.

        Provider-admin login is configuration-backed in this branch so JWT
        authorization can be enabled without introducing a new user store.
        """
        _ = engine
        if email.strip().lower() != settings.provider_admin_email.strip().lower():
            logger.warning("Rejected provider-admin authentication for '%s'.", email)
            raise AuthenticationServiceError("The supplied provider-admin credentials are invalid.")
        if password != settings.provider_admin_password:
            logger.warning("Rejected provider-admin authentication for '%s'.", email)
            raise AuthenticationServiceError("The supplied provider-admin credentials are invalid.")
        return settings.provider_admin_email


provider_auth_service = ProviderAuthService()

