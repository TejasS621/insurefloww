"""Structured logging helpers for the InsureFlow MCP server."""

from __future__ import annotations

import logging


def configure_logging(level: str) -> None:
    """Configure process-wide logging with a structured single-line format."""

    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format=(
            "%(asctime)s "
            "level=%(levelname)s "
            "logger=%(name)s "
            "message=%(message)s"
        ),
    )

