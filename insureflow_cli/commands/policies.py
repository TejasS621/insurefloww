"""Customer policy retrieval and download commands."""

from __future__ import annotations

from pathlib import Path

import typer

from insureflow_cli.errors import CLIError
from insureflow_cli.rendering import print_success, show_kv_table, show_rows_table
from insureflow_cli.utils import require_context, run_async, unwrap_data
from insureflow_mcp.schemas.policies import DownloadPolicyInput, GetPolicyInput

app = typer.Typer(help="Customer policy listing, retrieval, and download commands.")


@app.command("list")
def list_policies(ctx: typer.Context) -> None:
    """List policies for the currently logged-in customer."""

    cli = require_context(ctx)
    response = run_async(cli.client.list_policies(cli.session.require_customer_token()))
    data = unwrap_data(response)
    if not isinstance(data, list):
        raise CLIError("Backend returned an invalid policy list response.")
    print_success(cli.console, response.get("message", "Policies fetched successfully."))
    show_rows_table(
        cli.console,
        "Policies",
        ["policy_number", "transaction_reference", "policy_status", "coverage_amount", "premium_amount", "issue_date"],
        [item for item in data if isinstance(item, dict)],
    )


@app.command("get")
def get_policy(
    ctx: typer.Context,
    policy_number: str = typer.Option(..., prompt=True, help="Policy number."),
) -> None:
    """Fetch a single policy summary for the logged-in customer."""

    cli = require_context(ctx)
    payload = GetPolicyInput(policy_number=policy_number)
    response = run_async(cli.client.get_policy(payload.policy_number, cli.session.require_customer_token()))
    data = unwrap_data(response)
    if not isinstance(data, dict):
        raise CLIError("Backend returned an invalid policy response.")
    print_success(cli.console, response.get("message", "Policy fetched successfully."))
    show_kv_table(cli.console, "Policy", data)


@app.command("download")
def download_policy(
    ctx: typer.Context,
    policy_number: str = typer.Option(..., prompt=True, help="Policy number."),
    output: Path | None = typer.Option(None, help="Optional output file path."),
) -> None:
    """Download a policy PDF for the logged-in customer."""

    cli = require_context(ctx)
    payload = DownloadPolicyInput(policy_number=policy_number)
    destination = output or (cli.settings.download_directory / f"{payload.policy_number}.pdf")
    file_path = run_async(
        cli.client.download_policy(
            payload.policy_number,
            token=cli.session.require_customer_token(),
            destination=destination,
        )
    )
    print_success(cli.console, "Policy document downloaded successfully.")
    show_kv_table(
        cli.console,
        "Downloaded File",
        {
            "file_name": file_path.name,
            "local_file_path": file_path.resolve(),
        },
    )
