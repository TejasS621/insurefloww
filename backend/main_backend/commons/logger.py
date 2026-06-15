"""
Provide centralized logger configuration for the main backend.

Args:
    None: This module defines helper functions for building named loggers with
    consistent console and file handlers for the main backend.

Returns:
    None: Helper functions return configured `logging.Logger` instances.

Raises:
    OSError: Propagates if the log directory or log file cannot be created.
"""

from __future__ import annotations

import logging
from pathlib import Path

LOG_DIRECTORY = Path("logs") / "main_backend"
LOG_FORMAT = (
    "[pid=%(process)s] [%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
)


def _build_formatter() -> logging.Formatter:
    """Return the shared formatter used by main backend log handlers."""
    return logging.Formatter(LOG_FORMAT)


def configure_logger(logger_name: str, *, level: int = logging.INFO) -> logging.Logger:
    """
    Configure and return a named logger for the main backend.

    Args:
        logger_name: Module-qualified logger name, usually `__name__`.
        level: Logging level applied to the configured logger and handlers.

    Returns:
        logging.Logger: Logger configured with console and file handlers.

    Raises:
        OSError: Propagates if the log directory or file cannot be created.
    """
    logger = logging.getLogger(logger_name)
    if getattr(logger, "_insureflow_configured", False):
        return logger

    LOG_DIRECTORY.mkdir(parents=True, exist_ok=True)
    formatter = _build_formatter()

    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(LOG_DIRECTORY / "app.log", mode="a", encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)

    logger.handlers.clear()
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    logger.setLevel(level)
    logger.propagate = False
    setattr(logger, "_insureflow_configured", True)
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Return a configured logger for the main backend.

    Args:
        name: Module-qualified logger name, usually `__name__`.

    Returns:
        logging.Logger: Configured logger instance for the module.

    Raises:
        OSError: Propagates if the log directory or file cannot be created.
    """
    return configure_logger(name)
