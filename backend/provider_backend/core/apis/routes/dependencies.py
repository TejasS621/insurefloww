"""Authentication and integration dependencies for provider backend routes."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from odmantic import AIOEngine

from backend.provider_backend.commons.auth import (
    ExpiredSignatureError,
    JWTClaims,
    JWTError,
    decode_access_token,
)
from backend.provider_backend.commons.config import settings
from backend.provider_backend.core.database.database import get_database
from backend.provider_backend.core.models.broker_registry_model import BrokerRegistry
from backend.provider_backend.core.services.service_exceptions import (
    AuthenticationServiceError,
    AuthorizationServiceError,
)

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(slots=True)
class ProviderPrincipal:
    """Normalized provider principal extracted from a JWT access token.

    Provider admin routes depend on this object to keep authorization logic
    focused on business behavior instead of repeated token parsing code.
    """

    subject: str
    role: str
    expires_at: object


@dataclass(slots=True)
class AuthenticatedBroker:
    """Broker identity extracted from broker API key headers.

    Quote creation, payment session creation, and provider sync operations use
    broker API keys so external broker integrations avoid provider-admin JWTs.
    """

    broker_code: str


async def get_current_provider_admin_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> ProviderPrincipal:
    """Require a valid provider-admin JWT and return the authenticated principal."""
    if credentials is None:
        raise AuthenticationServiceError("A valid provider-admin access token is required.")
    if credentials.scheme.lower() != "bearer":
        raise AuthenticationServiceError("Authorization credentials must use the Bearer scheme.")
    try:
        claims: JWTClaims = decode_access_token(
            token=credentials.credentials,
        )
    except ExpiredSignatureError as exc:
        raise AuthenticationServiceError("The access token has expired.") from exc
    except JWTError as exc:
        raise AuthenticationServiceError("The access token is invalid.") from exc
    if claims.role != "provider_admin":
        raise AuthorizationServiceError("This endpoint only accepts provider-admin access tokens.")
    return ProviderPrincipal(subject=claims.subject, role=claims.role, expires_at=claims.expires_at)


async def get_authenticated_broker(
    x_broker_code: str | None = Header(default=None, alias="X-Broker-Code"),
    x_broker_api_key: str | None = Header(default=None, alias="X-Broker-Api-Key"),
    engine: AIOEngine = Depends(get_database),
) -> AuthenticatedBroker:
    """Validate broker integration headers and return the authenticated broker.

    Provider integration endpoints are intentionally broker-key protected so
    backend-to-backend calls do not depend on a provider-admin JWT session.
    """
    broker_code = (x_broker_code or "").strip()
    api_key = (x_broker_api_key or "").strip()
    if not broker_code or not api_key:
        raise AuthenticationServiceError("Broker integration headers are required.")

    broker = await engine.find_one(BrokerRegistry, BrokerRegistry.broker_code == broker_code)
    if broker is None:
        raise AuthenticationServiceError("The supplied broker integration key is not recognized.")

    if broker.api_key_hash != hashlib.sha256(api_key.encode("utf-8")).hexdigest():
        raise AuthenticationServiceError("The supplied broker integration key is invalid.")

    return AuthenticatedBroker(broker_code=broker.broker_code)
