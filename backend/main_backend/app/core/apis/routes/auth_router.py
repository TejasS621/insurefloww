"""Authentication routes for the main backend."""

from __future__ import annotations

from fastapi import APIRouter, status

from backend.main_backend.app.core.apis.routes._helpers import raise_not_implemented
from backend.main_backend.app.core.apis.schemas.requests.auth_request import (
    AdminLoginRequest,
    AdminVerifyRequest,
    OTPLoginRequest,
    OTPVerifyRequest,
)
from backend.main_backend.app.core.apis.schemas.responses.auth_response import (
    AuthTokenResponse,
    OTPDispatchResponse,
)
from backend.main_backend.app.core.apis.schemas.responses.common_response import APIResponse

auth_router = APIRouter(prefix="/api/v1/auth", tags=["Auth"])


@auth_router.post("/login/otp", response_model=APIResponse[OTPDispatchResponse], status_code=status.HTTP_202_ACCEPTED)
async def request_customer_otp(_: OTPLoginRequest) -> APIResponse[OTPDispatchResponse]:
    """Start the customer OTP login flow."""
    raise_not_implemented("Customer OTP login request")


@auth_router.post("/login/verify", response_model=APIResponse[AuthTokenResponse])
async def verify_customer_otp(_: OTPVerifyRequest) -> APIResponse[AuthTokenResponse]:
    """Verify the customer OTP and issue an access token."""
    raise_not_implemented("Customer OTP verification")


@auth_router.post("/admin/login", response_model=APIResponse[OTPDispatchResponse], status_code=status.HTTP_202_ACCEPTED)
async def request_admin_login(_: AdminLoginRequest) -> APIResponse[OTPDispatchResponse]:
    """Start the admin login and second-factor flow."""
    raise_not_implemented("Admin login request")


@auth_router.post("/admin/login/verify", response_model=APIResponse[AuthTokenResponse])
async def verify_admin_login(_: AdminVerifyRequest) -> APIResponse[AuthTokenResponse]:
    """Verify the admin second factor and issue an admin token."""
    raise_not_implemented("Admin login verification")

