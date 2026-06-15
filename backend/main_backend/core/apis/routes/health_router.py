"""
Handle health-check routes for the main backend.

Args:
    None: This module defines lightweight liveness endpoints used by local
    development, monitoring, and deployment checks.

Returns:
    None: Route handlers return structured health responses for the backend.

Raises:
    HTTPException: Unexpected failures are normalized through the shared
    route guard before being returned to the caller.
"""

from __future__ import annotations

from fastapi import APIRouter

from backend.main_backend.core.apis.routes._helpers import route_guard
from backend.main_backend.core.apis.schemas.responses.common_response import APIResponse

health_router = APIRouter(prefix="/api/v1", tags=["Health"])


@health_router.get("/health", response_model=APIResponse[dict[str, str]])
@route_guard
async def health_check() -> APIResponse[dict[str, str]]:
    """
    Return a simple liveness response for the main backend.

    Args:
        None: This endpoint does not accept request payload input.

    Returns:
        APIResponse[dict[str, str]]: Structured health payload containing
        the backend status marker.

    Raises:
        HTTPException: Unexpected failures are wrapped as internal server
        errors through the route guard.
    """
    return APIResponse(message="Main backend is healthy.", data={"status": "ok"})
