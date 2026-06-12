"""Payment routes for the provider backend."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.responses import HTMLResponse
from odmantic import AIOEngine

from backend.provider_backend.app.core.apis.routes._mappers import (
    to_mock_payment_session_response,
    to_provider_payment_response,
)
from backend.provider_backend.app.core.apis.schemas.requests.payment_request import (
    MockPaymentCreateRequest,
    PaymentSessionCreateRequest,
)
from backend.provider_backend.app.core.apis.schemas.responses.common_response import APIResponse
from backend.provider_backend.app.core.apis.schemas.responses.payment_response import (
    MockPaymentSessionResponse,
    ProviderPaymentResponse,
)
from backend.provider_backend.app.core.database.database import get_database
from backend.provider_backend.app.core.services.payment_service import provider_payment_service
from backend.provider_backend.app.core.services.service_exceptions import NotFoundServiceError

payment_router = APIRouter(prefix="/api/v1/provider/payments", tags=["Provider Payments"])
mock_payment_router = APIRouter(prefix="/mock-razorpay", tags=["Mock Razorpay"])


@payment_router.post("/create-session", response_model=APIResponse[ProviderPaymentResponse], status_code=status.HTTP_201_CREATED)
async def create_payment_session(
    request_data: PaymentSessionCreateRequest,
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[ProviderPaymentResponse]:
    """Create a provider-owned payment order or checkout session."""
    payment = await provider_payment_service.create_payment_session(engine, request_data)
    return APIResponse(
        message="Provider payment session created successfully.",
        data=to_provider_payment_response(payment),
    )


@payment_router.post("/create", response_model=APIResponse[MockPaymentSessionResponse], status_code=status.HTTP_201_CREATED)
async def create_mock_payment_session(
    request_data: MockPaymentCreateRequest,
    engine: AIOEngine = Depends(get_database),
) -> APIResponse[MockPaymentSessionResponse]:
    """Create a mock Razorpay-style hosted payment session for frontend redirection."""
    session = await provider_payment_service.create_mock_payment_session(engine, request_data)
    return APIResponse(
        message="Mock payment session created successfully.",
        data=to_mock_payment_session_response(session),
    )


@mock_payment_router.get("/pay/{payment_reference}", response_class=HTMLResponse)
async def render_mock_payment_page(
    payment_reference: str,
    engine: AIOEngine = Depends(get_database),
) -> HTMLResponse:
    """Render a simple hosted mock payment page for local redirect integration testing."""
    payment = await provider_payment_service.get_payment_by_reference(
        engine,
        payment_reference=payment_reference,
    )
    if payment is None:
        raise NotFoundServiceError("Mock payment page not found for the supplied payment reference.")

    payment_methods_markup = "".join(
        f"<li>{method}</li>" for method in provider_payment_service.AVAILABLE_PAYMENT_METHODS
    )
    html = f"""
    <html>
      <head>
        <title>Mock Razorpay Checkout</title>
        <style>
          body {{ font-family: Arial, sans-serif; margin: 40px; background: #f4f7fb; color: #1f2937; }}
          .card {{ max-width: 560px; margin: 0 auto; background: white; padding: 32px; border-radius: 16px; box-shadow: 0 12px 30px rgba(15, 23, 42, 0.08); }}
          h1 {{ margin-top: 0; }}
          .amount {{ font-size: 28px; font-weight: 700; margin: 16px 0; }}
          ul {{ padding-left: 20px; }}
          .note {{ margin-top: 24px; color: #475569; }}
        </style>
      </head>
      <body>
        <div class="card">
          <h1>Mock Razorpay Checkout</h1>
          <p>Payment Reference: <strong>{payment.payment_reference}</strong></p>
          <p>Gateway Order ID: <strong>{payment.gateway_order_id or "N/A"}</strong></p>
          <p class="amount">{payment.currency} {payment.amount:,.2f}</p>
          <p>Available payment methods:</p>
          <ul>{payment_methods_markup}</ul>
          <p class="note">
            This is a local simulation page for frontend redirect testing. Use the existing webhook
            endpoint to mark the payment as successful after completing your mock flow.
          </p>
        </div>
      </body>
    </html>
    """
    return HTMLResponse(content=html)

