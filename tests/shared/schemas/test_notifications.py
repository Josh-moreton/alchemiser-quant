#!/usr/bin/env python3
"""Test suite for shared.schemas.notifications module.

Tests OrderNotificationDTO, TradingSummaryDTO, StrategyDataDTO for:
- Successful instantiation with valid data
- Field validation and constraints
- Frozen/immutability enforcement
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from pydantic import ValidationError

from the_alchemiser.shared.schemas.notifications import (
    OrderNotificationDTO,
    OrderSide,
    StrategyDataDTO,
    TradingSummaryDTO,
)


class TestOrderSide:
    """Test OrderSide enum."""

    def test_order_side_values(self):
        """Test OrderSide enum values."""
        assert OrderSide.BUY.value == "BUY"
        assert OrderSide.SELL.value == "SELL"


class TestOrderNotificationDTO:
    """Test OrderNotificationDTO."""

    def test_create_order_notification_valid(self):
        """Test creating OrderNotificationDTO with valid data."""
        order = OrderNotificationDTO(
            side=OrderSide.BUY,
            symbol="AAPL",
            qty=Decimal("10.5"),
            estimated_value=Decimal("1500.50"),
        )

        assert order.side == OrderSide.BUY
        assert order.symbol == "AAPL"
        assert order.qty == Decimal("10.5")
        assert order.estimated_value == Decimal("1500.50")

    def test_create_order_notification_without_value(self):
        """Test creating OrderNotificationDTO without estimated_value."""
        order = OrderNotificationDTO(
            side=OrderSide.SELL,
            symbol="TSLA",
            qty=Decimal("5"),
        )

        assert order.side == OrderSide.SELL
        assert order.estimated_value is None

    def test_order_notification_frozen(self):
        """Test that OrderNotificationDTO is immutable."""
        order = OrderNotificationDTO(
            side=OrderSide.BUY,
            symbol="AAPL",
            qty=Decimal("10"),
        )

        with pytest.raises(ValidationError):
            order.symbol = "TSLA"

    def test_order_notification_negative_qty_fails(self):
        """Test that negative qty raises validation error."""
        with pytest.raises(ValidationError):
            OrderNotificationDTO(
                side=OrderSide.BUY,
                symbol="AAPL",
                qty=Decimal("-10"),
            )


class TestTradingSummaryDTO:
    """Test TradingSummaryDTO."""

    def test_create_trading_summary_valid(self):
        """Test creating TradingSummaryDTO with valid data."""
        summary = TradingSummaryDTO(
            total_trades=10,
            total_buy_value=Decimal("50000"),
            total_sell_value=Decimal("30000"),
            net_value=Decimal("20000"),
            buy_orders=6,
            sell_orders=4,
        )

        assert summary.total_trades == 10
        assert summary.total_buy_value == Decimal("50000")
        assert summary.net_value == Decimal("20000")

    def test_trading_summary_frozen(self):
        """Test that TradingSummaryDTO is immutable."""
        summary = TradingSummaryDTO(
            total_trades=5,
            total_buy_value=Decimal("10000"),
            total_sell_value=Decimal("8000"),
            net_value=Decimal("2000"),
            buy_orders=3,
            sell_orders=2,
        )

        with pytest.raises(ValidationError):
            summary.total_trades = 10

    def test_trading_summary_negative_counts_fail(self):
        """Test that negative counts raise validation error."""
        with pytest.raises(ValidationError):
            TradingSummaryDTO(
                total_trades=-1,
                total_buy_value=Decimal("10000"),
                total_sell_value=Decimal("8000"),
                net_value=Decimal("2000"),
                buy_orders=3,
                sell_orders=2,
            )


class TestStrategyDataDTO:
    """Test StrategyDataDTO."""

    def test_create_strategy_data_valid(self):
        """Test creating StrategyDataDTO with valid data."""
        strategy = StrategyDataDTO(
            allocation=0.5,
            signal="BUY",
            symbol="AAPL",
            reason="Strong momentum",
        )

        assert strategy.allocation == 0.5
        assert strategy.signal == "BUY"
        assert strategy.symbol == "AAPL"
        assert strategy.reason == "Strong momentum"

    def test_strategy_data_without_reason(self):
        """Test creating StrategyDataDTO without reason."""
        strategy = StrategyDataDTO(
            allocation=0.3,
            signal="SELL",
            symbol="TSLA",
        )

        assert strategy.reason == ""

    def test_strategy_data_allocation_bounds(self):
        """Test allocation validation (must be 0.0 to 1.0)."""
        # Valid at boundaries
        strategy = StrategyDataDTO(
            allocation=0.0,
            signal="HOLD",
            symbol="MSFT",
        )
        assert strategy.allocation == 0.0

        strategy = StrategyDataDTO(
            allocation=1.0,
            signal="BUY",
            symbol="GOOGL",
        )
        assert strategy.allocation == 1.0

        # Invalid: negative
        with pytest.raises(ValidationError):
            StrategyDataDTO(
                allocation=-0.1,
                signal="BUY",
                symbol="AAPL",
            )

        # Invalid: > 1.0
        with pytest.raises(ValidationError):
            StrategyDataDTO(
                allocation=1.5,
                signal="BUY",
                symbol="AAPL",
            )

    def test_strategy_data_frozen(self):
        """Test that StrategyDataDTO is immutable."""
        strategy = StrategyDataDTO(
            allocation=0.5,
            signal="BUY",
            symbol="AAPL",
        )

        with pytest.raises(ValidationError):
            strategy.allocation = 0.7
