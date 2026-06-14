"""Unit tests for broker MCP tools."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from insureflow_mcp.schemas.brokers import RegisterBrokerInput
from insureflow_mcp.tools.brokers import BrokerTools


@pytest.mark.asyncio
@respx.mock
async def test_list_brokers_returns_backend_records(main_client, auth_session) -> None:
    """The broker-listing tool should return the admin broker list directly."""

    respx.get("http://test-main/api/v1/admin/brokers").mock(
        return_value=Response(
            200,
            json={
                "success": True,
                "data": [
                    {
                        "broker_code": "B1",
                        "broker_name": "Broker One",
                        "status": "ACTIVE",
                        "callback_url": "https://broker.one/callback",
                        "webhook_url": "https://broker.one/webhook",
                    },
                    {
                        "broker_code": "B2",
                        "broker_name": "Broker Two",
                        "status": "INACTIVE",
                        "callback_url": "https://broker.two/callback",
                        "webhook_url": "https://broker.two/webhook",
                    },
                ],
            },
        )
    )

    tools = BrokerTools(auth_session=auth_session, main_client=main_client)
    result = await tools.list_brokers()

    assert result.success is True
    assert result.data is not None
    assert len(result.data) == 2
    assert result.data[0].broker_code == "B1"


@pytest.mark.asyncio
@respx.mock
async def test_register_broker_returns_api_key(main_client, auth_session) -> None:
    """The broker-registration tool should return the one-time backend API key."""

    respx.post("http://test-main/api/v1/admin/brokers").mock(
        return_value=Response(
            201,
            json={
                "success": True,
                "data": {
                    "broker_code": "B1",
                    "api_key": "brk_live_demo",
                    "created_at": "2026-06-14T10:00:00Z",
                    "status": "ACTIVE",
                },
            },
        )
    )

    tools = BrokerTools(auth_session=auth_session, main_client=main_client)
    result = await tools.register_broker(
        RegisterBrokerInput(
            broker_name="Broker One",
            broker_code="B1",
            callback_url="https://broker.one/callback",
            webhook_url="https://broker.one/webhook",
        )
    )

    assert result.success is True
    assert result.data is not None
    assert result.data.api_key == "brk_live_demo"
