"""
Handle health-check routes for the provider backend.

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

from backend.provider_backend.commons.logger import get_logger
from backend.provider_backend.core.apis.routes._helpers import route_guard
from backend.provider_backend.core.apis.schemas.responses.common_response import (
    APIResponse,
)
from backend.provider_backend.core.services.service_exceptions import ServiceError

health_router = APIRouter(prefix="/api/v1", tags=["Health"])
logger = get_logger(__name__)


@health_router.get("/health", response_model=APIResponse[dict[str, str]])
@route_guard
async def health_check() -> APIResponse[dict[str, str]]:
    """
    Return a simple liveness response for the provider backend.

    Args:
        None: This endpoint does not accept request payload input.

    Returns:
        APIResponse[dict[str, str]]: Structured health payload containing
        the backend status marker.

    Raises:
        HTTPException: Unexpected failures are wrapped as internal server
        errors through the route guard.
    """
    try:
        return APIResponse(message="Provider backend is healthy.", data={"status": "ok"})
    except ServiceError:
        raise
    except Exception:
        logger.exception("Failed to build provider backend health response.")
        raise
