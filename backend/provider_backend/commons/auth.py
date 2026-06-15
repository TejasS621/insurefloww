"""
Provide authentication helpers for the provider backend.

Args:
    None: This module defines JWT creation and validation helpers together
    with password hashing utilities for the provider backend.

Returns:
    None: Helper functions return signed tokens, decoded claims, or hashed
    password values for use across provider auth and dependency modules.

Raises:
    JWTError: Token decoding errors are propagated so route dependencies can
    normalize them into project-standard authentication responses.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

from jose import JWTError, ExpiredSignatureError, jwt
from passlib.context import CryptContext

from backend.provider_backend.commons.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


@dataclass(slots=True)
class JWTClaims:
    """
    Represent normalized JWT claims extracted from an access token.

    Args:
        subject: Authenticated principal identifier stored in the token.
        role: Role claim used by route authorization helpers.
        expires_at: Expiry timestamp extracted from the token payload.

    Returns:
        None: Instances are used as typed auth context objects.

    Raises:
        ValueError: Propagates if invalid claim data is supplied during construction.
    """

    subject: str
    role: str
    expires_at: datetime


def create_access_token(
    *,
    subject: str,
    role: str,
    expires_delta: timedelta,
    additional_claims: dict[str, Any] | None = None,
) -> tuple[str, datetime]:
    """
    Create a signed JWT access token for a backend principal.

    Args:
        subject: Principal identifier stored in the `sub` claim.
        role: Authorization role stored in the `role` claim.
        expires_delta: Duration after which the token should expire.
        additional_claims: Optional extra claims merged into the token payload.

    Returns:
        tuple[str, datetime]: Signed JWT token string and its expiry timestamp.

    Raises:
        JWTError: Propagates if token encoding fails.
    """
    expires_at = datetime.now(timezone.utc) + expires_delta
    payload: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "exp": expires_at,
    }
    if additional_claims:
        payload.update(additional_claims)
    return (
        jwt.encode(payload, settings.jwt_secret_key, algorithm=settings.jwt_algorithm),
        expires_at,
    )


def decode_access_token(*, token: str) -> JWTClaims:
    """
    Decode a JWT access token and return normalized claims.

    Args:
        token: Signed JWT string supplied by the caller.

    Returns:
        JWTClaims: Normalized typed claims extracted from the token payload.

    Raises:
        ExpiredSignatureError: Raised when the token expiry has passed.
        JWTError: Raised when the token is malformed or missing required claims.
    """
    payload = jwt.decode(
        token,
        settings.jwt_secret_key,
        algorithms=[settings.jwt_algorithm],
    )
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


def hash_password(password: str) -> str:
    """
    Hash a plain-text password for secure storage.

    Args:
        password: Plain-text password supplied by the caller.

    Returns:
        str: Bcrypt password hash.

    Raises:
        ValueError: Propagates if the hashing backend rejects the input.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain-text password against a stored password hash.

    Args:
        plain_password: Plain-text password supplied for verification.
        hashed_password: Stored bcrypt hash to compare against.

    Returns:
        bool: `True` when the password matches the hash, otherwise `False`.

    Raises:
        ValueError: Propagates if the hashing backend rejects the input.
    """
    return pwd_context.verify(plain_password, hashed_password)
