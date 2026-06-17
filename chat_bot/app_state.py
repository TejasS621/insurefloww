"""Shared application state and dependency helpers for the chatbot service."""

from __future__ import annotations

from chat_bot.handlers.conversation_handler import ConversationHandler
from chat_bot.runtime import ChatBotRuntime

_runtime = ChatBotRuntime.build()
_conversation_handler = ConversationHandler(_runtime)


def get_runtime() -> ChatBotRuntime:
    """Return the process-wide chatbot runtime."""

    return _runtime


def get_conversation_handler() -> ConversationHandler:
    """Return the process-wide conversation handler graph."""

    return _conversation_handler
