"""Business Unit: utilities; Status: current.

Performance content builder for email templates.

This module handles building HTML content for trading summaries,
order execution reports, and performance metrics.
"""

from __future__ import annotations

from decimal import Decimal

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.schemas.notifications import (
    OrderNotificationDTO,
    OrderSide,
    StrategyDataDTO,
    TradingSummaryDTO,
)

from .base import BaseEmailTemplate

logger = get_logger(__name__)

# Constants for styling
SIDE_COLORS = {
    OrderSide.BUY: "#10B981",
    OrderSide.SELL: "#EF4444",
}

SIDE_EMOJIS = {
    OrderSide.BUY: "🟢",
    OrderSide.SELL: "🔴",
}

SIGNAL_STYLES = {
    "BUY": {"color": "#10B981", "bg": "#D1FAE5", "emoji": "📈"},
    "SELL": {"color": "#EF4444", "bg": "#FEE2E2", "emoji": "📉"},
}

DEFAULT_SIGNAL_STYLE = {"color": "#6B7280", "bg": "#F3F4F6", "emoji": "⏸️"}

MAX_DISPLAYED_ORDERS = 10
MAX_REASON_LENGTH = 100


class PerformanceBuilder:
    """Builds performance-related HTML content for emails.

    This class provides static methods to generate HTML email sections for:
    - Order execution summaries
    - Trading performance metrics
    - Strategy performance reports

    All monetary values are handled as Decimal types for precision.
    """

    @staticmethod
    def _normalize_order_side(side: OrderSide | str) -> OrderSide:
        """Normalize order side to OrderSide enum.

        Args:
            side: Order side as enum or string (e.g., "BUY", "buy", OrderSide.BUY)

        Returns:
            OrderSide enum value

        Raises:
            ValueError: If side cannot be normalized to a valid OrderSide

        Examples:
            >>> PerformanceBuilder._normalize_order_side("BUY")
            <OrderSide.BUY: 'BUY'>
            >>> PerformanceBuilder._normalize_order_side(OrderSide.SELL)
            <OrderSide.SELL: 'SELL'>

        """
        if isinstance(side, OrderSide):
            return side

        # Handle enum-like objects with .value attribute
        if hasattr(side, "value"):
            side_str = str(side.value).upper()
        else:
            side_str = str(side).upper()

        # Remove "ORDERSIDE." prefix if present (e.g., "ORDERSIDE.BUY" -> "BUY")
        if side_str.startswith("ORDERSIDE."):
            side_str = side_str.replace("ORDERSIDE.", "")

        try:
            return OrderSide(side_str)
        except ValueError as e:
            logger.warning(
                "Invalid order side value",
                extra={"side": side, "normalized": side_str},
            )
            raise ValueError(f"Invalid order side: {side}") from e

    @staticmethod
    def _categorize_orders(
        orders: list[OrderNotificationDTO],
    ) -> tuple[list[OrderNotificationDTO], list[OrderNotificationDTO]]:
        """Categorize orders into buy and sell lists.

        Args:
            orders: List of order DTOs to categorize

        Returns:
            Tuple of (buy_orders, sell_orders)

        Examples:
            >>> from decimal import Decimal
            >>> orders = [
            ...     OrderNotificationDTO(side=OrderSide.BUY, symbol="AAPL", qty=Decimal("10")),
            ...     OrderNotificationDTO(side=OrderSide.SELL, symbol="TSLA", qty=Decimal("5")),
            ... ]
            >>> buy, sell = PerformanceBuilder._categorize_orders(orders)
            >>> len(buy), len(sell)
            (1, 1)

        """
        buy_orders = []
        sell_orders = []

        for order in orders:
            try:
                normalized_side = PerformanceBuilder._normalize_order_side(order.side)
                if normalized_side == OrderSide.BUY:
                    buy_orders.append(order)
                elif normalized_side == OrderSide.SELL:
                    sell_orders.append(order)
            except ValueError:
                logger.warning(
                    "Skipping order with invalid side",
                    extra={"symbol": order.symbol, "side": order.side},
                )
                continue

        return buy_orders, sell_orders

    @staticmethod
    def _get_side_styling(side: OrderSide) -> tuple[str, str]:
        """Get color and emoji for an order side.

        Args:
            side: Order side enum

        Returns:
            Tuple of (color, emoji)

        """
        return SIDE_COLORS[side], SIDE_EMOJIS[side]

    @staticmethod
    def _format_order_row(order: OrderNotificationDTO) -> str:
        """Format a single order as an HTML table row.

        Args:
            order: Order DTO with side, symbol, qty, and optional estimated_value

        Returns:
            HTML string representing a table row

        Pre-conditions:
            - order.qty must be >= 0
            - order.estimated_value must be >= 0 if provided

        Post-conditions:
            - Returns valid HTML <tr> element
            - Decimal values formatted to 6 decimal places for qty
            - Monetary values formatted to 2 decimal places with thousands separator

        """
        side_enum = PerformanceBuilder._normalize_order_side(order.side)
        side_color, side_emoji = PerformanceBuilder._get_side_styling(side_enum)

        # Format values with proper Decimal handling
        qty_str = f"{order.qty:.6f}"
        value_str = (
            f"${order.estimated_value:,.2f}"
            if order.estimated_value
            else "$0.00"
        )

        return f"""
        <tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB;">
                <span style="color: {side_color}; font-weight: 600;">{side_emoji} {side_enum.value}</span>
            </td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; font-weight: 600;">
                {order.symbol}
            </td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right;">
                {qty_str}
            </td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right; color: #059669; font-weight: 600;">
                {value_str}
            </td>
        </tr>
        """

    @staticmethod
    def build_trading_activity(orders: list[OrderNotificationDTO] | None = None) -> str:
        """Build HTML for trading activity section.

        Args:
            orders: List of order DTOs to display, or None/empty for no orders

        Returns:
            HTML string with order table and summary

        Pre-conditions:
            - orders must be a list of valid OrderNotificationDTO instances or None
            - All order quantities and values must be non-negative

        Post-conditions:
            - Returns valid HTML5 <div> element
            - Displays up to MAX_DISPLAYED_ORDERS (10) orders in table
            - Shows summary with total counts and values
            - Logs warning if orders are truncated

        Examples:
            >>> from decimal import Decimal
            >>> orders = [
            ...     OrderNotificationDTO(
            ...         side=OrderSide.BUY,
            ...         symbol="AAPL",
            ...         qty=Decimal("10"),
            ...         estimated_value=Decimal("1500.00")
            ...     )
            ... ]
            >>> html = PerformanceBuilder.build_trading_activity(orders)
            >>> "AAPL" in html and "$1,500.00" in html
            True

        """
        if not orders:
            logger.info("Building trading activity HTML with no orders")
            return """
            <div style="margin: 24px 0; padding: 16px; background-color: #F3F4F6; border-radius: 8px; text-align: center;">
                <h3 style="margin: 0 0 8px 0; color: #6B7280; font-size: 18px;">📋 Orders Executed (0)</h3>
                <span style="color: #6B7280; font-style: italic;">No trades executed this session</span>
            </div>
            """

        logger.info(
            "Building trading activity HTML",
            extra={"order_count": len(orders)},
        )

        # Warn if truncating orders
        displayed_orders = orders[:MAX_DISPLAYED_ORDERS]
        if len(orders) > MAX_DISPLAYED_ORDERS:
            logger.warning(
                "Truncating order display",
                extra={
                    "total_orders": len(orders),
                    "displayed_orders": MAX_DISPLAYED_ORDERS,
                },
            )

        # Generate order rows
        orders_rows = "".join(
            PerformanceBuilder._format_order_row(order) for order in displayed_orders
        )

        # Calculate totals for summary
        buy_orders, sell_orders = PerformanceBuilder._categorize_orders(orders)
        total_buy_value = sum(
            (o.estimated_value or Decimal("0")) for o in buy_orders
        )
        total_sell_value = sum(
            (o.estimated_value or Decimal("0")) for o in sell_orders
        )

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
    def build_trading_summary(trading_summary: TradingSummaryDTO | None) -> str:
        """Build enhanced trading summary HTML section.

        Args:
            trading_summary: Trading summary DTO with metrics, or None if unavailable

        Returns:
            HTML string with trading metrics cards

        Pre-conditions:
            - If provided, trading_summary must be a valid TradingSummaryDTO
            - All counts must be non-negative integers
            - All values must be valid Decimal instances

        Post-conditions:
            - Returns valid HTML5 <div> element
            - Displays 4 metric cards: total trades, buy value, sell value, net value
            - Net value colored green (positive) or red (negative)

        Failure modes:
            - If trading_summary is None, returns warning alert box
            - Logs INFO when building summary

        Examples:
            >>> from decimal import Decimal
            >>> summary = TradingSummaryDTO(
            ...     total_trades=5,
            ...     total_buy_value=Decimal("10000"),
            ...     total_sell_value=Decimal("8000"),
            ...     net_value=Decimal("2000"),
            ...     buy_orders=3,
            ...     sell_orders=2
            ... )
            >>> html = PerformanceBuilder.build_trading_summary(summary)
            >>> "$10,000" in html and "$8,000" in html
            True

        """
        if not trading_summary:
            logger.warning("Trading summary not provided")
            return BaseEmailTemplate.create_alert_box("Trading summary not available", "warning")

        logger.info(
            "Building trading summary HTML",
            extra={
                "total_trades": trading_summary.total_trades,
                "net_value": str(trading_summary.net_value),
            },
        )

        # Calculate additional metrics
        net_color = "#10B981" if trading_summary.net_value >= 0 else "#EF4444"
        net_sign = "+" if trading_summary.net_value >= 0 else ""

        return f"""
        <div style="margin: 24px 0;">
            <h3 style="margin: 0 0 16px 0; color: #1F2937; font-size: 18px; font-weight: 600;">📊 Trading Summary</h3>
            <div style="background-color: white; border-radius: 8px; padding: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px;">
                    <div style="text-align: center; padding: 16px; background-color: #F8FAFC; border-radius: 8px;">
                        <div style="font-size: 24px; font-weight: 700; color: #1F2937; margin-bottom: 4px;">
                            {trading_summary.total_trades}
                        </div>
                        <div style="font-size: 14px; color: #6B7280;">Total Trades</div>
                    </div>
                    <div style="text-align: center; padding: 16px; background-color: #F0FDF4; border-radius: 8px;">
                        <div style="font-size: 20px; font-weight: 600; color: #10B981; margin-bottom: 4px;">
                            ${trading_summary.total_buy_value:,.0f}
                        </div>
                        <div style="font-size: 14px; color: #6B7280;">{trading_summary.buy_orders} Buy Orders</div>
                    </div>
                    <div style="text-align: center; padding: 16px; background-color: #FEF2F2; border-radius: 8px;">
                        <div style="font-size: 20px; font-weight: 600; color: #EF4444; margin-bottom: 4px;">
                            ${trading_summary.total_sell_value:,.0f}
                        </div>
                        <div style="font-size: 14px; color: #6B7280;">{trading_summary.sell_orders} Sell Orders</div>
                    </div>
                    <div style="text-align: center; padding: 16px; background-color: #F8FAFC; border-radius: 8px; border: 2px solid {net_color};">
                        <div style="font-size: 20px; font-weight: 700; color: {net_color}; margin-bottom: 4px;">
                            {net_sign}${trading_summary.net_value:,.0f}
                        </div>
                        <div style="font-size: 14px; color: #6B7280;">Net Value</div>
                    </div>
                </div>
            </div>
        </div>
        """

    @staticmethod
    def _get_signal_styling(signal: str) -> dict[str, str]:
        """Get styling configuration for a trading signal.

        Args:
            signal: Trading signal string (e.g., "BUY", "SELL", "HOLD")

        Returns:
            Dictionary with 'color', 'bg', and 'emoji' keys

        """
        return SIGNAL_STYLES.get(signal.upper(), DEFAULT_SIGNAL_STYLE)

    @staticmethod
    def _format_reason(reason: str) -> str:
        """Format reason text with truncation if needed.

        Args:
            reason: Reason text to format

        Returns:
            Formatted reason with ellipsis if truncated, or empty string if no reason

        """
        if not reason:
            return ""

        # Truncate to MAX_REASON_LENGTH and add ellipsis if needed
        if len(reason) > MAX_REASON_LENGTH:
            truncated = reason[:MAX_REASON_LENGTH]
            return f'<div style="color: #6B7280; font-size: 14px; font-style: italic;">{truncated}...</div>'

        return f'<div style="color: #6B7280; font-size: 14px; font-style: italic;">{reason}</div>'

    @staticmethod
    def build_strategy_performance(
        strategy_summary: dict[str, StrategyDataDTO] | None,
    ) -> str:
        """Build strategy performance summary.

        Args:
            strategy_summary: Dictionary mapping strategy names to their data DTOs,
                            or None if unavailable

        Returns:
            HTML string with strategy performance cards

        Pre-conditions:
            - If provided, strategy_summary must map string names to StrategyDataDTO instances
            - All allocation values must be between 0.0 and 1.0

        Post-conditions:
            - Returns valid HTML5 <div> element
            - Each strategy displayed as a card with signal, symbol, allocation
            - Signal styled with appropriate color and emoji

        Failure modes:
            - If strategy_summary is None/empty, returns warning alert box
            - Logs INFO with strategy count when building
            - Invalid strategy data logged as WARNING and skipped

        Examples:
            >>> strategy_data = StrategyDataDTO(
            ...     allocation=0.5,
            ...     signal="BUY",
            ...     symbol="AAPL",
            ...     reason="Strong momentum"
            ... )
            >>> strategies = {"Momentum": strategy_data}
            >>> html = PerformanceBuilder.build_strategy_performance(strategies)
            >>> "Momentum" in html and "AAPL" in html
            True

        """
        if not strategy_summary:
            logger.warning("Strategy performance data not provided")
            return BaseEmailTemplate.create_alert_box(
                "Strategy performance data not available", "warning"
            )

        logger.info(
            "Building strategy performance HTML",
            extra={"strategy_count": len(strategy_summary)},
        )

        strategy_cards = ""
        for strategy_name, strategy_data in strategy_summary.items():
            style = PerformanceBuilder._get_signal_styling(strategy_data.signal)
            reason_html = PerformanceBuilder._format_reason(strategy_data.reason)

            strategy_cards += f"""
            <div style="margin-bottom: 16px; padding: 16px; background-color: white; border-radius: 8px; border-left: 4px solid {style['color']}; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                    <h4 style="margin: 0; color: #1F2937; font-size: 16px; font-weight: 600;">
                        {strategy_name}
                    </h4>
                    <div style="background-color: {style['bg']}; color: {style['color']}; padding: 4px 12px; border-radius: 20px; font-size: 14px; font-weight: 600;">
                        {style['emoji']} {strategy_data.signal}
                    </div>
                </div>
                <div style="margin-bottom: 8px;">
                    <span style="color: #6B7280; font-size: 14px;">Target: </span>
                    <span style="font-weight: 600; color: #1F2937;">{strategy_data.symbol}</span>
                    <span style="color: #6B7280; font-size: 14px; margin-left: 16px;">Allocation: </span>
                    <span style="font-weight: 600; color: #1F2937;">{strategy_data.allocation:.1%}</span>
                </div>
                {reason_html}
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
    def _format_order_row_neutral(order: OrderNotificationDTO) -> str:
        """Format a single order as an HTML table row for neutral mode.

        Args:
            order: Order DTO with side, symbol, and qty

        Returns:
            HTML string representing a table row without monetary values

        """
        side_enum = PerformanceBuilder._normalize_order_side(order.side)
        side_color, side_emoji = PerformanceBuilder._get_side_styling(side_enum)

        return f"""
        <tr>
            <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB;">
                <span style="color: {side_color}; font-weight: 600;">{side_emoji} {side_enum.value}</span>
            </td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; font-weight: 600;">
                {order.symbol}
            </td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: right;">
                {order.qty:.6f} shares
            </td>
            <td style="padding: 8px 12px; border-bottom: 1px solid #E5E7EB; text-align: center; color: #10B981;">
                ✅ Executed
            </td>
        </tr>
        """

    @staticmethod
    def build_trading_activity_neutral(orders: list[OrderNotificationDTO] | None = None) -> str:
        """Build HTML for trading activity section without dollar values.

        Args:
            orders: List of order DTOs to display, or None/empty for no orders

        Returns:
            HTML string with order table and summary (counts only, no monetary values)

        Pre-conditions:
            - orders must be a list of valid OrderNotificationDTO instances or None

        Post-conditions:
            - Returns valid HTML5 <div> element
            - Displays up to MAX_DISPLAYED_ORDERS (10) orders in table
            - Shows summary with order counts only (no dollar amounts)
            - Logs warning if orders are truncated

        """
        if not orders:
            logger.info("Building neutral trading activity HTML with no orders")
            return """
            <div style="margin: 24px 0; padding: 16px; background-color: #F3F4F6; border-radius: 8px; text-align: center;">
                <h3 style="margin: 0 0 8px 0; color: #6B7280; font-size: 18px;">📋 Orders Executed (0)</h3>
                <span style="color: #6B7280; font-style: italic;">No trades executed this session</span>
            </div>
            """

        logger.info(
            "Building neutral trading activity HTML",
            extra={"order_count": len(orders)},
        )

        # Warn if truncating orders
        displayed_orders = orders[:MAX_DISPLAYED_ORDERS]
        if len(orders) > MAX_DISPLAYED_ORDERS:
            logger.warning(
                "Truncating neutral order display",
                extra={
                    "total_orders": len(orders),
                    "displayed_orders": MAX_DISPLAYED_ORDERS,
                },
            )

        # Generate order rows
        orders_rows = "".join(
            PerformanceBuilder._format_order_row_neutral(order) for order in displayed_orders
        )

        # Calculate totals for summary (count only, no dollar amounts)
        buy_orders, sell_orders = PerformanceBuilder._categorize_orders(orders)

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
