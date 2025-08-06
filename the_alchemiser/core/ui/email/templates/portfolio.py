"""Portfolio content builder for email templates.

This module handles building HTML content for portfolio tables,
position summaries, and portfolio allocations.
"""

from typing import Any

from .base import BaseEmailTemplate

# TODO: Phase 10 - Types available for future migration to structured types
# from the_alchemiser.core.types import AccountInfo, ExecutionResult, PositionInfo


class PortfolioBuilder:
    """Builds portfolio-related HTML content for emails."""

    @staticmethod
    def build_positions_table(
        open_positions: list[dict[str, Any]],
    ) -> str:  # TODO: Phase 8 - Migrate to list[PositionInfo]
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
    def build_account_summary(
        account_info: dict[str, Any],
    ) -> str:  # TODO: Phase 8 - Migrate to AccountInfo
        """Build HTML summary of account information."""
        if not account_info:
            return BaseEmailTemplate.create_alert_box("Account information unavailable", "warning")

        equity = float(account_info.get("equity", 0))
        cash = float(account_info.get("cash", 0))

        # Calculate additional metrics if available
        rows = f"""
        <tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB;">
                <span style="font-weight: 600;">Portfolio Value:</span>
            </td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right;">
                ${equity:,.2f}
            </td>
        </tr>
        <tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB;">
                <span style="font-weight: 600;">Cash Available:</span>
            </td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right;">
                ${cash:,.2f}
            </td>
        </tr>
        """

        # Add daily P&L if available
        if "daily_pl" in account_info:
            daily_pl = float(account_info["daily_pl"])
            daily_pl_pct = float(account_info.get("daily_pl_percent", 0))
            pl_color = "#10B981" if daily_pl >= 0 else "#EF4444"
            pl_sign = "+" if daily_pl >= 0 else ""

            rows += f"""
            <tr>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB;">
                    <span style="font-weight: 600;">Daily P&L:</span>
                </td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right; color: {pl_color}; font-weight: 600;">
                    {pl_sign}${daily_pl:.2f} ({pl_sign}{daily_pl_pct:.2%})
                </td>
            </tr>
            """

        return f"""
        <table style="width: 100%; border-collapse: collapse; background-color: #F9FAFB; border-radius: 8px; overflow: hidden;">
            {rows}
        </table>
        """

    @staticmethod
    def build_portfolio_allocation(
        result: Any,
    ) -> str:  # TODO: Phase 8 - Migrate to ExecutionResult
        """Build HTML display of portfolio allocation from execution result."""
        try:
            # Try to get actual final portfolio state first
            if hasattr(result, "final_portfolio_state") and result.final_portfolio_state:
                allocations = result.final_portfolio_state.get("allocations", {})
                if allocations:
                    # Show actual current positions
                    portfolio_lines: list[str] = (
                        []
                    )  # TODO: Phase 10 - Added type annotation for clarity
                    for symbol, data in allocations.items():
                        current_percent = data.get("current_percent", 0)
                        if current_percent > 0.1:  # Only show positions > 0.1%
                            portfolio_lines.append(
                                f"<span style='font-weight: 600;'>{symbol}:</span> {current_percent:.1f}%"
                            )

                    if portfolio_lines:
                        return "<br>".join(portfolio_lines)

            # Fallback to target allocations from consolidated portfolio
            if hasattr(result, "consolidated_portfolio") and result.consolidated_portfolio:
                return "<br>".join(
                    [
                        f"<span style='font-weight: 600;'>{symbol}:</span> {weight:.1%}"
                        for symbol, weight in list(result.consolidated_portfolio.items())[:5]
                    ]
                )

            return "<span style='color: #6B7280; font-style: italic;'>Portfolio data unavailable</span>"
        except Exception as e:
            return f"<span style='color: #EF4444;'>Error loading portfolio: {str(e)}</span>"

    @staticmethod
    def build_closed_positions_pnl(
        account_info: dict[str, Any],
    ) -> str:  # TODO: Phase 8 - Migrate to AccountInfo
        """Build HTML display of closed positions P&L information."""
        if not account_info or not account_info.get("recent_closed_pnl"):
            return ""

        closed_positions = account_info["recent_closed_pnl"]
        if not closed_positions:
            return ""

        # Calculate totals
        total_realized_pnl = sum(pos.get("realized_pnl", 0) for pos in closed_positions)
        total_trades = sum(pos.get("trade_count", 0) for pos in closed_positions)

        # Build rows for each position
        rows = ""
        for position in closed_positions[:10]:  # Show top 10
            symbol = position.get("symbol", "N/A")
            realized_pnl = float(position.get("realized_pnl", 0))
            realized_pnl_pct = float(position.get("realized_pnl_pct", 0))
            trade_count = position.get("trade_count", 0)

            pnl_color = "#10B981" if realized_pnl >= 0 else "#EF4444"
            pnl_sign = "+" if realized_pnl >= 0 else ""

            rows += f"""
            <tr>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; font-weight: 600;">
                    {symbol}
                </td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right; color: {pnl_color}; font-weight: 600;">
                    {pnl_sign}${realized_pnl:.2f}
                </td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right; color: {pnl_color};">
                    {pnl_sign}{realized_pnl_pct:.2%}
                </td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: center;">
                    {trade_count}
                </td>
            </tr>
            """

        # Summary row
        total_color = "#10B981" if total_realized_pnl >= 0 else "#EF4444"
        total_sign = "+" if total_realized_pnl >= 0 else ""

        summary_row = f"""
        <tr style="background-color: #F9FAFB; font-weight: 600;">
            <td style="padding: 12px; border-top: 2px solid #E5E7EB;">Total Realized</td>
            <td style="padding: 12px; text-align: right; color: {total_color}; border-top: 2px solid #E5E7EB;">
                {total_sign}${total_realized_pnl:.2f}
            </td>
            <td style="padding: 12px; border-top: 2px solid #E5E7EB;"></td>
            <td style="padding: 12px; text-align: center; border-top: 2px solid #E5E7EB;">
                {total_trades}
            </td>
        </tr>
        """

        return f"""
        <div style="margin: 24px 0;">
            <h3 style="margin: 0 0 16px 0; color: #1F2937; font-size: 18px; font-weight: 600;">💰 Recent Closed Positions P&L (7 days)</h3>
            <table style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <thead>
                    <tr style="background-color: #F9FAFB;">
                        <th style="padding: 12px; text-align: left; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">Symbol</th>
                        <th style="padding: 12px; text-align: right; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">Realized P&L</th>
                        <th style="padding: 12px; text-align: right; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">P&L %</th>
                        <th style="padding: 12px; text-align: center; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">Trades</th>
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
        open_positions: list[dict[str, Any]],
    ) -> str:  # TODO: Phase 8 - Migrate to list[PositionInfo]
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
        account_info: dict[str, Any],
    ) -> str:  # TODO: Phase 8 - Migrate to AccountInfo
        """Build neutral HTML summary of account information (no dollar amounts)."""
        if not account_info:
            return BaseEmailTemplate.create_alert_box("Account information unavailable", "warning")

        # Get basic account status information
        account_status = account_info.get("status", "UNKNOWN")
        daytrade_count = account_info.get("daytrade_count", 0)

        # Calculate portfolio deployment percentage
        cash = float(account_info.get("cash", 0))
        equity = float(account_info.get("equity", 0))
        portfolio_deployed_pct = 0.0
        if equity > 0:
            portfolio_deployed_pct = ((equity - cash) / equity) * 100

        status_color = "#10B981" if account_status == "ACTIVE" else "#EF4444"

        # Color coding for deployment percentage
        if portfolio_deployed_pct >= 95:
            deployment_color = "#10B981"  # Green for high deployment
            deployment_emoji = "🟢"
        elif portfolio_deployed_pct >= 80:
            deployment_color = "#F59E0B"  # Yellow for moderate deployment
            deployment_emoji = "🟡"
        else:
            deployment_color = "#EF4444"  # Red for low deployment
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
                        {daytrade_count}/3
                    </td>
                </tr>
                <tr>
                    <td style="padding: 16px 20px; border-bottom: 1px solid #E5E7EB;">
                        <span style="font-weight: 600; font-size: 14px;">Portfolio Deployed:</span>
                    </td>
                    <td style="padding: 16px 20px; border-bottom: 1px solid #E5E7EB; text-align: right; color: {deployment_color}; font-weight: 600; font-size: 14px;">
                        {deployment_emoji} {portfolio_deployed_pct:.1f}%
                    </td>
                </tr>
                <tr>
                    <td style="padding: 16px 20px;">
                        <span style="font-weight: 600; font-size: 14px;">Portfolio Status:</span>
                    </td>
                    <td style="padding: 16px 20px; text-align: right; color: #10B981; font-weight: 600; font-size: 14px;">
                        ✅ Active
                    </td>
                </tr>
            </tbody>
        </table>
        """

    @staticmethod
    def build_portfolio_rebalancing_table(result: Any) -> str:
        """Build a portfolio rebalancing summary table for neutral mode (percentages only)."""

        # Get target portfolio from consolidated_portfolio
        target_portfolio = getattr(result, "consolidated_portfolio", {})

        # Get current positions from multiple possible sources
        account_after = getattr(result, "account_info_after", {})
        execution_summary = getattr(result, "execution_summary", {})

        # Try to get portfolio value and positions from different sources
        portfolio_value = 0.0
        current_positions = {}

        # First try account_info_after from execution_summary
        if execution_summary and "account_info_after" in execution_summary:
            account_data = execution_summary["account_info_after"]
            portfolio_value = float(account_data.get("equity", 0)) or float(
                account_data.get("portfolio_value", 0)
            )
            open_positions = account_data.get("open_positions", [])
        # Fallback to direct account_after
        elif account_after:
            portfolio_value = float(account_after.get("equity", 0)) or float(
                account_after.get("portfolio_value", 0)
            )
            open_positions = account_after.get("open_positions", [])
        else:
            open_positions = []

        # Process positions to get current allocations
        for pos in open_positions:
            if isinstance(pos, dict):
                symbol = pos.get("symbol", "")
                market_value = float(pos.get("market_value", 0))
                if symbol and market_value > 0:
                    current_positions[symbol] = market_value

        if not target_portfolio:
            return "<p>No rebalancing data available</p>"

        # Build the table
        table_rows = []

        for symbol in sorted(target_portfolio.keys()):
            target_weight = target_portfolio.get(symbol, 0.0)
            current_value = current_positions.get(symbol, 0.0)
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

    @staticmethod
    def build_neutral_account_summary(account_info: dict[str, Any]) -> str:
        """Build a neutral account summary without financial values."""

        # Extract basic status information
        account_status = account_info.get("status", "UNKNOWN")
        daytrade_count = account_info.get("day_trade_count", 0)

        # For paper trading accounts, override confusing status indicators
        if account_status == "INACTIVE" and daytrade_count >= 10:
            # This is likely a paper trading account misreporting status
            account_status = "ACTIVE (Paper)"
            daytrade_count = 0  # Paper trading doesn't have day trade limits

        # Status color
        status_color = "#10B981" if "ACTIVE" in account_status else "#EF4444"

        # Trading status based on day trades
        if daytrade_count >= 3:
            trading_status = "⚠️ Day Trade Limit Reached"
            trading_color = "#EF4444"
        elif daytrade_count >= 2:
            trading_status = "🟡 Approaching Day Trade Limit"
            trading_color = "#F59E0B"
        else:
            trading_status = "🟢 Trading Available"
            trading_color = "#10B981"

        # Override for paper trading
        if "Paper" in account_status:
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
                        {"N/A (Paper)" if "Paper" in account_status else f"{daytrade_count}/3"}
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
