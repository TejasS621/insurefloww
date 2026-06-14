"""Payment initiation and status commands for checkout workflows."""

from __future__ import annotations

import typer

from insureflow_cli.errors import CLIError
from insureflow_cli.rendering import print_success, show_kv_table
from insureflow_cli.utils import require_context, run_async, to_json_payload, unwrap_data
from insureflow_mcp.schemas.payments import GetPaymentStatusInput, InitiatePaymentInput

app = typer.Typer(help="Hosted payment initiation and payment status commands.")


@app.command("initiate")
def initiate_payment(
    ctx: typer.Context,
    transaction_reference: str = typer.Option(..., prompt=True, help="Transaction reference."),
    selected_payment_method: str | None = typer.Option(None, help="Optional preferred payment method."),
) -> None:
    """Create a hosted payment session for a selected transaction."""

    cli = require_context(ctx)
    payload = InitiatePaymentInput(
        transaction_reference=transaction_reference,
        selected_payment_method=selected_payment_method,
    )
    response = run_async(
        cli.client.initiate_payment(
            payload.transaction_reference,
            to_json_payload(payload, exclude={"transaction_reference"}, exclude_none=True),
        )
    )
    data = unwrap_data(response)
    if not isinstance(data, dict):
        raise CLIError("Backend returned an invalid payment initiation response.")
    print_success(cli.console, response.get("message", "Payment session created successfully."))
    show_kv_table(
        cli.console,
        "Payment Session",
        {
            "payment_reference": data.get("payment_reference"),
            "payment_url": data.get("payment_url"),
            "amount": data.get("amount"),
            "currency": data.get("currency"),
            "available_payment_methods": data.get("available_payment_methods"),
            "status": data.get("status"),
        },
    )


@app.command("status")
def payment_status(
    ctx: typer.Context,
    transaction_reference: str = typer.Option(..., prompt=True, help="Transaction reference."),
) -> None:
    """Fetch current payment and transaction status for a transaction."""

    cli = require_context(ctx)
    payload = GetPaymentStatusInput(transaction_reference=transaction_reference)
    response = run_async(cli.client.get_payment_status(payload.transaction_reference))
    data = unwrap_data(response)
    if not isinstance(data, dict):
        raise CLIError("Backend returned an invalid payment status response.")
    print_success(cli.console, response.get("message", "Payment status fetched successfully."))
    show_kv_table(
        cli.console,
        "Payment Status",
        {
            "payment_status": data.get("payment_status"),
            "transaction_status": data.get("transaction_status"),
            "provider_payment_reference": data.get("provider_payment_reference"),
        },
    )
