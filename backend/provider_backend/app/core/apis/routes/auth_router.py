"""Authentication routes for the provider backend."""

from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends
from odmantic import AIOEngine

from backend.provider_backend.app.core.apis.schemas.requests.auth_request import ProviderAdminLoginRequest
from backend.provider_backend.app.core.apis.schemas.responses.auth_response import ProviderAuthResponse
from backend.provider_backend.app.core.apis.schemas.responses.common_response import APIResponse
from backend.provider_backend.app.core.database.database import get_database
from backend.provider_backend.app.core.services.auth_service import provider_auth_service

auth_router = APIRouter(prefix="/api/v1/provider/auth", tags=["Provider Auth"])


@auth_router.post("/login", response_model=APIResponse[ProviderAuthResponse])
async def provider_admin_login(
    request_data: ProviderAdminLoginRequest,
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[ProviderAuthResponse]:
    """Authenticate a provider admin user."""
    await provider_auth_service.authenticate_provider_admin(
        engine,
        email=request_data.email,
        password=request_data.password,
    )
    return APIResponse(
        message="Provider admin authenticated successfully.",
        data=ProviderAuthResponse(
            access_token=f"provider_admin_{secrets.token_urlsafe(24)}",
            expires_in_seconds=3600,
        ),
    )

