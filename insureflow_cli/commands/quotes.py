"""Quote and application commands for guest insurance flows."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import typer

from insureflow_cli.context import CLIContext
from insureflow_cli.errors import CLIError
from insureflow_cli.rendering import print_info, print_success, show_kv_table, show_rows_table
from insureflow_cli.utils import load_json_file, require_context, run_async, to_json_payload, unwrap_data
from insureflow_mcp.schemas.common import CoverageDetailsInput, HealthDetailsInput, PersonalDetailsInput
from insureflow_mcp.schemas.quotes import GenerateQuoteInput, SelectQuoteInput

app = typer.Typer(help="Application, quote generation, and quote selection commands.")


@app.command("generate")
def generate_quote(
    ctx: typer.Context,
    payload_file: Path | None = typer.Option(None, help="Optional JSON file for the full application payload."),
) -> None:
    """Create an application and return generated quotes."""

    cli = require_context(ctx)
    payload = _build_generate_payload(payload_file, cli)
    response = run_async(cli.client.create_application(to_json_payload(payload, exclude_none=True)))
    data = unwrap_data(response)
    if not isinstance(data, dict):
        raise CLIError("Backend returned an invalid application response.")

    print_success(cli.console, response.get("message", "Application created successfully."))
    show_kv_table(
        cli.console,
        "Application",
        {
            "application_reference": data.get("application_reference"),
            "transaction_reference": data.get("transaction_reference"),
            "application_status": data.get("application_status"),
        },
    )

    quotes = data.get("quotes", [])
    if isinstance(quotes, list) and quotes:
        show_rows_table(
            cli.console,
            "Generated Quotes",
            ["quote_id", "provider_name", "plan_name", "total_premium", "coverage_amount", "quote_status"],
            [quote for quote in quotes if isinstance(quote, dict)],
        )


@app.command("select")
def select_quote(
    ctx: typer.Context,
    quote_id: str = typer.Option(..., prompt=True, help="Quote identifier to select."),
    selected_addons: str = typer.Option("", help="Comma-separated addon codes."),
    idempotency_key: str | None = typer.Option(None, help="Optional idempotency key."),
) -> None:
    """Select a quote and show the normalized backend quote payload."""

    cli = require_context(ctx)
    payload = SelectQuoteInput(
        quote_id=quote_id,
        selected_addons=[item.strip() for item in selected_addons.split(",") if item.strip()],
        idempotency_key=idempotency_key,
    )
    response = run_async(
        cli.client.select_quote(
            payload.quote_id,
            to_json_payload(payload, exclude={"quote_id"}, exclude_none=True),
        )
    )
    data = unwrap_data(response)
    if not isinstance(data, dict):
        raise CLIError("Backend returned an invalid quote selection response.")

    print_success(cli.console, response.get("message", "Quote selected successfully."))
    show_kv_table(
        cli.console,
        "Selected Quote",
        {
            "quote_id": data.get("quote_id"),
            "provider_name": data.get("provider_name"),
            "plan_code": data.get("plan_code"),
            "plan_name": data.get("plan_name"),
            "base_premium": data.get("base_premium"),
            "tax_amount": data.get("tax_amount"),
            "total_premium": data.get("total_premium"),
            "coverage_amount": data.get("coverage_amount"),
            "quote_status": data.get("quote_status"),
            "expires_at": data.get("expires_at"),
        },
    )
    addons = data.get("available_addons", [])
    if isinstance(addons, list) and addons:
        show_rows_table(
            cli.console,
            "Available Addons",
            ["addon_code", "addon_name", "addon_price"],
            [addon for addon in addons if isinstance(addon, dict)],
        )


def _build_generate_payload(payload_file: Path | None, cli: CLIContext) -> GenerateQuoteInput:
    """Build a quote-generation payload from file input or interactive prompts."""

    if payload_file is not None:
        return GenerateQuoteInput.model_validate(load_json_file(payload_file))

    insurance_type = typer.prompt("Insurance type").upper()
    mobile_number = typer.prompt("Mobile number")
    personal_details = PersonalDetailsInput(
        first_name=typer.prompt("First name"),
        last_name=typer.prompt("Last name"),
        email=typer.prompt("Email"),
        mobile_number=mobile_number,
        date_of_birth=typer.prompt("Date of birth (YYYY-MM-DD or DD/MM/YYYY)"),
        gender=typer.prompt("Gender (MALE/FEMALE/OTHER)").upper(),
        address_line_1=typer.prompt("Address line 1"),
        address_line_2=None,
        city=typer.prompt("City"),
        state=typer.prompt("State"),
        pincode=typer.prompt("Pincode"),
        gstin=None,
        politically_exposed_person=False,
    )
    default_relation = "SELF" if insurance_type == "HEALTH" else ""
    insured_members = _prompt_optional_int("Number of insured members")
    coverage_details = CoverageDetailsInput(
        insurance_type=insurance_type,
        coverage_amount=typer.prompt("Coverage amount", type=float),
        sum_insured=_prompt_optional_float("Sum insured"),
        tenure_years=_prompt_optional_int("Tenure years"),
        relation=_resolve_relation(
            insurance_type=insurance_type,
            insured_members=insured_members,
            default_relation=default_relation,
        ),
        insured_members=insured_members,
        pan_india_cover=typer.confirm("Pan-India cover?", default=True),
    )

    health_details = None
    if insurance_type == "HEALTH":
        other_conditions = typer.prompt("Other conditions (comma-separated)", default="")
        height_cm = _prompt_optional_float("Height in cm")
        weight_kg = _prompt_optional_float("Weight in kg")
        calculated_bmi = _calculate_bmi(height_cm=height_cm, weight_kg=weight_kg)
        health_details = HealthDetailsInput(
            height_cm=height_cm,
            weight_kg=weight_kg,
            calculated_bmi=calculated_bmi,
            smoker=typer.confirm("Smoker?", default=False),
            diabetes=typer.confirm("Diabetes?", default=False),
            blood_pressure=typer.confirm("Blood pressure history?", default=False),
            heart_ailments=typer.confirm("Heart ailments?", default=False),
            pre_existing_disease=typer.confirm("Pre-existing disease?", default=False),
            other_conditions=_normalize_other_conditions(other_conditions),
        )
        if calculated_bmi is not None:
            print_info(
                cli.console,
                f"Calculated BMI automatically: {calculated_bmi}",
            )

    generated_guest_identifier = f"guest-{mobile_number}"
    generated_idempotency_key = f"quote-{uuid4()}"
    payload = GenerateQuoteInput(
        insurance_type=insurance_type,
        guest_identifier=generated_guest_identifier,
        personal_details=personal_details,
        coverage_details=coverage_details,
        health_details=health_details,
        idempotency_key=generated_idempotency_key,
    )
    print_info(
        cli.console,
        f"Generated guest identifier `{generated_guest_identifier}` and idempotency key `{generated_idempotency_key}` automatically.",
    )
    return payload


def _prompt_optional_float(label: str) -> float | None:
    """Prompt for an optional float value and return None when left blank."""

    raw = typer.prompt(label, default="")
    if not raw:
        return None
    try:
        return float(raw)
    except ValueError as exc:
        raise CLIError(f"{label} must be a number.") from exc


def _prompt_optional_int(label: str) -> int | None:
    """Prompt for an optional integer value and return None when left blank."""

    raw = typer.prompt(label, default="")
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError as exc:
        raise CLIError(f"{label} must be an integer.") from exc


def _normalize_relation(value: str | None) -> str | None:
    """Normalize user-friendly relation text into backend-supported enum values."""

    if value is None:
        return None
    normalized = value.strip().upper()
    if not normalized:
        return None
    aliases = {
        "SELF": "SELF",
        "ME": "SELF",
        "SPOUSE": "SPOUSE",
        "WIFE": "SPOUSE",
        "HUSBAND": "SPOUSE",
        "CHILD": "CHILD",
        "SON": "CHILD",
        "DAUGHTER": "CHILD",
        "PARENT": "PARENT",
        "FATHER": "PARENT",
        "MOTHER": "PARENT",
        "FAMILY": "FAMILY",
    }
    if normalized not in aliases:
        raise CLIError("Relation must be one of: SELF, SPOUSE, CHILD, PARENT, FAMILY.")
    return aliases[normalized]


def _normalize_other_conditions(value: str) -> list[str]:
    """Convert free-form condition input into a clean condition list."""

    normalized = value.strip().lower()
    if normalized in {"", "no", "none", "nil", "na", "n/a"}:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def _resolve_relation(*, insurance_type: str, insured_members: int | None, default_relation: str) -> str | None:
    """Pick a sensible relation automatically for common single-person health applications."""

    if insurance_type == "HEALTH" and insured_members in {None, 1}:
        return "SELF"
    return _normalize_relation(typer.prompt("Relation", default=default_relation))


def _calculate_bmi(*, height_cm: float | None, weight_kg: float | None) -> float | None:
    """Calculate BMI from height and weight when both values are available."""

    if height_cm is None and weight_kg is None:
        return None
    if height_cm is None or weight_kg is None:
        raise CLIError("Height and weight must both be provided for health applications.")
    height_m = height_cm / 100
    if height_m <= 0:
        raise CLIError("Height must be greater than zero.")
    return round(weight_kg / (height_m * height_m), 2)
