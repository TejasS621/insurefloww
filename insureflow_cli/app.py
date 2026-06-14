"""Top-level Typer application for the InsureFlow CLI."""

from __future__ import annotations

import typer
from pydantic import ValidationError
from rich.console import Console

from insureflow_cli.client import CLIBackendClient
from insureflow_cli.commands.auth import app as auth_app
from insureflow_cli.commands.brokers import app as broker_app
from insureflow_cli.commands.payments import app as payment_app
from insureflow_cli.commands.policies import app as policy_app
from insureflow_cli.commands.quotes import app as quote_app
from insureflow_cli.commands.tickets import app as ticket_app
from insureflow_cli.config import get_settings
from insureflow_cli.context import CLIContext
from insureflow_cli.errors import CLIError
from insureflow_cli.rendering import print_error
from insureflow_cli.session import SessionStore

app = typer.Typer(
    help="InsureFlow command line interface for auth, quote, payment, policy, ticket, and broker workflows.",
    no_args_is_help=True,
)
app.add_typer(auth_app, name="auth")
app.add_typer(quote_app, name="quote")
app.add_typer(payment_app, name="payment")
app.add_typer(policy_app, name="policy")
app.add_typer(ticket_app, name="ticket")
app.add_typer(broker_app, name="broker")


@app.callback()
def main(ctx: typer.Context) -> None:
    """Initialize shared CLI context before any subcommand runs."""

    settings = get_settings()
    console = Console()
    ctx.obj = CLIContext(
        settings=settings,
        client=CLIBackendClient(settings),
        session=SessionStore(settings.session_file),
        console=console,
    )


def run() -> None:
    """Run the Typer application with friendly CLI error handling."""

    try:
        app()
    except CLIError as exc:
        print_error(Console(), str(exc))
        raise SystemExit(1) from exc
    except ValidationError as exc:
        print_error(Console(), str(exc))
        raise SystemExit(1) from exc
