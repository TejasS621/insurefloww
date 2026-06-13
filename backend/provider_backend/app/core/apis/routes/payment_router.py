"""Payment routes for the provider backend."""

from __future__ import annotations

from fastapi import APIRouter, Depends, status
from fastapi.responses import HTMLResponse
from odmantic import AIOEngine

from backend.provider_backend.app.core.apis.routes._mappers import (
    to_mock_payment_session_response,
    to_provider_payment_response,
)
from backend.provider_backend.app.core.apis.routes.dependencies import get_authenticated_broker
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
    _: object = Depends(get_authenticated_broker),
) -> APIResponse[ProviderPaymentResponse]:
    """Create a provider-owned payment session for an authenticated broker."""
    payment = await provider_payment_service.create_payment_session(engine, request_data)
    return APIResponse(
        message="Provider payment session created successfully.",
        data=to_provider_payment_response(payment),
    )


@payment_router.post("/create", response_model=APIResponse[MockPaymentSessionResponse], status_code=status.HTTP_201_CREATED)
async def create_mock_payment_session(
    request_data: MockPaymentCreateRequest,
    engine: AIOEngine = Depends(get_database),
    _: object = Depends(get_authenticated_broker),
) -> APIResponse[MockPaymentSessionResponse]:
    """Create a mock hosted payment session for an authenticated broker request."""
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
        f"""
        <label class="method-card">
          <input type="radio" name="payment_method" value="{method}" onchange="selectMethod('{method}')" />
          <span>{method}</span>
        </label>
        """
        for method in provider_payment_service.AVAILABLE_PAYMENT_METHODS
    )
    html = f"""
    <html>
      <head>
        <title>Mock Razorpay Checkout</title>
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap" rel="stylesheet">
        <style>
          :root {{
            --bg-color: #f6f5fa;
            --card-bg: #ffffff;
            --text-primary: #1d1b20;
            --text-secondary: #49454f;
            --primary: #6750a4;
            --primary-hover: #584193;
            --primary-container: #e8def8;
            --on-primary-container: #21005d;
            --success: #1b5e20;
            --error: #b3261e;
            --border: #cac4d0;
            --shadow: 0 4px 30px rgba(0, 0, 0, 0.03), 0 1px 3px rgba(0, 0, 0, 0.05);
            --transition: all 0.25s cubic-bezier(0.2, 0, 0, 1);
          }}
          @media (prefers-color-scheme: dark) {{
            :root {{
              --bg-color: #141218;
              --card-bg: #1d1b20;
              --text-primary: #e6e1e5;
              --text-secondary: #cac4d0;
              --primary: #d0bcff;
              --primary-hover: #bda6fa;
              --primary-container: #4a4458;
              --on-primary-container: #e8def8;
              --border: #49454f;
              --shadow: 0 4px 35px rgba(0, 0, 0, 0.2), 0 1px 4px rgba(0, 0, 0, 0.1);
            }}
          }}
          body {{
            font-family: 'Outfit', sans-serif;
            margin: 0;
            padding: 24px;
            background: var(--bg-color);
            color: var(--text-primary);
            display: flex;
            align-items: center;
            justify-content: center;
            min-height: 90vh;
            transition: var(--transition);
          }}
          .card {{
            max-width: 500px;
            width: 100%;
            background: var(--card-bg);
            border: 1px solid var(--border);
            padding: 32px;
            border-radius: 28px;
            box-shadow: var(--shadow);
            transition: var(--transition);
          }}
          .header {{
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 24px;
          }}
          .logo {{
            width: 40px;
            height: 40px;
            background: var(--primary);
            border-radius: 12px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: var(--card-bg);
            font-weight: 700;
            font-size: 20px;
          }}
          h1 {{
            margin: 0;
            font-size: 24px;
            font-weight: 600;
          }}
          .badge {{
            display: inline-block;
            background: var(--primary-container);
            color: var(--on-primary-container);
            padding: 6px 12px;
            border-radius: 8px;
            font-size: 12px;
            font-weight: 500;
            margin-bottom: 20px;
          }}
          .details {{
            background: rgba(0, 0, 0, 0.02);
            border: 1px solid var(--border);
            padding: 16px;
            border-radius: 16px;
            margin-bottom: 24px;
          }}
          @media (prefers-color-scheme: dark) {{
            .details {{
              background: rgba(255, 255, 255, 0.02);
            }}
          }}
          .detail-row {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 12px;
            font-size: 14px;
          }}
          .detail-row:last-child {{
            margin-bottom: 0;
            border-top: 1px solid var(--border);
            padding-top: 12px;
          }}
          .label {{
            color: var(--text-secondary);
          }}
          .value {{
            font-weight: 500;
          }}
          .amount {{
            font-size: 22px;
            font-weight: 700;
            color: var(--primary);
          }}
          .btn {{
            display: flex;
            align-items: center;
            justify-content: center;
            width: 100%;
            height: 56px;
            background: var(--primary);
            color: var(--card-bg);
            border: none;
            border-radius: 9999px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: var(--transition);
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          }}
          .btn:hover {{
            background: var(--primary-hover);
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
          }}
          .btn:active {{
            transform: scale(0.95);
          }}
          .btn:disabled {{
            background: var(--border);
            cursor: not-allowed;
            transform: none;
            box-shadow: none;
          }}
          .method-grid {{
            display: grid;
            gap: 12px;
            margin-bottom: 20px;
          }}
          .method-card {{
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 14px 16px;
            border: 1px solid var(--border);
            border-radius: 16px;
            cursor: pointer;
            transition: var(--transition);
            font-size: 15px;
            font-weight: 500;
          }}
          .method-card:hover {{
            border-color: var(--primary);
            background: rgba(103, 80, 164, 0.06);
          }}
          .method-card input {{
            accent-color: var(--primary);
          }}
          .helper {{
            color: var(--text-secondary);
            font-size: 13px;
            margin-bottom: 16px;
          }}
          .status-msg {{
            margin-top: 16px;
            padding: 12px;
            border-radius: 12px;
            font-size: 14px;
            text-align: center;
            display: none;
          }}
          .status-msg.success {{
            display: block;
            background: rgba(27, 94, 32, 0.15);
            color: var(--success);
            border: 1px solid var(--success);
          }}
          .status-msg.error {{
            display: block;
            background: rgba(179, 38, 30, 0.15);
            color: var(--error);
            border: 1px solid var(--error);
          }}
          .spinner {{
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: #fff;
            animation: spin 1s ease-in-out infinite;
            margin-right: 8px;
          }}
          @keyframes spin {{
            to {{ transform: rotate(360deg); }}
          }}
        </style>
      </head>
      <body>
        <div class="card">
          <div class="header">
            <div class="logo">R</div>
            <h1>Razorpay Simulator</h1>
          </div>
          <span class="badge">SANDBOX ENVIRONMENT</span>
          
          <div class="details">
            <div class="detail-row">
              <span class="label">Payment Reference</span>
              <span class="value">{payment.payment_reference}</span>
            </div>
            <div class="detail-row">
              <span class="label">Order ID</span>
              <span class="value">{payment.gateway_order_id or "N/A"}</span>
            </div>
            <div class="detail-row">
              <span class="label">Amount Due</span>
              <span class="value amount">{payment.currency} {payment.amount:,.2f}</span>
            </div>
          </div>

          <div class="helper">Select a payment option to continue.</div>
          <div class="method-grid">
            {payment_methods_markup}
          </div>

          <button id="pay-btn" class="btn" onclick="simulatePayment()" disabled>
            Pay Securely
          </button>

          <div id="status-box" class="status-msg"></div>
        </div>

        <script>
          let selectedMethod = '';

          function selectMethod(method) {{
            selectedMethod = method;
            const btn = document.getElementById('pay-btn');
            btn.disabled = false;
            btn.innerText = `Pay with ${{method}}`;
          }}

          function returnToApp() {{
            if (window.opener && !window.opener.closed) {{
              window.opener.focus();
            }}
            window.close();
          }}

          async function simulatePayment() {{
            const btn = document.getElementById('pay-btn');
            const statusBox = document.getElementById('status-box');
            if (!selectedMethod) {{
              statusBox.innerText = 'Please select a payment method first.';
              statusBox.className = 'status-msg error';
              return;
            }}
            
            btn.disabled = true;
            btn.innerHTML = '<div class="spinner"></div> Processing Payment...';
            statusBox.className = 'status-msg';
            statusBox.style.display = 'none';

            const payload = {{
              gateway_order_id: "{payment.gateway_order_id}",
              gateway_payment_id: "pay_" + Math.random().toString(36).substring(2, 15),
              gateway_signature: "sig_" + Math.random().toString(36).substring(2, 15),
              payload: {{}}
            }};

            try {{
              const response = await fetch('/api/v1/provider/webhooks/payment-success', {{
                method: 'POST',
                headers: {{
                  'Content-Type': 'application/json'
                }},
                body: JSON.stringify(payload)
              }});

              const result = await response.json();
              if (response.ok && result.success) {{
                if (window.opener && !window.opener.closed) {{
                  window.opener.postMessage(
                    {{
                      type: 'INSUREFLOW_PAYMENT_SUCCESS',
                      paymentReference: '{payment.payment_reference}',
                      paymentMethod: selectedMethod
                    }},
                    '*'
                  );
                }}
                statusBox.innerHTML = 'Payment Successful via <strong>' + selectedMethod + '</strong>.<br/><br/><button class="btn" type="button" onclick="returnToApp()">Return to InsureFlow</button>';
                statusBox.className = 'status-msg success';
                btn.innerHTML = 'Payment Completed';
              }} else {{
                throw new Error(result.message || 'Payment simulation failed.');
              }}
            }} catch (error) {{
              console.error(error);
              statusBox.innerText = 'Error: ' + error.message;
              statusBox.className = 'status-msg error';
              btn.disabled = false;
              btn.innerHTML = 'Simulate Successful Payment';
            }}
          }}
        </script>
      </body>
    </html>
    """
    return HTMLResponse(content=html)

