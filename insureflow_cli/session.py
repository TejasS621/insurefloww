"""Persistent token session storage for CLI login workflows."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict

from insureflow_cli.errors import AuthenticationRequiredError


class SessionState(BaseModel):
    """Serializable customer and admin session state persisted on disk."""

    model_config = ConfigDict(extra="forbid")

    customer_token: str | None = None
    customer_user_id: str | None = None
    admin_token: str | None = None
    admin_user_id: str | None = None


class SessionStore:
    """Load, save, and clear CLI session tokens between command invocations."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.state = self._load()

    def save(self) -> None:
        """Persist the current session state to disk."""

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(self.state.model_dump_json(indent=2), encoding="utf-8")

    def set_customer(self, *, token: str, user_id: str | None) -> None:
        """Persist the latest customer bearer token and identity."""

        self.state.customer_token = token
        self.state.customer_user_id = user_id
        self.save()

    def set_admin(self, *, token: str, user_id: str | None) -> None:
        """Persist the latest admin bearer token and identity."""

        self.state.admin_token = token
        self.state.admin_user_id = user_id
        self.save()

    def require_customer_token(self) -> str:
        """Return the stored customer token or raise a clean auth error."""

        if not self.state.customer_token:
            raise AuthenticationRequiredError(
                "Customer login required. Run `python -m insureflow_cli auth customer-verify` first."
            )
        return self.state.customer_token

    def require_admin_token(self) -> str:
        """Return the stored admin token or raise a clean auth error."""

        if not self.state.admin_token:
            raise AuthenticationRequiredError(
                "Admin login required. Run `python -m insureflow_cli auth admin-login` first."
            )
        return self.state.admin_token

    def clear(self, scope: str) -> None:
        """Clear customer, admin, or all stored session tokens."""

        if scope in {"customer", "all"}:
            self.state.customer_token = None
            self.state.customer_user_id = None
        if scope in {"admin", "all"}:
            self.state.admin_token = None
            self.state.admin_user_id = None
        self.save()

    def _load(self) -> SessionState:
        """Load session state from disk when present, otherwise return empty state."""

        if not self.path.exists():
            return SessionState()
        try:
            return SessionState.model_validate(json.loads(self.path.read_text(encoding="utf-8")))
        except (json.JSONDecodeError, ValueError):
            return SessionState()
