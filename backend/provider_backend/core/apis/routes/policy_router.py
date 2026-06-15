"""Policy routes for the provider backend."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from odmantic import AIOEngine

from backend.provider_backend.core.apis.routes._helpers import route_guard
from backend.provider_backend.core.apis.routes._mappers import to_provider_policy_response
from backend.provider_backend.core.apis.routes.dependencies import get_current_provider_admin_principal
from backend.provider_backend.core.apis.schemas.responses.common_response import APIResponse
from backend.provider_backend.core.apis.schemas.responses.policy_response import (
    ProviderPolicyResponse,
)
from backend.provider_backend.core.database.database import get_database
from backend.provider_backend.core.services.policy_service import provider_policy_service
from backend.provider_backend.core.services.service_exceptions import NotFoundServiceError

policy_router = APIRouter(prefix="/api/v1/policies", tags=["Provider Policies"])


@policy_router.get("/{policy_number}", response_model=APIResponse[ProviderPolicyResponse])
@route_guard
async def get_policy(
    policy_number: str,
    engine: AIOEngine = Depends(get_database),
    _: object = Depends(get_current_provider_admin_principal),
) -> APIResponse[ProviderPolicyResponse]:
    """Fetch a provider-issued policy by policy number."""
    policy = await provider_policy_service.get_policy_by_number(
        engine,
        policy_number=policy_number,
    )
    if policy is None:
        raise NotFoundServiceError("The requested provider policy could not be found.")
    return APIResponse(
        message="Provider policy fetched successfully.",
        data=to_provider_policy_response(policy),
    )


@policy_router.get("/{policy_number}/document", response_class=FileResponse)
@route_guard
async def view_policy_document(
    policy_number: str,
    engine: AIOEngine = Depends(get_database),
    _: object = Depends(get_current_provider_admin_principal),
) -> FileResponse:
    """Render an issued provider policy PDF inline for browser viewing."""
    policy = await provider_policy_service.get_policy_by_number(
        engine,
        policy_number=policy_number,
    )
    if policy is None:
        raise NotFoundServiceError("The requested provider policy could not be found.")
    if not policy.policy_pdf_path:
        raise NotFoundServiceError("The requested policy document is not available.")

    document_path = Path(policy.policy_pdf_path)
    if not document_path.exists():
        raise NotFoundServiceError("The requested policy document file is missing.")

    return FileResponse(
        path=document_path,
        media_type="application/pdf",
        filename=f"{policy.policy_number}.pdf",
        content_disposition_type="inline",
    )


@policy_router.get("/{policy_number}/download", response_class=FileResponse)
@route_guard
async def download_policy_document(
    policy_number: str,
    engine: AIOEngine = Depends(get_database),
    _: object = Depends(get_current_provider_admin_principal),
) -> FileResponse:
    """Download an issued provider policy PDF as an attachment."""
    policy = await provider_policy_service.get_policy_by_number(
        engine,
        policy_number=policy_number,
    )
    if policy is None:
        raise NotFoundServiceError("The requested provider policy could not be found.")
    if not policy.policy_pdf_path:
        raise NotFoundServiceError("The requested policy document is not available.")

    document_path = Path(policy.policy_pdf_path)
    if not document_path.exists():
        raise NotFoundServiceError("The requested policy document file is missing.")

    return FileResponse(
        path=document_path,
        media_type="application/pdf",
        filename=f"{policy.policy_number}.pdf",
    )
