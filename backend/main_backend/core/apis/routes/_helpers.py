"""Shared route helpers for main backend placeholder endpoints."""

from __future__ import annotations

from fastapi import HTTPException, status


def raise_not_implemented(operation: str) -> None:
    """Raise a uniform not-implemented API error."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail={
            "type": "not_implemented",
            "detail": f"{operation} has not been implemented yet.",
        },
    )

