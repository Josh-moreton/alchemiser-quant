#!/usr/bin/env python3
"""Business Unit: utilities; Status: current.

CLI error display utilities for order error classification.

This module extends the existing CLI formatting to display classified order errors
with proper categorization, remediation hints, and visual styling.
"""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from the_alchemiser.domain.trading.errors import OrderError, OrderErrorCategory


def render_order_error(
    error: OrderError,
    console: Console | None = None,
    show_details: bool = True,
    show_remediation: bool = True,
) -> None:
    """Render a single OrderError with rich formatting.

    Args:
        error: The OrderError to display
        console: Console instance for output
        show_details: Whether to show error details
        show_remediation: Whether to show remediation hints

    """
    c = console or Console()

    # Determine color scheme based on category
    category_colors = {
        OrderErrorCategory.VALIDATION: "yellow",
        OrderErrorCategory.LIQUIDITY: "blue",
        OrderErrorCategory.RISK_MANAGEMENT: "red",
        OrderErrorCategory.MARKET_CONDITIONS: "magenta",
        OrderErrorCategory.SYSTEM: "bright_red",
        OrderErrorCategory.CONNECTIVITY: "cyan",
        OrderErrorCategory.AUTHORIZATION: "bright_red",
        OrderErrorCategory.CONFIGURATION: "orange3",
    }

    color = category_colors.get(error.category, "white")

    # Build header with category and code
    header = Text()
    header.append("[", style="dim")
    header.append(error.category.value.upper(), style=f"bold {color}")
    header.append("|", style="dim")
    header.append(error.code.value.upper(), style=f"{color}")
    header.append("]", style="dim")

    if error.is_transient:
        header.append(" (transient)", style="dim green")

    # Build content
    content_lines = [error.message]

    if show_details and error.details:
        content_lines.append("")
        content_lines.append("Details:")
        for key, value in error.details.items():
            content_lines.append(f"  {key}: {value}")

    if error.order_id:
        content_lines.append(f"Order ID: {error.order_id}")

    if show_remediation:
        from the_alchemiser.domain.trading.errors.order_error import get_remediation_hint

        hint = get_remediation_hint(error.code)
        if hint:
            content_lines.append("")
            content_lines.append(f"💡 Remediation: {hint}")

    # Render as panel
    c.print(
        Panel(
            "\n".join(content_lines),
            title=header,
            border_style=color,
            expand=False,
        )
    )


def render_order_errors_table(
    errors: list[OrderError],
    console: Console | None = None,
    title: str = "Order Errors",
) -> None:
    """Render multiple OrderErrors in a table format.

    Args:
        errors: List of OrderErrors to display
        console: Console instance for output
        title: Table title

    """
    c = console or Console()

    if not errors:
        c.print(Panel("No errors to display", title=title, style="green"))
        return

    table = Table(title=title, show_lines=True)
    table.add_column("Category", style="bold", justify="center", width=12)
    table.add_column("Code", style="bold", justify="center", width=20)
    table.add_column("Message", style="white", width=40)
    table.add_column("Order ID", style="dim", justify="center", width=12)
    table.add_column("Transient", style="green", justify="center", width=8)

    for error in errors:
        # Color coding based on category
        if error.category == OrderErrorCategory.VALIDATION:
            category_style = "yellow"
        elif error.category == OrderErrorCategory.RISK_MANAGEMENT:
            category_style = "red"
        elif error.category == OrderErrorCategory.SYSTEM:
            category_style = "bright_red"
        elif error.category == OrderErrorCategory.CONNECTIVITY:
            category_style = "cyan"
        elif error.category == OrderErrorCategory.AUTHORIZATION:
            category_style = "bright_red"
        else:
            category_style = "white"

        # Truncate message if too long
        message = error.message
        if len(message) > 35:
            message = message[:32] + "..."

        # Format order ID
        order_id_str = str(error.order_id)[:8] + "..." if error.order_id else "-"

        table.add_row(
            f"[{category_style}]{error.category.value.upper()}[/{category_style}]",
            f"[{category_style}]{error.code.value.replace('_', ' ').title()}[/{category_style}]",
            message,
            order_id_str,
            "✓" if error.is_transient else "✗",
        )

    c.print(table)


def render_error_summary(
    errors: list[OrderError],
    console: Console | None = None,
) -> None:
    """Render a summary of errors by category.

    Args:
        errors: List of OrderErrors to summarize
        console: Console instance for output

    """
    c = console or Console()

    if not errors:
        c.print(Panel("No errors recorded", title="Error Summary", style="green"))
        return

    # Group errors by category
    by_category: dict[OrderErrorCategory, list[OrderError]] = {}
    for error in errors:
        if error.category not in by_category:
            by_category[error.category] = []
        by_category[error.category].append(error)

    table = Table(title="Error Summary by Category", show_header=True)
    table.add_column("Category", style="bold", justify="left")
    table.add_column("Count", style="bold cyan", justify="center")
    table.add_column("Transient", style="green", justify="center")
    table.add_column("Most Common Code", style="yellow", justify="left")

    for category in OrderErrorCategory:
        errors_in_category = by_category.get(category, [])
        if not errors_in_category:
            continue

        count = len(errors_in_category)
        transient_count = sum(1 for e in errors_in_category if e.is_transient)

        # Find most common code
        code_counts: dict[str, int] = {}
        for error in errors_in_category:
            code = error.code.value
            code_counts[code] = code_counts.get(code, 0) + 1

        most_common_code = max(code_counts.items(), key=lambda x: x[1])[0] if code_counts else "-"

        # Color based on severity
        if category in [OrderErrorCategory.SYSTEM, OrderErrorCategory.AUTHORIZATION]:
            style = "bright_red"
        elif category == OrderErrorCategory.RISK_MANAGEMENT:
            style = "red"
        elif category == OrderErrorCategory.VALIDATION:
            style = "yellow"
        else:
            style = "white"

        table.add_row(
            f"[{style}]{category.value.upper()}[/{style}]",
            str(count),
            f"{transient_count}/{count}",
            most_common_code.replace("_", " ").title(),
        )

    c.print(table)


def format_error_for_notification(error: OrderError) -> dict[str, Any]:
    """Format an OrderError for email/notification systems.

    Args:
        error: The OrderError to format

    Returns:
        Dictionary suitable for notification templates

    """
    from the_alchemiser.domain.trading.errors.order_error import get_remediation_hint

    return {
        "category": error.category.value,
        "code": error.code.value,
        "message": error.message,
        "order_id": str(error.order_id) if error.order_id else None,
        "details": dict(error.details) if error.details else {},
        "is_transient": error.is_transient,
        "timestamp": error.timestamp.isoformat() if error.timestamp else None,
        "remediation_hint": get_remediation_hint(error.code),
        "severity": _get_error_severity(error),
    }


def _get_error_severity(error: OrderError) -> str:
    """Get severity level for an error."""
    if error.category in [OrderErrorCategory.SYSTEM, OrderErrorCategory.AUTHORIZATION]:
        return "HIGH"
    if error.category == OrderErrorCategory.RISK_MANAGEMENT:
        return "MEDIUM"
    if error.category in [OrderErrorCategory.CONNECTIVITY, OrderErrorCategory.MARKET_CONDITIONS]:
        return "LOW" if error.is_transient else "MEDIUM"
    return "LOW"
