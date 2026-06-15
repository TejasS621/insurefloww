"""Reusable request-context dependencies for main backend routes."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass

from fastapi import Depends, Header
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from odmantic import AIOEngine

from backend.main_backend.commons.auth import (
    ExpiredSignatureError,
    JWTClaims,
    JWTError,
    decode_access_token,
)
from backend.main_backend.commons.config import settings
from backend.main_backend.core.database.database import get_database
from backend.main_backend.core.services.service_exceptions import (
    AuthenticationServiceError,
    AuthorizationServiceError,
)
from backend.provider_backend.core.models.broker_registry_model import BrokerRegistry

bearer_scheme = HTTPBearer(auto_error=False)


@dataclass(slots=True)
class AuthenticatedPrincipal:
    """Normalized authenticated principal extracted from a JWT access token.

    Routes use this typed object instead of raw JWT payloads so customer and
    admin authorization stays readable and consistent across the codebase.
    """

    subject: str
    role: str
    expires_at: object


@dataclass(slots=True)
class AuthenticatedBroker:
    """Broker identity extracted from integration API key headers.

    Provider synchronization and broker-facing provider APIs use this object
    to confirm which broker integration key was presented on the request.
    """

    broker_code: str


async def get_optional_customer_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedPrincipal | None:
    """Return a customer principal when a valid customer JWT is provided.

    Guest-compatible routes can depend on this helper to accept anonymous
    requests while still linking state to a customer when a token is present.
    """
    principal = _decode_optional_principal(credentials)
    if principal is None:
        return None
    if principal.role != "customer":
        raise AuthorizationServiceError("This endpoint only accepts customer access tokens.")
    return principal


async def get_current_customer_principal(
    principal: AuthenticatedPrincipal | None = Depends(get_optional_customer_principal),
) -> AuthenticatedPrincipal:
    """Require a customer JWT and return the authenticated principal."""
    if principal is None:
        raise AuthenticationServiceError("A valid customer access token is required.")
    return principal


async def get_optional_admin_principal(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> AuthenticatedPrincipal | None:
    """Return an admin principal when a valid admin JWT is provided."""
    principal = _decode_optional_principal(credentials)
    if principal is None:
        return None
    if principal.role != "admin":
        raise AuthorizationServiceError("This endpoint only accepts admin access tokens.")
    return principal


async def get_current_admin_principal(
    principal: AuthenticatedPrincipal | None = Depends(get_optional_admin_principal),
) -> AuthenticatedPrincipal:
    """Require an admin JWT and return the authenticated principal."""
    if principal is None:
        raise AuthenticationServiceError("A valid admin access token is required.")
    return principal


async def get_current_user_id(
    principal: AuthenticatedPrincipal = Depends(get_current_customer_principal),
) -> str:
    """Return the authenticated customer identifier extracted from the JWT token."""
    return principal.subject


async def get_optional_user_id(
    principal: AuthenticatedPrincipal | None = Depends(get_optional_customer_principal),
) -> str | None:
    """Return the authenticated customer identifier when a valid JWT is present."""
    return principal.subject if principal is not None else None


async def get_optional_admin_email(
    principal: AuthenticatedPrincipal | None = Depends(get_optional_admin_principal),
) -> str | None:
    """Return the authenticated admin identity when an admin JWT is present."""
    return principal.subject if principal is not None else None


async def get_current_admin_actor(
    principal: AuthenticatedPrincipal = Depends(get_current_admin_principal),
) -> str:
    """Return the authenticated admin identity extracted from the JWT token."""
    return principal.subject


async def get_authenticated_broker(
    x_broker_code: str | None = Header(default=None, alias="X-Broker-Code"),
    x_broker_api_key: str | None = Header(default=None, alias="X-Broker-Api-Key"),
    engine: AIOEngine = Depends(get_database),
) -> AuthenticatedBroker:
    """Validate broker integration headers and return the authenticated broker code.

    Provider synchronization and provider integration routes rely on broker API
    keys instead of JWTs so backend-to-backend requests remain easy to rotate.
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


def _decode_optional_principal(
    credentials: HTTPAuthorizationCredentials | None,
) -> AuthenticatedPrincipal | None:
    """Decode a bearer token into a normalized authenticated principal.

    Missing tokens return `None` so guest-compatible routes can continue to
    work, while malformed or expired tokens raise typed auth errors.
    """
    if credentials is None:
        return None
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
    return AuthenticatedPrincipal(
        subject=claims.subject,
        role=claims.role,
        expires_at=claims.expires_at,
    )
