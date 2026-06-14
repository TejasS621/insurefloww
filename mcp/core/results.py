"""Shared tool result envelopes returned by MCP tools."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict

from mcp.core.errors import MCPToolError

ResultT = TypeVar("ResultT")


class ToolErrorDetails(BaseModel):
    """Structured error payload returned to MCP clients."""

    model_config = ConfigDict(extra="forbid")

    code: str
    detail: str
    status_code: int | None = None
    retryable: bool = False


class ToolResult(BaseModel, Generic[ResultT]):
    """Uniform success or error wrapper returned by each MCP tool."""

    model_config = ConfigDict(extra="forbid")

    success: bool
    message: str
    data: ResultT | None = None
    error: ToolErrorDetails | None = None


def success_result(message: str, data: ResultT) -> ToolResult[ResultT]:
    """Build a successful tool result payload."""

    return ToolResult(success=True, message=message, data=data)


def error_result(exc: MCPToolError) -> ToolResult[None]:
    """Build a structured tool error payload."""

    return ToolResult(
        success=False,
        message=exc.message,
        error=ToolErrorDetails(
            code=exc.code,
            detail=exc.message,
            status_code=exc.status_code,
            retryable=exc.retryable,
        ),
    )

