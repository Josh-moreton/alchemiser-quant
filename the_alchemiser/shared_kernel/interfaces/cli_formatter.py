"""Business Unit: utilities; Status: current."""

from __future__ import annotations

from typing import Any

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

from the_alchemiser.interfaces.schemas.common import MultiStrategyExecutionResultDTO
from the_alchemiser.domain.shared_kernel import floats_equal

"""Console formatting utilities for quantitative trading system output using rich."""


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
    all_indicators: dict[str, dict[str, Any]] = {}
    for _, data in strategy_signals.items():
        if data.get("indicators"):
            all_indicators.update(data["indicators"])

    if not all_indicators:
        (console or Console()).print(
            Panel("No indicator data available", title="TECHNICAL INDICATORS", style="yellow")
        )
        return

    table = Table(title="Technical Indicators", show_lines=True, expand=True, box=None)
    table.add_column("Symbol", style="bold cyan", justify="right")
    table.add_column("Price", style="bold", justify="right")
    table.add_column("RSI", style="magenta", justify="center")
    table.add_column("MA", style="green", justify="center")
    table.add_column("Other", style="white", justify="center")
    table.add_column("Trend", style="bold yellow", justify="center")

    for symbol in sorted(all_indicators.keys()):
        ind = all_indicators[symbol]
        price = ind.get("current_price", 0)
        # Format price nicely
        if price < 10:
            price_str = f"${price:.3f}"
        elif price < 100:
            price_str = f"${price:.2f}"
        else:
            price_str = f"${price:.1f}"

        # Collect all RSI and MA values
        rsi_parts = []
        ma_parts = []
        for k, v in ind.items():
            if k.startswith("rsi_"):
                rsi_parts.append(f"{k.upper()}:{v:.1f}")
            if k.startswith("ma_"):
                ma_parts.append(f"{k.upper()}:{v:.1f}")
        # Add other indicators if present
        other_parts = []
        for k, v in ind.items():
            if k not in ("current_price",) and not k.startswith("rsi_") and not k.startswith("ma_"):
                other_parts.append(f"{k}:{v:.2f}")

        # RSI indicator for rsi_10 if present
        rsi_10 = ind.get("rsi_10", ind.get("rsi_9", 50))
        rsi_level = ""
        if rsi_10 > 80:
            rsi_level = "HIGH"
        elif rsi_10 < 30:
            rsi_level = "LOW"
        else:
            rsi_level = "MID"

        # Trend indicator for ma_200 if present
        ma_200 = ind.get("ma_200")
        trend_indicator = ""
        if ma_200 and price > 0:
            trend_indicator = "↗" if price > ma_200 else "↘"

        table.add_row(
            symbol,
            price_str,
            f"{rsi_level} " + ", ".join(rsi_parts) if rsi_parts else "-",
            ", ".join(ma_parts) if ma_parts else "-",
            ", ".join(other_parts) if other_parts else "-",
            trend_indicator or "-",
        )

    # Add market regime summary as a panel below the table if SPY is present
    regime_panel = None
    if "SPY" in all_indicators:
        spy_data = all_indicators["SPY"]
        spy_price = spy_data.get("current_price", 0)
        spy_ma200 = spy_data.get("ma_200", 0)
        if spy_price > 0 and spy_ma200 > 0:
            regime = (
                "[bold green]BULL MARKET[/bold green]"
                if spy_price > spy_ma200
                else "[bold red]BEAR MARKET[/bold red]"
            )
            regime_panel = Panel(
                f"Market Regime: {regime} (SPY {spy_price:.1f} vs 200MA {spy_ma200:.1f})",
                style="bold white",
                title="Market Regime",
            )

    c = console or Console()
    c.print(table)
    if regime_panel:
        c.print(regime_panel)


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
        action = signal.get("action", "HOLD")
        symbol = signal.get("symbol", "N/A")
        # Support both legacy 'reason' and typed 'reasoning'
        reason = signal.get("reason", signal.get("reasoning", "No reason provided"))
        # Prefer new canonical fractional field; fallback to legacy alias
        allocation = signal.get("allocation_weight", signal.get("allocation_percentage"))
        confidence = signal.get("confidence")

        # Color code by action
        if action == "BUY":
            style = "green"
            indicator = "BUY"
        elif action == "SELL":
            style = "red"
            indicator = "SELL"
        else:
            style = "yellow"
            indicator = "HOLD"

        # Create header with action and symbol
        header = f"[bold]{indicator} {symbol}[/bold]"

        # Extra details block: allocation/confidence and special symbol expansions
        details_lines: list[str] = []
        try:
            if isinstance(allocation, int | float):
                details_lines.append(f"Target Allocation: {float(allocation):.1%}")
        except Exception:
            pass
        try:
            if isinstance(confidence, int | float) and 0 <= float(confidence) <= 1:
                details_lines.append(f"Confidence: {float(confidence):.0%}")
        except Exception:
            pass

        # Expand well-known portfolio symbols for clarity
        if str(symbol) == "UVXY_BTAL_PORTFOLIO" and action == "BUY":
            details_lines.append("Portfolio Components:")
            details_lines.append("• UVXY: 75% (volatility hedge)")
            details_lines.append("• BTAL: 25% (anti-beta hedge)")

        # Format the detailed explanation with better spacing
        formatted_reason = reason.replace("\n", "\n\n")  # Add extra spacing between sections

        # Combine content sections
        content_sections = [header]
        if details_lines:
            content_sections.append("\n".join(details_lines))
        content_sections.append(formatted_reason)
        content = "\n\n".join(content_sections)
        panel = Panel(
            content,
            title=f"{strategy_type.value if hasattr(strategy_type, 'value') else strategy_type}",
            style=style,
            padding=(1, 2),  # Add more padding for readability
            expand=False,
        )
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
    table.add_column("Symbol", style="bold cyan", justify="center")
    table.add_column("Allocation", style="bold green", justify="center")
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


def _format_money(value: Any) -> str:
    """Format value that may be a Money domain object or raw number."""
    # Domain Money path
    try:
        # Money has amount (Decimal) and currency; access directly when present
        if hasattr(value, "amount") and hasattr(value, "currency"):
            amt = float(value.amount)
            cur = str(value.currency)
            symbol = "$" if cur == "USD" else f"{cur} "
            return f"{symbol}{amt:,.2f}"
    except Exception:
        pass
    # Legacy numeric path
    try:
        return f"${float(value):,.2f}"
    except Exception:
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

    # Account basics
    portfolio_value = account_data.get("portfolio_value", account_data.get("equity", 0))
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
    c.print(Panel(content, title="ACCOUNT INFO", style="bold white"))

    # Open positions table if we have positions
    if open_positions:
        positions_table = Table(title="Open Positions", show_lines=True, box=None)
        positions_table.add_column("Symbol", style="bold cyan")
        positions_table.add_column("Qty", style="white", justify="right")
        positions_table.add_column("Avg Price", style="white", justify="right")
        positions_table.add_column("Current Price", style="white", justify="right")
        positions_table.add_column("Market Value", style="white", justify="right")
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

            # Color coding for P&L
            pl_color = "green" if unrealized_pl >= 0 else "red"
            pl_sign = "+" if unrealized_pl >= 0 else ""

            positions_table.add_row(
                symbol,
                f"{qty:.4f}",
                f"${avg_price:.2f}",
                f"${current_price:.2f}",
                f"${market_value:.2f}",
                f"[{pl_color}]{pl_sign}${unrealized_pl:.2f} ({pl_sign}{unrealized_plpc:.2%})[/{pl_color}]",
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
                f"[bold]${total_market_value:.2f}[/bold]",
                f"[bold {total_pl_color}]{total_pl_sign}${total_unrealized_pl:.2f} ({total_pl_sign}{total_pl_pct:.2%})[/bold {total_pl_color}]",
            )

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


def render_footer(message: str, success: bool = True, console: Console | None = None) -> None:
    """Render a footer message."""
    c = console or Console()

    style = "bold green" if success else "bold red"
    indicator = "SUCCESS" if success else "ERROR"

    c.print()
    c.print(Rule())
    c.print(Align.center(f"[{style}]{indicator}: {message}[/{style}]"))
    c.print()


def render_target_vs_current_allocations(
    target_portfolio: dict[str, float],
    account_info: dict[str, Any],
    current_positions: dict[str, Any],
    console: Console | None = None,
    allocation_comparison: dict[str, Any] | None = None,
) -> None:
    """Pretty-print target vs current allocations using optional precomputed Decimal comparison.

    If allocation_comparison provided, expects keys: target_values, current_values, deltas
    with Decimal values. Falls back to on-the-fly float computation otherwise.
    """
    from decimal import Decimal

    c = console or Console()

    if allocation_comparison:
        target_values = allocation_comparison.get("target_values", {})
        current_values = allocation_comparison.get("current_values", {})
        deltas = allocation_comparison.get("deltas", {})
        # Derive portfolio_value from sum of target values if not present
        try:
            portfolio_value = sum(target_values.values()) or account_info.get(
                "portfolio_value", 0.0
            )
        except Exception:
            portfolio_value = account_info.get("portfolio_value", 0.0)
    else:
        portfolio_value = account_info.get("portfolio_value", 0.0)
        target_values = {
            symbol: portfolio_value * weight for symbol, weight in target_portfolio.items()
        }
        current_values = {}
        for symbol, pos in current_positions.items():
            if isinstance(pos, dict):
                market_value = float(pos.get("market_value", 0.0))
            else:
                market_value = float(getattr(pos, "market_value", 0.0))
            current_values[symbol] = market_value
        deltas = {
            s: (Decimal(str(target_values.get(s, 0))) - Decimal(str(current_values.get(s, 0))))
            for s in set(target_values) | set(current_values)
        }

    table = Table(title="Portfolio Rebalancing Summary", show_lines=True, expand=True, box=None)
    table.add_column("Symbol", style="bold cyan", justify="center", width=8)
    table.add_column("Target", style="green", justify="right", width=14)
    table.add_column("Current", style="blue", justify="right", width=14)
    table.add_column("Dollar Diff", style="yellow", justify="right", width=12)
    table.add_column("Action", style="bold", justify="center", width=10)

    all_symbols = set(target_portfolio.keys()) | set(current_positions.keys())
    for symbol in sorted(all_symbols):
        target_weight = target_portfolio.get(symbol, 0.0)
        target_value = target_values.get(symbol, 0)
        current_value = current_values.get(symbol, 0)
        # Normalize to floats for percentage weight calculation
        try:
            tv_float = float(target_value)
            cv_float = float(current_value)
        except Exception:
            tv_float = 0.0
            cv_float = 0.0
        current_weight = cv_float / float(portfolio_value) if float(portfolio_value) > 0 else 0.0
        percent_diff = abs(target_weight - current_weight)
        dollar_diff = deltas.get(symbol, 0)
        try:
            dollar_diff_float = float(dollar_diff)
        except Exception:
            dollar_diff_float = 0.0

        if percent_diff > 0.01:
            if dollar_diff_float > 50:
                action = "[green]BUY[/green]"
            elif dollar_diff_float < -50:
                action = "[red]SELL[/red]"
            else:
                action = "[yellow]REBAL[/yellow]"
        else:
            action = "[dim]HOLD[/dim]"

        if dollar_diff_float > 0:
            dollar_color = "green"
            dollar_sign = "+"
        elif dollar_diff_float < 0:
            dollar_color = "red"
            dollar_sign = ""
        else:
            dollar_color = "dim"
            dollar_sign = ""

        table.add_row(
            symbol,
            f"{target_weight:.1%}\n[dim]${tv_float:,.0f}[/dim]",
            f"{current_weight:.1%}\n[dim]${cv_float:,.0f}[/dim]",
            f"[{dollar_color}]{dollar_sign}${abs(dollar_diff_float):,.0f}[/{dollar_color}]",
            action,
        )

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
    table.add_column("Symbol", style="bold cyan", justify="center")
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

        status_color = (
            "green"
            if status == "FILLED"
            else ("yellow" if status in {"NEW", "PARTIALLY_FILLED"} else "red")
        )

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
    from rich.table import Table
    from rich.text import Text

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

        c.print(orders_table)
        c.print()
    else:
        no_orders_panel = Panel(
            "[green]Portfolio already balanced - no trades needed[/green]",
            title="Orders Executed",
            style="green",
        )
        c.print(no_orders_panel)
        c.print()

    # Account summary
    if execution_result.account_info_after:
        from typing import cast

        from the_alchemiser.domain.types import EnrichedAccountInfo, PortfolioHistoryData

        # Build enriched account dict for display
        base_account: EnrichedAccountInfo = cast(
            EnrichedAccountInfo, dict(execution_result.account_info_after)
        )
        if enriched_account:
            base_account.update(cast(EnrichedAccountInfo, enriched_account))

        account_content = Text()
        pv_raw = base_account.get("portfolio_value", base_account.get("equity", 0))
        cash_raw = base_account.get("cash", 0)
        try:
            pv = float(pv_raw)
        except Exception:
            pv = 0.0
        try:
            cash = float(cash_raw)
        except Exception:
            cash = 0.0
        account_content.append(f"Portfolio Value: ${pv:,.2f}\n", style="bold green")
        account_content.append(f"Cash Balance: ${cash:,.2f}\n", style="bold blue")

        portfolio_history = base_account.get("portfolio_history")
        if isinstance(portfolio_history, dict):  # runtime safety
            ph: PortfolioHistoryData = portfolio_history  # mypy: treat as PortfolioHistoryData
            profit_loss = ph.get("profit_loss", []) or []
            profit_loss_pct = ph.get("profit_loss_pct", []) or []
            if profit_loss:
                recent_pl = profit_loss[-1]
                recent_pl_pct = profit_loss_pct[-1] if profit_loss_pct else 0
                pl_color = "green" if recent_pl >= 0 else "red"
                pl_sign = "+" if recent_pl >= 0 else ""
                account_content.append(
                    f"Recent P&L: {pl_sign}${recent_pl:,.2f} ({pl_sign}{recent_pl_pct * 100:.2f}%)\n",
                    style=f"bold {pl_color}",
                )

        account_panel = Panel(account_content, title="Account Summary", style="bold white")
        c.print(account_panel)
        c.print()

    # Recent closed positions P&L table
    if enriched_account:
        closed_pnl = enriched_account.get("recent_closed_pnl", [])
        if closed_pnl:
            closed_pnl_table = Table(
                title="Recent Closed Positions P&L (Last 7 Days)", show_lines=False
            )
            closed_pnl_table.add_column("Symbol", style="bold cyan", justify="center")
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

            c.print(closed_pnl_table)
            c.print()

    # Success message
    c.print(
        Panel(
            "[bold green]Multi-strategy execution completed successfully[/bold green]",
            title="Execution Complete",
            style="green",
        )
    )
