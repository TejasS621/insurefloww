"""Request schemas accepted by the chatbot API endpoints."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ChatMessageRequest(BaseModel):
    """Incoming chat message payload from the customer-facing frontend."""

    model_config = ConfigDict(extra="forbid")

    session_id: str = Field(..., min_length=3, max_length=120)
    message: str = Field(default="", max_length=4000)
    intent_hint: str | None = Field(
        default=None,
        description="Optional frontend hint such as GENERATE_QUOTE or VERIFY_CUSTOMER_OTP.",
    )
    payload: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional structured payload collected from chatbot-driven UI forms.",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Optional channel metadata such as web, mobile, or widget context.",
    )
