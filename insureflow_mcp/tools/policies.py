"""MCP policy tools implemented as thin adapters over InsureFlow APIs."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from insureflow_mcp.clients.main_backend_client import MainBackendClient
from insureflow_mcp.core.auth_session import AuthSessionStore
from insureflow_mcp.core.config import MCPSettings
from insureflow_mcp.core.errors import BackendRequestError, MCPToolError
from insureflow_mcp.core.results import ToolResult, error_result, success_result
from insureflow_mcp.schemas.common import extract_api_data
from insureflow_mcp.schemas.policies import DownloadPolicyInput, DownloadPolicyOutput, GetPolicyInput, PolicyOutput


class PolicyTools:
    """Policy-oriented orchestration helpers used by the MCP server."""

    def __init__(self, *, settings: MCPSettings, auth_session: AuthSessionStore, main_client: MainBackendClient) -> None:
        self.settings = settings
        self.auth_session = auth_session
        self.main_client = main_client

    async def get_policy(self, payload: GetPolicyInput) -> ToolResult[PolicyOutput]:
        """Fetch a policy summary through the authenticated main backend route."""

        try:
            response = await self.main_client.get_policy(payload.policy_number, self.auth_session.get_customer_token())
            data = extract_api_data(response)
            if not isinstance(data, dict):
                raise BackendRequestError("Main backend returned a malformed policy response.")
            result = PolicyOutput(
                policy_number=str(data.get("policy_number")),
                transaction_reference=str(data.get("transaction_reference")),
                policy_status=str(data.get("policy_status", "UNKNOWN")),
                coverage_amount=float(data.get("coverage_amount", 0.0)),
                premium_amount=float(data.get("premium_amount", 0.0)),
                issue_date=(
                    str(data["issue_date"]) if data.get("issue_date") is not None else None
                ),
                start_date=(
                    str(data["start_date"]) if data.get("start_date") is not None else None
                ),
                end_date=(
                    str(data["end_date"]) if data.get("end_date") is not None else None
                ),
                policy_document_url=(
                    str(data["document_url"]) if data.get("document_url") is not None else None
                ),
            )
            return success_result("Policy fetched successfully.", result)
        except MCPToolError as exc:
            return error_result(exc)

    async def download_policy(self, payload: DownloadPolicyInput) -> ToolResult[DownloadPolicyOutput]:
        """Download a policy document and return the local file reference."""

        try:
            destination = Path(self.settings.download_directory) / f"{payload.policy_number}.pdf"
            file_path = await self.main_client.download_policy(
                payload.policy_number,
                token=self.auth_session.get_customer_token(),
                destination=destination,
            )
            result = DownloadPolicyOutput(
                file_name=file_path.name,
                local_file_path=str(file_path.resolve()),
            )
            return success_result("Policy document downloaded successfully.", result)
        except MCPToolError as exc:
            return error_result(exc)


def register_policy_tools(mcp_server: Any, tools: PolicyTools) -> None:
    """Register policy tool handlers on the running MCP server."""

    @mcp_server.tool(
        name="get_policy",
        description="Retrieve customer policy details by policy number using the authenticated main backend API.",
    )
    async def get_policy(payload: GetPolicyInput) -> dict[str, Any]:
        """Fetch policy details for Claude."""

        return (await tools.get_policy(payload)).model_dump(mode="json")

    @mcp_server.tool(
        name="download_policy",
        description=(
            "Download a customer policy PDF and return local file metadata. "
            "This tool stores the file in the MCP download directory."
        ),
    )
    async def download_policy(payload: DownloadPolicyInput) -> dict[str, Any]:
        """Download a customer policy PDF and return the saved file reference."""

        return (await tools.download_policy(payload)).model_dump(mode="json")
