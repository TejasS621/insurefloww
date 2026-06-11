"""Authentication routes for the main backend."""

from __future__ import annotations

import secrets
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, status
from odmantic import AIOEngine

from backend.main_backend.app.core.apis.schemas.requests.auth_request import (
    AdminLoginRequest,
    AdminVerifyRequest,
    OTPLoginRequest,
    OTPVerifyRequest,
)
from backend.main_backend.app.core.apis.schemas.responses.auth_response import (
    AuthTokenResponse,
    OTPDispatchResponse,
    TokenData,
)
from backend.main_backend.app.core.apis.schemas.responses.common_response import APIResponse
from backend.main_backend.app.core.database.database import get_database
from backend.main_backend.app.core.models.user_model import OTPPurpose, User, UserRole
from backend.main_backend.app.core.services.auth_service import auth_service
from backend.main_backend.app.core.services.service_exceptions import IntegrationServiceError

auth_router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@auth_router.post("/login/otp", response_model=APIResponse[OTPDispatchResponse], status_code=status.HTTP_202_ACCEPTED)
async def request_customer_otp(
    request_data: OTPLoginRequest,
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[OTPDispatchResponse]:
    """Start the customer OTP login flow and persist the OTP session."""
    dispatch = await auth_service.request_customer_otp(
        engine,
        request_data.mobile_number,
        purpose=OTPPurpose.LOGIN,
    )
    expires_in = int((dispatch.expires_at - datetime.now(timezone.utc)).total_seconds())
    return APIResponse(
        message="OTP generated successfully.",
        data=OTPDispatchResponse(
            mobile_number=dispatch.mobile_number,
            expires_in_seconds=max(expires_in, 0),
        ),
    )


@auth_router.post("/login/verify", response_model=APIResponse[AuthTokenResponse])
async def verify_customer_otp(
    request_data: OTPVerifyRequest,
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[AuthTokenResponse]:
    """Verify the customer OTP and issue a lightweight access token."""
    token_record = await auth_service.verify_customer_otp(
        engine,
        request_data.mobile_number,
        request_data.otp_code,
        purpose=OTPPurpose.LOGIN,
    )
    user = await engine.find_one(User, User.mobile_number == token_record.mobile_number)
    if user is None:
        user = User(
            full_name=f"Customer {token_record.mobile_number[-4:]}",
            mobile_number=token_record.mobile_number,
            user_role=UserRole.CUSTOMER,
            is_verified=True,
        )
    else:
        user.is_verified = True
        user.updated_at = datetime.now(timezone.utc)
    await engine.save(user)

    return APIResponse(
        message="Customer authentication successful.",
        data=AuthTokenResponse(
            user_id=str(user.id),
            token=TokenData(
                access_token=_generate_access_token(subject=token_record.mobile_number, role=UserRole.CUSTOMER.value),
                expires_in_seconds=3600,
                user_role=UserRole.CUSTOMER.value,
            ),
        ),
    )


@auth_router.post("/admin/login", response_model=APIResponse[OTPDispatchResponse], status_code=status.HTTP_202_ACCEPTED)
async def request_admin_login(
    _: AdminLoginRequest,
) -> APIResponse[OTPDispatchResponse]:
    """Start the admin login flow once admin persistence is available."""
    raise IntegrationServiceError(
        "Admin authentication is not available until admin user persistence is implemented."
    )


@auth_router.post("/admin/login/verify", response_model=APIResponse[AuthTokenResponse])
async def verify_admin_login(
    _: AdminVerifyRequest,
) -> APIResponse[AuthTokenResponse]:
    """Verify the admin login flow once admin persistence is available."""
    raise IntegrationServiceError(
        "Admin authentication verification is not available until admin user persistence is implemented."
    )


def _generate_access_token(*, subject: str, role: str) -> str:
    """Generate a lightweight opaque access token for local development flows."""
    return f"{role.lower()}_{subject}_{secrets.token_urlsafe(24)}"

