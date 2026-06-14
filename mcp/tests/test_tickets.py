"""Unit tests for ticket MCP tools."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from insureflow_mcp.schemas.tickets import CreateTicketInput
from insureflow_mcp.tools.tickets import TicketTools


@pytest.mark.asyncio
@respx.mock
async def test_create_ticket_returns_ticket(main_client, auth_session) -> None:
    """The ticket-creation tool should return the created ticket payload."""

    respx.post("http://test-main/api/v1/tickets").mock(
        return_value=Response(
            201,
            json={
                "success": True,
                "data": {
                    "ticket_reference": "TKT-1",
                    "transaction_reference": "TXN-1",
                    "category": "PAYMENT",
                    "priority": "HIGH",
                    "status": "OPEN",
                    "subject": "Help",
                    "message": "Need help",
                    "created_at": "2026-06-14T10:00:00Z",
                    "updated_at": "2026-06-14T10:00:00Z",
                },
            },
        )
    )

    tools = TicketTools(auth_session=auth_session, main_client=main_client)
    result = await tools.create_ticket(
        CreateTicketInput(category="PAYMENT", priority="HIGH", subject="Help", message="Need help")
    )

    assert result.success is True
    assert result.data is not None
    assert result.data.ticket_reference == "TKT-1"
