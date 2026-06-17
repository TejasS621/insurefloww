"""Support-ticket handlers for authenticated chatbot sessions."""

from __future__ import annotations

from pydantic import ValidationError

from chat_bot.handlers.base import build_chat_message
from chat_bot.prompts import CHATBOT_AUTH_REQUIRED_MESSAGE
from chat_bot.schemas.chat_request import ChatMessageRequest
from chat_bot.schemas.chat_response import ChatMessageData
from chat_bot.schemas.session_state import ChatSessionState
from chat_bot.runtime import ChatBotRuntime
from insureflow_mcp.schemas.tickets import CreateTicketInput


class TicketHandler:
    """Handle secure support-ticket creation through the chatbot."""

    def __init__(self, runtime: ChatBotRuntime) -> None:
        self.runtime = runtime

    async def create_ticket(
        self,
        *,
        request: ChatMessageRequest,
        session: ChatSessionState,
    ) -> ChatMessageData:
        """Create a support ticket after confirming customer authentication."""

        if not session.authenticated:
            return build_chat_message(
                session=session,
                reply=CHATBOT_AUTH_REQUIRED_MESSAGE,
                intent="CREATE_TICKET",
                ui_action="REQUEST_OTP",
                suggested_replies=["Send OTP"],
            )

        payload = dict(request.payload)
        payload.setdefault("customer_access_token", session.customer_access_token)
        payload.setdefault("transaction_reference", session.transaction_reference)
        try:
            ticket_input = CreateTicketInput.model_validate(payload)
        except ValidationError as exc:
            return build_chat_message(
                session=session,
                reply="Please complete the ticket subject and message so I can create your support request.",
                intent="CREATE_TICKET",
                ui_action="SHOW_TICKET_FORM",
                missing_fields=self._validation_fields(exc),
            )

        tools = self.runtime.bind_session_tools(session)
        result = await tools.ticket_tools.create_ticket(ticket_input)
        if not result.success:
            return build_chat_message(
                session=session,
                reply=result.message,
                intent="CREATE_TICKET",
                ui_action="SHOW_TICKET_FORM",
                payload={"error": result.error.model_dump(mode="json") if result.error else {}},
            )
        session.current_flow = "TICKET"
        return build_chat_message(
            session=session,
            reply="Your support ticket has been created successfully.",
            intent="CREATE_TICKET",
            ui_action="SHOW_TICKET_CONFIRMATION",
            payload=result.data.model_dump(mode="json") if result.data else {},
        )

    @staticmethod
    def _validation_fields(exc: ValidationError) -> list[str]:
        """Flatten Pydantic validation errors into frontend-friendly field paths."""

        fields: list[str] = []
        for error in exc.errors():
            location = [str(item) for item in error.get("loc", []) if str(item) != "__root__"]
            if location:
                fields.append(".".join(location))
        return fields
