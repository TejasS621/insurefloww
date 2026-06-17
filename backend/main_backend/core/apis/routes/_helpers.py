"""
Provide shared route helpers for main backend API modules.

Args:
    None: This module exposes reusable helpers for route-level error
    normalization and placeholder responses.

Returns:
    None: Helper functions are imported by route modules when needed.

Raises:
    HTTPException: Helpers raise normalized HTTP responses for unsupported
    operations and unexpected route failures.
"""

from __future__ import annotations

import inspect
from functools import wraps
from typing import Any, Awaitable, Callable, TypeVar

from fastapi import HTTPException, status

from backend.main_backend.commons.logger import get_logger
from backend.main_backend.core.services.service_exceptions import ServiceError

RouteFunc = TypeVar("RouteFunc", bound=Callable[..., Awaitable[Any]])


def raise_not_implemented(operation: str) -> None:
    """
    Raise a uniform not-implemented API error.

    Args:
        operation: Human-readable operation label used in the error payload.

    Returns:
        None: This helper always raises an exception instead of returning.

    Raises:
        HTTPException: Always raised with a 501 response payload.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "type": "not_implemented",
            "detail": f"{operation} has not been implemented yet.",
        },
    )


def route_guard(func: RouteFunc) -> RouteFunc:
    """
    Wrap a route so unexpected exceptions are logged and normalized.

    Args:
        func: Async FastAPI route handler to wrap.

    Returns:
        RouteFunc: Wrapped route function preserving the original signature.

    Raises:
        HTTPException: Re-raises HTTP exceptions and converts unexpected
        exceptions into a generic internal server error response.
        ServiceError: Re-raised unchanged so the global service handler can
        format the response consistently.
    """

    logger = get_logger(func.__module__)

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except HTTPException:
            raise
        except ServiceError:
            raise
        except Exception as exc:
            logger.exception("Unexpected error in %s", func.__name__)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal server error",
            ) from exc

    wrapper.__signature__ = inspect.signature(func)
    return wrapper  # type: ignore[return-value]
