"""Session models used by the chatbot orchestration layer."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ChatSessionState(BaseModel):
    """Conversation state stored for one chatbot session identifier."""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    authenticated: bool = False
    customer_access_token: str | None = None
    mobile_number: str | None = None
    current_flow: str = "GENERAL"
    insurance_type: str | None = None
    application_reference: str | None = None
    transaction_reference: str | None = None
    selected_quote_id: str | None = None
    selected_addons: list[str] = Field(default_factory=list)
    policy_number: str | None = None
    payment_reference: str | None = None
    quote_summary: list[dict[str, Any]] = Field(default_factory=list)
    collected_personal_details: dict[str, Any] = Field(default_factory=dict)
    collected_coverage_details: dict[str, Any] = Field(default_factory=dict)
    collected_health_details: dict[str, Any] = Field(default_factory=dict)
    last_intent: str | None = None
    last_bot_reply: str | None = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
