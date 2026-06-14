"""Authentication commands for customer and admin login flows."""

from __future__ import annotations

import typer

from insureflow_cli.context import CLIContext
from insureflow_cli.errors import CLIError
from insureflow_cli.rendering import print_info, print_success, show_kv_table
from insureflow_cli.utils import require_context, run_async, to_json_payload, unwrap_data
from insureflow_mcp.schemas.auth import (
    AdminLoginInput,
    AdminVerifyInput,
    RequestCustomerOTPInput,
    VerifyCustomerOTPInput,
)

app = typer.Typer(help="Customer and admin authentication commands.")


@app.command("customer-otp")
def customer_otp(
    ctx: typer.Context,
    mobile_number: str = typer.Option(..., prompt=True, help="Customer mobile number."),
) -> None:
    """Request an OTP for the customer login flow."""

    cli = require_context(ctx)
    payload = RequestCustomerOTPInput(mobile_number=mobile_number)
    response = run_async(cli.client.request_customer_otp(to_json_payload(payload)))
    data = unwrap_data(response)
    if not isinstance(data, dict):
        raise CLIError("Backend returned an invalid customer OTP response.")
    print_success(cli.console, response.get("message", "OTP requested successfully."))
    show_kv_table(cli.console, "Customer OTP", data)
    print_info(cli.console, "Use `auth customer-verify` after reading the OTP from the backend logs.")


@app.command("customer-verify")
def customer_verify(
    ctx: typer.Context,
    mobile_number: str = typer.Option(..., prompt=True, help="Customer mobile number."),
    otp_code: str = typer.Option(..., prompt=True, help="Customer OTP code."),
) -> None:
    """Verify the customer OTP and persist the customer bearer token."""

    cli = require_context(ctx)
    payload = VerifyCustomerOTPInput(mobile_number=mobile_number, otp_code=otp_code)
    response = run_async(cli.client.verify_customer_otp(to_json_payload(payload)))
    data = unwrap_data(response)
    if not isinstance(data, dict) or not isinstance(data.get("token"), dict):
        raise CLIError("Backend returned an invalid customer authentication response.")
    cli.session.set_customer(
        token=str(data["token"]["access_token"]),
        user_id=str(data["user_id"]) if data.get("user_id") is not None else None,
    )
    print_success(cli.console, response.get("message", "Customer authentication successful."))
    show_kv_table(
        cli.console,
        "Customer Session",
        {
            "user_id": data.get("user_id"),
            "user_role": data["token"].get("user_role"),
            "expires_in_seconds": data["token"].get("expires_in_seconds"),
        },
    )


@app.command("admin-login")
def admin_login(
    ctx: typer.Context,
    email: str = typer.Option(..., prompt=True, help="Admin email."),
    password: str = typer.Option(..., prompt=True, hide_input=True, help="Admin password."),
) -> None:
    """Authenticate an admin and persist the returned admin bearer token."""

    cli = require_context(ctx)
    payload = AdminLoginInput(email=email, password=password)
    response = run_async(cli.client.admin_login(to_json_payload(payload)))
    data = unwrap_data(response)
    if not isinstance(data, dict) or not isinstance(data.get("token"), dict):
        raise CLIError("Backend returned an invalid admin login response.")
    cli.session.set_admin(
        token=str(data["token"]["access_token"]),
        user_id=str(data["user_id"]) if data.get("user_id") is not None else None,
    )
    print_success(cli.console, response.get("message", "Admin authentication successful."))
    show_kv_table(
        cli.console,
        "Admin Session",
        {
            "user_id": data.get("user_id"),
            "user_role": data["token"].get("user_role"),
            "expires_in_seconds": data["token"].get("expires_in_seconds"),
        },
    )
    print_info(cli.console, "If your flow requires OTP verification too, run `auth admin-verify` next.")


@app.command("admin-verify")
def admin_verify(
    ctx: typer.Context,
    email: str = typer.Option(..., prompt=True, help="Admin email."),
    otp_code: str = typer.Option(..., prompt=True, help="Admin OTP code."),
) -> None:
    """Verify the admin OTP and persist the returned admin bearer token."""

    cli = require_context(ctx)
    payload = AdminVerifyInput(email=email, otp_code=otp_code)
    response = run_async(cli.client.admin_verify(to_json_payload(payload)))
    data = unwrap_data(response)
    if not isinstance(data, dict) or not isinstance(data.get("token"), dict):
        raise CLIError("Backend returned an invalid admin verification response.")
    cli.session.set_admin(
        token=str(data["token"]["access_token"]),
        user_id=str(data["user_id"]) if data.get("user_id") is not None else None,
    )
    print_success(cli.console, response.get("message", "Admin verification successful."))
    show_kv_table(
        cli.console,
        "Admin Session",
        {
            "user_id": data.get("user_id"),
            "user_role": data["token"].get("user_role"),
            "expires_in_seconds": data["token"].get("expires_in_seconds"),
        },
    )


@app.command("status")
def auth_status(ctx: typer.Context) -> None:
    """Show the currently stored customer and admin session state."""

    cli = require_context(ctx)
    show_kv_table(
        cli.console,
        "Stored Session",
        {
            "customer_user_id": cli.session.state.customer_user_id,
            "customer_token": "stored" if cli.session.state.customer_token else "-",
            "admin_user_id": cli.session.state.admin_user_id,
            "admin_token": "stored" if cli.session.state.admin_token else "-",
            "session_file": cli.session.path,
        },
    )


@app.command("logout")
def logout(
    ctx: typer.Context,
    scope: str = typer.Option("all", help="One of: customer, admin, all."),
) -> None:
    """Clear stored customer, admin, or all session tokens."""

    cli = require_context(ctx)
    normalized = scope.lower()
    if normalized not in {"customer", "admin", "all"}:
        raise CLIError("Scope must be one of: customer, admin, all.")
    cli.session.clear(normalized)
    print_success(cli.console, f"Cleared {normalized} session state.")
