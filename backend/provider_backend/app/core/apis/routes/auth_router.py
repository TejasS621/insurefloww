"""Authentication routes for the provider backend."""

from __future__ import annotations

from fastapi import APIRouter

from backend.provider_backend.app.core.apis.routes._helpers import raise_not_implemented
from backend.provider_backend.app.core.apis.schemas.requests.auth_request import ProviderAdminLoginRequest
from backend.provider_backend.app.core.apis.schemas.responses.auth_response import ProviderAuthResponse
from backend.provider_backend.app.core.apis.schemas.responses.common_response import APIResponse

auth_router = APIRouter(prefix="/api/v1/provider/auth", tags=["Provider Auth"])


@auth_router.post("/login", response_model=APIResponse[ProviderAuthResponse])
async def provider_admin_login(
    _: ProviderAdminLoginRequest,
) -> APIResponse[ProviderAuthResponse]:
    """Authenticate a provider admin user."""
    raise_not_implemented("Provider admin login")

