"""Application routes for the main backend."""

from __future__ import annotations

from fastapi import APIRouter, status

from backend.main_backend.app.core.apis.routes._helpers import raise_not_implemented
from backend.main_backend.app.core.apis.schemas.requests.application_request import ApplicationCreateRequest
from backend.main_backend.app.core.apis.schemas.responses.application_response import ApplicationSummaryResponse
from backend.main_backend.app.core.apis.schemas.responses.common_response import APIResponse

application_router = APIRouter(prefix="/api/v1/applications", tags=["Applications"])


@application_router.post("", response_model=APIResponse[ApplicationSummaryResponse], status_code=status.HTTP_201_CREATED)
async def create_application(_: ApplicationCreateRequest) -> APIResponse[ApplicationSummaryResponse]:
    """Create or resume a customer insurance application."""
    raise_not_implemented("Application creation")

