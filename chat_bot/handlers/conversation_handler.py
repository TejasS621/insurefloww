"""Top-level chatbot conversation router for customer workflows."""

from __future__ import annotations

from chat_bot.handlers.auth_handler import AuthHandler
from chat_bot.handlers.base import build_chat_message
from chat_bot.handlers.payment_handler import PaymentHandler
from chat_bot.handlers.policy_handler import PolicyHandler
from chat_bot.handlers.quote_handler import QuoteHandler
from chat_bot.handlers.ticket_handler import TicketHandler
from chat_bot.prompts import CHATBOT_WELCOME_MESSAGE
from chat_bot.runtime import ChatBotRuntime
from chat_bot.schemas.chat_request import ChatMessageRequest
from chat_bot.schemas.chat_response import ChatMessageData
from chat_bot.schemas.session_state import ChatSessionState
from chat_bot.services.intent_service import IntentService


class ConversationHandler:
    """Coordinate chatbot intents across auth, quote, payment, policy, and support flows."""

    def __init__(self, runtime: ChatBotRuntime) -> None:
        self.runtime = runtime
        self.intent_service = IntentService()
        self.auth_handler = AuthHandler(runtime)
        self.quote_handler = QuoteHandler(runtime)
        self.payment_handler = PaymentHandler(runtime)
        self.policy_handler = PolicyHandler(runtime)
        self.ticket_handler = TicketHandler(runtime)

    async def handle(self, request: ChatMessageRequest, session: ChatSessionState) -> ChatMessageData:
        """Route one incoming chat message to the correct domain handler."""

        intent = self.intent_service.detect_intent(request, session)

        if intent == "GREETING":
            session.current_flow = "GENERAL"
            return build_chat_message(
                session=session,
                reply=CHATBOT_WELCOME_MESSAGE,
                intent="GREETING",
                ui_action="SHOW_MESSAGE",
                suggested_replies=[
                    "I want a health insurance quote",
                    "I want to compare insurance plans",
                    "Help me check my policy status",
                ],
            )
        if intent == "REQUEST_CUSTOMER_OTP":
            return await self.auth_handler.request_customer_otp(request=request, session=session)
        if intent == "VERIFY_CUSTOMER_OTP":
            return await self.auth_handler.verify_customer_otp(request=request, session=session)
        if intent == "GENERATE_QUOTE":
            return await self.quote_handler.generate_quote(request=request, session=session)
        if intent == "SELECT_QUOTE":
            return await self.quote_handler.select_quote(request=request, session=session)
        if intent == "INITIATE_PAYMENT":
            return await self.payment_handler.initiate_payment(request=request, session=session)
        if intent == "GET_PAYMENT_STATUS":
            return await self.payment_handler.get_payment_status(request=request, session=session)
        if intent == "GET_POLICY":
            return await self.policy_handler.get_policy(request=request, session=session)
        if intent == "DOWNLOAD_POLICY":
            return await self.policy_handler.download_policy(request=request, session=session)
        if intent == "CREATE_TICKET":
            return await self.ticket_handler.create_ticket(request=request, session=session)

        return build_chat_message(
            session=session,
            reply=(
                "I am here to help with your insurance. Please tell me what you would like to do."
            ),
            intent="UNKNOWN",
            ui_action="SHOW_MESSAGE",
            suggested_replies=[
                "I want a health insurance quote",
                "Help me with payment",
                "Help me with my policy",
            ],
        )
