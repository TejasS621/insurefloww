"""Rule-based intent detection for the initial chatbot release."""

from __future__ import annotations

from chat_bot.schemas.chat_request import ChatMessageRequest
from chat_bot.schemas.session_state import ChatSessionState


class IntentService:
    """Detect chatbot intents from frontend hints, payloads, and plain text."""

    def detect_intent(self, request: ChatMessageRequest, session: ChatSessionState) -> str:
        """Return the best matching intent for the current message."""

        if request.intent_hint:
            return request.intent_hint.strip().upper()

        payload = request.payload
        message = request.message.strip().lower()

        if payload.get("otp_code"):
            return "VERIFY_CUSTOMER_OTP"
        if payload.get("quote_id"):
            return "SELECT_QUOTE"
        if payload.get("policy_number") and "download" in message:
            return "DOWNLOAD_POLICY"
        if payload.get("policy_number"):
            return "GET_POLICY"
        if payload.get("transaction_reference") and "status" in message:
            return "GET_PAYMENT_STATUS"
        if payload.get("transaction_reference") or "payment" in message or "pay" in message:
            if "status" in message:
                return "GET_PAYMENT_STATUS"
            return "INITIATE_PAYMENT"
        if payload.get("mobile_number") and ("otp" in message or "login" in message or "verify" in message):
            if payload.get("otp_code"):
                return "VERIFY_CUSTOMER_OTP"
            return "REQUEST_CUSTOMER_OTP"
        if any(word in message for word in ["otp", "login", "sign in", "verify mobile"]):
            return "REQUEST_CUSTOMER_OTP"
        if any(word in message for word in ["ticket", "support", "issue", "help with policy"]):
            return "CREATE_TICKET"
        if payload.get("insurance_type") or payload.get("personal_details") or payload.get("coverage_details"):
            return "GENERATE_QUOTE"
        if any(
            word in message
            for word in ["quote", "insurance", "health", "life", "travel", "vehicle", "home plan"]
        ):
            return "GENERATE_QUOTE"
        if any(word in message for word in ["policy", "download policy"]):
            return "GET_POLICY"
        if any(word in message for word in ["hi", "hello", "hey", "start"]):
            return "GREETING"
        if session.transaction_reference and "status" in message:
            return "GET_PAYMENT_STATUS"
        return "UNKNOWN"
