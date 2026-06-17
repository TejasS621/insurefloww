"""Authentication handlers for guest-to-customer chatbot transitions."""

from __future__ import annotations

from chat_bot.handlers.base import build_chat_message
from chat_bot.schemas.chat_request import ChatMessageRequest
from chat_bot.schemas.chat_response import ChatMessageData
from chat_bot.schemas.session_state import ChatSessionState
from chat_bot.runtime import ChatBotRuntime
from insureflow_mcp.schemas.auth import RequestCustomerOTPInput, VerifyCustomerOTPInput


class AuthHandler:
    """Handle OTP request and verification flows for the chatbot."""

    def __init__(self, runtime: ChatBotRuntime) -> None:
        self.runtime = runtime

    async def request_customer_otp(
        self,
        *,
        request: ChatMessageRequest,
        session: ChatSessionState,
    ) -> ChatMessageData:
        """Dispatch a customer OTP or ask for the mobile number if missing."""

        mobile_number = str(request.payload.get("mobile_number") or session.mobile_number or "").strip()
        if not mobile_number:
            session.current_flow = "AUTH"
            return build_chat_message(
                session=session,
                reply="Please share your mobile number so I can send an OTP.",
                intent="REQUEST_CUSTOMER_OTP",
                ui_action="REQUEST_OTP",
                missing_fields=["mobile_number"],
                suggested_replies=["Send OTP", "Use another number"],
            )

        tools = self.runtime.bind_session_tools(session)
        result = await tools.auth_tools.request_customer_otp(
            RequestCustomerOTPInput(mobile_number=mobile_number)
        )
        if not result.success:
            return build_chat_message(
                session=session,
                reply=result.message,
                intent="REQUEST_CUSTOMER_OTP",
                ui_action="REQUEST_OTP",
                payload={"error": result.error.model_dump(mode="json") if result.error else {}},
            )
        session.mobile_number = mobile_number
        session.current_flow = "AUTH"
        return build_chat_message(
            session=session,
            reply=(
                "I have sent an OTP to your mobile number. "
                "Please share the code to continue."
            ),
            intent="REQUEST_CUSTOMER_OTP",
            ui_action="VERIFY_OTP",
            payload=result.data.model_dump(mode="json") if result.data else {},
            suggested_replies=["Verify OTP"],
        )

    async def verify_customer_otp(
        self,
        *,
        request: ChatMessageRequest,
        session: ChatSessionState,
    ) -> ChatMessageData:
        """Verify the supplied OTP and attach the authenticated session."""

        mobile_number = str(request.payload.get("mobile_number") or session.mobile_number or "").strip()
        otp_code = str(request.payload.get("otp_code") or "").strip()
        missing_fields = []
        if not mobile_number:
            missing_fields.append("mobile_number")
        if not otp_code:
            missing_fields.append("otp_code")
        if missing_fields:
            return build_chat_message(
                session=session,
                reply="Please provide the missing OTP details so I can verify your account.",
                intent="VERIFY_CUSTOMER_OTP",
                ui_action="VERIFY_OTP",
                missing_fields=missing_fields,
            )

        tools = self.runtime.bind_session_tools(session)
        result = await tools.auth_tools.verify_customer_otp(
            VerifyCustomerOTPInput(
                mobile_number=mobile_number,
                otp_code=otp_code,
            )
        )
        if not result.success:
            session.current_flow = "AUTH"
            return build_chat_message(
                session=session,
                reply=result.message,
                intent="VERIFY_CUSTOMER_OTP",
                ui_action="VERIFY_OTP",
                payload={"error": result.error.model_dump(mode="json") if result.error else {}},
                suggested_replies=["Request a new OTP"],
            )
        session.mobile_number = mobile_number
        session.authenticated = True
        session.current_flow = "AUTHENTICATED"
        return build_chat_message(
            session=session,
            reply="Your mobile number is verified. You can now access protected policy and support actions.",
            intent="VERIFY_CUSTOMER_OTP",
            ui_action="AUTHENTICATED",
            payload=result.data.model_dump(mode="json") if result.data else {},
            suggested_replies=["Download my policy", "Create support ticket"],
        )
