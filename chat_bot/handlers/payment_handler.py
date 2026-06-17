"""Payment handlers for chatbot payment initiation and status checks."""

from __future__ import annotations

from pydantic import ValidationError

from chat_bot.handlers.base import build_chat_message
from chat_bot.schemas.chat_request import ChatMessageRequest
from chat_bot.schemas.chat_response import ChatMessageData
from chat_bot.schemas.session_state import ChatSessionState
from chat_bot.runtime import ChatBotRuntime
from insureflow_mcp.schemas.payments import GetPaymentStatusInput, InitiatePaymentInput


class PaymentHandler:
    """Handle payment initiation and payment-status retrieval for chatbot sessions."""

    def __init__(self, runtime: ChatBotRuntime) -> None:
        self.runtime = runtime

    async def initiate_payment(
        self,
        *,
        request: ChatMessageRequest,
        session: ChatSessionState,
    ) -> ChatMessageData:
        """Create a hosted payment session using the current transaction reference."""

        payload = dict(request.payload)
        payload.setdefault("transaction_reference", session.transaction_reference)
        try:
            payment_input = InitiatePaymentInput.model_validate(payload)
        except ValidationError as exc:
            return build_chat_message(
                session=session,
                reply="Please select a quote first so I can start your payment session.",
                intent="INITIATE_PAYMENT",
                ui_action="SHOW_PAYMENT_CTA",
                missing_fields=self._validation_fields(exc),
            )

        tools = self.runtime.bind_session_tools(session)
        result = await tools.payment_tools.initiate_payment(payment_input)
        if not result.success:
            return build_chat_message(
                session=session,
                reply=result.message,
                intent="INITIATE_PAYMENT",
                ui_action="SHOW_PAYMENT_CTA",
                payload={"error": result.error.model_dump(mode="json") if result.error else {}},
            )
        data = result.data
        session.current_flow = "PAYMENT"
        session.transaction_reference = payment_input.transaction_reference
        if data is not None:
            session.payment_reference = data.payment_reference
        return build_chat_message(
            session=session,
            reply="Your payment session is ready. Please continue using the payment link below.",
            intent="INITIATE_PAYMENT",
            ui_action="SHOW_PAYMENT_LINK",
            payload=data.model_dump(mode="json") if data else {},
            suggested_replies=["Check payment status"],
        )

    async def get_payment_status(
        self,
        *,
        request: ChatMessageRequest,
        session: ChatSessionState,
    ) -> ChatMessageData:
        """Return the latest payment status using a stored or explicit transaction reference."""

        payload = dict(request.payload)
        payload.setdefault("transaction_reference", session.transaction_reference)
        try:
            status_input = GetPaymentStatusInput.model_validate(payload)
        except ValidationError as exc:
            return build_chat_message(
                session=session,
                reply="Please share the transaction reference you want me to check.",
                intent="GET_PAYMENT_STATUS",
                ui_action="SHOW_PAYMENT_STATUS",
                missing_fields=self._validation_fields(exc),
            )

        tools = self.runtime.bind_session_tools(session)
        result = await tools.payment_tools.get_payment_status(status_input)
        if not result.success:
            return build_chat_message(
                session=session,
                reply=result.message,
                intent="GET_PAYMENT_STATUS",
                ui_action="SHOW_PAYMENT_STATUS",
                payload={"error": result.error.model_dump(mode="json") if result.error else {}},
            )
        data = result.data
        session.current_flow = "PAYMENT_STATUS"
        return build_chat_message(
            session=session,
            reply="Here is the latest payment status for your transaction.",
            intent="GET_PAYMENT_STATUS",
            ui_action="SHOW_PAYMENT_STATUS",
            payload=data.model_dump(mode="json") if data else {},
            suggested_replies=["Download policy", "Create support ticket"],
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
