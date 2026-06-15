"""Unit tests for payment MCP tools."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from insureflow_mcp.schemas.payments import GetPaymentStatusInput, InitiatePaymentInput
from insureflow_mcp.tools.payments import PaymentTools


@pytest.mark.asyncio
@respx.mock
async def test_initiate_payment_returns_checkout_payload(main_client) -> None:
    """The payment-initiation tool should normalize hosted payment output."""

    respx.post("http://test-main/api/v1/payments/initiate/TXN-1").mock(
        return_value=Response(
            200,
            json={
                "success": True,
                "data": {
                    "payment_reference": "PAY-1",
                    "payment_url": "http://localhost/mock",
                    "amount": 12000,
                    "currency": "INR",
                    "available_payment_methods": ["UPI"],
                    "status": "PAYMENT_INITIATED",
                },
            },
        )
    )

    tools = PaymentTools(main_client=main_client)
    result = await tools.initiate_payment(InitiatePaymentInput(transaction_reference="TXN-1"))

    assert result.success is True
    assert result.data is not None
    assert result.data.payment_reference == "PAY-1"


@pytest.mark.asyncio
@respx.mock
async def test_get_payment_status_returns_status(main_client) -> None:
    """The payment-status tool should return backend polling fields."""

    respx.get("http://test-main/api/v1/payments/status/TXN-1").mock(
        return_value=Response(
            200,
            json={
                "success": True,
                "data": {
                    "payment_status": "SUCCESS",
                    "transaction_status": "POLICY_ISSUED",
                    "provider_payment_reference": "PAY-1",
                },
            },
        )
    )

    tools = PaymentTools(main_client=main_client)
    result = await tools.get_payment_status(GetPaymentStatusInput(transaction_reference="TXN-1"))

    assert result.success is True
    assert result.data is not None
    assert result.data.payment_status == "SUCCESS"
