"""Unit tests for quote MCP tools."""

from __future__ import annotations

import pytest
import respx
from httpx import Response

from insureflow_mcp.schemas.common import CoverageDetailsInput, PersonalDetailsInput
from insureflow_mcp.schemas.quotes import GenerateQuoteInput, SelectQuoteInput
from insureflow_mcp.tools.quotes import QuoteTools


@pytest.mark.asyncio
@respx.mock
async def test_generate_quote_returns_summary(settings, main_client) -> None:
    """The quote-generation tool should summarize quotes from the application response."""

    respx.post("http://test-main/api/v1/applications").mock(
        return_value=Response(
            201,
            json={
                "success": True,
                "message": "ok",
                "data": {
                    "application_reference": "APP-1",
                    "transaction_reference": "TXN-1",
                    "application_status": "QUOTE_GENERATED",
                    "quotes": [
                        {
                            "quote_id": "Q1",
                            "provider_name": "Provider A",
                            "plan_name": "Gold Plan",
                            "total_premium": 12000,
                            "coverage_amount": 1000000,
                            "quote_status": "ACTIVE",
                        }
                    ],
                },
            },
        )
    )
    tools = QuoteTools(main_client=main_client)
    payload = GenerateQuoteInput(
        insurance_type="LIFE",
        personal_details=PersonalDetailsInput(
            first_name="Tejas",
            last_name="Sahare",
            email="tejas@example.com",
            mobile_number="9999999999",
            date_of_birth="1999-11-02",
            gender="MALE",
            address_line_1="Line 1",
            city="Pune",
            state="Maharashtra",
            pincode="411001",
        ),
        coverage_details=CoverageDetailsInput(
            insurance_type="LIFE",
            coverage_amount=1000000,
            tenure_years=1,
        ),
    )

    result = await tools.generate_quote(payload)

    assert result.success is True
    assert result.data is not None
    assert result.data.application_reference == "APP-1"
    assert result.data.quote_ids == ["Q1"]


@pytest.mark.asyncio
@respx.mock
async def test_select_quote_returns_direct_quote_payload(main_client) -> None:
    """The quote-selection tool should mirror the backend normalized quote response."""

    respx.post("http://test-main/api/v1/quotes/select/Q1").mock(
        return_value=Response(
            200,
            json={
                "success": True,
                "data": {
                    "quote_id": "Q1",
                    "base_premium": 10000,
                    "tax_amount": 2000,
                    "total_premium": 12000,
                    "coverage_amount": 1000000,
                    "available_addons": [
                        {"addon_code": "A1", "addon_name": "Addon", "addon_price": 500}
                    ],
                    "quote_status": "ACTIVE",
                    "expires_at": "2026-06-15T10:00:00Z",
                },
            },
        )
    )

    tools = QuoteTools(main_client=main_client)
    result = await tools.select_quote(SelectQuoteInput(quote_id="Q1", selected_addons=["A1"]))

    assert result.success is True
    assert result.data is not None
    assert result.data.quote_status == "ACTIVE"
    assert result.data.total_premium == 12000
