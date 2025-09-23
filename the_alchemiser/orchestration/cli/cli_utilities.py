"""Business Unit: orchestration | Status: current.

Essential CLI utilities extracted from legacy cli_formatter.

This module contains only the functions still actively used by the CLI system,
extracted from the large legacy cli_formatter.py file for better maintainability.
"""

from __future__ import annotations

import logging
from decimal import Decimal
from typing import Any, Protocol

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from the_alchemiser.shared.constants import STYLE_BOLD_CYAN, STYLE_BOLD_GREEN

# Module logger
logger = logging.getLogger(__name__)


class MoneyLike(Protocol):
    """Protocol for money-like objects."""

    amount: Decimal
    currency: str


def _format_money_object(value: MoneyLike) -> str | None:
    """Format a Money domain object with amount and currency."""
    try:
        amt = float(value.amount)  # Only for formatting, preserve precision
        cur = str(value.currency)
        symbol = "$" if cur == "USD" else f"{cur} "
        return f"{symbol}{amt:,.2f}"
    except (ValueError, TypeError, AttributeError) as e:
        logger.debug(f"Failed to format Money object {value}: {e}")
        return None


def _format_decimal_value(value: Decimal) -> str | None:
    """Format a Decimal value for money display."""
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError) as e:
        logger.debug(f"Failed to format Decimal {value}: {e}")
        return None


def _format_money(value: float | int | Decimal | str | MoneyLike) -> str:
    """Format various money value types for display."""
    if value is None:
        return "$0.00"

    # Try MoneyLike (domain Money objects with currency)
    if hasattr(value, "amount") and hasattr(value, "currency"):
        result = _format_money_object(value)
        if result:
            return result

    # Try Decimal
    if isinstance(value, Decimal):
        result = _format_decimal_value(value)
        if result:
            return result

    # Fallback to float conversion
    try:
        if not isinstance(value, (int, float, str, Decimal)):
            return str(value)
        float_val = float(value)
        return f"${float_val:,.2f}"
    except (ValueError, TypeError):
        return str(value)


def render_footer(message: str, *, success: bool = True, console: Console | None = None) -> None:
    """Render a footer message."""
    c = console or Console()

    style = STYLE_BOLD_GREEN if success else "bold red"
    indicator = "SUCCESS" if success else "ERROR"

    c.print()
    c.print(Rule())
    c.print(Align.center(f"[{style}]{indicator}: {message}[/{style}]"))
    c.print()


def render_account_info(account_info: dict[str, Any], console: Console | None = None) -> None:
    """Render account information including P&L data."""
    c = console or Console()

    if not account_info:
        c.print(Panel("Account information not available", title="ACCOUNT INFO", style="red"))
        return

    account_data = account_info.get("account", account_info)  # Support both formats
    portfolio_history = account_info.get("portfolio_history", {})
    open_positions = account_info.get("open_positions", [])

    # Account basics - fail fast if portfolio_value not available
    portfolio_value = account_data.get("portfolio_value") or account_data.get("equity")
    if portfolio_value is None:
        raise ValueError(
            "Portfolio value not available in account data. "
            "Check API connection and account status. "
            "Cannot display portfolio information without portfolio value."
        )
    cash = account_data.get("cash", 0)
    buying_power = account_data.get("buying_power", 0)

    # Format money values
    pv_display = _format_money(account_data.get("portfolio_value_money", portfolio_value))
    cash_display = _format_money(account_data.get("cash_money", cash))
    bp_display = _format_money(account_data.get("buying_power_money", buying_power))

    # Create account summary with P&L
    content_lines = [
        f"[bold green]Portfolio Value:[/bold green] {pv_display}",
        f"[bold blue]Available Cash:[/bold blue] {cash_display}",
        f"[bold yellow]Buying Power:[/bold yellow] {bp_display}",
    ]

    # Add P&L from portfolio history if available
    if portfolio_history and "profit_loss" in portfolio_history:
        profit_loss = portfolio_history["profit_loss"]
        profit_loss_pct = portfolio_history["profit_loss_pct"]

        if profit_loss and len(profit_loss) > 0:
            recent_pl = profit_loss[-1]
            recent_pl_pct = profit_loss_pct[-1] if profit_loss_pct else 0

            pl_color = "green" if recent_pl >= 0 else "red"
            pl_sign = "+" if recent_pl > 0 else ""

            content_lines.append(
                f"[bold {pl_color}]Daily P&L:[/bold {pl_color}] "
                f"[{pl_color}]{pl_sign}{_format_money(recent_pl)} ({pl_sign}{recent_pl_pct:.2%})[/{pl_color}]"
            )

    content = Text.from_markup("\n".join(content_lines))

    # Show positions if available
    if open_positions:
        positions_table = Table(title="Current Positions", show_lines=False)
        positions_table.add_column("Symbol", style="cyan")
        positions_table.add_column("Quantity", style="white", justify="right")
        positions_table.add_column("Avg Price", style="white", justify="right")
        positions_table.add_column("Current Price", style="white", justify="right")
        positions_table.add_column("Market Value", style="green", justify="right")
        positions_table.add_column("Unrealized P&L", style="white", justify="right")

        total_market_value: float = 0.0
        total_unrealized_pl: float = 0.0

        for position in open_positions:
            symbol = position.get("symbol", "N/A")
            qty = float(position.get("qty", 0))
            avg_price = float(position.get("avg_entry_price", 0))
            current_price = float(position.get("current_price", 0))
            market_value = float(position.get("market_value", 0))
            unrealized_pl = float(position.get("unrealized_pl", 0))
            unrealized_plpc = float(position.get("unrealized_plpc", 0))

            total_market_value += market_value
            total_unrealized_pl += unrealized_pl

            pl_color = "green" if unrealized_pl >= 0 else "red"
            pl_sign = "+" if unrealized_pl > 0 else ""

            positions_table.add_row(
                symbol,
                f"{qty:.6f}",
                _format_money(avg_price),
                _format_money(current_price),
                _format_money(market_value),
                f"[{pl_color}]{pl_sign}{_format_money(unrealized_pl)} ({pl_sign}{unrealized_plpc:.2%})[/{pl_color}]",
            )

        # Add totals row
        total_pl_color = "green" if total_unrealized_pl >= 0 else "red"
        total_pl_sign = "+" if total_unrealized_pl > 0 else ""
        total_pl_pct = (
            total_unrealized_pl / (total_market_value - total_unrealized_pl)
            if (total_market_value - total_unrealized_pl) != 0
            else 0
        )

        positions_table.add_row(
            "[bold]TOTAL",
            "",
            "",
            "",
            f"[bold]{_format_money(total_market_value)}[/bold]",
            f"[bold {total_pl_color}]{total_pl_sign}{_format_money(total_unrealized_pl)} ({total_pl_sign}{total_pl_pct:.2%})[/bold {total_pl_color}]",
            style="bold",
        )

        c.print(positions_table)

    c.print(Panel(content, title="ACCOUNT SUMMARY", style=STYLE_BOLD_CYAN))
