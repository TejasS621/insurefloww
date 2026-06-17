"""Quote and application handlers for the guest-first chatbot journey."""

from __future__ import annotations

from pydantic import ValidationError

from chat_bot.handlers.base import build_chat_message
from chat_bot.schemas.chat_request import ChatMessageRequest
from chat_bot.schemas.chat_response import ChatMessageData
from chat_bot.schemas.session_state import ChatSessionState
from chat_bot.runtime import ChatBotRuntime
from insureflow_mcp.schemas.quotes import GenerateQuoteInput, SelectQuoteInput


class QuoteHandler:
    """Handle application creation, quote generation, and quote selection."""

    def __init__(self, runtime: ChatBotRuntime) -> None:
        self.runtime = runtime

    async def generate_quote(
        self,
        *,
        request: ChatMessageRequest,
        session: ChatSessionState,
    ) -> ChatMessageData:
        """Generate quotes when the frontend supplies a complete application payload."""

        payload = dict(request.payload)
        if session.insurance_type and "insurance_type" not in payload:
            payload["insurance_type"] = session.insurance_type
        if "guest_identifier" not in payload:
            payload["guest_identifier"] = request.payload.get("guest_identifier") or session.session_id

        try:
            quote_input = GenerateQuoteInput.model_validate(payload)
        except ValidationError as exc:
            missing_fields = self._validation_fields(exc)
            session.current_flow = "QUOTE_COLLECTION"
            if payload.get("insurance_type"):
                session.insurance_type = str(payload.get("insurance_type")).upper()
            return build_chat_message(
                session=session,
                reply=(
                    "I can help generate your quote. Please complete the required customer, "
                    "coverage, and health details first."
                ),
                intent="GENERATE_QUOTE",
                ui_action="COLLECT_QUOTE_DETAILS",
                missing_fields=missing_fields,
                payload={"required_payload": "GenerateQuoteInput"},
                suggested_replies=["Submit application details", "Health insurance quote"],
            )

        tools = self.runtime.bind_session_tools(session)
        result = await tools.quote_tools.generate_quote(quote_input)
        if not result.success:
            session.current_flow = "QUOTE_COLLECTION"
            return build_chat_message(
                session=session,
                reply=result.message,
                intent="GENERATE_QUOTE",
                ui_action="COLLECT_QUOTE_DETAILS",
                payload={"error": result.error.model_dump(mode="json") if result.error else {}},
            )
        data = result.data
        session.current_flow = "QUOTE_RESULTS"
        session.insurance_type = quote_input.insurance_type.upper()
        session.collected_personal_details = quote_input.personal_details.model_dump(mode="json")
        session.collected_coverage_details = quote_input.coverage_details.model_dump(mode="json")
        session.collected_health_details = (
            quote_input.health_details.model_dump(mode="json")
            if quote_input.health_details is not None
            else {}
        )
        if data is not None:
            session.application_reference = data.application_reference
            session.transaction_reference = data.transaction_reference
            session.quote_summary = [quote.model_dump(mode="json") for quote in data.quote_summary]
        return build_chat_message(
            session=session,
            reply="I found quote options for you. Please review and select the plan you want.",
            intent="GENERATE_QUOTE",
            ui_action="SHOW_QUOTES",
            payload=data.model_dump(mode="json") if data else {},
            suggested_replies=["Select this quote", "Show payment options"],
        )

    async def select_quote(
        self,
        *,
        request: ChatMessageRequest,
        session: ChatSessionState,
    ) -> ChatMessageData:
        """Select a quote and return the updated pricing summary."""

        try:
            quote_input = SelectQuoteInput.model_validate(request.payload)
        except ValidationError as exc:
            return build_chat_message(
                session=session,
                reply="Please tell me which quote you want to select.",
                intent="SELECT_QUOTE",
                ui_action="SELECT_QUOTE",
                missing_fields=self._validation_fields(exc),
            )

        tools = self.runtime.bind_session_tools(session)
        result = await tools.quote_tools.select_quote(quote_input)
        if not result.success:
            return build_chat_message(
                session=session,
                reply=result.message,
                intent="SELECT_QUOTE",
                ui_action="SELECT_QUOTE",
                payload={"error": result.error.model_dump(mode="json") if result.error else {}},
            )
        data = result.data
        session.current_flow = "QUOTE_SELECTED"
        session.selected_quote_id = quote_input.quote_id
        session.selected_addons = quote_input.selected_addons
        return build_chat_message(
            session=session,
            reply="Your quote has been selected. You can proceed to payment whenever you are ready.",
            intent="SELECT_QUOTE",
            ui_action="SHOW_SELECTED_QUOTE",
            payload=(
                {
                    **(data.model_dump(mode="json") if data else {}),
                    "selected_addons": session.selected_addons,
                }
            ),
            suggested_replies=["Proceed to payment", "Check payment status"],
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
