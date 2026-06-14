"""Customer support ticket commands."""

from __future__ import annotations

import typer

from insureflow_cli.errors import CLIError
from insureflow_cli.rendering import print_success, show_kv_table, show_rows_table
from insureflow_cli.utils import require_context, run_async, to_json_payload, unwrap_data
from insureflow_mcp.schemas.tickets import CreateTicketInput

app = typer.Typer(help="Customer ticket creation and listing commands.")


@app.command("create")
def create_ticket(
    ctx: typer.Context,
    transaction_reference: str | None = typer.Option(None, help="Optional transaction reference."),
    category: str = typer.Option("GENERAL", prompt=True, help="Ticket category."),
    priority: str = typer.Option("MEDIUM", prompt=True, help="Ticket priority."),
    subject: str = typer.Option(..., prompt=True, help="Ticket subject."),
    message: str = typer.Option(..., prompt=True, help="Ticket message."),
) -> None:
    """Create a support ticket for the logged-in customer."""

    cli = require_context(ctx)
    payload = CreateTicketInput(
        transaction_reference=transaction_reference,
        category=category.upper(),
        priority=priority.upper(),
        subject=subject,
        message=message,
    )
    response = run_async(
        cli.client.create_ticket(
            to_json_payload(payload, exclude_none=True),
            cli.session.require_customer_token(),
        )
    )
    data = unwrap_data(response)
    if not isinstance(data, dict):
        raise CLIError("Backend returned an invalid ticket creation response.")
    print_success(cli.console, response.get("message", "Ticket created successfully."))
    show_kv_table(cli.console, "Ticket", data)


@app.command("list")
def list_tickets(ctx: typer.Context) -> None:
    """List support tickets for the logged-in customer."""

    cli = require_context(ctx)
    response = run_async(cli.client.list_tickets(cli.session.require_customer_token()))
    data = unwrap_data(response)
    if not isinstance(data, list):
        raise CLIError("Backend returned an invalid ticket list response.")
    print_success(cli.console, response.get("message", "Tickets fetched successfully."))
    show_rows_table(
        cli.console,
        "Tickets",
        ["ticket_reference", "transaction_reference", "category", "priority", "status", "subject", "updated_at"],
        [item for item in data if isinstance(item, dict)],
    )
