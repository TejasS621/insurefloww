"""Authentication routes for the main backend."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, status

logger = logging.getLogger(__name__)
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
from backend.main_backend.app.core.models.application_model import Application
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
    # DEV: print OTP to console so developers can copy it without an SMS gateway
    logger.warning(
        "[DEV] OTP for %s: %s (expires in %ds)",
        dispatch.mobile_number,
        dispatch.otp_code,
        max(expires_in, 0),
    )
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

    linked_applications = await _link_customer_records_by_mobile(
        engine,
        user=user,
        mobile_number=token_record.mobile_number,
    )
    if linked_applications and user.full_name.startswith("Customer "):
        latest_application = max(linked_applications, key=lambda application: application.updated_at)
        first_name = latest_application.personal_details.first_name.strip()
        last_name = latest_application.personal_details.last_name.strip()
        full_name = " ".join(part for part in [first_name, last_name] if part)
        if full_name:
            user.full_name = full_name

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


async def _link_customer_records_by_mobile(
    engine: AIOEngine,
    *,
    user: User,
    mobile_number: str,
) -> list[Application]:
    """Attach guest applications for the verified mobile number to the logged-in user."""
    applications = await engine.find(Application)
    matched_applications: list[Application] = []

    for application in applications:
        if application.personal_details.mobile_number != mobile_number:
            continue
        matched_applications.append(application)
        if application.user_id == str(user.id):
            continue
        if application.user_id is not None and application.user_id != str(user.id):
            continue
        application.user_id = str(user.id)
        application.updated_at = datetime.now(timezone.utc)
        await engine.save(application)

    return matched_applications


@auth_router.post("/admin/login", response_model=APIResponse[AuthTokenResponse])
async def request_admin_login(
    request_data: AdminLoginRequest,
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[AuthTokenResponse]:
    """Validate admin credentials and return a signed JWT access token."""
    admin_identity = await auth_service.authenticate_admin_credentials(
        email=str(request_data.email),
        password=request_data.password,
    )
    dispatch = await auth_service.request_admin_otp(
        engine,
        email=admin_identity,
    )
    logger.warning(
        "[DEV] Admin OTP for %s: %s",
        admin_identity,
        dispatch.otp_code,
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
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[AuthTokenResponse]:
    """Verify the admin compatibility OTP flow and return a signed JWT token."""
    admin_identity = await auth_service.verify_admin_otp(
        engine,
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

