"""Unit tests for authentication MCP tools."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from insureflow_mcp.schemas.auth import (
    AdminLoginInput,
    RequestCustomerOTPInput,
    VerifyCustomerOTPInput,
)
from insureflow_mcp.tools.auth import AuthTools


@pytest.mark.asyncio
@respx.mock
async def test_request_customer_otp_returns_dispatch(main_client, auth_session) -> None:
    """The customer OTP tool should return the backend dispatch payload."""

    respx.post("http://test-main/api/v1/auth/login/otp").mock(
        return_value=Response(
            202,
            json={
                "success": True,
                "data": {
                    "mobile_number": "9999999999",
                    "expires_in_seconds": 600,
                },
            },
        )
    )

    tools = AuthTools(main_client=main_client, auth_session=auth_session)
    result = await tools.request_customer_otp(RequestCustomerOTPInput(mobile_number="9999999999"))

    assert result.success is True
    assert result.data is not None
    assert result.data.expires_in_seconds == 600


@pytest.mark.asyncio
@respx.mock
async def test_verify_customer_otp_stores_customer_token(main_client, auth_session) -> None:
    """The customer verify tool should persist the returned customer token."""

    respx.post("http://test-main/api/v1/auth/login/verify").mock(
        return_value=Response(
            200,
            json={
                "success": True,
                "data": {
                    "user_id": "user-1",
                    "token": {
                        "access_token": "customer-new-token",
                        "token_type": "bearer",
                        "expires_in_seconds": 3600,
                        "user_role": "customer",
                    },
                },
            },
        )
    )

    tools = AuthTools(main_client=main_client, auth_session=auth_session)
    result = await tools.verify_customer_otp(
        VerifyCustomerOTPInput(mobile_number="9999999999", otp_code="123456")
    )

    assert result.success is True
    assert result.data is not None
    assert auth_session.customer_token == "customer-new-token"


@pytest.mark.asyncio
@respx.mock
async def test_admin_login_stores_admin_token(main_client, auth_session) -> None:
    """The admin login tool should persist the returned admin token."""

    respx.post("http://test-main/api/v1/auth/admin/login").mock(
        return_value=Response(
            200,
            json={
                "success": True,
                "data": {
                    "user_id": "admin@example.com",
                    "token": {
                        "access_token": "admin-new-token",
                        "token_type": "bearer",
                        "expires_in_seconds": 3600,
                        "user_role": "admin",
                    },
                },
            },
        )
    )

    tools = AuthTools(main_client=main_client, auth_session=auth_session)
    result = await tools.admin_login(
        AdminLoginInput(email="admin@example.com", password="Password123")
    )

    assert result.success is True
    assert result.data is not None
    assert auth_session.admin_token == "admin-new-token"
