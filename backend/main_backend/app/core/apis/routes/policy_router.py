"""Policy routes for the main backend."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from odmantic import AIOEngine

from backend.main_backend.app.core.apis.routes._mappers import to_policy_summary_response
from backend.main_backend.app.core.apis.routes.dependencies import get_current_user_id
from backend.main_backend.app.core.apis.schemas.responses.common_response import APIResponse
from backend.main_backend.app.core.apis.schemas.responses.policy_response import PolicySummaryResponse
from backend.main_backend.app.core.database.database import get_database
from backend.main_backend.app.core.models.application_model import Application
from backend.main_backend.app.core.services.service_exceptions import (
    NotFoundServiceError,
)
from backend.provider_backend.app.core.models.policy_model import Policy

policy_router = APIRouter(prefix="/api/v1/policies", tags=["Policies"])


@policy_router.get("/me", response_model=APIResponse[list[PolicySummaryResponse]])
async def list_my_policies(
    engine: AIOEngine = Depends(get_database),
    user_id: str = Depends(get_current_user_id),
) -> APIResponse[list[PolicySummaryResponse]]:
    """List policies for a customer identified by the current request header."""
    applications = await engine.find(Application, Application.user_id == user_id)
    transaction_references = {
        application.transaction_reference
        for application in applications
        if application.transaction_reference
    }
    policies = await engine.find(Policy)
    matched_policies = [
        to_policy_summary_response(policy)
        for policy in policies
        if policy.main_transaction_reference in transaction_references
    ]
    return APIResponse(
        message="Policies fetched successfully.",
        data=matched_policies,
    )


@policy_router.get("/{policy_number}", response_model=APIResponse[PolicySummaryResponse])
async def get_policy(
    policy_number: str,
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[PolicySummaryResponse]:
    """Fetch a single policy summary by policy number."""
    policy = await engine.find_one(Policy, Policy.policy_number == policy_number)
    if policy is None:
        raise NotFoundServiceError("The requested policy could not be found.")
    return APIResponse(
        message="Policy fetched successfully.",
        data=to_policy_summary_response(policy),
    )
