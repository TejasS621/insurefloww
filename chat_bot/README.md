# InsureFlow Chat Bot

This package adds a backend-aligned chatbot service for InsureFlow customer workflows.

It is designed to:

- keep the customer journey guest-first
- reuse the real `main_backend` APIs through the existing `insureflow_mcp` tool layer
- avoid duplicating quote, payment, policy, or ticket business logic
- request OTP only when the customer asks for protected actions

## Supported Chat Workflows

- Request customer OTP
- Verify customer OTP
- Generate quotes from a complete application payload
- Select a quote
- Initiate payment
- Check payment status
- Get policy details
- Download policy documents
- Create support tickets

## Guest-First Authentication Model

The chatbot follows the same customer flow as the frontend:

- guest users can generate quotes, select plans, and move toward payment
- OTP login is only requested when the user needs protected actions such as:
  - policy download
  - secure policy lookup
  - account-linked support ticket creation

## Folder Overview

- `chat_bot/config.py`
  Reads environment variables for the chatbot service.
- `chat_bot/session.py`
  Stores guest and authenticated conversation state in memory.
- `chat_bot/runtime.py`
  Builds the MCP-backed backend tool runtime used by handlers.
- `chat_bot/services/intent_service.py`
  Detects chatbot intents from frontend hints, payloads, and plain text.
- `chat_bot/handlers/`
  Contains domain handlers for auth, quotes, payment, policy, tickets, and top-level routing.
- `chat_bot/routers/chat_router.py`
  Exposes the `POST /chat/message` API endpoint.
- `chat_bot/app.py`
  Creates the FastAPI application.
- `chat_bot/__main__.py`
  Allows `python -m chat_bot` to start the service.

## API Contract

### `POST /chat/message`

Request:

```json
{
  "session_id": "guest-123",
  "message": "I want a health insurance quote",
  "intent_hint": "GENERATE_QUOTE",
  "payload": {
    "insurance_type": "HEALTH",
    "personal_details": {},
    "coverage_details": {},
    "health_details": {}
  }
}
```

Response:

```json
{
  "success": true,
  "message": "Chat response generated successfully.",
  "data": {
    "reply": "I found quote options for you. Please review and select the plan you want.",
    "intent": "GENERATE_QUOTE",
    "ui_action": "SHOW_QUOTES",
    "payload": {},
    "missing_fields": [],
    "suggested_replies": [],
    "session_state": {
      "session_id": "guest-123",
      "authenticated": false,
      "current_flow": "QUOTE_RESULTS"
    }
  },
  "errors": []
}
```

## Install

```powershell
pip install -r chat_bot/requirements.txt
```

## Local Run

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\start-chat-bot.ps1
```

The chatbot runs by default on `http://127.0.0.1:8090`.
