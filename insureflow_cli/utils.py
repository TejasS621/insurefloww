"""General helper functions used across CLI commands."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

import typer
from pydantic import BaseModel

from insureflow_cli.context import CLIContext
from insureflow_cli.errors import CLIError
from insureflow_mcp.schemas.common import extract_api_data


def run_async(coro: Any) -> Any:
    """Execute an async coroutine from a Typer command function."""

    return asyncio.run(coro)


def unwrap_data(payload: dict[str, Any]) -> Any:
    """Return the standard InsureFlow API `data` envelope payload."""

    return extract_api_data(payload)


def to_json_payload(model: BaseModel, **dump_kwargs: Any) -> dict[str, Any]:
    """Convert a Pydantic model into a guaranteed JSON-safe dictionary."""

    return json.loads(model.model_dump_json(**dump_kwargs))


def load_json_file(path: Path) -> dict[str, Any]:
    """Load a JSON object from disk or raise a clean CLI error."""

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise CLIError(f"Payload file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise CLIError(f"Invalid JSON in payload file: {path}") from exc
    if not isinstance(data, dict):
        raise CLIError("Payload file must contain a JSON object.")
    return data


def require_context(ctx: typer.Context) -> CLIContext:
    """Return the initialized CLI context from the Typer callback."""

    context = ctx.obj
    if not isinstance(context, CLIContext):
        raise RuntimeError("CLI context was not initialized.")
    return context
