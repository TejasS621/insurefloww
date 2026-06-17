"""Reusable backend and tool wiring for the InsureFlow chatbot service."""

from __future__ import annotations

from dataclasses import dataclass

from chat_bot.config import ChatBotSettings, get_chat_bot_settings
from chat_bot.schemas.session_state import ChatSessionState
from chat_bot.session import SessionAuthStore, ChatSessionStore
from insureflow_mcp.clients.main_backend_client import MainBackendClient
from insureflow_mcp.core.config import MCPSettings, get_settings
from insureflow_mcp.core.logging import configure_logging
from insureflow_mcp.tools.auth import AuthTools
from insureflow_mcp.tools.payments import PaymentTools
from insureflow_mcp.tools.policies import PolicyTools
from insureflow_mcp.tools.quotes import QuoteTools
from insureflow_mcp.tools.tickets import TicketTools


@dataclass(slots=True)
class SessionBoundChatTools:
    """Tool set bound to one chatbot session and its auth context."""

    auth_tools: AuthTools
    quote_tools: QuoteTools
    payment_tools: PaymentTools
    policy_tools: PolicyTools
    ticket_tools: TicketTools


@dataclass(slots=True)
class ChatBotRuntime:
    """Shared runtime objects used by the chatbot request handlers."""

    chat_settings: ChatBotSettings
    mcp_settings: MCPSettings
    session_store: ChatSessionStore
    main_client: MainBackendClient

    @classmethod
    def build(cls) -> "ChatBotRuntime":
        """Create the chatbot runtime graph from environment-backed settings."""

        chat_settings = get_chat_bot_settings()
        mcp_settings = get_settings()
        configure_logging(chat_settings.log_level)

        return cls(
            chat_settings=chat_settings,
            mcp_settings=mcp_settings,
            session_store=ChatSessionStore(settings=chat_settings),
            main_client=MainBackendClient(mcp_settings),
        )

    def bind_session_tools(self, session: ChatSessionState) -> SessionBoundChatTools:
        """Create MCP-backed tools that share one chatbot session token context."""

        auth_session = SessionAuthStore(session)
        return SessionBoundChatTools(
            auth_tools=AuthTools(main_client=self.main_client, auth_session=auth_session),
            quote_tools=QuoteTools(main_client=self.main_client),
            payment_tools=PaymentTools(main_client=self.main_client),
            policy_tools=PolicyTools(
                settings=self.mcp_settings,
                auth_session=auth_session,
                main_client=self.main_client,
            ),
            ticket_tools=TicketTools(auth_session=auth_session, main_client=self.main_client),
        )
