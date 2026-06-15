"""Health-check routes for the provider backend."""

from __future__ import annotations

from fastapi import APIRouter

from backend.provider_backend.core.apis.schemas.responses.common_response import APIResponse

health_router = APIRouter(tags=["Health"])


@health_router.get("/health", response_model=APIResponse[dict[str, str]])
async def health_check() -> APIResponse[dict[str, str]]:
    """Return a simple service liveness signal."""
    return APIResponse(message="Provider backend is healthy.", data={"status": "ok"})

