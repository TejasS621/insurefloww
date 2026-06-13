"""Authentication routes for the main backend."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, status
from odmantic import AIOEngine

from backend.main_backend.app.commons.config import settings
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
from backend.shared.auth.jwt_utils import create_access_token

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
    """Verify the customer OTP and return a signed JWT access token."""
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
    access_token, expires_at = create_access_token(
        subject=str(user.id),
        role="customer",
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes),
    )
    expires_in = int((expires_at - datetime.now(timezone.utc)).total_seconds())

    return APIResponse(
        message="Customer authentication successful.",
        data=AuthTokenResponse(
            user_id=str(user.id),
            token=TokenData(
                access_token=access_token,
                expires_in_seconds=max(expires_in, 0),
                user_role="customer",
            ),
        ),
    )


@auth_router.post("/admin/login", response_model=APIResponse[AuthTokenResponse])
async def request_admin_login(
    request_data: AdminLoginRequest,
) -> APIResponse[AuthTokenResponse]:
    """Validate admin credentials and return a signed JWT access token."""
    admin_identity = await auth_service.authenticate_admin_credentials(
        email=str(request_data.email),
        password=request_data.password,
    )
    access_token, expires_at = create_access_token(
        subject=admin_identity,
        role="admin",
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes),
    )
    expires_in = int((expires_at - datetime.now(timezone.utc)).total_seconds())
    return APIResponse(
        message="Admin authentication successful.",
        data=AuthTokenResponse(
            user_id=admin_identity,
            token=TokenData(
                access_token=access_token,
                expires_in_seconds=max(expires_in, 0),
                user_role="admin",
            ),
        ),
    )


@auth_router.post("/admin/login/verify", response_model=APIResponse[AuthTokenResponse])
async def verify_admin_login(
    request_data: AdminVerifyRequest,
) -> APIResponse[AuthTokenResponse]:
    """Verify the admin compatibility OTP flow and return a signed JWT token."""
    admin_identity = await auth_service.verify_admin_otp(
        email=str(request_data.email),
        otp_code=request_data.otp_code,
    )
    access_token, expires_at = create_access_token(
        subject=admin_identity,
        role="admin",
        secret_key=settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
        expires_delta=timedelta(minutes=settings.jwt_access_token_expire_minutes),
    )
    expires_in = int((expires_at - datetime.now(timezone.utc)).total_seconds())
    return APIResponse(
        message="Admin verification successful.",
        data=AuthTokenResponse(
            user_id=admin_identity,
            token=TokenData(
                access_token=access_token,
                expires_in_seconds=max(expires_in, 0),
                user_role="admin",
            ),
        ),
    )

