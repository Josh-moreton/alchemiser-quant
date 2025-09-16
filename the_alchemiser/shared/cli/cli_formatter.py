"""Business Unit: shared | Status: current.

CLI formatting utilities for the trading system.
"""

from __future__ import annotations

import logging
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table
from rich.text import Text

from the_alchemiser.shared.math.num import floats_equal
from the_alchemiser.shared.schemas.common import (
    AllocationComparisonDTO,
    MultiStrategyExecutionResultDTO,
    MultiStrategySummaryDTO,
)
from the_alchemiser.strategy_v2.engines.nuclear import NUCLEAR_SYMBOLS

"""Console formatting utilities for quantitative trading system output using rich."""

# Module logger for consistent logging
logger = logging.getLogger(__name__)

# Style constants to avoid duplication
STYLE_BOLD_CYAN = "bold cyan"
STYLE_BOLD_WHITE = "bold white"
STYLE_BOLD_GREEN = "bold green"


class StrategyType(Protocol):
    """Protocol for strategy type that may have value attribute."""

    def __str__(self) -> str: ...

    @property
    def value(self) -> str: ...


class MoneyLike(Protocol):
    """Protocol for money-like objects."""

    amount: Decimal
    currency: str


def _truncate_table_data(data: list[Any], max_rows: int = 50) -> tuple[list[Any], bool]:
    """Truncate table data if it exceeds maximum rows.

    Args:
        data: List of data rows to potentially truncate
        max_rows: Maximum number of rows to display (default: 50)

    Returns:
        Tuple of (truncated_data, was_truncated)

    """
    if len(data) <= max_rows:
        return data, False
    return data[:max_rows], True


def _add_truncation_notice(table: Table, truncated_count: int, table_type: str) -> None:
    """Add a notice row to table indicating truncation.

    Args:
        table: The Rich table to add the notice to
        truncated_count: Number of rows that were truncated
        table_type: Description of what type of data was truncated

    """
    notice = f"... and {truncated_count} more {table_type}"
    # Add row with notice spanning all columns
    num_columns = len(table.columns)
    row_data = [notice] + [""] * (num_columns - 1)
    table.add_row(*row_data, style="dim italic")


def _extract_indicators_from_signals(strategy_signals: dict[Any, Any]) -> dict[str, dict[str, Any]]:
    """Extract all indicators from strategy signals."""
    all_indicators: dict[str, dict[str, Any]] = {}
    for data in strategy_signals.values():
        if data.get("indicators"):
            all_indicators.update(data["indicators"])
    return all_indicators


def _format_price_string(price: float) -> str:
    """Format price with appropriate decimal places."""
    if price < 10:
        return f"${price:.3f}"
    if price < 100:
        return f"${price:.2f}"
    return f"${price:.1f}"


def _collect_indicator_parts(indicators: dict[str, Any]) -> tuple[list[str], list[str], list[str]]:
    """Collect RSI, MA, and other indicator parts from indicator data."""
    rsi_parts = []
    ma_parts = []
    other_parts = []

    for k, v in indicators.items():
        if k.startswith("rsi_"):
            rsi_parts.append(f"{k.upper()}:{v:.1f}")
        elif k.startswith("ma_"):
            ma_parts.append(f"{k.upper()}:{v:.1f}")
        elif k != "current_price":
            other_parts.append(f"{k}:{v:.2f}")

    return rsi_parts, ma_parts, other_parts


def _get_rsi_level(indicators: dict[str, Any]) -> str:
    """Get RSI level classification (HIGH/MID/LOW)."""
    rsi_10 = indicators.get("rsi_10", indicators.get("rsi_9", 50))
    if rsi_10 > 80:
        return "HIGH"
    if rsi_10 < 30:
        return "LOW"
    return "MID"


def _get_trend_indicator(indicators: dict[str, Any], price: float) -> str:
    """Get trend indicator based on MA200."""
    ma_200 = indicators.get("ma_200")
    if ma_200 and price > 0:
        return "↗" if price > ma_200 else "↘"
    return ""


def _create_market_regime_panel(all_indicators: dict[str, dict[str, Any]]) -> Panel | None:
    """Create market regime panel if SPY data is available."""
    if "SPY" not in all_indicators:
        return None

    spy_data = all_indicators["SPY"]
    spy_price = spy_data.get("current_price", 0)
    spy_ma200 = spy_data.get("ma_200", 0)

    if spy_price > 0 and spy_ma200 > 0:
        regime = (
            "[bold green]BULL MARKET[/bold green]"
            if spy_price > spy_ma200
            else "[bold red]BEAR MARKET[/bold red]"
        )
        return Panel(
            f"Market Regime: {regime} (SPY {spy_price:.1f} vs 200MA {spy_ma200:.1f})",
            style=STYLE_BOLD_WHITE,
            title="Market Regime",
        )
    return None


def render_technical_indicators(
    strategy_signals: dict[Any, Any],
    console: Console | None = None,
) -> None:
    """Render technical indicators as a Rich table.

    Args:
        strategy_signals: Mapping of strategy identifiers to indicator data.
        console: Optional console used for rendering. Creates a new console if ``None``.

    Returns:
        None

    """
    all_indicators = _extract_indicators_from_signals(strategy_signals)

    if not all_indicators:
        (console or Console()).print(
            Panel("No indicator data available", title="TECHNICAL INDICATORS", style="yellow")
        )
        return

    table = Table(title="Technical Indicators", show_lines=True, expand=True, box=None)
    table.add_column("Symbol", style=STYLE_BOLD_CYAN, justify="right")
    table.add_column("Price", style="bold", justify="right")
    table.add_column("RSI", style="magenta", justify="center")
    table.add_column("MA", style="green", justify="center")
    table.add_column("Other", style="white", justify="center")
    table.add_column("Trend", style="bold yellow", justify="center")

    for symbol in sorted(all_indicators.keys()):
        ind = all_indicators[symbol]
        price = ind.get("current_price", 0)
        price_str = _format_price_string(price)

        rsi_parts, ma_parts, other_parts = _collect_indicator_parts(ind)
        rsi_level = _get_rsi_level(ind)
        trend_indicator = _get_trend_indicator(ind, price)

        table.add_row(
            symbol,
            price_str,
            f"{rsi_level} " + ", ".join(rsi_parts) if rsi_parts else "-",
            ", ".join(ma_parts) if ma_parts else "-",
            ", ".join(other_parts) if other_parts else "-",
            trend_indicator or "-",
        )

    c = console or Console()
    c.print(table)

    regime_panel = _create_market_regime_panel(all_indicators)
    if regime_panel:
        c.print(regime_panel)


def _determine_action_style(action: str) -> tuple[str, str]:
    """Determine style and indicator text based on action."""
    if action == "BUY":
        return "green", "BUY"
    if action == "SELL":
        return "red", "SELL"
    return "yellow", "HOLD"


def _build_signal_details(
    allocation: float | int | None, confidence: float | int | None, symbol: str, action: str
) -> list[str]:
    """Build details lines for signal display."""
    details_lines: list[str] = []

    # Add allocation if valid
    if allocation is not None:
        try:
            if isinstance(allocation, int | float):
                details_lines.append(f"Target Allocation: {float(allocation):.1%}")
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to format allocation {allocation}: {e}")

    # Add confidence if valid
    if confidence is not None:
        try:
            if isinstance(confidence, int | float) and 0 <= float(confidence) <= 1:
                details_lines.append(f"Confidence: {float(confidence):.0%}")
        except (ValueError, TypeError) as e:
            logger.debug(f"Failed to format confidence {confidence}: {e}")

    # Expand well-known portfolio symbols for clarity
    if str(symbol) == "UVXY_BTAL_PORTFOLIO" and action == "BUY":
        details_lines.append("Portfolio Components:")
        details_lines.append("• UVXY: 75% (volatility hedge)")
        details_lines.append("• BTAL: 25% (anti-beta hedge)")

    return details_lines


def _create_signal_panel(strategy_type: str | StrategyType, signal: dict[str, Any]) -> Panel:
    """Create a Rich panel for a single strategy signal."""
    action = signal.get("action", "HOLD")
    symbol = signal.get("symbol", "N/A")
    is_multi_symbol = signal.get("is_multi_symbol", False)
    symbols = signal.get("symbols", [])

    # Support both legacy 'reason' and typed 'reasoning'
    reason = signal.get("reason", signal.get("reasoning", "No reason provided"))
    # Prefer new canonical fractional field; fallback to legacy alias
    allocation = signal.get("allocation_weight", signal.get("allocation_percentage"))
    confidence = signal.get("confidence")

    style, indicator = _determine_action_style(action)

    # Handle multi-symbol display for portfolio strategies
    if is_multi_symbol and symbols:
        # For multi-symbol strategies, show all symbols
        header = f"[bold]{indicator} {' + '.join(symbols)}[/bold]"
    else:
        header = f"[bold]{indicator} {symbol}[/bold]"

    details_lines = _build_signal_details(allocation, confidence, symbol, action)

    # Format the detailed explanation with better spacing
    formatted_reason = reason.replace("\n", "\n\n")  # Add extra spacing between sections

    # Combine content sections
    content_sections = [header]
    if details_lines:
        content_sections.append("\n".join(details_lines))
    content_sections.append(formatted_reason)
    content = "\n\n".join(content_sections)

    # Extract nested conditional expression into a statement
    panel_title = strategy_type.value if hasattr(strategy_type, "value") else strategy_type

    return Panel(
        content,
        title=f"{panel_title}",
        style=style,
        padding=(1, 2),  # Add more padding for readability
        expand=False,
    )


def render_strategy_signals(
    strategy_signals: dict[Any, Any],
    console: Console | None = None,
) -> None:
    """Render strategy signals using Rich panels.

    Args:
        strategy_signals: Mapping of strategy identifiers to their signal data.
        console: Optional console used for rendering. A new console is created if ``None``.

    Returns:
        None

    """
    c = console or Console()

    if not strategy_signals:
        c.print(Panel("No strategy signals available", title="STRATEGY SIGNALS", style="yellow"))
        return

    panels: list[Panel] = []
    for strategy_type, signal in strategy_signals.items():
        panel = _create_signal_panel(strategy_type, signal)
        panels.append(panel)

    # Display panels in a column layout for better readability of detailed explanations
    for panel in panels:
        c.print(panel)
        c.print()  # Add spacing between strategy panels


def render_portfolio_allocation(
    portfolio: dict[str, float],
    title: str = "PORTFOLIO ALLOCATION",
    console: Console | None = None,
) -> None:
    """Pretty-print portfolio allocation using rich table."""
    c = console or Console()

    if not portfolio:
        c.print(Panel("No portfolio allocation available", title=title, style="yellow"))
        return

    table = Table(title=title, show_lines=False, expand=True)
    table.add_column("Symbol", style=STYLE_BOLD_CYAN, justify="center")
    table.add_column("Allocation", style=STYLE_BOLD_GREEN, justify="center")
    table.add_column("Visual", style="white", justify="left")

    for symbol, weight in sorted(portfolio.items(), key=lambda x: x[1], reverse=True):
        # Create visual bar
        bar_length = int(weight * 20)  # Scale to 20 chars max
        bar = "█" * bar_length + "░" * (20 - bar_length)

        table.add_row(symbol, f"{weight:.1%}", f"[green]{bar}[/green] {weight:.1%}")

    c.print(table)


def render_orders_executed(
    orders_executed: list[dict[str, Any]],
    console: Console | None = None,
) -> None:
    """Pretty-print trading execution summary."""
    c = console or Console()

    if not orders_executed:
        c.print(Panel("No trades executed", title="TRADING SUMMARY", style="yellow"))
        return

    # Analyze orders
    buy_orders: list[dict[str, Any]] = []
    sell_orders: list[dict[str, Any]] = []

    for order in orders_executed:
        side = order.get("side")
        if side:
            # Handle both string and enum values
            side_value = side.value.upper() if hasattr(side, "value") else str(side).upper()

            if side_value == "BUY":
                buy_orders.append(order)
            elif side_value == "SELL":
                sell_orders.append(order)

    total_buy_value = sum(o.get("estimated_value", 0) for o in buy_orders)
    total_sell_value = sum(o.get("estimated_value", 0) for o in sell_orders)
    net_value = total_buy_value - total_sell_value

    # Create summary table
    table = Table(title="TRADING SUMMARY", show_lines=True, expand=True)
    table.add_column("Type", style="bold", justify="center")
    table.add_column("Orders", style="cyan", justify="center")
    table.add_column("Total Value", style="green", justify="right")

    table.add_row("Buys", str(len(buy_orders)), f"${total_buy_value:,.2f}")
    table.add_row("Sells", str(len(sell_orders)), f"${total_sell_value:,.2f}")
    table.add_row("[bold]Net", f"[bold]{len(orders_executed)}", f"[bold]${net_value:+,.2f}")

    c.print(table)

    # Detailed order list if needed
    if len(orders_executed) <= 10:  # Only show details for small number of orders
        detail_table = Table(title="Order Details", show_lines=False)
        detail_table.add_column("Symbol", style="cyan")
        detail_table.add_column("Side", style="bold")
        detail_table.add_column("Quantity", style="white", justify="right")
        detail_table.add_column("Value", style="green", justify="right")

        for order in orders_executed:
            side = str(order.get("side", "")).replace("OrderSide.", "")
            side_color = "green" if side == "BUY" else "red"

            detail_table.add_row(
                order.get("symbol", "N/A"),
                f"[{side_color}]{side}[/{side_color}]",
                f"{order.get('qty', 0):.6f}",
                f"${order.get('estimated_value', 0):,.2f}",
            )

        c.print(detail_table)


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


def _format_string_value(value: str) -> str | None:
    """Format a string representation of a number."""
    if not value.replace(".", "").replace("-", "").isdigit():
        return None

    try:
        decimal_value = Decimal(value)
        return f"${float(decimal_value):,.2f}"
    except (ValueError, TypeError, InvalidOperation) as e:
        logger.debug(f"Failed to convert string to Decimal {value}: {e}")
        return None


def _format_numeric_value(value: int | float) -> str | None:
    """Format a numeric value for money display."""
    try:
        return f"${float(value):,.2f}"
    except (ValueError, TypeError) as e:
        logger.debug(f"Failed to format numeric value {value}: {e}")
        return None


def _format_money(value: float | int | Decimal | str | MoneyLike) -> str:
    """Format value that may be a Money domain object, Decimal, or raw number.

    Handles:
    - Money domain objects with amount (Decimal) and currency
    - Decimal values directly
    - Float/int values (legacy support)
    - String representations of numbers
    """
    # Try Money domain object path
    if hasattr(value, "amount") and hasattr(value, "currency"):
        result = _format_money_object(value)
        if result is not None:
            return result

    # Try Decimal path
    if isinstance(value, Decimal):
        result = _format_decimal_value(value)
        if result is not None:
            return result

    # Try string conversion path
    if isinstance(value, str):
        result = _format_string_value(value)
        if result is not None:
            return result

    # Try numeric path
    if isinstance(value, int | float):
        result = _format_numeric_value(value)
        if result is not None:
            return result

    return "-"


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

    # Always use typed domain Money display (using typed domain)
    # If account_data contains nested money fields, honor them; otherwise fallback
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
            latest_pl = profit_loss[-1]
            latest_pl_pct = profit_loss_pct[-1] if profit_loss_pct else 0

            pl_color = "green" if latest_pl >= 0 else "red"
            pl_sign = "+" if latest_pl >= 0 else ""

            content_lines.append(
                f"[bold {pl_color}]Total P&L:[/bold {pl_color}] {pl_sign}${latest_pl:,.2f} ({pl_sign}{latest_pl_pct:.2%})"
            )

    content = "\n".join(content_lines)
    c.print(Panel(content, title="ACCOUNT INFO", style=STYLE_BOLD_WHITE))

    # Open positions table if we have positions
    if open_positions:
        # Apply truncation for large position lists
        display_positions, was_truncated = _truncate_table_data(open_positions, max_rows=50)

        positions_table = Table(title="Open Positions", show_lines=True, box=None)
        positions_table.add_column("Symbol", style=STYLE_BOLD_CYAN)
        positions_table.add_column("Qty", style="white", justify="right")
        positions_table.add_column("Avg Price", style="white", justify="right")
        positions_table.add_column("Current Price", style="white", justify="right")
        positions_table.add_column("Market Value", style="white", justify="right")
        positions_table.add_column("Unrealized P&L", style="white", justify="right")

        total_market_value: float = 0.0
        total_unrealized_pl: float = 0.0

        for position in display_positions:
            symbol = position.get("symbol", "N/A")
            qty = float(position.get("qty", 0))
            avg_price = float(position.get("avg_entry_price", 0))
            current_price = float(position.get("current_price", 0))
            market_value = float(position.get("market_value", 0))
            unrealized_pl = float(position.get("unrealized_pl", 0))
            unrealized_plpc = float(position.get("unrealized_plpc", 0))

            total_market_value += market_value
            total_unrealized_pl += unrealized_pl

            # Color coding for P&L
            pl_color = "green" if unrealized_pl >= 0 else "red"
            pl_sign = "+" if unrealized_pl >= 0 else ""

            positions_table.add_row(
                symbol,
                f"{qty:.4f}",
                _format_money(avg_price),
                _format_money(current_price),
                _format_money(market_value),
                f"[{pl_color}]{pl_sign}{_format_money(unrealized_pl)} ({pl_sign}{unrealized_plpc:.2%})[/{pl_color}]",
            )

        # Add totals row
        if len(open_positions) > 1:
            total_pl_color = "green" if total_unrealized_pl >= 0 else "red"
            total_pl_sign = "+" if total_unrealized_pl >= 0 else ""
            total_pl_pct = (
                (total_unrealized_pl / total_market_value) * 100 if total_market_value > 0 else 0
            )

            positions_table.add_row(
                "[bold]TOTAL[/bold]",
                "",
                "",
                "",
                f"[bold]{_format_money(total_market_value)}[/bold]",
                f"[bold {total_pl_color}]{total_pl_sign}{_format_money(total_unrealized_pl)} ({total_pl_sign}{total_pl_pct:.2%})[/bold {total_pl_color}]",
            )

        # Add truncation notice if needed
        if was_truncated:
            truncated_count = len(open_positions) - len(display_positions)
            _add_truncation_notice(positions_table, truncated_count, "positions")

        c.print()
        c.print(positions_table)


def render_header(title: str, subtitle: str = "", console: Console | None = None) -> None:
    """Render a beautiful header for the bot."""
    c = console or Console()

    c.print()
    c.print(Rule(title, style="bold blue"))
    if subtitle:
        c.print(Align.center(f"[italic]{subtitle}[/italic]"))
    c.print()


def render_footer(message: str, *, success: bool = True, console: Console | None = None) -> None:
    """Render a footer message."""
    c = console or Console()

    style = STYLE_BOLD_GREEN if success else "bold red"
    indicator = "SUCCESS" if success else "ERROR"

    c.print()
    c.print(Rule())
    c.print(Align.center(f"[{style}]{indicator}: {message}[/{style}]"))
    c.print()


def _compute_allocation_values_from_dto(
    allocation_comparison: AllocationComparisonDTO, account_info: dict[str, Any]
) -> tuple[dict[str, Decimal], dict[str, Decimal], dict[str, Decimal], Decimal]:
    """Compute allocation values from AllocationComparisonDTO."""
    target_values = allocation_comparison.target_values
    current_values = allocation_comparison.current_values
    deltas = allocation_comparison.deltas

    # Derive portfolio_value from sum of target values if not present
    portfolio_value: Decimal
    try:
        calculated_value = sum(target_values.values(), Decimal("0"))
        if calculated_value <= 0:
            pv_from_account = account_info.get("portfolio_value")
            if pv_from_account is None:
                raise ValueError("Portfolio value is 0 or not available")
            portfolio_value = Decimal(str(pv_from_account))
        else:
            portfolio_value = calculated_value
    except Exception as e:
        pv_from_account = account_info.get("portfolio_value")
        if pv_from_account is None:
            raise ValueError(
                f"Unable to determine portfolio value: {e}. "
                "Portfolio value is required for allocation comparison display."
            ) from e
        portfolio_value = Decimal(str(pv_from_account))

    return target_values, current_values, deltas, portfolio_value


def _compute_allocation_values_on_fly(
    target_portfolio: dict[str, float],
    account_info: dict[str, Any],
    current_positions: dict[str, Any],
) -> tuple[dict[str, Decimal], dict[str, Decimal], dict[str, Decimal], Decimal]:
    """Compute allocation values on-the-fly from raw data."""
    from decimal import Decimal

    pv_from_account = account_info.get("portfolio_value")
    if pv_from_account is None:
        raise ValueError(
            "Portfolio value not available in account info. "
            "Cannot calculate target allocation values without portfolio value."
        )
    portfolio_value = Decimal(str(pv_from_account))
    # Apply 95% reduction to avoid buying power issues with broker constraints
    # This ensures we don't try to use 100% of portfolio value which can
    # exceed available buying power
    effective_portfolio_value = portfolio_value * Decimal("0.95")
    target_values = {
        symbol: effective_portfolio_value * Decimal(str(weight))
        for symbol, weight in target_portfolio.items()
    }
    current_values = {}
    for symbol, pos in current_positions.items():
        if isinstance(pos, dict):
            market_value = float(pos.get("market_value", 0.0))
        else:
            market_value = float(getattr(pos, "market_value", 0.0))
        current_values[symbol] = Decimal(str(market_value))
    deltas = {
        s: (target_values.get(s, Decimal("0")) - current_values.get(s, Decimal("0")))
        for s in set(target_values) | set(current_values)
    }

    return target_values, current_values, deltas, portfolio_value


def _determine_action(percent_diff: float, dollar_diff_float: float) -> str:
    """Determine action color and text based on percentage and dollar differences."""
    if percent_diff > 0.01:
        if dollar_diff_float > 50:
            return "[green]BUY[/green]"
        if dollar_diff_float < -50:
            return "[red]SELL[/red]"
        return "[yellow]REBAL[/yellow]"
    return "[dim]HOLD[/dim]"


def _determine_dollar_color_and_sign(dollar_diff_float: float) -> tuple[str, str]:
    """Determine color and sign for dollar difference display."""
    if dollar_diff_float > 0:
        return "green", "+"
    if dollar_diff_float < 0:
        return "red", ""
    return "dim", ""


def _process_symbol_allocation_row(
    symbol: str,
    target_portfolio: dict[str, float],
    target_values: dict[str, Decimal],
    current_values: dict[str, Decimal],
    deltas: dict[str, Decimal],
    portfolio_value: Decimal,
) -> tuple[str, str, str, str, str]:
    """Process a single symbol allocation row for the allocation table.

    Returns table row data: symbol, target_column, current_column, dollar_diff_column, action_column.
    Extracted to reduce cognitive complexity of render_target_vs_current_allocations.
    """
    target_weight = target_portfolio.get(symbol, 0.0)
    target_value = target_values.get(symbol, Decimal("0"))
    current_value = current_values.get(symbol, Decimal("0"))

    # Calculate current weight with Decimal precision
    try:
        current_weight = float(current_value / portfolio_value) if portfolio_value > 0 else 0.0
    except Exception:
        current_weight = 0.0

    percent_diff = abs(target_weight - current_weight)
    dollar_diff = deltas.get(symbol, Decimal("0"))
    try:
        dollar_diff_float = float(dollar_diff)
    except Exception:
        dollar_diff_float = 0.0

    action = _determine_action(percent_diff, dollar_diff_float)
    dollar_color, dollar_sign = _determine_dollar_color_and_sign(dollar_diff_float)

    # Format the row columns
    target_column = f"{target_weight:.1%}\n[dim]{_format_money(target_value)}[/dim]"
    current_column = f"{current_weight:.1%}\n[dim]{_format_money(current_value)}[/dim]"
    dollar_diff_column = (
        f"[{dollar_color}]{dollar_sign}{_format_money(abs(dollar_diff_float))}[/{dollar_color}]"
    )

    return symbol, target_column, current_column, dollar_diff_column, action


def render_target_vs_current_allocations(
    target_portfolio: dict[str, float],
    account_info: dict[str, Any],
    current_positions: dict[str, Any],
    console: Console | None = None,
    allocation_comparison: AllocationComparisonDTO | None = None,
) -> None:
    """Pretty-print target vs current allocations using optional precomputed Decimal comparison.

    If allocation_comparison provided, expects an AllocationComparisonDTO object with
    target_values, current_values, deltas attributes with Decimal precision.
    Falls back to on-the-fly float computation otherwise.
    """
    c = console or Console()

    if allocation_comparison:
        target_values, current_values, deltas, portfolio_value = (
            _compute_allocation_values_from_dto(allocation_comparison, account_info)
        )
    else:
        target_values, current_values, deltas, portfolio_value = _compute_allocation_values_on_fly(
            target_portfolio, account_info, current_positions
        )

    table = Table(title="Portfolio Rebalancing Summary", show_lines=True, expand=True, box=None)
    table.add_column("Symbol", style=STYLE_BOLD_CYAN, justify="center", width=8)
    table.add_column("Target", style="green", justify="right", width=14)
    table.add_column("Current", style="blue", justify="right", width=14)
    table.add_column("Dollar Diff", style="yellow", justify="right", width=12)
    table.add_column("Action", style="bold", justify="center", width=10)

    all_symbols = set(target_portfolio.keys()) | set(current_positions.keys())
    for symbol in sorted(all_symbols):
        symbol_data = _process_symbol_allocation_row(
            symbol, target_portfolio, target_values, current_values, deltas, portfolio_value
        )
        table.add_row(*symbol_data)

    c.print(table)


def render_execution_plan(
    sell_orders: list[dict[str, Any]],
    buy_orders: list[dict[str, Any]],
    console: Console | None = None,
) -> None:
    """Pretty-print the execution plan before trading."""
    c = console or Console()

    total_sell_proceeds = sum(o.get("estimated_proceeds", 0) for o in sell_orders)
    total_buy_cost = sum(o.get("estimated_cost", 0) for o in buy_orders)

    # Create execution plan table
    table = Table(title="Execution Plan", show_lines=True, expand=True)
    table.add_column("Phase", style="bold", justify="center")
    table.add_column("Orders", style="cyan", justify="center")
    table.add_column("Total Value", style="green", justify="right")
    table.add_column("Details", style="white", justify="left")

    sell_details = ", ".join([f"{o['symbol']} ({o['qty']:.2f})" for o in sell_orders[:3]])
    if len(sell_orders) > 3:
        sell_details += f" +{len(sell_orders) - 3} more"

    buy_details = ", ".join([f"{o['symbol']} ({o['qty']:.2f})" for o in buy_orders[:3]])
    if len(buy_orders) > 3:
        buy_details += f" +{len(buy_orders) - 3} more"

    table.add_row("Sells", str(len(sell_orders)), f"${total_sell_proceeds:,.2f}", sell_details)
    table.add_row("Buys", str(len(buy_orders)), f"${total_buy_cost:,.2f}", buy_details)

    c.print(table)


__all__ = [
    "render_account_info",
    "render_enriched_order_summaries",
    "render_execution_plan",
    "render_footer",
    "render_header",
    "render_multi_strategy_summary",
    "render_multi_strategy_summary_dto",
    "render_orders_executed",
    "render_portfolio_allocation",
    "render_strategy_signals",
    "render_target_vs_current_allocations",
    "render_technical_indicators",
]


def render_enriched_order_summaries(
    orders: list[dict[str, Any]],
    console: Console | None = None,
) -> None:
    """Render enriched order summaries returned by TradingServiceManager.

    Accepts a list of items where each item may be an enriched dict with a 'summary' key
    or already a summary-like dict. Safely formats a concise table.
    """
    c = console or Console()

    if not orders:
        c.print(Panel("No open orders", title="Open Orders (Enriched)", style="yellow"))
        return

    # Normalize to summary dicts
    summaries: list[dict[str, Any]] = []
    for item in orders:
        if isinstance(item, dict) and "summary" in item:
            maybe = item.get("summary")
            if isinstance(maybe, dict):
                summaries.append(maybe)
        elif isinstance(item, dict):
            summaries.append(item)

    if not summaries:
        c.print(Panel("No enriched order summaries available", title="Open Orders", style="yellow"))
        return

    table = Table(title="Open Orders (Enriched)", show_lines=False, expand=True)
    table.add_column("ID", style="dim", justify="left")
    table.add_column("Symbol", style=STYLE_BOLD_CYAN, justify="center")
    table.add_column("Type", style="white", justify="center")
    table.add_column("Qty", style="white", justify="right")
    table.add_column("Limit", style="white", justify="right")
    table.add_column("Status", style="bold", justify="center")
    table.add_column("Created", style="dim", justify="left")

    for s in summaries[:50]:  # cap to avoid very large output
        oid = str(s.get("id", ""))
        short_id = oid[:8] + "…" if len(oid) > 12 else oid
        symbol = str(s.get("symbol", ""))
        otype = str(s.get("type", "")).upper()
        qty = s.get("qty", 0.0)
        try:
            qty_str = f"{float(qty):.6f}"
        except Exception:
            qty_str = "-"
        limit = s.get("limit_price")
        limit_str = _format_money(limit) if limit is not None else "-"
        status = str(s.get("status", "")).upper()
        created = str(s.get("created_at", ""))

        # Determine status color based on order state
        def _get_status_color(order_status: str) -> str:
            """Get color for order status display."""
            if order_status == "FILLED":
                return "green"
            if order_status in {"NEW", "PARTIALLY_FILLED"}:
                return "yellow"
            return "red"
        
        status_color = _get_status_color(status)

        table.add_row(
            short_id,
            symbol,
            otype,
            qty_str,
            limit_str,
            f"[{status_color}]{status}[/{status_color}]",
            created,
        )

    c.print(table)


def _render_orders_executed_table(
    execution_result: MultiStrategyExecutionResultDTO, console: Console
) -> None:
    """Render the orders executed table for multi-strategy summary."""
    orders_table = Table(
        title=f"Orders Executed ({len(execution_result.orders_executed)})", show_lines=False
    )
    orders_table.add_column("Type", style="bold", justify="center")
    orders_table.add_column("Symbol", style="cyan", justify="center")
    orders_table.add_column("Quantity", style="white", justify="right")
    orders_table.add_column("Actual Value", style="green", justify="right")

    for order in execution_result.orders_executed:
        side = order.get("side", "")
        side_value = str(side).upper()
        side_color = "green" if side_value == "BUY" else "red"

        # Calculate actual filled value
        filled_qty = float(order.get("filled_qty", 0))
        filled_avg_price = float(order.get("filled_avg_price", 0) or 0)
        actual_value = filled_qty * filled_avg_price

        # Fall back to estimated value if no filled data available
        if floats_equal(actual_value, 0.0):
            estimated_value = order.get("estimated_value", 0)
            try:
                if isinstance(estimated_value, int | float | str):
                    actual_value = float(estimated_value)
                else:
                    actual_value = 0.0
            except (ValueError, TypeError):
                actual_value = 0.0

        orders_table.add_row(
            f"[{side_color}]{side_value}[/{side_color}]",
            order.get("symbol", ""),
            f"{order.get('qty', 0):.6f}",
            f"${actual_value:.2f}",
        )

    console.print(orders_table)
    console.print()


def _log_no_orders_context(execution_result: MultiStrategyExecutionResultDTO) -> None:
    """Log context when no orders were executed for debugging."""
    logger.warning("=== CLI: DISPLAYING 'PORTFOLIO ALREADY BALANCED' MESSAGE ===")
    logger.warning("CLI: Displaying 'Portfolio already balanced' message")
    logger.warning(f"Execution result success: {execution_result.success}")
    logger.warning(
        f"Number of orders in execution result: {len(execution_result.orders_executed) if execution_result.orders_executed else 0}"
    )

    if hasattr(execution_result, "strategy_signals") and execution_result.strategy_signals:
        logger.warning(
            f"Strategy signals received: {len(execution_result.strategy_signals)} strategies"
        )
        for strategy, signals in execution_result.strategy_signals.items():
            logger.warning(f"  Strategy {strategy}: {signals}")
    else:
        logger.warning("No strategy signals in execution result")

    if (
        hasattr(execution_result, "consolidated_portfolio")
        and execution_result.consolidated_portfolio
    ):
        logger.warning(f"Consolidated portfolio: {execution_result.consolidated_portfolio}")
        total_allocation = sum(execution_result.consolidated_portfolio.values())
        logger.warning(
            f"Total portfolio allocation: {total_allocation:.3f} ({total_allocation * 100:.1f}%)"
        )
    else:
        logger.warning("No consolidated portfolio in execution result")

    logger.warning("*** THIS IS WHERE TRADES MAY BE GETTING LOST ***")


def _build_enriched_account_info(
    execution_result: MultiStrategyExecutionResultDTO, enriched_account: dict[str, Any] | None
) -> dict[str, Any]:
    """Build enriched account dictionary for display."""
    from typing import cast

    from the_alchemiser.shared.value_objects.core_types import EnrichedAccountInfo

    base_account: EnrichedAccountInfo = cast(
        EnrichedAccountInfo, dict(execution_result.account_info_after)
    )
    if enriched_account:
        base_account.update(cast(EnrichedAccountInfo, enriched_account))
    return dict(base_account)


def _extract_and_validate_financial_values(base_account: dict[str, Any]) -> tuple[float, float]:
    """Extract and validate portfolio value and cash from account data."""
    pv_raw = base_account.get("portfolio_value") or base_account.get("equity")
    if pv_raw is None:
        raise ValueError(
            "Portfolio value not available in execution result account info. "
            "Cannot display execution summary without portfolio value."
        )

    cash_raw = base_account.get("cash", 0)

    try:
        pv = float(pv_raw)
    except Exception as e:
        raise ValueError(f"Invalid portfolio value format: {pv_raw}") from e

    try:
        cash = float(cash_raw)
    except Exception:
        cash = 0.0

    return pv, cash


def _append_portfolio_history_to_content(
    base_account: dict[str, Any], account_content: Text
) -> None:
    """Add portfolio history P&L information to account content."""
    from typing import cast

    from the_alchemiser.shared.value_objects.core_types import PortfolioHistoryData

    portfolio_history = base_account.get("portfolio_history")
    if not isinstance(portfolio_history, dict):
        return

    ph: PortfolioHistoryData = cast(PortfolioHistoryData, portfolio_history)
    profit_loss = ph.get("profit_loss", []) or []
    profit_loss_pct = ph.get("profit_loss_pct", []) or []

    if not profit_loss:
        return

    recent_pl = profit_loss[-1]
    recent_pl_pct = profit_loss_pct[-1] if profit_loss_pct else 0
    pl_color = "green" if recent_pl >= 0 else "red"
    pl_sign = "+" if recent_pl >= 0 else ""

    account_content.append(
        f"Recent P&L: {pl_sign}${recent_pl:,.2f} ({pl_sign}{recent_pl_pct * 100:.2f}%)\n",
        style=f"bold {pl_color}",
    )


def _render_account_summary(
    execution_result: MultiStrategyExecutionResultDTO,
    enriched_account: dict[str, Any] | None,
    console: Console,
) -> None:
    """Render account summary section."""
    from rich.panel import Panel
    from rich.text import Text

    base_account = _build_enriched_account_info(execution_result, enriched_account)
    pv, cash = _extract_and_validate_financial_values(base_account)

    account_content = Text()
    account_content.append(f"Portfolio Value: ${pv:,.2f}\n", style=STYLE_BOLD_GREEN)
    account_content.append(f"Cash Balance: ${cash:,.2f}\n", style="bold blue")

    _append_portfolio_history_to_content(base_account, account_content)

    account_panel = Panel(account_content, title="Account Summary", style=STYLE_BOLD_WHITE)
    console.print(account_panel)
    console.print()


def _render_closed_pnl_table(enriched_account: dict[str, Any], console: Console) -> None:
    """Render recent closed positions P&L table."""
    closed_pnl = enriched_account.get("recent_closed_pnl", [])
    if not closed_pnl:
        return

    closed_pnl_table = Table(title="Recent Closed Positions P&L (Last 7 Days)", show_lines=False)
    closed_pnl_table.add_column("Symbol", style=STYLE_BOLD_CYAN, justify="center")
    closed_pnl_table.add_column("Realized P&L", style="bold", justify="right")
    closed_pnl_table.add_column("P&L %", style="bold", justify="right")
    closed_pnl_table.add_column("Trades", style="white", justify="center")

    total_realized_pnl = 0.0

    for position in closed_pnl[:8]:  # Show top 8 in CLI summary
        symbol = position.get("symbol", "N/A")
        realized_pnl = position.get("realized_pnl", 0)
        realized_pnl_pct = position.get("realized_pnl_pct", 0)
        trade_count = position.get("trade_count", 0)

        total_realized_pnl += realized_pnl

        # Color coding for P&L
        pnl_color = "green" if realized_pnl >= 0 else "red"
        pnl_sign = "+" if realized_pnl >= 0 else ""

        closed_pnl_table.add_row(
            symbol,
            f"[{pnl_color}]{pnl_sign}${realized_pnl:,.2f}[/{pnl_color}]",
            f"[{pnl_color}]{pnl_sign}{realized_pnl_pct:.2f}%[/{pnl_color}]",
            str(trade_count),
        )

    # Add total row
    if len(closed_pnl) > 0:
        total_pnl_color = "green" if total_realized_pnl >= 0 else "red"
        total_pnl_sign = "+" if total_realized_pnl >= 0 else ""
        closed_pnl_table.add_row(
            "[bold]TOTAL[/bold]",
            f"[bold {total_pnl_color}]{total_pnl_sign}${total_realized_pnl:,.2f}[/bold {total_pnl_color}]",
            "-",
            "-",
        )

    console.print(closed_pnl_table)
    console.print()


def render_multi_strategy_summary(
    execution_result: MultiStrategyExecutionResultDTO,
    enriched_account: dict[str, Any] | None = None,
    console: Console | None = None,
) -> None:
    """Render a summary of multi-strategy execution results using Rich.

    Args:
        execution_result: The execution result DTO to display
        enriched_account: Optional enriched account info for enhanced display
        console: Optional console for rendering

    """
    from rich.panel import Panel

    c = console or Console()

    if not execution_result.success:
        c.print(
            Panel(
                f"[bold red]Execution failed: {execution_result.execution_summary.pnl_summary if execution_result.execution_summary else 'Unknown error'}[/bold red]",
                title="Execution Result",
                style="red",
            )
        )
        return

    # Portfolio allocation display using existing function
    render_portfolio_allocation(
        execution_result.consolidated_portfolio,
        title="Consolidated Portfolio",
        console=c,
    )
    c.print()

    # Orders executed table
    if execution_result.orders_executed:
        _render_orders_executed_table(execution_result, c)
    else:
        _log_no_orders_context(execution_result)
        no_orders_panel = Panel(
            "[green]Portfolio already balanced - no trades needed[/green]",
            title="Orders Executed",
            style="green",
        )
        c.print(no_orders_panel)
        c.print()

    # Account summary
    if execution_result.account_info_after:
        _render_account_summary(execution_result, enriched_account, c)

    # Recent closed positions P&L table
    if enriched_account:
        _render_closed_pnl_table(enriched_account, c)

    # Success message
    c.print(
        Panel(
            "[bold green]Multi-strategy execution completed successfully[/bold green]",
            title="Execution Complete",
            style="green",
        )
    )


def render_multi_strategy_summary_dto(
    summary: MultiStrategySummaryDTO,
    console: Console | None = None,
) -> None:
    """Render a summary using the new MultiStrategySummaryDTO structure.

    Args:
        summary: The multi-strategy summary DTO containing execution result,
                allocation comparison, and enriched account info
        console: Optional console for rendering

    """
    c = console or Console()

    # Display target vs current allocations with enhanced precision
    if summary.allocation_comparison and summary.execution_result.consolidated_portfolio:
        try:
            # Convert account info from execution result
            account_dict = dict(summary.execution_result.account_info_after)
            current_positions: dict[
                str, Any
            ] = {}  # Extract from final_portfolio_state if available

            render_target_vs_current_allocations(
                summary.execution_result.consolidated_portfolio,
                account_dict,
                current_positions,
                allocation_comparison=summary.allocation_comparison,
                console=c,
            )
        except Exception:
            # Fallback to original function
            render_multi_strategy_summary(
                summary.execution_result,
                summary.enriched_account,
                console=c,
            )
            return

    # Render the main execution summary
    render_multi_strategy_summary(
        summary.execution_result,
        summary.enriched_account,
        console=c,
    )


def _render_account_section(
    account_info: dict[str, Any] | None,
    current_positions: dict[str, Any] | None,
) -> None:
    """Render account information section with error handling."""
    if not account_info:
        return

    try:
        render_account_info(
            {
                "account": account_info,
                "open_positions": list(current_positions.values()) if current_positions else [],
            }
        )
    except Exception as e:
        logger.warning(f"Failed to display account info: {e}")


def _render_allocation_section(
    consolidated_portfolio: dict[str, float],
    account_info: dict[str, Any] | None,
    current_positions: dict[str, Any] | None,
    allocation_comparison: AllocationComparisonDTO | None,
) -> None:
    """Render allocation comparison section with fallback logic."""
    has_allocation_data = consolidated_portfolio and account_info and current_positions is not None

    if has_allocation_data and account_info is not None and current_positions is not None:
        try:
            render_target_vs_current_allocations(
                consolidated_portfolio,
                account_info,
                current_positions,
                allocation_comparison=allocation_comparison,
            )
        except Exception as e:
            logger.warning(f"Failed to display allocation comparison: {e}")
            # Fallback to basic portfolio allocation display
            render_portfolio_allocation(consolidated_portfolio)
    elif consolidated_portfolio:
        # Fallback to basic portfolio allocation display
        render_portfolio_allocation(consolidated_portfolio)


def _render_orders_section(open_orders: list[dict[str, Any]] | None) -> None:
    """Render open orders section with error handling."""
    if not open_orders:
        return

    try:
        render_enriched_order_summaries(open_orders)
    except Exception as e:
        logger.warning(f"Failed to display open orders: {e}")


def render_comprehensive_trading_results(
    strategy_signals: dict[str, Any],
    consolidated_portfolio: dict[str, float],
    account_info: dict[str, Any] | None = None,
    current_positions: dict[str, Any] | None = None,
    allocation_comparison: AllocationComparisonDTO | None = None,
    open_orders: list[dict[str, Any]] | None = None,
    console: Console | None = None,
) -> None:
    """Render comprehensive trading results including signals, account info, and allocations.

    This function consolidates the display logic for trading results.

    Args:
        strategy_signals: Strategy signals dictionary
        consolidated_portfolio: Target portfolio allocation
        account_info: Account information dictionary
        current_positions: Current positions dictionary
        allocation_comparison: AllocationComparisonDTO for allocation comparison analysis
        open_orders: List of open orders
        console: Rich console instance (unused - kept for API compatibility)

    """
    # Display strategy signals
    if strategy_signals:
        render_strategy_signals(strategy_signals, console)

    # Display account information section
    _render_account_section(account_info, current_positions)

    # Display allocation comparison section
    _render_allocation_section(
        consolidated_portfolio, account_info, current_positions, allocation_comparison
    )

    # Display open orders section
    _render_orders_section(open_orders)


def render_strategy_summary(
    strategy_signals: dict[str, Any],
    consolidated_portfolio: dict[str, float],
    allocations: dict[str, float],
    console: Console | None = None,
) -> None:
    """Render strategy allocation summary.

    Args:
        strategy_signals: Strategy signals dictionary
        consolidated_portfolio: Target portfolio allocation
        allocations: Strategy allocation percentages from config
        console: Rich console instance (created if None)

    """
    if console is None:
        console = Console()

    strategy_lines = []

    # Build summary for each strategy
    for strategy_name, allocation in allocations.items():
        if allocation > 0:
            pct = int(allocation * 100)
            # Calculate positions from signals for each strategy
            positions = _count_positions_for_strategy(
                strategy_name, strategy_signals, consolidated_portfolio
            )
            strategy_lines.append(
                f"[bold cyan]{strategy_name.upper()}:[/bold cyan] "
                f"{positions} positions, {pct}% allocation"
            )

    strategy_summary = "\n".join(strategy_lines)

    try:
        from rich.panel import Panel

        console.print(Panel(strategy_summary, title="Strategy Summary", border_style="blue"))
    except ImportError:
        logger.info(f"Strategy Summary:\n{strategy_summary}")


def _count_positions_for_strategy(
    strategy_name: str,
    strategy_signals: dict[str, Any],
    consolidated_portfolio: dict[str, float],
) -> int:
    """Count positions for a specific strategy.

    Args:
        strategy_name: Name of the strategy
        strategy_signals: Strategy signals dictionary
        consolidated_portfolio: Target portfolio allocation

    Returns:
        Number of positions for the strategy

    """
    # Count positions actually allocated to this strategy by examining
    # the strategy signal and how many symbols it targets
    strategy_key = strategy_name.upper()

    # Look for this strategy in the signals
    for signal_key, signal_data in strategy_signals.items():
        if (
            signal_key.upper() == strategy_key or strategy_key in signal_key.upper()
        ) and signal_data.get("action") == "BUY":
            # Check if this is a multi-symbol strategy by looking at consolidated portfolio
            # For nuclear strategy, check known nuclear symbols in the portfolio
            if strategy_name.upper() == "NUCLEAR":
                nuclear_positions = sum(
                    1
                    for symbol in consolidated_portfolio
                    if symbol in NUCLEAR_SYMBOLS and consolidated_portfolio[symbol] > 0
                )
                return nuclear_positions if nuclear_positions > 0 else 1
            return 1

    # Fallback: if strategy not found in signals, return 0
    return 0
