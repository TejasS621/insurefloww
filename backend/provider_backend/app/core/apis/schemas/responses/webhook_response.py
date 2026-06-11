"""Webhook acknowledgement response schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class WebhookAcknowledgementResponse(BaseModel):
    """Acknowledgement payload returned to webhook senders."""

    model_config = ConfigDict(extra="forbid")

    event_type: str
    processing_status: str
