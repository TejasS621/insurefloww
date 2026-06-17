"""HTTP routes for the InsureFlow chatbot service."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status

from chat_bot.handlers.conversation_handler import ConversationHandler
from chat_bot.runtime import ChatBotRuntime
from chat_bot.schemas.chat_request import ChatMessageRequest
from chat_bot.schemas.chat_response import ChatAPIResponse, ChatErrorItem
from chat_bot.app_state import get_conversation_handler, get_runtime

chat_router = APIRouter(prefix="/chat", tags=["Chat Bot"])


@chat_router.post("/message", response_model=ChatAPIResponse, status_code=status.HTTP_200_OK)
async def post_chat_message(
    request_data: ChatMessageRequest,
    runtime: ChatBotRuntime = Depends(get_runtime),
    conversation_handler: ConversationHandler = Depends(get_conversation_handler),
) -> ChatAPIResponse:
    """
    Handle one customer chatbot message and return the next UI action.

    The chatbot keeps guest-first session state, calls the real backend tool
    layer, and only asks for OTP when a protected customer action is needed.
    """

    session = runtime.session_store.get_or_create(request_data.session_id)
    try:
        result = await conversation_handler.handle(request_data, session)
        runtime.session_store.save(session)
        return ChatAPIResponse(
            success=True,
            message="Chat response generated successfully.",
            data=result,
        )
    except Exception as exc:  # pragma: no cover - defensive API guard
        return ChatAPIResponse(
            success=False,
            message="The chatbot could not process this request.",
            errors=[
                ChatErrorItem(
                    type="chatbot_runtime_error",
                    detail=str(exc),
                )
            ],
        )
