"""In-memory session management for chatbot conversation state."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from chat_bot.config import ChatBotSettings
from chat_bot.schemas.session_state import ChatSessionState
from insureflow_mcp.core.errors import AuthenticationRequiredError


class ChatSessionStore:
    """Keep chatbot session state in memory for guest and authenticated flows."""

    def __init__(self, *, settings: ChatBotSettings) -> None:
        self.settings = settings
        self._sessions: dict[str, ChatSessionState] = {}

    def get_or_create(self, session_id: str) -> ChatSessionState:
        """Return an existing session or create a new guest session record."""

        self.purge_expired()
        session = self._sessions.get(session_id)
        if session is None:
            session = ChatSessionState(session_id=session_id)
            self._sessions[session_id] = session
        return session

    def save(self, session: ChatSessionState) -> ChatSessionState:
        """Persist the updated session and refresh its last-updated timestamp."""

        session.updated_at = datetime.now(timezone.utc)
        self._sessions[session.session_id] = session
        return session

    def purge_expired(self) -> None:
        """Remove old sessions whose TTL has passed."""

        cutoff = datetime.now(timezone.utc) - timedelta(minutes=self.settings.session_ttl_minutes)
        expired_keys = [
            session_id
            for session_id, session in self._sessions.items()
            if session.updated_at < cutoff
        ]
        for session_id in expired_keys:
            self._sessions.pop(session_id, None)


class SessionAuthStore:
    """Adapt a chatbot session into the MCP auth-session interface."""

    def __init__(self, session: ChatSessionState) -> None:
        self.session = session

    def set_customer_token(self, token: str) -> None:
        """Persist a verified customer token on the chatbot session."""

        self.session.customer_access_token = token
        self.session.authenticated = True

    def get_customer_token(self) -> str:
        """Return the stored customer token or raise a typed auth error."""

        if not self.session.customer_access_token:
            raise AuthenticationRequiredError(
                "Customer authentication is required for this chatbot action."
            )
        return self.session.customer_access_token
