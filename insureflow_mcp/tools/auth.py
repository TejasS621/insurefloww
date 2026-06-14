"""MCP authentication tools implemented as thin adapters over InsureFlow auth APIs."""

from __future__ import annotations

from typing import Any

from insureflow_mcp.clients.main_backend_client import MainBackendClient
from insureflow_mcp.core.auth_session import AuthSessionStore
from insureflow_mcp.core.errors import BackendRequestError, MCPToolError
from insureflow_mcp.core.results import ToolResult, error_result, success_result
from insureflow_mcp.schemas.auth import (
    AdminLoginInput,
    AdminVerifyInput,
    AuthTokenOutput,
    OTPDispatchOutput,
    RequestCustomerOTPInput,
    TokenPayloadOutput,
    VerifyCustomerOTPInput,
)
from insureflow_mcp.schemas.common import extract_api_data


class AuthTools:
    """Login-oriented orchestration helpers used by the MCP server."""

    def __init__(self, *, main_client: MainBackendClient, auth_session: AuthSessionStore) -> None:
        self.main_client = main_client
        self.auth_session = auth_session

    async def request_customer_otp(self, payload: RequestCustomerOTPInput) -> ToolResult[OTPDispatchOutput]:
        """Call the customer OTP-dispatch endpoint and return its direct payload."""

        try:
            response = await self.main_client.request_customer_otp(payload.model_dump())
            data = extract_api_data(response)
            if not isinstance(data, dict):
                raise BackendRequestError("Main backend returned a malformed customer OTP response.")
            return success_result("Customer OTP requested successfully.", OTPDispatchOutput(**data))
        except MCPToolError as exc:
            return error_result(exc)

    async def verify_customer_otp(self, payload: VerifyCustomerOTPInput) -> ToolResult[AuthTokenOutput]:
        """Call the customer OTP-verification endpoint and persist the returned token."""

        try:
            response = await self.main_client.verify_customer_otp(payload.model_dump())
            result = self._parse_auth_token_response(response, malformed_message="Main backend returned a malformed customer auth response.")
            self.auth_session.set_customer_token(result.token.access_token)
            return success_result("Customer authentication successful.", result)
        except MCPToolError as exc:
            return error_result(exc)

    async def admin_login(self, payload: AdminLoginInput) -> ToolResult[AuthTokenOutput]:
        """Call the admin credential-login endpoint and persist the returned token."""

        try:
            response = await self.main_client.admin_login(payload.model_dump(mode="json"))
            result = self._parse_auth_token_response(response, malformed_message="Main backend returned a malformed admin login response.")
            self.auth_session.set_admin_token(result.token.access_token)
            return success_result("Admin authentication successful.", result)
        except MCPToolError as exc:
            return error_result(exc)

    async def admin_verify(self, payload: AdminVerifyInput) -> ToolResult[AuthTokenOutput]:
        """Call the admin OTP-verification endpoint and persist the returned token."""

        try:
            response = await self.main_client.admin_verify(payload.model_dump(mode="json"))
            result = self._parse_auth_token_response(response, malformed_message="Main backend returned a malformed admin verify response.")
            self.auth_session.set_admin_token(result.token.access_token)
            return success_result("Admin verification successful.", result)
        except MCPToolError as exc:
            return error_result(exc)

    @staticmethod
    def _parse_auth_token_response(
        response: dict[str, Any],
        *,
        malformed_message: str,
    ) -> AuthTokenOutput:
        """Normalize a backend auth response into the MCP auth schema."""

        data = extract_api_data(response)
        if not isinstance(data, dict) or not isinstance(data.get("token"), dict):
            raise BackendRequestError(malformed_message)
        return AuthTokenOutput(
            user_id=str(data["user_id"]) if data.get("user_id") is not None else None,
            token=TokenPayloadOutput(
                access_token=str(data["token"].get("access_token")),
                token_type=str(data["token"].get("token_type", "bearer")),
                expires_in_seconds=int(data["token"].get("expires_in_seconds", 0)),
                user_role=str(data["token"].get("user_role", "")),
            ),
        )


def register_auth_tools(mcp_server: Any, tools: AuthTools) -> None:
    """Register auth tool handlers on the running MCP server."""

    @mcp_server.tool(
        name="request_customer_otp",
        description="Request a customer login OTP via POST /api/v1/auth/login/otp.",
    )
    async def request_customer_otp(payload: RequestCustomerOTPInput) -> dict[str, Any]:
        """Start the customer OTP login flow and return the dispatch metadata."""

        return (await tools.request_customer_otp(payload)).model_dump(mode="json")

    @mcp_server.tool(
        name="verify_customer_otp",
        description=(
            "Verify a customer login OTP via POST /api/v1/auth/login/verify. "
            "On success, the returned customer bearer token is stored in the MCP server session."
        ),
    )
    async def verify_customer_otp(payload: VerifyCustomerOTPInput) -> dict[str, Any]:
        """Verify a customer OTP and persist the customer bearer token."""

        return (await tools.verify_customer_otp(payload)).model_dump(mode="json")

    @mcp_server.tool(
        name="admin_login",
        description=(
            "Authenticate an admin with email and password via POST /api/v1/auth/admin/login. "
            "On success, the returned admin bearer token is stored in the MCP server session."
        ),
    )
    async def admin_login(payload: AdminLoginInput) -> dict[str, Any]:
        """Authenticate an admin and persist the admin bearer token."""

        return (await tools.admin_login(payload)).model_dump(mode="json")

    @mcp_server.tool(
        name="admin_verify",
        description=(
            "Verify the admin OTP flow via POST /api/v1/auth/admin/login/verify. "
            "On success, the returned admin bearer token is stored in the MCP server session."
        ),
    )
    async def admin_verify(payload: AdminVerifyInput) -> dict[str, Any]:
        """Verify an admin OTP and persist the admin bearer token."""

        return (await tools.admin_verify(payload)).model_dump(mode="json")
