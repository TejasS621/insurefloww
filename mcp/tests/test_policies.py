"""Unit tests for policy MCP tools."""

from __future__ import annotations

from pathlib import Path

import pytest
import respx
from httpx import Response

from insureflow_mcp.schemas.policies import DownloadPolicyInput, GetPolicyInput
from insureflow_mcp.tools.policies import PolicyTools


@pytest.mark.asyncio
@respx.mock
async def test_get_policy_returns_policy_details(settings, main_client, auth_session) -> None:
    """The policy tool should normalize policy summaries from the main backend."""

    respx.get("http://test-main/api/v1/policies/POL-1").mock(
        return_value=Response(
            200,
            json={
                "success": True,
                "data": {
                    "policy_number": "POL-1",
                    "transaction_reference": "TXN-1",
                    "policy_status": "ISSUED",
                    "coverage_amount": 1000000,
                    "premium_amount": 12000,
                    "issue_date": "2026-06-14",
                    "start_date": "2026-06-14",
                    "end_date": "2027-06-13",
                    "document_url": "/api/v1/policies/POL-1/view",
                },
            },
        )
    )

    tools = PolicyTools(settings=settings, auth_session=auth_session, main_client=main_client)
    result = await tools.get_policy(GetPolicyInput(policy_number="POL-1"))

    assert result.success is True
    assert result.data is not None
    assert result.data.policy_status == "ISSUED"


@pytest.mark.asyncio
@respx.mock
async def test_download_policy_saves_file(tmp_path: Path, settings, main_client, auth_session) -> None:
    """The policy-download tool should persist the downloaded PDF."""

    settings.download_directory = str(tmp_path)
    respx.get("http://test-main/api/v1/policies/POL-1/download").mock(
        return_value=Response(200, content=b"%PDF-1.4")
    )

    tools = PolicyTools(settings=settings, auth_session=auth_session, main_client=main_client)
    result = await tools.download_policy(DownloadPolicyInput(policy_number="POL-1"))

    assert result.success is True
    assert result.data is not None
    assert Path(result.data.local_file_path).exists()
