"""Policy routes for the provider backend."""

from __future__ import annotations

from fastapi import APIRouter

from backend.provider_backend.app.core.apis.routes._helpers import raise_not_implemented
from backend.provider_backend.app.core.apis.schemas.responses.common_response import APIResponse
from backend.provider_backend.app.core.apis.schemas.responses.policy_response import (
    ProviderPolicyResponse,
)

policy_router = APIRouter(prefix="/api/v1/provider/policies", tags=["Provider Policies"])


@policy_router.get("/{policy_number}", response_model=APIResponse[ProviderPolicyResponse])
async def get_policy(policy_number: str) -> APIResponse[ProviderPolicyResponse]:
    """Fetch a provider-issued policy by policy number."""
    raise_not_implemented("Provider policy fetch")
