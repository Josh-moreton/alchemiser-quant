#!/usr/bin/env python3
"""Test suite for performance.py notification templates.

Tests PerformanceBuilder for:
- Type safety with DTOs
- Decimal handling for monetary values
- HTML generation correctness
- Order truncation warnings
- Error handling and logging
- Edge cases (empty inputs, invalid data)
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from the_alchemiser.shared.notifications.templates.performance import (
    MAX_DISPLAYED_ORDERS,
    PerformanceBuilder,
)
from the_alchemiser.shared.schemas.notifications import (
    OrderNotificationDTO,
    OrderSide,
    StrategyDataDTO,
    TradingSummaryDTO,
)


class TestNormalizeOrderSide:
    """Test _normalize_order_side method."""

    def test_normalize_order_side_enum(self):
        """Test normalizing OrderSide enum."""
        result = PerformanceBuilder._normalize_order_side(OrderSide.BUY)
        assert result == OrderSide.BUY

    def test_normalize_order_side_string_buy(self):
        """Test normalizing 'BUY' string."""
        result = PerformanceBuilder._normalize_order_side("BUY")
        assert result == OrderSide.BUY

    def test_normalize_order_side_string_sell_lowercase(self):
        """Test normalizing 'sell' string (lowercase)."""
        result = PerformanceBuilder._normalize_order_side("sell")
        assert result == OrderSide.SELL

    def test_normalize_order_side_orderside_prefix(self):
        """Test normalizing 'ORDERSIDE.BUY' string."""
        result = PerformanceBuilder._normalize_order_side("ORDERSIDE.BUY")
        assert result == OrderSide.BUY

    def test_normalize_order_side_invalid_raises_error(self):
        """Test that invalid side raises ValueError."""
        with pytest.raises(ValueError, match="Invalid order side"):
            PerformanceBuilder._normalize_order_side("INVALID")


class TestCategorizeOrders:
    """Test _categorize_orders method."""

    def test_categorize_orders_empty_list(self):
        """Test categorizing empty order list."""
        buy, sell = PerformanceBuilder._categorize_orders([])
        assert buy == []
        assert sell == []

    def test_categorize_orders_all_buys(self):
        """Test categorizing all buy orders."""
        orders = [
            OrderNotificationDTO(
                side=OrderSide.BUY,
                symbol="AAPL",
                qty=Decimal("10"),
            ),
            OrderNotificationDTO(
                side=OrderSide.BUY,
                symbol="TSLA",
                qty=Decimal("5"),
            ),
        ]
        buy, sell = PerformanceBuilder._categorize_orders(orders)
        assert len(buy) == 2
        assert len(sell) == 0

    def test_categorize_orders_mixed(self):
        """Test categorizing mixed buy/sell orders."""
        orders = [
            OrderNotificationDTO(
                side=OrderSide.BUY,
                symbol="AAPL",
                qty=Decimal("10"),
            ),
            OrderNotificationDTO(
                side=OrderSide.SELL,
                symbol="TSLA",
                qty=Decimal("5"),
            ),
            OrderNotificationDTO(
                side=OrderSide.BUY,
                symbol="MSFT",
                qty=Decimal("8"),
            ),
        ]
        buy, sell = PerformanceBuilder._categorize_orders(orders)
        assert len(buy) == 2
        assert len(sell) == 1
        assert buy[0].symbol == "AAPL"
        assert buy[1].symbol == "MSFT"
        assert sell[0].symbol == "TSLA"


class TestGetSideStyling:
    """Test _get_side_styling method."""

    def test_get_side_styling_buy(self):
        """Test styling for BUY side."""
        color, emoji = PerformanceBuilder._get_side_styling(OrderSide.BUY)
        assert color == "#10B981"
        assert emoji == "🟢"

    def test_get_side_styling_sell(self):
        """Test styling for SELL side."""
        color, emoji = PerformanceBuilder._get_side_styling(OrderSide.SELL)
        assert color == "#EF4444"
        assert emoji == "🔴"


class TestFormatOrderRow:
    """Test _format_order_row method."""

    def test_format_order_row_with_value(self):
        """Test formatting order row with estimated value."""
        order = OrderNotificationDTO(
            side=OrderSide.BUY,
            symbol="AAPL",
            qty=Decimal("10.5"),
            estimated_value=Decimal("1500.50"),
        )
        html = PerformanceBuilder._format_order_row(order)

        assert "AAPL" in html
        assert "10.500000" in html
        assert "$1,500.50" in html
        assert "BUY" in html
        assert "<tr>" in html

    def test_format_order_row_without_value(self):
        """Test formatting order row without estimated value."""
        order = OrderNotificationDTO(
            side=OrderSide.SELL,
            symbol="TSLA",
            qty=Decimal("5"),
        )
        html = PerformanceBuilder._format_order_row(order)

        assert "TSLA" in html
        assert "5.000000" in html
        assert "$0.00" in html
        assert "SELL" in html


class TestBuildTradingActivity:
    """Test build_trading_activity method."""

    def test_build_trading_activity_no_orders(self):
        """Test building activity with no orders."""
        html = PerformanceBuilder.build_trading_activity(None)
        assert "Orders Executed (0)" in html
        assert "No trades executed" in html

    def test_build_trading_activity_empty_list(self):
        """Test building activity with empty list."""
        html = PerformanceBuilder.build_trading_activity([])
        assert "Orders Executed (0)" in html

    def test_build_trading_activity_single_order(self):
        """Test building activity with one order."""
        orders = [
            OrderNotificationDTO(
                side=OrderSide.BUY,
                symbol="AAPL",
                qty=Decimal("10"),
                estimated_value=Decimal("1500"),
            )
        ]
        html = PerformanceBuilder.build_trading_activity(orders)

        assert "Orders Executed (1)" in html
        assert "AAPL" in html
        assert "$1,500.00" in html
        assert "1 total orders" in html

    def test_build_trading_activity_multiple_orders(self):
        """Test building activity with multiple orders."""
        orders = [
            OrderNotificationDTO(
                side=OrderSide.BUY,
                symbol="AAPL",
                qty=Decimal("10"),
                estimated_value=Decimal("1500"),
            ),
            OrderNotificationDTO(
                side=OrderSide.SELL,
                symbol="TSLA",
                qty=Decimal("5"),
                estimated_value=Decimal("800"),
            ),
        ]
        html = PerformanceBuilder.build_trading_activity(orders)

        assert "Orders Executed (2)" in html
        assert "AAPL" in html
        assert "TSLA" in html
        assert "$1,500.00" in html
        assert "$800.00" in html

    def test_build_trading_activity_truncates_at_max(self):
        """Test that more than MAX_DISPLAYED_ORDERS orders are truncated."""
        # Create more than MAX_DISPLAYED_ORDERS (10) orders
        orders = [
            OrderNotificationDTO(
                side=OrderSide.BUY,
                symbol=f"SYM{i}",
                qty=Decimal("1"),
                estimated_value=Decimal("100"),
            )
            for i in range(15)
        ]
        html = PerformanceBuilder.build_trading_activity(orders)

        # Should show total count
        assert "Orders Executed (15)" in html
        # Should only display first 10 symbols
        assert "SYM0" in html
        assert "SYM9" in html
        # Should NOT display 11th+ symbols
        assert "SYM14" not in html


class TestBuildTradingSummary:
    """Test build_trading_summary method."""

    def test_build_trading_summary_none(self):
        """Test building summary with None."""
        html = PerformanceBuilder.build_trading_summary(None)
        assert "not available" in html

    def test_build_trading_summary_positive_net(self):
        """Test building summary with positive net value."""
        summary = TradingSummaryDTO(
            total_trades=5,
            total_buy_value=Decimal("10000"),
            total_sell_value=Decimal("8000"),
            net_value=Decimal("2000"),
            buy_orders=3,
            sell_orders=2,
        )
        html = PerformanceBuilder.build_trading_summary(summary)

        assert "5" in html  # total trades
        assert "$10,000" in html  # buy value
        assert "$8,000" in html  # sell value
        assert "+$2,000" in html  # net value with plus sign
        assert "3 Buy Orders" in html
        assert "2 Sell Orders" in html

    def test_build_trading_summary_negative_net(self):
        """Test building summary with negative net value."""
        summary = TradingSummaryDTO(
            total_trades=3,
            total_buy_value=Decimal("5000"),
            total_sell_value=Decimal("7000"),
            net_value=Decimal("-2000"),
            buy_orders=1,
            sell_orders=2,
        )
        html = PerformanceBuilder.build_trading_summary(summary)

        assert "$5,000" in html
        assert "$7,000" in html
        assert "-$2,000" in html  # negative net value (no plus sign)


class TestGetSignalStyling:
    """Test _get_signal_styling method."""

    def test_get_signal_styling_buy(self):
        """Test styling for BUY signal."""
        style = PerformanceBuilder._get_signal_styling("BUY")
        assert style["color"] == "#10B981"
        assert style["emoji"] == "📈"

    def test_get_signal_styling_sell(self):
        """Test styling for SELL signal."""
        style = PerformanceBuilder._get_signal_styling("SELL")
        assert style["color"] == "#EF4444"
        assert style["emoji"] == "📉"

    def test_get_signal_styling_unknown(self):
        """Test styling for unknown signal."""
        style = PerformanceBuilder._get_signal_styling("HOLD")
        assert style["color"] == "#6B7280"
        assert style["emoji"] == "⏸️"


class TestFormatReason:
    """Test _format_reason method."""

    def test_format_reason_empty(self):
        """Test formatting empty reason."""
        result = PerformanceBuilder._format_reason("")
        assert result == ""

    def test_format_reason_short(self):
        """Test formatting short reason."""
        reason = "Strong momentum signal"
        result = PerformanceBuilder._format_reason(reason)
        assert reason in result
        assert "..." not in result

    def test_format_reason_truncated(self):
        """Test formatting reason that exceeds MAX_REASON_LENGTH."""
        reason = "A" * 150  # Longer than MAX_REASON_LENGTH (100)
        result = PerformanceBuilder._format_reason(reason)
        assert "..." in result
        assert len(reason) > len(result)


class TestBuildStrategyPerformance:
    """Test build_strategy_performance method."""

    def test_build_strategy_performance_none(self):
        """Test building strategy performance with None."""
        html = PerformanceBuilder.build_strategy_performance(None)
        assert "not available" in html

    def test_build_strategy_performance_empty(self):
        """Test building strategy performance with empty dict."""
        html = PerformanceBuilder.build_strategy_performance({})
        assert "not available" in html

    def test_build_strategy_performance_single_strategy(self):
        """Test building strategy performance with one strategy."""
        strategies = {
            "Momentum": StrategyDataDTO(
                allocation=0.5,
                signal="BUY",
                symbol="AAPL",
                reason="Strong uptrend",
            )
        }
        html = PerformanceBuilder.build_strategy_performance(strategies)

        assert "Momentum" in html
        assert "AAPL" in html
        assert "50.0%" in html
        assert "BUY" in html
        assert "Strong uptrend" in html

    def test_build_strategy_performance_multiple_strategies(self):
        """Test building strategy performance with multiple strategies."""
        strategies = {
            "Momentum": StrategyDataDTO(
                allocation=0.6,
                signal="BUY",
                symbol="AAPL",
                reason="",
            ),
            "Mean Reversion": StrategyDataDTO(
                allocation=0.4,
                signal="SELL",
                symbol="TSLA",
                reason="Oversold",
            ),
        }
        html = PerformanceBuilder.build_strategy_performance(strategies)

        assert "Momentum" in html
        assert "Mean Reversion" in html
        assert "AAPL" in html
        assert "TSLA" in html
        assert "60.0%" in html
        assert "40.0%" in html


class TestBuildTradingActivityNeutral:
    """Test build_trading_activity_neutral method."""

    def test_build_trading_activity_neutral_no_orders(self):
        """Test building neutral activity with no orders."""
        html = PerformanceBuilder.build_trading_activity_neutral(None)
        assert "Orders Executed (0)" in html
        assert "No trades executed" in html

    def test_build_trading_activity_neutral_with_orders(self):
        """Test building neutral activity with orders."""
        orders = [
            OrderNotificationDTO(
                side=OrderSide.BUY,
                symbol="AAPL",
                qty=Decimal("10"),
            )
        ]
        html = PerformanceBuilder.build_trading_activity_neutral(orders)

        assert "Orders Executed (1)" in html
        assert "AAPL" in html
        assert "10.000000 shares" in html
        # Should NOT contain dollar amounts
        assert "$" not in html

    def test_build_trading_activity_neutral_truncates(self):
        """Test that neutral mode also truncates orders."""
        orders = [
            OrderNotificationDTO(
                side=OrderSide.BUY,
                symbol=f"SYM{i}",
                qty=Decimal("1"),
            )
            for i in range(15)
        ]
        html = PerformanceBuilder.build_trading_activity_neutral(orders)

        assert "Orders Executed (15)" in html
        assert "SYM0" in html
        assert "SYM9" in html
        assert "SYM14" not in html


class TestFormatOrderRowNeutral:
    """Test _format_order_row_neutral method."""

    def test_format_order_row_neutral(self):
        """Test formatting neutral order row."""
        order = OrderNotificationDTO(
            side=OrderSide.BUY,
            symbol="AAPL",
            qty=Decimal("10.5"),
        )
        html = PerformanceBuilder._format_order_row_neutral(order)

        assert "AAPL" in html
        assert "10.500000 shares" in html
        assert "BUY" in html
        assert "✅ Executed" in html
        # Should NOT contain dollar amounts
        assert "$" not in html
