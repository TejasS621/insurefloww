"""Shared response helpers for chatbot conversation handlers."""

from __future__ import annotations

from typing import Any

from chat_bot.schemas.chat_response import ChatMessageData, ChatSessionSnapshot
from chat_bot.schemas.session_state import ChatSessionState


def build_chat_message(
    *,
    session: ChatSessionState,
    reply: str,
    intent: str,
    ui_action: str,
    payload: dict[str, Any] | None = None,
    missing_fields: list[str] | None = None,
    suggested_replies: list[str] | None = None,
) -> ChatMessageData:
    """Build a consistent structured chatbot reply for the frontend."""

    session.last_intent = intent
    session.last_bot_reply = reply
    return ChatMessageData(
        reply=reply,
        intent=intent,
        ui_action=ui_action,
        payload=payload or {},
        missing_fields=missing_fields or [],
        suggested_replies=suggested_replies or [],
        session_state=ChatSessionSnapshot.from_session(session),
    )
