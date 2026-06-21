"""
Handle authentication routes for the main backend.

Args:
    None: This module defines customer and admin authentication handlers
    exposed under the versioned auth router.

Returns:
    None: Route handlers return structured API responses containing OTP
    dispatch metadata or signed JWT payloads.

Raises:
    HTTPException: Unexpected failures are normalized through the shared
    route guard before being returned to the caller.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Body, Depends, status
from odmantic import AIOEngine

from backend.main_backend.commons.auth import create_access_token
from backend.main_backend.commons.config import settings
from backend.main_backend.commons.logger import get_logger
from backend.main_backend.core.apis.schemas.requests.auth_request import (
    AdminLoginRequest,
    AdminVerifyRequest,
    OTPLoginRequest,
    OTPVerifyRequest,
)
from backend.main_backend.core.apis.schemas.responses.auth_response import (
    AuthTokenResponse,
    OTPDispatchResponse,
    TokenData,
)
from backend.main_backend.core.apis.schemas.responses.common_response import APIResponse
from backend.main_backend.core.database.database import get_database
from backend.main_backend.core.models.application_model import Application
from backend.main_backend.core.models.user_model import OTPPurpose, User, UserRole
from backend.main_backend.core.services.auth_service import auth_service
from backend.main_backend.core.services.service_exceptions import ServiceError

logger = get_logger(__name__)

auth_router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@auth_router.post(
    "/login/otp",
    response_model=APIResponse[OTPDispatchResponse],
    status_code=status.HTTP_202_ACCEPTED,
)
async def request_customer_otp(
    request_data: OTPLoginRequest = Body(...),
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[OTPDispatchResponse]:
    """
    Start the customer OTP login flow and persist a new OTP session.

    Args:
        request_data: Validated login payload containing the mobile number.
        engine: Active ODMantic database engine dependency.

    Returns:
        APIResponse[OTPDispatchResponse]: OTP dispatch metadata without
        exposing the OTP in the API response.

    Raises:
        HTTPException: Re-raises controller validation errors or wraps
        unexpected exceptions as HTTP 500 responses through the route guard.
    """
    try:
        dispatch = await auth_service.request_customer_otp(
            engine,
            request_data.mobile_number,
            purpose=OTPPurpose.LOGIN,
        )
        expires_in = int((dispatch.expires_at - datetime.now(timezone.utc)).total_seconds())
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
    except ServiceError:
        raise
    except Exception:
        logger.exception("Failed to generate customer OTP for %s.", request_data.mobile_number)
        raise


@auth_router.post("/login/verify", response_model=APIResponse[AuthTokenResponse])
async def verify_customer_otp(
    request_data: OTPVerifyRequest = Body(...),
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[AuthTokenResponse]:
    """
    Verify a customer OTP and issue a signed JWT access token.

    Args:
        request_data: Validated OTP verification payload for the customer.
        engine: Active ODMantic database engine dependency.

    Returns:
        APIResponse[AuthTokenResponse]: Authenticated customer identity and
        access-token metadata for subsequent requests.

    Raises:
        HTTPException: Re-raises controller validation errors or wraps
        unexpected exceptions as HTTP 500 responses through the route guard.
    """
    try:
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
            latest_application = max(
                linked_applications, key=lambda application: application.updated_at
            )
            first_name = latest_application.personal_details.first_name.strip()
            last_name = latest_application.personal_details.last_name.strip()
            full_name = " ".join(part for part in [first_name, last_name] if part)
            if full_name:
                user.full_name = full_name

        await engine.save(user)
        access_token, expires_at = create_access_token(
            subject=str(user.id),
            role="customer",
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
    except ServiceError:
        raise
    except Exception:
        logger.exception(
            "Failed to verify customer OTP for %s.",
            request_data.mobile_number,
        )
        raise


async def _link_customer_records_by_mobile(
    engine: AIOEngine,
    *,
    user: User,
    mobile_number: str,
) -> list[Application]:
    """
    Attach guest applications for a verified mobile number to a user record.

    Args:
        engine: Active ODMantic database engine dependency.
        user: Persisted user record to associate with prior guest applications.
        mobile_number: Verified mobile number used to locate matching records.

    Returns:
        list[Application]: Matching applications found for the supplied mobile number.

    Raises:
        HTTPException: Any unexpected persistence error is allowed to bubble to
        the route guard and global exception handlers.
    """
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
    request_data: AdminLoginRequest = Body(...),
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[AuthTokenResponse]:
    """
    Validate admin credentials, dispatch an OTP, and issue a JWT token.

    Args:
        request_data: Validated admin login payload containing email and password.
        engine: Active ODMantic database engine dependency.

    Returns:
        APIResponse[AuthTokenResponse]: Admin identity and signed JWT metadata.

    Raises:
        HTTPException: Re-raises controller validation errors or wraps
        unexpected exceptions as HTTP 500 responses through the route guard.
    """
    try:
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
    except ServiceError:
        raise
    except Exception:
        logger.exception("Failed to authenticate admin %s.", request_data.email)
        raise


@auth_router.post("/admin/login/verify", response_model=APIResponse[AuthTokenResponse])
async def verify_admin_login(
    request_data: AdminVerifyRequest = Body(...),
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[AuthTokenResponse]:
    """
    Verify the admin OTP challenge and return a signed JWT token.

    Args:
        request_data: Validated admin OTP verification payload.
        engine: Active ODMantic database engine dependency.

    Returns:
        APIResponse[AuthTokenResponse]: Admin identity and refreshed JWT data.

    Raises:
        HTTPException: Re-raises controller validation errors or wraps
        unexpected exceptions as HTTP 500 responses through the route guard.
    """
    try:
        admin_identity = await auth_service.verify_admin_otp(
            engine,
            email=str(request_data.email),
            otp_code=request_data.otp_code,
        )
        access_token, expires_at = create_access_token(
            subject=admin_identity,
            role="admin",
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
    except ServiceError:
        raise
    except Exception:
        logger.exception("Failed to verify admin OTP for %s.", request_data.email)
        raise
