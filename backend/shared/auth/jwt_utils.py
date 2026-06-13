"""Shared JWT helpers for issuing and validating access tokens."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, ExpiredSignatureError, jwt


@dataclass(slots=True)
class JWTClaims:
    """Normalized JWT claims extracted from an access token.

    The helper keeps authentication dependencies small by returning a typed
    object instead of making each backend parse raw JWT claim dictionaries.
    """

    subject: str
    role: str
    expires_at: datetime


def create_access_token(
    *,
    subject: str,
    role: str,
    secret_key: str,
    algorithm: str,
    expires_delta: timedelta,
    additional_claims: dict[str, Any] | None = None,
) -> tuple[str, datetime]:
    """Create a signed JWT access token and return it with its expiry timestamp.

    The token always carries `sub` and `role` claims so role-based route
    dependencies can authorize customer, admin, and provider-admin access.
    """
    expires_at = datetime.now(timezone.utc) + expires_delta
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "exp": expires_at,
    }
    if additional_claims:
        payload.update(additional_claims)
    return jwt.encode(payload, secret_key, algorithm=algorithm), expires_at


def decode_access_token(
    *,
    token: str,
    secret_key: str,
    algorithm: str,
) -> JWTClaims:
    """Decode a JWT access token and return normalized subject and role claims.

    `ExpiredSignatureError` and `JWTError` are intentionally propagated so the
    backend dependencies can convert them into project-standard API errors.
    """
    payload = jwt.decode(token, secret_key, algorithms=[algorithm])
    subject = str(payload.get("sub") or "").strip()
    role = str(payload.get("role") or "").strip()
    if not subject or not role:
        raise JWTError("The access token is missing required claims.")

    exp_claim = payload.get("exp")
    if exp_claim is None:
        raise JWTError("The access token is missing an expiry claim.")
    expires_at = (
        datetime.fromtimestamp(exp_claim, tz=timezone.utc)
        if isinstance(exp_claim, (int, float))
        else exp_claim
    )
    if not isinstance(expires_at, datetime):
        raise JWTError("The access token has an invalid expiry claim.")

    return JWTClaims(subject=subject, role=role, expires_at=expires_at)


__all__ = ["ExpiredSignatureError", "JWTError", "JWTClaims", "create_access_token", "decode_access_token"]
