"""Reusable request-context dependencies for main backend routes."""

from __future__ import annotations

from fastapi import Header
from pydantic import EmailStr, TypeAdapter

from backend.main_backend.app.core.services.service_exceptions import (
    ValidationServiceError,
)

email_adapter = TypeAdapter(EmailStr)


async def get_current_user_id(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> str:
    """Resolve the current user identifier from a temporary request header.

    This keeps router implementations stable until token-based authentication
    is introduced in a later branch.
    """
    if x_user_id is None or not x_user_id.strip():
        raise ValidationServiceError("The X-User-Id header is required for this endpoint.")
    return x_user_id.strip()


async def get_optional_user_id(
    x_user_id: str | None = Header(default=None, alias="X-User-Id"),
) -> str | None:
    """Resolve an optional user identifier from the current request."""
    if x_user_id is None:
        return None
    normalized = x_user_id.strip()
    return normalized or None


async def get_optional_admin_email(
    x_admin_email: str | None = Header(default=None, alias="X-Admin-Email"),
) -> str | None:
    """Resolve an optional admin email used for broker audit metadata."""
    if x_admin_email is None:
        return None
    normalized = x_admin_email.strip()
    if not normalized:
        return None
    return str(email_adapter.validate_python(normalized))


async def get_current_admin_actor(
    x_admin_id: str | None = Header(default=None, alias="X-Admin-Id"),
    x_admin_email: str | None = Header(default=None, alias="X-Admin-Email"),
) -> str:
    """Resolve the current admin identity from temporary request headers."""
    if x_admin_id is not None and x_admin_id.strip():
        return x_admin_id.strip()
    admin_email = await get_optional_admin_email(x_admin_email)
    if admin_email is not None:
        return admin_email
    raise ValidationServiceError(
        "Either the X-Admin-Id or X-Admin-Email header is required for admin workflows."
    )
