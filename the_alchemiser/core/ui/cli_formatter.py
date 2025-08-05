from typing import Any

from rich.align import Align
from rich.console import Console
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table

# TODO: Phase 13 - Replace dict[Any, Any] with proper CLISignalData
# TODO: Phase 13 - Replace dict[str, Any] with AccountInfo from core.types
# TODO: Phase 13 - Replace dict[str, float] with CLIPortfolioData
# TODO: Phase 13 - Replace list[dict[str, Any]] with list[CLIOrderDisplay]

"""Console formatting utilities for quantitative trading system output using rich."""


def render_technical_indicators(
    strategy_signals: dict[Any, Any],
    console: Console | None = None,  # TODO: Phase 13 - CLISignalData
) -> None:
    """
    Pretty-print technical indicators using rich Table.
    If console is None, creates a new Console and prints directly.
    """
    all_indicators: dict[str, dict[str, Any]] = {}
    for _, data in strategy_signals.items():
        if "indicators" in data and data["indicators"]:
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
            if price > ma_200:
                trend_indicator = "↗"
            else:
                trend_indicator = "↘"

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
    console: Console | None = None,  # TODO: Phase 13 - CLISignalData
) -> None:
    """Pretty-print strategy signals using rich panels with detailed explanations."""
    c = console or Console()

    if not strategy_signals:
        c.print(Panel("No strategy signals available", title="STRATEGY SIGNALS", style="yellow"))
        return

    panels: list[Panel] = []  # TODO: Phase 13 - Use structured type
    for strategy_type, signal in strategy_signals.items():
        action = signal.get("action", "HOLD")
        symbol = signal.get("symbol", "N/A")
        reason = signal.get("reason", "No reason provided")

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

        # Format the detailed explanation with better spacing
        formatted_reason = reason.replace("\n", "\n\n")  # Add extra spacing between sections

        content = f"{header}\n\n{formatted_reason}"
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
    console: Console | None = None,  # TODO: Phase 13 - Use CLIPortfolioData list
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
    console: Console | None = None,  # TODO: Phase 13 - list[CLIOrderDisplay]
) -> None:
    """Pretty-print trading execution summary."""
    c = console or Console()

    if not orders_executed:
        c.print(Panel("No trades executed", title="TRADING SUMMARY", style="yellow"))
        return

    # Analyze orders
    # TODO: Phase 13 - Use proper typing for buy/sell orders
    buy_orders: list[dict[str, Any]] = []  # TODO: Phase 13 - list[CLIOrderDisplay]
    sell_orders: list[dict[str, Any]] = []  # TODO: Phase 13 - list[CLIOrderDisplay]

    for order in orders_executed:
        side = order.get("side")
        if side:
            # Handle both string and enum values
            if hasattr(side, "value"):
                side_value = side.value.upper()
            else:
                side_value = str(side).upper()

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


def render_account_info(
    account_info: dict[str, Any], console: Console | None = None
) -> None:  # TODO: Phase 13 - Use AccountInfo type
    """Render account information including P&L data"""
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

    # Create account summary with P&L
    content_lines = [
        f"[bold green]Portfolio Value:[/bold green] ${float(portfolio_value):,.2f}",
        f"[bold blue]Available Cash:[/bold blue] ${float(cash):,.2f}",
        f"[bold yellow]Buying Power:[/bold yellow] ${float(buying_power):,.2f}",
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
    target_portfolio: dict[str, float],  # TODO: Phase 13 - Use CLIPortfolioData list
    account_info: dict[str, Any],  # TODO: Phase 13 - Use AccountInfo
    current_positions: dict[str, Any],  # TODO: Phase 13 - Use dict[str, PositionInfo]
    console: Console | None = None,
) -> None:
    """Pretty-print target vs current allocations comparison with enhanced Rich table."""
    c = console or Console()

    portfolio_value = account_info.get("portfolio_value", 0.0)

    # Calculate target and current values
    target_values = {
        symbol: portfolio_value * weight for symbol, weight in target_portfolio.items()
    }

    current_values = {
        symbol: float(getattr(pos, "market_value", 0.0))
        for symbol, pos in current_positions.items()
    }

    # Create enhanced comparison table
    table = Table(title="Portfolio Rebalancing Summary", show_lines=True, expand=True, box=None)
    table.add_column("Symbol", style="bold cyan", justify="center", width=8)
    table.add_column("Target", style="green", justify="right", width=14)
    table.add_column("Current", style="blue", justify="right", width=14)
    table.add_column("Dollar Diff", style="yellow", justify="right", width=12)
    table.add_column("Action", style="bold", justify="center", width=10)

    all_symbols = set(target_portfolio.keys()) | set(current_positions.keys())

    for symbol in sorted(all_symbols):
        target_weight = target_portfolio.get(symbol, 0.0)
        target_value = target_values.get(symbol, 0.0)
        current_value = current_values.get(symbol, 0.0)
        current_weight = current_value / portfolio_value if portfolio_value > 0 else 0.0
        percent_diff = abs(target_weight - current_weight)
        dollar_diff = target_value - current_value

        # Determine action based on difference
        if percent_diff > 0.01:  # 1% threshold
            if dollar_diff > 50:
                action = "[green]BUY[/green]"
            elif dollar_diff < -50:
                action = "[red]SELL[/red]"
            else:
                action = "[yellow]REBAL[/yellow]"
        else:
            action = "[dim]HOLD[/dim]"

        # Color coding for dollar difference
        if dollar_diff > 0:
            dollar_color = "green"
            dollar_sign = "+"
        elif dollar_diff < 0:
            dollar_color = "red"
            dollar_sign = ""
        else:
            dollar_color = "dim"
            dollar_sign = ""

        table.add_row(
            symbol,
            f"{target_weight:.1%}\n[dim]${target_value:,.0f}[/dim]",
            f"{current_weight:.1%}\n[dim]${current_value:,.0f}[/dim]",
            f"[{dollar_color}]{dollar_sign}${abs(dollar_diff):,.0f}[/{dollar_color}]",
            action,
        )

    c.print(table)


def render_execution_plan(
    sell_orders: list[dict[str, Any]],  # TODO: Phase 13 - list[CLIOrderDisplay]
    buy_orders: list[dict[str, Any]],  # TODO: Phase 13 - list[CLIOrderDisplay]
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
        sell_details += f" +{len(sell_orders)-3} more"

    buy_details = ", ".join([f"{o['symbol']} ({o['qty']:.2f})" for o in buy_orders[:3]])
    if len(buy_orders) > 3:
        buy_details += f" +{len(buy_orders)-3} more"

    table.add_row("Sells", str(len(sell_orders)), f"${total_sell_proceeds:,.2f}", sell_details)
    table.add_row("Buys", str(len(buy_orders)), f"${total_buy_cost:,.2f}", buy_details)

    c.print(table)


__all__ = [
    "render_technical_indicators",
    "render_strategy_signals",
    "render_portfolio_allocation",
    "render_orders_executed",  # TODO: Phase 13 - Updated function name
    "render_account_info",
    "render_header",
    "render_footer",
    "render_target_vs_current_allocations",
    "render_execution_plan",
]
