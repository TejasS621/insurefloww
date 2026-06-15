"""Authentication routes for the provider backend."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from odmantic import AIOEngine

from backend.provider_backend.commons.config import settings
from backend.provider_backend.core.apis.schemas.requests.auth_request import ProviderAdminLoginRequest
from backend.provider_backend.core.apis.schemas.responses.auth_response import ProviderAuthResponse
from backend.provider_backend.core.apis.schemas.responses.common_response import APIResponse
from backend.provider_backend.core.database.database import get_database
from backend.provider_backend.core.services.auth_service import provider_auth_service
from backend.shared.auth.jwt_utils import create_access_token

auth_router = APIRouter(prefix="/api/v1/provider/auth", tags=["Provider Auth"])


@auth_router.post("/login", response_model=APIResponse[ProviderAuthResponse])
async def provider_admin_login(
    request_data: ProviderAdminLoginRequest,
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[ProviderAuthResponse]:
    """Authenticate a provider admin and return a signed JWT access token."""
    provider_admin_identity = await provider_auth_service.authenticate_provider_admin(
        engine,
        email=request_data.email,
        password=request_data.password,
    )
    access_token, expires_at = create_access_token(
        subject=provider_admin_identity,
        role="provider_admin",
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes),
    )
    expires_in = int((expires_at - datetime.now(timezone.utc)).total_seconds())
    return APIResponse(
        message="Provider admin authenticated successfully.",
        data=ProviderAuthResponse(
            access_token=access_token,
            expires_in_seconds=max(expires_in, 0),
        ),
    )

