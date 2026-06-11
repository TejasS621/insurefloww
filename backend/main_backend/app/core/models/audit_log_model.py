from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from odmantic import Field, Model
from pydantic import ConfigDict


class AuditAction(str, Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    STATUS_CHANGE = "STATUS_CHANGE"
    LOGIN = "LOGIN"
    VERIFY = "VERIFY"


class AuditLog(Model):
    actor_id: str | None = Field(default=None)
    actor_role: str | None = Field(default=None)
    action: AuditAction = Field(...)
    entity_type: str = Field(...)
    entity_id: str = Field(...)
    transaction_reference: str | None = Field(default=None)
    old_state: dict[str, object] | None = Field(default=None)
    new_state: dict[str, object] | None = Field(default=None)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    model_config = ConfigDict(collection="audit_logs", extra="forbid")

