"""Admin broker registry commands."""

from __future__ import annotations

import typer

from insureflow_cli.errors import CLIError
from insureflow_cli.rendering import print_success, show_kv_table, show_rows_table
from insureflow_cli.utils import require_context, run_async, unwrap_data
from insureflow_mcp.schemas.brokers import RegisterBrokerInput

app = typer.Typer(help="Admin broker registry management commands.")


@app.command("list")
def list_brokers(ctx: typer.Context) -> None:
    """List broker registry records for the logged-in admin."""

    cli = require_context(ctx)
    response = run_async(cli.client.list_brokers(cli.session.require_admin_token()))
    data = unwrap_data(response)
    if not isinstance(data, list):
        raise CLIError("Backend returned an invalid broker list response.")
    print_success(cli.console, response.get("message", "Brokers fetched successfully."))
    show_rows_table(
        cli.console,
        "Broker Registry",
        ["broker_code", "broker_name", "status", "callback_url", "webhook_url"],
        [item for item in data if isinstance(item, dict)],
    )


@app.command("register")
def register_broker(
    ctx: typer.Context,
    broker_name: str = typer.Option(..., prompt=True, help="Broker display name."),
    broker_code: str = typer.Option(..., prompt=True, help="Unique broker code."),
    callback_url: str = typer.Option(..., prompt=True, help="Broker callback URL."),
    webhook_url: str = typer.Option(..., prompt=True, help="Broker webhook URL."),
) -> None:
    """Register a broker through the admin API."""

    cli = require_context(ctx)
    payload = RegisterBrokerInput(
        broker_name=broker_name,
        broker_code=broker_code.upper(),
        callback_url=callback_url,
        webhook_url=webhook_url,
    )
    response = run_async(
        cli.client.register_broker(
            payload.model_dump(mode="json"),
            cli.session.require_admin_token(),
        )
    )
    data = unwrap_data(response)
    if not isinstance(data, dict):
        raise CLIError("Backend returned an invalid broker registration response.")
    print_success(cli.console, response.get("message", "Broker registered successfully."))
    show_kv_table(cli.console, "Registered Broker", data)


@app.command("update-status")
def update_broker_status(
    ctx: typer.Context,
    broker_code: str = typer.Option(..., prompt=True, help="Broker code."),
    status: str = typer.Option(..., prompt=True, help="ACTIVE, INACTIVE, or SUSPENDED."),
    reason: str | None = typer.Option(None, help="Optional audit reason."),
) -> None:
    """Update a broker lifecycle status through the admin API."""

    cli = require_context(ctx)
    response = run_async(
        cli.client.update_broker_status(
            broker_code=broker_code.upper(),
            payload={"status": status.upper(), "reason": reason},
            token=cli.session.require_admin_token(),
        )
    )
    data = unwrap_data(response)
    if not isinstance(data, dict):
        raise CLIError("Backend returned an invalid broker status response.")
    print_success(cli.console, response.get("message", "Broker status updated successfully."))
    show_kv_table(cli.console, "Broker Status", data)


@app.command("rotate-key")
def rotate_broker_key(
    ctx: typer.Context,
    broker_code: str = typer.Option(..., prompt=True, help="Broker code."),
    initiated_by: str | None = typer.Option(None, help="Optional admin identifier for audit logs."),
    reason: str | None = typer.Option(None, help="Optional rotation reason."),
) -> None:
    """Rotate broker credentials through the admin API."""

    cli = require_context(ctx)
    response = run_async(
        cli.client.rotate_broker_key(
            broker_code=broker_code.upper(),
            payload={"initiated_by": initiated_by, "reason": reason},
            token=cli.session.require_admin_token(),
        )
    )
    data = unwrap_data(response)
    if not isinstance(data, dict):
        raise CLIError("Backend returned an invalid broker key rotation response.")
    print_success(cli.console, response.get("message", "Broker key rotated successfully."))
    show_kv_table(cli.console, "Rotated Broker Key", data)
