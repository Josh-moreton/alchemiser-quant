"""Performance content builder for email templates.

This module handles building HTML content for trading summaries,
order execution reports, and performance metrics.
"""

from typing import Any

from .base import BaseEmailTemplate


class PerformanceBuilder:
    """Builds performance-related HTML content for emails."""

    @staticmethod
    def build_trading_activity(orders: list[dict[str, Any]] | None = None) -> str:
        """Build HTML for trading activity section."""
        if not orders or len(orders) == 0:
            return """
            <div style="margin: 24px 0; padding: 16px; background-color: #F3F4F6; border-radius: 8px; text-align: center;">
                <h3 style="margin: 0 0 8px 0; color: #6B7280; font-size: 18px;">📋 Orders Executed (0)</h3>
                <span style="color: #6B7280; font-style: italic;">No trades executed this session</span>
            </div>
            """

        orders_rows = ""
        for order in orders[:10]:  # Show up to 10 orders
            side = order.get("side", "N/A")
            symbol = order.get("symbol", "N/A")
            qty = order.get("qty", 0)
            estimated_value = order.get("estimated_value", 0)

            # Handle both string and enum values for side
            if hasattr(side, "value"):
                side_str = side.value.upper()
            else:
                side_str = str(side).upper()

            side_color = "#10B981" if side_str == "BUY" else "#EF4444"
            side_emoji = "🟢" if side_str == "BUY" else "🔴"

            orders_rows += f"""
            <tr>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB;">
                    <span style="color: {side_color}; font-weight: 600;">{side_emoji} {side_str}</span>
                </td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; font-weight: 600;">
                    {symbol}
                </td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right;">
                    {qty:.6f}
                </td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right; color: #059669; font-weight: 600;">
                    ${estimated_value:,.2f}
                </td>
            </tr>
            """

        # Calculate totals for summary
        buy_orders = []
        sell_orders = []

        for o in orders:
            side = o.get("side")
            if side:
                if hasattr(side, "value") and side.value and side.value.upper() == "BUY":
                    buy_orders.append(o)
                elif hasattr(side, "value") and side.value and side.value.upper() == "SELL":
                    sell_orders.append(o)
                elif str(side).upper() in ["BUY", "OrderSide.BUY"]:
                    buy_orders.append(o)
                elif str(side).upper() in ["SELL", "OrderSide.SELL"]:
                    sell_orders.append(o)

        total_buy_value = sum(o.get("estimated_value", 0) for o in buy_orders)
        total_sell_value = sum(o.get("estimated_value", 0) for o in sell_orders)

        return f"""
        <div style="margin: 24px 0;">
            <h3 style="margin: 0 0 16px 0; color: #1F2937; font-size: 18px; font-weight: 600;">📋 Orders Executed ({len(orders)})</h3>
            <table style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <thead>
                    <tr style="background-color: #F9FAFB;">
                        <th style="padding: 12px; text-align: left; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">Type</th>
                        <th style="padding: 12px; text-align: left; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">Symbol</th>
                        <th style="padding: 12px; text-align: right; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">Quantity</th>
                        <th style="padding: 12px; text-align: right; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">Estimated Value</th>
                    </tr>
                </thead>
                <tbody>
                    {orders_rows}
                </tbody>
            </table>
            <div style="margin-top: 12px; padding: 12px; background-color: #F3F4F6; border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="color: #6B7280; font-size: 14px;">Summary:</span>
                    <span style="font-weight: 600; color: #1F2937;">{len(orders)} total orders</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <span style="color: #10B981; font-size: 14px;">📈 Purchases:</span>
                    <span style="color: #10B981; font-weight: 600;">${total_buy_value:,.2f}</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #EF4444; font-size: 14px;">📉 Sales:</span>
                    <span style="color: #EF4444; font-weight: 600;">${total_sell_value:,.2f}</span>
                </div>
            </div>
        </div>
        """

    @staticmethod
    def build_trading_summary(trading_summary: dict[str, Any]) -> str:
        """Build enhanced trading summary HTML section."""
        if not trading_summary:
            return BaseEmailTemplate.create_alert_box("Trading summary not available", "warning")

        total_trades = trading_summary.get("total_trades", 0)
        total_buy_value = trading_summary.get("total_buy_value", 0)
        total_sell_value = trading_summary.get("total_sell_value", 0)
        net_value = trading_summary.get("net_value", total_buy_value - total_sell_value)
        buy_orders = trading_summary.get("buy_orders", 0)
        sell_orders = trading_summary.get("sell_orders", 0)

        # Calculate additional metrics
        net_color = "#10B981" if net_value >= 0 else "#EF4444"
        net_sign = "+" if net_value >= 0 else ""

        return f"""
        <div style="margin: 24px 0;">
            <h3 style="margin: 0 0 16px 0; color: #1F2937; font-size: 18px; font-weight: 600;">📊 Trading Summary</h3>
            <div style="background-color: white; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
                    <div style="text-align: center; padding: 16px; background-color: #F8FAFC; border-radius: 8px;">
                        <div style="font-size: 24px; font-weight: 700; color: #1F2937; margin-bottom: 4px;">
                            {total_trades}
                        </div>
                        <div style="font-size: 14px; color: #6B7280;">Total Trades</div>
                    </div>
                    <div style="text-align: center; padding: 16px; background-color: #F0FDF4; border-radius: 8px;">
                        <div style="font-size: 20px; font-weight: 600; color: #10B981; margin-bottom: 4px;">
                            ${total_buy_value:,.0f}
                        </div>
                        <div style="font-size: 14px; color: #6B7280;">{buy_orders} Buy Orders</div>
                    </div>
                    <div style="text-align: center; padding: 16px; background-color: #FEF2F2; border-radius: 8px;">
                        <div style="font-size: 20px; font-weight: 600; color: #EF4444; margin-bottom: 4px;">
                            ${total_sell_value:,.0f}
                        </div>
                        <div style="font-size: 14px; color: #6B7280;">{sell_orders} Sell Orders</div>
                    </div>
                    <div style="text-align: center; padding: 16px; background-color: #F8FAFC; border-radius: 8px; border: 2px solid {net_color};">
                        <div style="font-size: 20px; font-weight: 700; color: {net_color}; margin-bottom: 4px;">
                            {net_sign}${net_value:,.0f}
                        </div>
                        <div style="font-size: 14px; color: #6B7280;">Net Value</div>
                    </div>
                </div>
            </div>
        </div>
        """

    @staticmethod
    def build_strategy_performance(strategy_summary: dict[str, Any]) -> str:
        """Build strategy performance summary."""
        if not strategy_summary:
            return BaseEmailTemplate.create_alert_box(
                "Strategy performance data not available", "warning"
            )

        strategy_cards = ""
        for strategy_name, strategy_data in strategy_summary.items():
            allocation = strategy_data.get("allocation", 0)
            signal = strategy_data.get("signal", "UNKNOWN")
            symbol = strategy_data.get("symbol", "N/A")
            reason = strategy_data.get("reason", "")

            # Determine color scheme based on signal
            if signal == "BUY":
                signal_color = "#10B981"
                signal_bg = "#D1FAE5"
                signal_emoji = "📈"
            elif signal == "SELL":
                signal_color = "#EF4444"
                signal_bg = "#FEE2E2"
                signal_emoji = "📉"
            else:
                signal_color = "#6B7280"
                signal_bg = "#F3F4F6"
                signal_emoji = "⏸️"

            strategy_cards += f"""
            <div style="margin-bottom: 16px; padding: 16px; background-color: white; border-radius: 8px; border-left: 4px solid {signal_color}; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <h4 style="margin: 0; color: #1F2937; font-size: 16px; font-weight: 600;">
                        {strategy_name}
                    </h4>
                    <div style="background-color: {signal_bg}; color: {signal_color}; padding: 4px 12px; border-radius: 20px; font-size: 14px; font-weight: 600;">
                        {signal_emoji} {signal}
                    </div>
                </div>
                <div style="margin-bottom: 8px;">
                    <span style="color: #6B7280; font-size: 14px;">Target: </span>
                    <span style="font-weight: 600; color: #1F2937;">{symbol}</span>
                    <span style="color: #6B7280; font-size: 14px; margin-left: 16px;">Allocation: </span>
                    <span style="font-weight: 600; color: #1F2937;">{allocation:.1%}</span>
                </div>
                {f'<div style="color: #6B7280; font-size: 14px; font-style: italic;">{reason[:100]}...</div>' if reason else ''}
            </div>
            """

        return f"""
        <div style="margin: 24px 0;">
            <h3 style="margin: 0 0 16px 0; color: #1F2937; font-size: 18px; font-weight: 600;">🎯 Strategy Performance</h3>
            {strategy_cards}
        </div>
        """

    # ====== NEUTRAL MODE FUNCTIONS (NO DOLLAR VALUES/PERCENTAGES) ======

    @staticmethod
    def build_trading_activity_neutral(orders: list[dict[str, Any]] | None = None) -> str:
        """Build HTML for trading activity section without dollar values."""
        if not orders or len(orders) == 0:
            return """
            <div style="margin: 24px 0; padding: 16px; background-color: #F3F4F6; border-radius: 8px; text-align: center;">
                <h3 style="margin: 0 0 8px 0; color: #6B7280; font-size: 18px;">📋 Orders Executed (0)</h3>
                <span style="color: #6B7280; font-style: italic;">No trades executed this session</span>
            </div>
            """

        orders_rows = ""
        for order in orders[:10]:  # Show up to 10 orders
            side = order.get("side", "N/A")
            symbol = order.get("symbol", "N/A")
            qty = order.get("qty", 0)

            # Handle both string and enum values for side
            if hasattr(side, "value"):
                side_str = side.value.upper()
            else:
                side_str = str(side).upper()

            side_color = "#10B981" if side_str == "BUY" else "#EF4444"
            side_emoji = "🟢" if side_str == "BUY" else "🔴"

            orders_rows += f"""
            <tr>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB;">
                    <span style="color: {side_color}; font-weight: 600;">{side_emoji} {side_str}</span>
                </td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; font-weight: 600;">
                    {symbol}
                </td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right;">
                    {qty:.6f} shares
                </td>
                <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: center; color: #10B981;">
                    ✅ Executed
                </td>
            </tr>
            """

        # Calculate totals for summary (count only, no dollar amounts)
        buy_orders = []
        sell_orders = []

        for o in orders:
            side = o.get("side")
            if side:
                if hasattr(side, "value") and side.value and side.value.upper() == "BUY":
                    buy_orders.append(o)
                elif hasattr(side, "value") and side.value and side.value.upper() == "SELL":
                    sell_orders.append(o)
                elif str(side).upper() in ["BUY", "OrderSide.BUY"]:
                    buy_orders.append(o)
                elif str(side).upper() in ["SELL", "OrderSide.SELL"]:
                    sell_orders.append(o)

        return f"""
        <div style="margin: 24px 0;">
            <h3 style="margin: 0 0 16px 0; color: #1F2937; font-size: 18px; font-weight: 600;">📋 Orders Executed ({len(orders)})</h3>
            <table style="width: 100%; border-collapse: collapse; background-color: white; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <thead>
                    <tr style="background-color: #F9FAFB;">
                        <th style="padding: 12px; text-align: left; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">Type</th>
                        <th style="padding: 12px; text-align: left; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">Symbol</th>
                        <th style="padding: 12px; text-align: right; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">Quantity</th>
                        <th style="padding: 12px; text-align: center; font-weight: 600; color: #374151; border-bottom: 1px solid #E5E7EB;">Status</th>
                    </tr>
                </thead>
                <tbody>
                    {orders_rows}
                </tbody>
            </table>
            <div style="margin-top: 12px; padding: 12px; background-color: #F3F4F6; border-radius: 8px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="color: #6B7280; font-size: 14px;">Summary:</span>
                    <span style="font-weight: 600; color: #1F2937;">{len(orders)} total orders</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <span style="color: #10B981; font-size: 14px;">📈 Purchases:</span>
                    <span style="color: #10B981; font-weight: 600;">{len(buy_orders)} orders</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <span style="color: #EF4444; font-size: 14px;">📉 Sales:</span>
                    <span style="color: #EF4444; font-weight: 600;">{len(sell_orders)} orders</span>
                </div>
            </div>
        </div>
        """
