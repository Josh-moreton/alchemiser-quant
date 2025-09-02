"""Business Unit: portfolio assessment & management; Status: current.

Portfolio content builder for email templates.

Builds HTML content for portfolio tables, position summaries, allocations, and
neutral-mode representations. This version removes the ad-hoc ExtendedAccountInfo
in favour of existing domain types and on-the-fly derivations (daily P&L, etc.).
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol, cast, runtime_checkable

from the_alchemiser.shared.value_objects.core_types import AccountInfo, EnrichedAccountInfo, PositionInfo
from the_alchemiser.interfaces.schemas.common import MultiStrategyExecutionResultDTO
from the_alchemiser.interfaces.schemas.execution import ExecutionResultDTO

from .base import BaseEmailTemplate


@runtime_checkable
class ExecutionSummaryLike(Protocol):  # pragma: no cover - structural typing helper
    """Minimal protocol abstraction for execution summary display.

    Avoids tight coupling to concrete DTO class names; any object supplying the
    accessed attributes will render. This supports forward evolution (e.g.
    future domain ExecutionAggregate model) without widespread refactors.
    """

    execution_summary: dict[str, Any]


ExecutionLike = (
    ExecutionResultDTO
    | MultiStrategyExecutionResultDTO
    | Mapping[str, Any]
    | ExecutionSummaryLike
    | Any
)


def _normalise_result(result: ExecutionLike) -> dict[str, Any]:
    """Return a plain dict for an execution result (handles TypedDict/Pydantic/mapping/object)."""
    # Pydantic DTO
    if isinstance(result, MultiStrategyExecutionResultDTO):  # pragma: no branch
        try:
            return result.model_dump()
        except Exception:  # pragma: no cover - defensive
            return {}

    # Any mapping (includes plain dict, TypedDict at runtime, or custom mapping)
    if isinstance(result, Mapping):  # pragma: no branch
        return dict(result)

    # Fallback: pull known attributes off an object-like container
    extracted: dict[str, Any] = {}
    for attr in (
        "final_portfolio_state",
        "execution_summary",
        "consolidated_portfolio",
        "account_info_after",
        "account_info_before",
        "orders_executed",
        "positions",
        "final_positions",
    ):
        value = getattr(result, attr, None)
        if value is not None:
            extracted[attr] = value
    return extracted


class PortfolioBuilder:
    """Builds portfolio-related HTML content for emails."""

    @staticmethod
    def build_positions_table(open_positions: list[PositionInfo]) -> str:
        """Build HTML table for open positions."""
        if not open_positions:
            return BaseEmailTemplate.create_alert_box("No open positions", "info")

        total_unrealized_pl = 0.0
        positions_rows = ""

        for position in open_positions[:10]:  # Show top 10 positions
            symbol = position.get("symbol", "N/A")
            market_value = float(position.get("market_value", 0))
            unrealized_pl = float(position.get("unrealized_pl", 0))
            unrealized_plpc = float(position.get("unrealized_plpc", 0))

            total_unrealized_pl += unrealized_pl

            pl_color = "#10B981" if unrealized_pl >= 0 else "#EF4444"
            pl_sign = "+" if unrealized_pl >= 0 else ""

            positions_rows += f"""
            <tr>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; font-weight: 600;">
                    {symbol}
                </td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right;">
                    ${market_value:,.0f}
                </td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right; color: {pl_color}; font-weight: 600;">
                    {pl_sign}${unrealized_pl:.2f}
                </td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right; color: {pl_color};">
                    {pl_sign}{unrealized_plpc:.2%}
                </td>
            </tr>
            """

        total_pl_color = "#10B981" if total_unrealized_pl >= 0 else "#EF4444"
        total_pl_sign = "+" if total_unrealized_pl >= 0 else ""

        return f"""
        <table style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <thead>
                <tr style="background-color: #F9FAFB;">
                    <th style="padding: 12px; text-align: left; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">Symbol</th>
                    <th style="padding: 12px; text-align: right; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">Value</th>
                    <th style="padding: 12px; text-align: right; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">P&L</th>
                    <th style="padding: 12px; text-align: right; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">P&L %</th>
                </tr>
            </thead>
            <tbody>
                {positions_rows}
                <tr style="background-color: #F9FAFB; font-weight: 600;">
                    <td style="padding: 12px; border-top: 2px solid #E5E7EB;">Total Unrealized</td>
                    <td style="padding: 12px; border-top: 2px solid #E5E7EB;"></td>
                    <td style="padding: 12px; text-align: right; color: {total_pl_color}; border-top: 2px solid #E5E7EB;">
                        {total_pl_sign}${total_unrealized_pl:.2f}
                    </td>
                    <td style="padding: 12px; border-top: 2px solid #E5E7EB;"></td>
                </tr>
            </tbody>
        </table>
        """

    @staticmethod
    def build_account_summary(account_info: AccountInfo | EnrichedAccountInfo) -> str:
        """Build HTML summary of account information using Decimal for money.

        Derives daily P&L from equity - last_equity if available.
        """
        try:
            raw_equity = account_info.get("equity", 0)
            raw_cash = account_info.get("cash", 0)
            raw_last_equity = account_info.get("last_equity", 0)
            equity = Decimal(str(raw_equity))
            cash = Decimal(str(raw_cash))
            last_equity = Decimal(str(raw_last_equity))
        except (InvalidOperation, TypeError):
            return BaseEmailTemplate.create_alert_box("Account information unavailable", "warning")

        daily_pl: Decimal | None = None
        daily_pl_pct: Decimal | None = None
        if last_equity > Decimal("0"):
            daily_pl = equity - last_equity
            if last_equity != 0:
                daily_pl_pct = daily_pl / last_equity

        rows = f"""
        <tr>
            <td style=\"padding: 8px 12px; border-bottom: 1px solid #E5E7EB;\">
                <span style=\"font-weight: 600;\">Portfolio Value:</span>
            </td>
            <td style=\"padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right;\">
                ${float(equity):,.2f}
            </td>
        </tr>
        <tr>
            <td style=\"padding: 8px 12px; border-bottom: 1px solid #E5E7EB;\">
                <span style=\"font-weight: 600;\">Cash Available:</span>
            </td>
            <td style=\"padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right;\">
                ${float(cash):,.2f}
            </td>
        </tr>
        """

        if daily_pl is not None and daily_pl_pct is not None:
            pl_color = "#10B981" if daily_pl >= 0 else "#EF4444"
            pl_sign = "+" if daily_pl >= 0 else ""
            rows += f"""
            <tr>
                <td style=\"padding: 8px 12px; border-bottom: 1px solid #E5E7EB;\">
                    <span style=\"font-weight: 600;\">Daily P&L:</span>
                </td>
                <td style=\"padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right; color: {pl_color}; font-weight: 600;\">
                    {pl_sign}${float(daily_pl):,.2f} ({pl_sign}{float(daily_pl_pct):.2%})
                </td>
            </tr>
            """

        return f"<table style='width: 100%; border-collapse: collapse; background-color: #F9FAFB; border-radius: 8px; overflow: hidden;'>{rows}</table>"

    @staticmethod
    def build_portfolio_allocation(result: ExecutionLike) -> str:
        """Build HTML display of portfolio allocation.

        Precedence:
        1. final_portfolio_state.allocations.current_percent
        2. top-level consolidated_portfolio (MultiStrategyExecutionResultDTO)
        3. execution_summary.consolidated_portfolio
        """
        data = _normalise_result(result)
        try:
            final_portfolio_state = data.get("final_portfolio_state") or {}
            if final_portfolio_state:
                allocations = final_portfolio_state.get("allocations", {})
                portfolio_lines: list[str] = []
                for symbol, info in allocations.items():
                    current_percent = info.get("current_percent", 0)
                    if current_percent and current_percent > 0.1:
                        portfolio_lines.append(
                            f"<span style='font-weight: 600;'>{symbol}:</span> {current_percent:.1f}%"
                        )
                if portfolio_lines:
                    return "<br>".join(portfolio_lines)

            top_consolidated = data.get("consolidated_portfolio", {}) or {}
            if top_consolidated:
                return "<br>".join(
                    [
                        f"<span style='font-weight: 600;'>{symbol}:</span> {weight:.1%}"
                        for symbol, weight in list(top_consolidated.items())[:5]
                    ]
                )

            exec_summary = data.get("execution_summary", {}) or {}
            summary_consolidated = exec_summary.get("consolidated_portfolio", {})
            if summary_consolidated:
                return "<br>".join(
                    [
                        f"<span style='font-weight: 600;'>{symbol}:</span> {weight:.1%}"
                        for symbol, weight in list(summary_consolidated.items())[:5]
                    ]
                )
            return "<span style='color: #6B7280; font-style: italic;'>Portfolio data unavailable</span>"
        except Exception as e:  # pragma: no cover - defensive path
            return f"<span style='color: #EF4444;'>Error loading portfolio: {e}</span>"

    @staticmethod
    def build_closed_positions_pnl(
        account_info: AccountInfo | EnrichedAccountInfo,
    ) -> str:
        """Build HTML display of closed positions P&L information."""
        if not account_info or "recent_closed_pnl" not in account_info:
            return ""
        enriched = cast(EnrichedAccountInfo, account_info)
        closed_positions = enriched["recent_closed_pnl"]
        if not closed_positions:
            return ""

        total_realized_pnl = sum(pos.get("realized_pnl", 0) for pos in closed_positions)
        total_trades = sum(pos.get("trade_count", 0) for pos in closed_positions)

        rows = ""
        for position in closed_positions[:10]:
            symbol = position.get("symbol", "N/A")
            realized_pnl = float(position.get("realized_pnl", 0))
            realized_pnl_pct = float(position.get("realized_pnl_pct", 0))
            trade_count = position.get("trade_count", 0)
            pnl_color = "#10B981" if realized_pnl >= 0 else "#EF4444"
            pnl_sign = "+" if realized_pnl >= 0 else ""
            rows += f"""
            <tr>
                <td style=\"padding: 8px 12px; border-bottom: 1px solid #E5E7EB; font-weight: 600;\">{symbol}</td>
                <td style=\"padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right; color: {pnl_color}; font-weight: 600;\">{pnl_sign}${realized_pnl:.2f}</td>
                <td style=\"padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right; color: {pnl_color};\">{pnl_sign}{realized_pnl_pct:.2%}</td>
                <td style=\"padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: center;\">{trade_count}</td>
            </tr>
            """

        total_color = "#10B981" if total_realized_pnl >= 0 else "#EF4444"
        total_sign = "+" if total_realized_pnl >= 0 else ""
        summary_row = f"""
        <tr style=\"background-color: #F9FAFB; font-weight: 600;\">
            <td style=\"padding: 12px; border-top: 2px solid #E5E7EB;\">Total Realized</td>
            <td style=\"padding: 12px; text-align: right; color: {total_color}; border-top: 2px solid #E5E7EB;\">{total_sign}${total_realized_pnl:.2f}</td>
            <td style=\"padding: 12px; border-top: 2px solid #E5E7EB;\"></td>
            <td style=\"padding: 12px; text-align: center; border-top: 2px solid #E5E7EB;\">{total_trades}</td>
        </tr>
        """
        return f"""
        <div style=\"margin: 24px 0;\">
            <h3 style=\"margin: 0 0 16px 0; color: #1F2937; font-size: 18px; font-weight: 600;\">💰 Recent Closed Positions P&L (7 days)</h3>
            <table style=\"width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);\">
                <thead>
                    <tr style=\"background-color: #F9FAFB;\">
                        <th style=\"padding: 12px; text-align: left; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;\">Symbol</th>
                        <th style=\"padding: 12px; text-align: right; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;\">Realized P&L</th>
                        <th style=\"padding: 12px; text-align: right; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;\">P&L %</th>
                        <th style=\"padding: 12px; text-align: center; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;\">Trades</th>
                    </tr>
                </thead>
                <tbody>
                    {rows}
                    {summary_row}
                </tbody>
            </table>
        </div>
        """

    # ====== NEUTRAL MODE FUNCTIONS (NO DOLLAR VALUES/PERCENTAGES) ======

    @staticmethod
    def build_positions_table_neutral(
        open_positions: list[PositionInfo],
    ) -> str:
        """Build neutral-styled HTML table for open positions."""
        if not open_positions:
            return BaseEmailTemplate.create_alert_box("No open positions", "info")

        positions_rows = ""

        for position in open_positions[:10]:  # Show top 10 positions
            symbol = position.get("symbol", "N/A")
            qty = float(position.get("qty", 0))

            positions_rows += f"""
            <tr>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; font-weight: 600;">
                    {symbol}
                </td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right;">
                    {qty:.4f} shares
                </td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: center; color: #10B981;">
                    ✅ Open
                </td>
            </tr>
            """

        return f"""
        <table style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <thead>
                <tr style="background-color: #F9FAFB;">
                    <th style="padding: 12px; text-align: left; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">Symbol</th>
                    <th style="padding: 12px; text-align: right; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">Quantity</th>
                    <th style="padding: 12px; text-align: center; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">Status</th>
                </tr>
            </thead>
            <tbody>
                {positions_rows}
            </tbody>
        </table>
        """

    @staticmethod
    def build_account_summary_neutral(
        account_info: AccountInfo | EnrichedAccountInfo,
    ) -> str:
        """Neutral account summary without dollar values; shows status & usage.

        Uses day_trades_remaining from AccountInfo and derives used count.
        """
        account_status = account_info.get("status", "UNKNOWN")
        remaining = account_info.get("day_trades_remaining")
        used_str = "—"
        if isinstance(remaining, int) and 0 <= remaining <= 3:
            used = 3 - remaining
            used_str = f"{used}/3"

        status_color = "#10B981" if account_status == "ACTIVE" else "#EF4444"

        try:
            equity = Decimal(str(account_info.get("equity", 0)))
            cash = Decimal(str(account_info.get("cash", 0)))
            deployed_pct = (
                ((equity - cash) / equity) * Decimal("100") if equity > 0 else Decimal("0")
            )
        except (InvalidOperation, TypeError):
            deployed_pct = Decimal("0")

        if deployed_pct >= 95:
            deployment_color = "#10B981"
            deployment_emoji = "🟢"
        elif deployed_pct >= 80:
            deployment_color = "#F59E0B"
            deployment_emoji = "🟡"
        else:
            deployment_color = "#EF4444"
            deployment_emoji = "🔴"

        return f"""
        <table style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin: 16px 0;">
            <tbody>
                <tr>
                    <td style="padding: 16px 20px; border-bottom: 1px solid #E5E7EB;">
                        <span style="font-weight: 600; font-size: 14px;">Account Status:</span>
                    </td>
                    <td style="padding: 16px 20px; border-bottom: 1px solid #E5E7EB; text-align: right; color: {status_color}; font-weight: 600; font-size: 14px;">
                        {account_status}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 16px 20px; border-bottom: 1px solid #E5E7EB;">
                        <span style="font-weight: 600; font-size: 14px;">Day Trades Used:</span>
                    </td>
                    <td style="padding: 16px 20px; border-bottom: 1px solid #E5E7EB; text-align: right; font-size: 14px;">
                        {used_str}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 16px 20px; border-bottom: 1px solid #E5E7EB;">
                        <span style="font-weight: 600; font-size: 14px;">Portfolio Deployed:</span>
                    </td>
                    <td style="padding: 16px 20px; border-bottom: 1px solid #E5E7EB; text-align: right; color: {deployment_color}; font-weight: 600; font-size: 14px;">
                        {deployment_emoji} {float(deployed_pct):.1f}%
                    </td>
                </tr>
            </tbody>
        </table>
        """

    @staticmethod
    def build_portfolio_rebalancing_table(result: ExecutionLike) -> str:
        """Build a portfolio rebalancing summary (percentages only)."""
        data = _normalise_result(result)
        execution_summary = data.get("execution_summary", {})
        target_portfolio = (
            data.get("consolidated_portfolio")
            or execution_summary.get("consolidated_portfolio", {})
            or {}
        )

        if not target_portfolio:
            return "<p>No target portfolio data available</p>"

        # Use the same logic as CLI - import the utility functions
        try:
            from the_alchemiser.services.account.account_utils import (
                extract_current_position_values,
            )

            # Try multiple sources for positions and account data
            account_after = data.get("account_info_after", {})
            final_portfolio_state = data.get("final_portfolio_state")

            # Try different methods to get current positions data
            current_positions: dict[str, Any] = {}

            # Method 1: Fresh positions data
            if final_portfolio_state and final_portfolio_state.get("current_positions"):
                current_positions = final_portfolio_state["current_positions"]

            # Method 2: account_after open_positions
            elif isinstance(account_after, dict) and account_after.get("open_positions"):
                open_positions = account_after.get("open_positions", [])
                current_positions = {}
                if isinstance(open_positions, list):
                    for pos in open_positions:
                        if isinstance(pos, dict) and pos.get("symbol"):
                            current_positions[pos["symbol"]] = pos

            # Method 3: final_positions attribute
            elif data.get("final_positions"):
                current_positions = data["final_positions"]

            # Method 4: positions attribute
            elif data.get("positions"):
                current_positions = data["positions"]

            # Method 5: execution_summary positions
            elif execution_summary and "positions" in execution_summary:
                current_positions = execution_summary["positions"]

            portfolio_value = 0.0
            if isinstance(account_after, dict):
                try:
                    portfolio_value = float(account_after.get("portfolio_value", 0)) or float(
                        account_after.get("equity", 0)
                    )
                except (TypeError, ValueError):
                    portfolio_value = 0.0

            # If we have positions, extract current values
            current_values: dict[str, float] = {}
            if current_positions:
                try:
                    current_values = extract_current_position_values(current_positions)
                except Exception:
                    # Try manual extraction if utility function fails
                    for symbol, pos in current_positions.items():
                        if isinstance(pos, dict):
                            try:
                                current_values[symbol] = float(pos.get("market_value", 0))
                            except (ValueError, TypeError):
                                current_values[symbol] = 0.0

            # Calculate total portfolio value from positions if not available
            # Avoid direct float equality; treat very small portfolio_value as zero
            if portfolio_value <= 1e-9 and current_values:
                portfolio_value = sum(current_values.values())

            # Build the table
            table_rows = []

            for symbol in sorted(target_portfolio.keys()):
                target_weight = target_portfolio.get(symbol, 0.0)
                current_value = current_values.get(symbol, 0.0)
                current_weight = (current_value / portfolio_value) if portfolio_value > 0 else 0.0

                weight_diff = target_weight - current_weight

                # Determine action
                if abs(weight_diff) < 0.01:  # Less than 1% difference
                    action = "HOLD"
                    action_color = "#6B7280"
                elif weight_diff > 0:
                    action = "BUY"
                    action_color = "#10B981"
                else:
                    action = "SELL"
                    action_color = "#EF4444"

                table_rows.append(
                    f"""
                    <tr>
                        <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; font-weight: 600; color: #1F2937;">
                            {symbol}
                        </td>
                        <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; text-align: center; color: #059669;">
                            {target_weight:.1%}
                        </td>
                        <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; text-align: center; color: #374151;">
                            {current_weight:.1%}
                        </td>
                        <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; text-align: center; font-weight: 600; color: {action_color};">
                            {action}
                        </td>
                    </tr>
                """
                )

            table_content = "".join(table_rows)

            return f"""
            <table style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin: 16px 0;">
                <thead>
                    <tr style="background-color: #F9FAFB;">
                        <th style="padding: 12px 16px; text-align: left; font-weight: 600; color: #374151; border-bottom: 2px solid #E5E7EB;">
                            Symbol
                        </th>
                        <th style="padding: 12px 16px; text-align: center; font-weight: 600; color: #374151; border-bottom: 2px solid #E5E7EB;">
                            Target %
                        </th>
                        <th style="padding: 12px 16px; text-align: center; font-weight: 600; color: #374151; border-bottom: 2px solid #E5E7EB;">
                            Current %
                        </th>
                        <th style="padding: 12px 16px; text-align: center; font-weight: 600; color: #374151; border-bottom: 2px solid #E5E7EB;">
                            Action
                        </th>
                    </tr>
                </thead>
                <tbody>
                    {table_content}
                </tbody>
            </table>
            """

        except Exception as e:
            # Enhanced debug information
            debug_info = (
                f'<div style="font-size: 12px; color: #666; margin: 10px 0;"><strong>Debug Information:</strong><br/>'
                f"• Target portfolio: {bool(target_portfolio)}<br/>"
                f"• account_after: {bool(account_after)}<br/>"
                f"• execution_summary: {bool(execution_summary)}<br/>"
                f"• final_portfolio_state: {bool(final_portfolio_state)}<br/>"
                f"• Error: {e}</div>"
            )
            return f"<p>Error loading portfolio data. Check logs for details.</p>{debug_info}"

    @staticmethod
    def build_neutral_account_summary(account_info: AccountInfo | EnrichedAccountInfo) -> str:
        """Build a neutral account summary without financial values."""
        # Extract basic status information
        account_status: str = account_info.get("status", "UNKNOWN")
        daytrade_count = account_info.get("day_trade_count", 0)

        # For paper trading accounts, override confusing status indicators
        if (
            account_status == "INACTIVE"
            and isinstance(daytrade_count, int)
            and daytrade_count >= 10
        ):
            # This is likely a paper trading account misreporting status
            account_status = "ACTIVE (Paper)"
            daytrade_count = 0  # Paper trading doesn't have day trade limits

        # Status color
        status_color = "#10B981" if "ACTIVE" in str(account_status) else "#EF4444"

        # Trading status based on day trades
        trading_status = "🟢 Trading Available"
        trading_color = "#10B981"

        if isinstance(daytrade_count, int):
            if daytrade_count >= 3:
                trading_status = "⚠️ Day Trade Limit Reached"
                trading_color = "#EF4444"
            elif daytrade_count >= 2:
                trading_status = "🟡 Approaching Day Trade Limit"
                trading_color = "#F59E0B"

        # Override for paper trading
        if "Paper" in str(account_status):
            trading_status = "🟢 Paper Trading (No Limits)"
            trading_color = "#10B981"

        return f"""
        <table style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin: 16px 0;">
            <tbody>
                <tr>
                    <td style="padding: 16px 20px; border-bottom: 1px solid #E5E7EB;">
                        <span style="font-weight: 600; font-size: 14px;">Account Status:</span>
                    </td>
                    <td style="padding: 16px 20px; border-bottom: 1px solid #E5E7EB; text-align: right; color: {status_color}; font-weight: 600; font-size: 14px;">
                        {account_status}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 16px 20px; border-bottom: 1px solid #E5E7EB;">
                        <span style="font-weight: 600; font-size: 14px;">Day Trades Used:</span>
                    </td>
                    <td style="padding: 16px 20px; border-bottom: 1px solid #E5E7EB; text-align: right; font-size: 14px;">
                        {"N/A (Paper)" if "Paper" in str(account_status) else f"{daytrade_count}/3"}
                    </td>
                </tr>
                <tr>
                    <td style="padding: 16px 20px;">
                        <span style="font-weight: 600; font-size: 14px;">Trading Status:</span>
                    </td>
                    <td style="padding: 16px 20px; text-align: right; color: {trading_color}; font-weight: 600; font-size: 14px;">
                        {trading_status}
                    </td>
                </tr>
            </tbody>
        </table>
        """

    @staticmethod
    def build_orders_table_neutral(orders: list[Any]) -> str:
        """Build a neutral orders table without financial values."""
        if not orders:
            return """
            <div style="text-align: center; padding: 20px; color: #6B7280;">
                <p>No orders executed</p>
            </div>
            """

        # Start building the table
        table_html = """
        <table style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1); margin: 16px 0;">
            <thead>
                <tr style="background-color: #F9FAFB;">
                    <th style="padding: 12px 16px; text-align: left; font-weight: 600; color: #374151; border-bottom: 2px solid #E5E7EB;">
                        Action
                    </th>
                    <th style="padding: 12px 16px; text-align: left; font-weight: 600; color: #374151; border-bottom: 2px solid #E5E7EB;">
                        Symbol
                    </th>
                    <th style="padding: 12px 16px; text-align: center; font-weight: 600; color: #374151; border-bottom: 2px solid #E5E7EB;">
                        Quantity
                    </th>
                    <th style="padding: 12px 16px; text-align: center; font-weight: 600; color: #374151; border-bottom: 2px solid #E5E7EB;">
                        Status
                    </th>
                </tr>
            </thead>
            <tbody>
        """

        for order in orders:
            # Extract order details safely
            side = str(order.get("side", "")).upper()
            symbol = str(order.get("symbol", ""))
            qty = order.get("qty", 0)
            status = str(order.get("status", "unknown")).upper()

            # Determine colors and formatting
            if side == "BUY":
                action_color = "#10B981"  # Green
                action_emoji = "📈"
            elif side == "SELL":
                action_color = "#EF4444"  # Red
                action_emoji = "📉"
            else:
                action_color = "#6B7280"  # Gray
                action_emoji = "📊"

            # Status colors
            if status in ["FILLED", "COMPLETE"]:
                status_color = "#10B981"  # Green
                status_display = f"✅ {status}"
            elif status in ["PARTIAL", "PARTIALLY_FILLED"]:
                status_color = "#F59E0B"  # Orange
                status_display = f"🔄 {status}"
            elif status in ["PENDING", "NEW", "ACCEPTED"]:
                status_color = "#3B82F6"  # Blue
                status_display = f"⏳ {status}"
            elif status in ["CANCELLED", "CANCELED", "REJECTED"]:
                status_color = "#EF4444"  # Red
                status_display = f"❌ {status}"
            else:
                status_color = "#6B7280"  # Gray
                status_display = f"i {status}"

            # Format quantity display
            if isinstance(qty, int | float) and qty != 0:
                qty_display = f"{qty:.2f}" if qty >= 1 else f"{qty:.6f}".rstrip("0").rstrip(".")
            else:
                qty_display = "—"

            table_html += f"""
                <tr>
                    <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; font-weight: 600; color: {action_color};">
                        {action_emoji} {side}
                    </td>
                    <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; font-weight: 600; color: #1F2937;">
                        {symbol}
                    </td>
                    <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; text-align: center; color: #374151;">
                        {qty_display}
                    </td>
                    <td style="padding: 12px 16px; border-bottom: 1px solid #E5E7EB; text-align: center; color: {status_color}; font-weight: 600;">
                        {status_display}
                    </td>
                </tr>
            """

        table_html += """
            </tbody>
        </table>
        """

        return table_html
