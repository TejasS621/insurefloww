"""Response schemas returned by the chatbot API endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from chat_bot.schemas.session_state import ChatSessionState


class ChatErrorItem(BaseModel):
    """Structured chat error details returned to the frontend."""

    model_config = ConfigDict(extra="forbid")

    type: str
    detail: str


class ChatSessionSnapshot(BaseModel):
    """Frontend-safe session snapshot returned with each chatbot reply."""

    model_config = ConfigDict(extra="forbid")

    session_id: str
    authenticated: bool
    current_flow: str
    insurance_type: str | None = None
    application_reference: str | None = None
    transaction_reference: str | None = None
    selected_quote_id: str | None = None
    policy_number: str | None = None

    @classmethod
    def from_session(cls, session: ChatSessionState) -> "ChatSessionSnapshot":
        """Build a frontend-safe snapshot from the mutable server session."""

        return cls(
            session_id=session.session_id,
            authenticated=session.authenticated,
            current_flow=session.current_flow,
            insurance_type=session.insurance_type,
            application_reference=session.application_reference,
            transaction_reference=session.transaction_reference,
            selected_quote_id=session.selected_quote_id,
            policy_number=session.policy_number,
        )


class ChatMessageData(BaseModel):
    """Structured chatbot reply returned to the customer frontend."""

    model_config = ConfigDict(extra="forbid")

    reply: str
    intent: str
    ui_action: str
    payload: dict[str, Any] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)
    suggested_replies: list[str] = Field(default_factory=list)
    session_state: ChatSessionSnapshot


class ChatAPIResponse(BaseModel):
    """Standard API wrapper returned from the chatbot service."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    message: str
    data: ChatMessageData | None = None
    errors: list[ChatErrorItem] = Field(default_factory=list)
