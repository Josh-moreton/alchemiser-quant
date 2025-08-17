#!/usr/bin/env python3
"""
Monthly Summary Email Template

This module provides email template building for comprehensive monthly trading summaries.
"""

from typing import Any

from .base import BaseEmailTemplate


class MonthlySummaryBuilder:
    """Builds monthly summary email templates."""

    @staticmethod
    def build_monthly_summary_email(summary_data: dict[str, Any]) -> str:
        """
        Build comprehensive monthly summary email.

        Args:
            summary_data: Monthly summary data from MonthlySummaryService

        Returns:
            HTML email content for monthly summary
        """
        month = summary_data.get("month", "Unknown Month")

        # Build content sections
        header = BaseEmailTemplate.get_header("The Alchemiser")
        status_banner = BaseEmailTemplate.get_status_banner(
            f"Monthly Trading Summary - {month}", "Complete", "#3B82F6", "📊"
        )

        # Performance overview
        performance_html = MonthlySummaryBuilder._build_performance_overview(summary_data)

        # Trading activity
        activity_html = MonthlySummaryBuilder._build_trading_activity(summary_data)

        # Strategy performance
        strategy_html = MonthlySummaryBuilder._build_strategy_performance(summary_data)

        # Positions summary
        positions_html = MonthlySummaryBuilder._build_positions_summary(summary_data)

        # Fees summary
        fees_html = MonthlySummaryBuilder._build_fees_summary(summary_data)

        footer = BaseEmailTemplate.get_footer()

        # Combine all content
        content = f"""
        {header}
        {status_banner}
        <tr>
            <td style="padding: 32px 24px; background-color: white;">
                {performance_html}
                {activity_html}
                {strategy_html}
                {positions_html}
                {fees_html}
            </td>
        </tr>
        {footer}
        """

        return BaseEmailTemplate.wrap_content(
            content, f"The Alchemiser - Monthly Summary ({month})"
        )

    @staticmethod
    def _build_performance_overview(summary_data: dict[str, Any]) -> str:
        """Build portfolio performance overview section."""
        performance = summary_data.get("portfolio_performance", {})
        account = summary_data.get("account_summary", {})

        if not performance and not account:
            return BaseEmailTemplate.create_alert_box("Performance data not available", "warning")

        # Extract performance metrics
        start_value = performance.get("start_value", 0)
        end_value = performance.get("end_value", 0)
        total_return = performance.get("total_return", 0)
        total_return_pct = performance.get("total_return_pct", 0)
        max_drawdown_pct = performance.get("max_drawdown_pct", 0)
        trading_days = performance.get("trading_days", 0)

        # Current account values
        portfolio_value = account.get("portfolio_value", end_value)
        cash = account.get("cash", 0)

        # Determine colors
        return_color = "#10B981" if total_return >= 0 else "#EF4444"
        return_sign = "+" if total_return >= 0 else ""

        return f"""
        <div style="margin: 24px 0;">
            <h2 style="color: #1F2937; margin-bottom: 16px; font-size: 20px;">
                📈 Portfolio Performance
            </h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; margin-bottom: 24px;">
                <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #EEF2FF 0%, #E0E7FF 100%); border-radius: 12px; border: 1px solid #C7D2FE;">
                    <div style="font-size: 28px; font-weight: 700; color: #1E40AF; margin-bottom: 8px;">
                        ${portfolio_value:,.0f}
                    </div>
                    <div style="font-size: 14px; color: #6B7280;">Current Portfolio Value</div>
                </div>
                <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, {('#F0FDF4' if total_return >= 0 else '#FEF2F2')} 0%, {('#DCFCE7' if total_return >= 0 else '#FEE2E2')} 100%); border-radius: 12px; border: 1px solid {('#BBF7D0' if total_return >= 0 else '#FECACA')};">
                    <div style="font-size: 24px; font-weight: 700; color: {return_color}; margin-bottom: 8px;">
                        {return_sign}${total_return:,.0f}
                    </div>
                    <div style="font-size: 14px; color: #6B7280;">Monthly Return</div>
                </div>
                <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, {('#F0FDF4' if total_return_pct >= 0 else '#FEF2F2')} 0%, {('#DCFCE7' if total_return_pct >= 0 else '#FEE2E2')} 100%); border-radius: 12px; border: 1px solid {('#BBF7D0' if total_return_pct >= 0 else '#FECACA')};">
                    <div style="font-size: 24px; font-weight: 700; color: {return_color}; margin-bottom: 8px;">
                        {return_sign}{total_return_pct:.1f}%
                    </div>
                    <div style="font-size: 14px; color: #6B7280;">Monthly Return %</div>
                </div>
                <div style="text-align: center; padding: 20px; background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%); border-radius: 12px; border: 1px solid #FCD34D;">
                    <div style="font-size: 20px; font-weight: 600; color: #D97706; margin-bottom: 8px;">
                        {max_drawdown_pct:.1f}%
                    </div>
                    <div style="font-size: 14px; color: #6B7280;">Max Drawdown</div>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 12px;">
                <div style="text-align: center; padding: 16px; background-color: #F9FAFB; border-radius: 8px;">
                    <div style="font-size: 18px; font-weight: 600; color: #1F2937;">${start_value:,.0f}</div>
                    <div style="font-size: 12px; color: #6B7280;">Start Value</div>
                </div>
                <div style="text-align: center; padding: 16px; background-color: #F9FAFB; border-radius: 8px;">
                    <div style="font-size: 18px; font-weight: 600; color: #1F2937;">${end_value:,.0f}</div>
                    <div style="font-size: 12px; color: #6B7280;">End Value</div>
                </div>
                <div style="text-align: center; padding: 16px; background-color: #F9FAFB; border-radius: 8px;">
                    <div style="font-size: 18px; font-weight: 600; color: #1F2937;">${cash:,.0f}</div>
                    <div style="font-size: 12px; color: #6B7280;">Cash</div>
                </div>
                <div style="text-align: center; padding: 16px; background-color: #F9FAFB; border-radius: 8px;">
                    <div style="font-size: 18px; font-weight: 600; color: #1F2937;">{trading_days}</div>
                    <div style="font-size: 12px; color: #6B7280;">Trading Days</div>
                </div>
            </div>
        </div>
        """

    @staticmethod
    def _build_trading_activity(summary_data: dict[str, Any]) -> str:
        """Build trading activity summary section."""
        activity = summary_data.get("trading_activity", {})

        if not activity:
            return BaseEmailTemplate.create_alert_box(
                "Trading activity data not available", "warning"
            )

        total_trades = activity.get("total_trades", 0)
        buy_trades = activity.get("buy_trades", 0)
        sell_trades = activity.get("sell_trades", 0)
        total_buy_volume = activity.get("total_buy_volume", 0)
        total_sell_volume = activity.get("total_sell_volume", 0)
        symbol_count = activity.get("symbol_count", 0)
        symbols_traded = activity.get("symbols_traded", [])

        # Display top symbols
        top_symbols = ", ".join(symbols_traded[:8]) if symbols_traded else "None"
        if len(symbols_traded) > 8:
            top_symbols += f" +{len(symbols_traded) - 8} more"

        return f"""
        <div style="margin: 24px 0;">
            <h2 style="color: #1F2937; margin-bottom: 16px; font-size: 20px;">
                💼 Trading Activity
            </h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-bottom: 20px;">
                <div style="text-align: center; padding: 16px; background-color: #F8FAFC; border-radius: 8px; border: 2px solid #E2E8F0;">
                    <div style="font-size: 24px; font-weight: 700; color: #1F2937; margin-bottom: 4px;">
                        {total_trades}
                    </div>
                    <div style="font-size: 14px; color: #6B7280;">Total Trades</div>
                </div>
                <div style="text-align: center; padding: 16px; background-color: #F0FDF4; border-radius: 8px;">
                    <div style="font-size: 20px; font-weight: 600; color: #10B981; margin-bottom: 4px;">
                        {buy_trades}
                    </div>
                    <div style="font-size: 14px; color: #6B7280;">Buy Orders</div>
                </div>
                <div style="text-align: center; padding: 16px; background-color: #FEF2F2; border-radius: 8px;">
                    <div style="font-size: 20px; font-weight: 600; color: #EF4444; margin-bottom: 4px;">
                        {sell_trades}
                    </div>
                    <div style="font-size: 14px; color: #6B7280;">Sell Orders</div>
                </div>
                <div style="text-align: center; padding: 16px; background-color: #F8FAFC; border-radius: 8px;">
                    <div style="font-size: 20px; font-weight: 600; color: #1F2937; margin-bottom: 4px;">
                        {symbol_count}
                    </div>
                    <div style="font-size: 14px; color: #6B7280;">Symbols Traded</div>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
                <div style="text-align: center; padding: 16px; background-color: #F0FDF4; border-radius: 8px;">
                    <div style="font-size: 18px; font-weight: 600; color: #10B981; margin-bottom: 4px;">
                        ${total_buy_volume:,.0f}
                    </div>
                    <div style="font-size: 14px; color: #6B7280;">Total Buy Volume</div>
                </div>
                <div style="text-align: center; padding: 16px; background-color: #FEF2F2; border-radius: 8px;">
                    <div style="font-size: 18px; font-weight: 600; color: #EF4444; margin-bottom: 4px;">
                        ${total_sell_volume:,.0f}
                    </div>
                    <div style="font-size: 14px; color: #6B7280;">Total Sell Volume</div>
                </div>
            </div>
            <div style="margin-top: 16px; padding: 16px; background-color: #F9FAFB; border-radius: 8px;">
                <div style="font-size: 14px; font-weight: 600; color: #374151; margin-bottom: 8px;">Symbols Traded:</div>
                <div style="font-size: 14px; color: #6B7280; line-height: 1.5;">
                    {top_symbols}
                </div>
            </div>
        </div>
        """

    @staticmethod
    def _build_strategy_performance(summary_data: dict[str, Any]) -> str:
        """Build strategy performance breakdown section."""
        strategy_perf = summary_data.get("strategy_performance", {})
        strategies = strategy_perf.get("strategies", {})

        if not strategies:
            return BaseEmailTemplate.create_alert_box(
                "Strategy performance data not available", "warning"
            )

        total_realized = strategy_perf.get("total_realized_pnl", 0)
        total_unrealized = strategy_perf.get("total_unrealized_pnl", 0)
        total_strategy_pnl = strategy_perf.get("total_strategy_pnl", 0)

        # Build strategy rows
        strategy_rows = ""
        for strategy_name, perf in strategies.items():
            realized_pnl = perf.get("realized_pnl", 0)
            unrealized_pnl = perf.get("unrealized_pnl", 0)
            total_pnl = perf.get("total_pnl", 0)
            allocation_value = perf.get("allocation_value", 0)
            position_count = perf.get("position_count", 0)

            # Colors for P&L
            realized_color = "#10B981" if realized_pnl >= 0 else "#EF4444"
            unrealized_color = "#10B981" if unrealized_pnl >= 0 else "#EF4444"
            total_color = "#10B981" if total_pnl >= 0 else "#EF4444"

            realized_sign = "+" if realized_pnl >= 0 else ""
            unrealized_sign = "+" if unrealized_pnl >= 0 else ""
            total_sign = "+" if total_pnl >= 0 else ""

            strategy_rows += f"""
            <tr style="border-bottom: 1px solid #E5E7EB;">
                <td style="padding: 12px 8px; font-weight: 600; color: #1F2937;">{strategy_name.upper()}</td>
                <td style="padding: 12px 8px; text-align: right; color: {realized_color}; font-weight: 500;">
                    {realized_sign}${realized_pnl:,.0f}
                </td>
                <td style="padding: 12px 8px; text-align: right; color: {unrealized_color}; font-weight: 500;">
                    {unrealized_sign}${unrealized_pnl:,.0f}
                </td>
                <td style="padding: 12px 8px; text-align: right; color: {total_color}; font-weight: 600;">
                    {total_sign}${total_pnl:,.0f}
                </td>
                <td style="padding: 12px 8px; text-align: right; color: #1F2937;">${allocation_value:,.0f}</td>
                <td style="padding: 12px 8px; text-align: right; color: #1F2937;">{position_count}</td>
            </tr>
            """

        # Summary colors
        total_realized_color = "#10B981" if total_realized >= 0 else "#EF4444"
        total_unrealized_color = "#10B981" if total_unrealized >= 0 else "#EF4444"
        total_color = "#10B981" if total_strategy_pnl >= 0 else "#EF4444"

        total_realized_sign = "+" if total_realized >= 0 else ""
        total_unrealized_sign = "+" if total_unrealized >= 0 else ""
        total_pnl_sign = "+" if total_strategy_pnl >= 0 else ""

        return f"""
        <div style="margin: 24px 0;">
            <h2 style="color: #1F2937; margin-bottom: 16px; font-size: 20px;">
                🎯 Strategy Performance
            </h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-bottom: 20px;">
                <div style="text-align: center; padding: 16px; background-color: {('#F0FDF4' if total_realized >= 0 else '#FEF2F2')}; border-radius: 8px;">
                    <div style="font-size: 20px; font-weight: 600; color: {total_realized_color}; margin-bottom: 4px;">
                        {total_realized_sign}${total_realized:,.0f}
                    </div>
                    <div style="font-size: 14px; color: #6B7280;">Total Realized P&L</div>
                </div>
                <div style="text-align: center; padding: 16px; background-color: {('#F0FDF4' if total_unrealized >= 0 else '#FEF2F2')}; border-radius: 8px;">
                    <div style="font-size: 20px; font-weight: 600; color: {total_unrealized_color}; margin-bottom: 4px;">
                        {total_unrealized_sign}${total_unrealized:,.0f}
                    </div>
                    <div style="font-size: 14px; color: #6B7280;">Total Unrealized P&L</div>
                </div>
                <div style="text-align: center; padding: 16px; background-color: {('#F0FDF4' if total_strategy_pnl >= 0 else '#FEF2F2')}; border-radius: 8px; border: 2px solid {total_color};">
                    <div style="font-size: 24px; font-weight: 700; color: {total_color}; margin-bottom: 4px;">
                        {total_pnl_sign}${total_strategy_pnl:,.0f}
                    </div>
                    <div style="font-size: 14px; color: #6B7280;">Total Strategy P&L</div>
                </div>
            </div>
            <div style="overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <thead>
                        <tr style="background-color: #F9FAFB;">
                            <th style="padding: 12px 8px; text-align: left; font-weight: 600; color: #374151; font-size: 14px;">Strategy</th>
                            <th style="padding: 12px 8px; text-align: right; font-weight: 600; color: #374151; font-size: 14px;">Realized P&L</th>
                            <th style="padding: 12px 8px; text-align: right; font-weight: 600; color: #374151; font-size: 14px;">Unrealized P&L</th>
                            <th style="padding: 12px 8px; text-align: right; font-weight: 600; color: #374151; font-size: 14px;">Total P&L</th>
                            <th style="padding: 12px 8px; text-align: right; font-weight: 600; color: #374151; font-size: 14px;">Allocation</th>
                            <th style="padding: 12px 8px; text-align: right; font-weight: 600; color: #374151; font-size: 14px;">Positions</th>
                        </tr>
                    </thead>
                    <tbody>
                        {strategy_rows}
                    </tbody>
                </table>
            </div>
        </div>
        """

    @staticmethod
    def _build_positions_summary(summary_data: dict[str, Any]) -> str:
        """Build current positions summary section."""
        positions = summary_data.get("positions_summary", {})

        if not positions:
            return BaseEmailTemplate.create_alert_box("Positions data not available", "warning")

        total_positions = positions.get("total_positions", 0)
        total_market_value = positions.get("total_market_value", 0)
        total_unrealized_pnl = positions.get("total_unrealized_pnl", 0)
        top_positions = positions.get("top_positions", [])

        # Build position rows for top positions
        position_rows = ""
        for pos in top_positions[:5]:  # Show top 5
            symbol = pos.get("symbol", "")
            qty = pos.get("qty", 0)
            market_value = pos.get("market_value", 0)
            unrealized_pl = pos.get("unrealized_pl", 0)
            current_price = pos.get("current_price", 0)

            pnl_color = "#10B981" if unrealized_pl >= 0 else "#EF4444"
            pnl_sign = "+" if unrealized_pl >= 0 else ""

            position_rows += f"""
            <tr style="border-bottom: 1px solid #E5E7EB;">
                <td style="padding: 10px 8px; font-weight: 600; color: #1F2937;">{symbol}</td>
                <td style="padding: 10px 8px; text-align: right; color: #1F2937;">{qty:,.0f}</td>
                <td style="padding: 10px 8px; text-align: right; color: #1F2937;">${current_price:.2f}</td>
                <td style="padding: 10px 8px; text-align: right; color: #1F2937;">${market_value:,.0f}</td>
                <td style="padding: 10px 8px; text-align: right; color: {pnl_color}; font-weight: 500;">
                    {pnl_sign}${unrealized_pl:,.0f}
                </td>
            </tr>
            """

        unrealized_color = "#10B981" if total_unrealized_pnl >= 0 else "#EF4444"
        unrealized_sign = "+" if total_unrealized_pnl >= 0 else ""

        return f"""
        <div style="margin: 24px 0;">
            <h2 style="color: #1F2937; margin-bottom: 16px; font-size: 20px;">
                📊 Current Positions
            </h2>
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: 16px; margin-bottom: 20px;">
                <div style="text-align: center; padding: 16px; background-color: #F8FAFC; border-radius: 8px; border: 2px solid #E2E8F0;">
                    <div style="font-size: 24px; font-weight: 700; color: #1F2937; margin-bottom: 4px;">
                        {total_positions}
                    </div>
                    <div style="font-size: 14px; color: #6B7280;">Total Positions</div>
                </div>
                <div style="text-align: center; padding: 16px; background-color: #EEF2FF; border-radius: 8px;">
                    <div style="font-size: 20px; font-weight: 600; color: #1E40AF; margin-bottom: 4px;">
                        ${total_market_value:,.0f}
                    </div>
                    <div style="font-size: 14px; color: #6B7280;">Total Market Value</div>
                </div>
                <div style="text-align: center; padding: 16px; background-color: {('#F0FDF4' if total_unrealized_pnl >= 0 else '#FEF2F2')}; border-radius: 8px;">
                    <div style="font-size: 20px; font-weight: 600; color: {unrealized_color}; margin-bottom: 4px;">
                        {unrealized_sign}${total_unrealized_pnl:,.0f}
                    </div>
                    <div style="font-size: 14px; color: #6B7280;">Unrealized P&L</div>
                </div>
            </div>
            {f'''
            <div style="overflow-x: auto;">
                <table style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <thead>
                        <tr style="background-color: #F9FAFB;">
                            <th style="padding: 12px 8px; text-align: left; font-weight: 600; color: #374151; font-size: 14px;">Symbol</th>
                            <th style="padding: 12px 8px; text-align: right; font-weight: 600; color: #374151; font-size: 14px;">Quantity</th>
                            <th style="padding: 12px 8px; text-align: right; font-weight: 600; color: #374151; font-size: 14px;">Price</th>
                            <th style="padding: 12px 8px; text-align: right; font-weight: 600; color: #374151; font-size: 14px;">Market Value</th>
                            <th style="padding: 12px 8px; text-align: right; font-weight: 600; color: #374151; font-size: 14px;">Unrealized P&L</th>
                        </tr>
                    </thead>
                    <tbody>
                        {position_rows}
                    </tbody>
                </table>
            </div>
            ''' if position_rows else '<div style="text-align: center; padding: 20px; color: #6B7280;">No positions to display</div>'}
        </div>
        """

    @staticmethod
    def _build_fees_summary(summary_data: dict[str, Any]) -> str:
        """Build fees and costs summary section."""
        fees = summary_data.get("fees_and_costs", {})

        if not fees:
            return ""

        total_fees = fees.get("total_fees", 0)
        note = fees.get("note", "")

        return f"""
        <div style="margin: 24px 0;">
            <h2 style="color: #1F2937; margin-bottom: 16px; font-size: 20px;">
                💰 Fees & Costs
            </h2>
            <div style="text-align: center; padding: 20px; background-color: #F0FDF4; border-radius: 12px; border: 1px solid #BBF7D0;">
                <div style="font-size: 28px; font-weight: 700; color: #10B981; margin-bottom: 8px;">
                    ${total_fees:.2f}
                </div>
                <div style="font-size: 16px; color: #374151; margin-bottom: 8px;">Total Fees</div>
                {f'<div style="font-size: 14px; color: #6B7280; font-style: italic;">{note}</div>' if note else ''}
            </div>
        </div>
        """
