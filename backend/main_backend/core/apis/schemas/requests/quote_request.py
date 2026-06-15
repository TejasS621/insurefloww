"""Quote interaction request schemas."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class QuoteSelectRequest(BaseModel):
    """Select a quote and optional add-ons."""

    model_config = ConfigDict(extra="forbid")

    selected_addons: list[str] = Field(default_factory=list)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=128)

