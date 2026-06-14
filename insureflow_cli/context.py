"""Shared CLI context object used by Typer command groups."""

from __future__ import annotations

from dataclasses import dataclass

from rich.console import Console

from insureflow_cli.client import CLIBackendClient
from insureflow_cli.config import CLISettings
from insureflow_cli.session import SessionStore


@dataclass(slots=True)
class CLIContext:
    """Hold settings, client, console, and session state for commands."""

    settings: CLISettings
    client: CLIBackendClient
    session: SessionStore
    console: Console
