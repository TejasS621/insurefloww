"""Policy routes for the main backend."""

from __future__ import annotations

from fastapi import APIRouter

from backend.main_backend.app.core.apis.routes._helpers import raise_not_implemented
from backend.main_backend.app.core.apis.schemas.responses.common_response import APIResponse
from backend.main_backend.app.core.apis.schemas.responses.policy_response import PolicySummaryResponse

policy_router = APIRouter(prefix="/api/v1/policies", tags=["Policies"])


@policy_router.get("/me", response_model=APIResponse[list[PolicySummaryResponse]])
async def list_my_policies() -> APIResponse[list[PolicySummaryResponse]]:
    """List policies owned by the authenticated customer."""
    raise_not_implemented("List customer policies")


@policy_router.get("/{policy_number}", response_model=APIResponse[PolicySummaryResponse])
async def get_policy(policy_number: str) -> APIResponse[PolicySummaryResponse]:
    """Fetch a single policy summary by policy number."""
    raise_not_implemented("Policy fetch")
