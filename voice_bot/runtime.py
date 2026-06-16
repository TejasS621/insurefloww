"""Reusable runtime dependencies for the InsureFlow voice bot."""

from __future__ import annotations

from dataclasses import dataclass

from insureflow_mcp.clients.main_backend_client import MainBackendClient
from insureflow_mcp.core.auth_session import AuthSessionStore
from insureflow_mcp.core.config import get_settings
from insureflow_mcp.core.logging import configure_logging
from insureflow_mcp.tools.auth import AuthTools
from insureflow_mcp.tools.payments import PaymentTools
from insureflow_mcp.tools.policies import PolicyTools
from insureflow_mcp.tools.quotes import QuoteTools
from insureflow_mcp.tools.tickets import TicketTools
from insureflow_mcp.schemas.policies import DownloadPolicyInput, GetPolicyInput
from insureflow_mcp.schemas.tickets import CreateTicketInput
from voice_bot.config import VoiceBotSettings, get_voice_bot_settings


@dataclass(slots=True)
class VoiceBotRuntime:
    """Shared runtime objects used by Pipecat function handlers."""

    voice_settings: VoiceBotSettings
    auth_session: AuthSessionStore
    auth_tools: AuthTools
    quote_tools: QuoteTools
    payment_tools: PaymentTools
    policy_tools: PolicyTools
    ticket_tools: TicketTools

    @classmethod
    def build(cls) -> "VoiceBotRuntime":
        """Create the full voice bot dependency graph from environment settings."""

        voice_settings = get_voice_bot_settings()
        mcp_settings = get_settings()
        configure_logging(voice_settings.log_level)

        main_client = MainBackendClient(mcp_settings)
        auth_session = AuthSessionStore()

        return cls(
            voice_settings=voice_settings,
            auth_session=auth_session,
            auth_tools=AuthTools(main_client=main_client, auth_session=auth_session),
            quote_tools=QuoteTools(main_client=main_client),
            payment_tools=PaymentTools(main_client=main_client),
            policy_tools=PolicyTools(settings=mcp_settings, auth_session=auth_session, main_client=main_client),
            ticket_tools=TicketTools(auth_session=auth_session, main_client=main_client),
        )

    async def get_policy_with_session(self, payload: GetPolicyInput) -> object:
        """Fetch policy details using the in-memory customer session token."""

        return await self.policy_tools.get_policy(
            GetPolicyInput(
                policy_number=payload.policy_number,
                customer_access_token=self.auth_session.get_customer_token(),
            )
        )

    async def download_policy_with_session(self, payload: DownloadPolicyInput) -> object:
        """Download a policy document using the in-memory customer session token."""

        return await self.policy_tools.download_policy(
            DownloadPolicyInput(
                policy_number=payload.policy_number,
                customer_access_token=self.auth_session.get_customer_token(),
            )
        )

    async def create_ticket_with_session(self, payload: CreateTicketInput) -> object:
        """Create a support ticket using the in-memory customer session token."""

        return await self.ticket_tools.create_ticket(
            CreateTicketInput(
                customer_access_token=self.auth_session.get_customer_token(),
                transaction_reference=payload.transaction_reference,
                category=payload.category,
                priority=payload.priority,
                subject=payload.subject,
                message=payload.message,
            )
        )
