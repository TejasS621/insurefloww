"""Unit and API integration tests for the InsureFlow chatbot service."""

from __future__ import annotations

from fastapi.testclient import TestClient

from chat_bot.schemas.session_state import ChatSessionState
from chat_bot.schemas.chat_request import ChatMessageRequest
from chat_bot.services.intent_service import IntentService


def test_health_endpoint(client: TestClient) -> None:
    """Verify that the health check endpoint returns 200 and 'ok'."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_chatbot_greeting(client: TestClient) -> None:
    """Verify that sending a greeting message triggers a GREETING response."""
    payload = {
        "session_id": "test-session-123",
        "message": "hello",
    }
    response = client.post("/chat/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["intent"] == "GREETING"
    assert "Hello, welcome to InsureFlow. How can I help you with your insurance needs today?" in data["data"]["reply"]


def test_chatbot_unknown(client: TestClient) -> None:
    """Verify that sending an unknown query returns the fallback prompt."""
    payload = {
        "session_id": "test-session-123",
        "message": "some completely random message that cannot be parsed",
    }
    response = client.post("/chat/message", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["intent"] == "UNKNOWN"
    assert "I am here to help with your insurance" in data["data"]["reply"]


def test_intent_detection() -> None:
    """Verify that IntentService correctly detects intents from message strings and payloads."""
    service = IntentService()
    session = ChatSessionState(session_id="test-session")

    # Greeting intents
    req_greet = ChatMessageRequest(session_id="test-session", message="hi")
    assert service.detect_intent(req_greet, session) == "GREETING"

    # Quote intents
    req_quote = ChatMessageRequest(session_id="test-session", message="I want a health quote")
    assert service.detect_intent(req_quote, session) == "GENERATE_QUOTE"

    # Support ticket intents
    req_support = ChatMessageRequest(session_id="test-session", message="need support help")
    assert service.detect_intent(req_support, session) == "CREATE_TICKET"

    # OTP authentication intents
    req_otp = ChatMessageRequest(session_id="test-session", message="send me otp to login")
    assert service.detect_intent(req_otp, session) == "REQUEST_CUSTOMER_OTP"
