"""Shared response envelope schemas."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    """Single structured API error item."""

    model_config = ConfigDict(extra="forbid")

    type: str
    detail: str


class ErrorResponse(BaseModel):
    """Error envelope returned by failed endpoints."""

    model_config = ConfigDict(extra="forbid")

    success: bool = False
    message: str
    errors: list[ErrorDetail] = Field(default_factory=list)


class APIResponse(BaseModel, Generic[T]):
    """Standard success envelope returned by API endpoints."""

    model_config = ConfigDict(extra="forbid")

    success: bool = True
    message: str
    data: T | None = None

