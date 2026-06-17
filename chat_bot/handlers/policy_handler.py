"""Policy retrieval and download handlers for authenticated chatbot actions."""

from __future__ import annotations

from pydantic import ValidationError

from chat_bot.handlers.base import build_chat_message
from chat_bot.prompts import CHATBOT_AUTH_REQUIRED_MESSAGE
from chat_bot.schemas.chat_request import ChatMessageRequest
from chat_bot.schemas.chat_response import ChatMessageData
from chat_bot.schemas.session_state import ChatSessionState
from chat_bot.runtime import ChatBotRuntime
from insureflow_mcp.schemas.policies import DownloadPolicyInput, GetPolicyInput


class PolicyHandler:
    """Handle secure policy actions that require customer authentication."""

    def __init__(self, runtime: ChatBotRuntime) -> None:
        self.runtime = runtime

    async def get_policy(
        self,
        *,
        request: ChatMessageRequest,
        session: ChatSessionState,
    ) -> ChatMessageData:
        """Fetch policy details after confirming the customer session is authenticated."""

        if not session.authenticated:
            return build_chat_message(
                session=session,
                reply=CHATBOT_AUTH_REQUIRED_MESSAGE,
                intent="GET_POLICY",
                ui_action="REQUEST_OTP",
                suggested_replies=["Send OTP", "Use my mobile number"],
            )

        payload = dict(request.payload)
        payload.setdefault("policy_number", session.policy_number)
        payload.setdefault("customer_access_token", session.customer_access_token)
        try:
            policy_input = GetPolicyInput.model_validate(payload)
        except ValidationError as exc:
            return build_chat_message(
                session=session,
                reply="Please share the policy number you want me to fetch.",
                intent="GET_POLICY",
                ui_action="SHOW_POLICY",
                missing_fields=self._validation_fields(exc),
            )

        tools = self.runtime.bind_session_tools(session)
        result = await tools.policy_tools.get_policy(policy_input)
        if not result.success:
            return build_chat_message(
                session=session,
                reply=result.message,
                intent="GET_POLICY",
                ui_action="SHOW_POLICY",
                payload={"error": result.error.model_dump(mode="json") if result.error else {}},
            )
        data = result.data
        if data is not None:
            session.policy_number = data.policy_number
        session.current_flow = "POLICY"
        return build_chat_message(
            session=session,
            reply="Here are your policy details.",
            intent="GET_POLICY",
            ui_action="SHOW_POLICY",
            payload=data.model_dump(mode="json") if data else {},
            suggested_replies=["Download policy"],
        )

    async def download_policy(
        self,
        *,
        request: ChatMessageRequest,
        session: ChatSessionState,
    ) -> ChatMessageData:
        """Download a policy PDF after confirming the customer session is authenticated."""

        if not session.authenticated:
            return build_chat_message(
                session=session,
                reply=CHATBOT_AUTH_REQUIRED_MESSAGE,
                intent="DOWNLOAD_POLICY",
                ui_action="REQUEST_OTP",
                suggested_replies=["Send OTP"],
            )

        payload = dict(request.payload)
        payload.setdefault("policy_number", session.policy_number)
        payload.setdefault("customer_access_token", session.customer_access_token)
        try:
            download_input = DownloadPolicyInput.model_validate(payload)
        except ValidationError as exc:
            return build_chat_message(
                session=session,
                reply="Please tell me which policy number you want to download.",
                intent="DOWNLOAD_POLICY",
                ui_action="SHOW_POLICY_DOWNLOAD",
                missing_fields=self._validation_fields(exc),
            )

        tools = self.runtime.bind_session_tools(session)
        result = await tools.policy_tools.download_policy(download_input)
        if not result.success:
            return build_chat_message(
                session=session,
                reply=result.message,
                intent="DOWNLOAD_POLICY",
                ui_action="SHOW_POLICY_DOWNLOAD",
                payload={"error": result.error.model_dump(mode="json") if result.error else {}},
            )
        session.current_flow = "POLICY_DOWNLOAD"
        return build_chat_message(
            session=session,
            reply="Your policy document is ready for download.",
            intent="DOWNLOAD_POLICY",
            ui_action="SHOW_POLICY_DOWNLOAD",
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
