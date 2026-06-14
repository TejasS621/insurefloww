"""Rich output helpers for CLI tables, panels, and formatted values."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table


def print_success(console: Console, message: str) -> None:
    """Render a success message with simple visual emphasis."""

    console.print(f"[bold green]{message}[/bold green]")


def print_error(console: Console, message: str) -> None:
    """Render an error message in a clear Rich style."""

    console.print(f"[bold red]{message}[/bold red]")


def print_info(console: Console, message: str) -> None:
    """Render an informational message for command progress or guidance."""

    console.print(f"[cyan]{message}[/cyan]")


def show_kv_table(console: Console, title: str, values: dict[str, Any]) -> None:
    """Render a key-value detail table for a single record."""

    table = Table(title=title, show_header=True, header_style="bold magenta")
    table.add_column("Field", style="bold")
    table.add_column("Value")
    for key, value in values.items():
        table.add_row(str(key), format_value(value))
    console.print(table)


def show_rows_table(console: Console, title: str, columns: list[str], rows: Iterable[dict[str, Any]]) -> None:
    """Render a list of dictionaries as a Rich table."""

    table = Table(title=title, show_header=True, header_style="bold magenta")
    for column in columns:
        table.add_column(column.replace("_", " ").title())
    for row in rows:
        table.add_row(*(format_value(row.get(column)) for column in columns))
    console.print(table)


def show_panel(console: Console, title: str, body: str) -> None:
    """Render a labeled information panel."""

    console.print(Panel.fit(body, title=title))


def format_value(value: Any) -> str:
    """Normalize values into readable display strings for Rich tables."""

    if value is None:
        return "-"
    if isinstance(value, float):
        return f"{value:,.2f}"
    if isinstance(value, list):
        return ", ".join(format_value(item) for item in value) if value else "-"
    return str(value)
