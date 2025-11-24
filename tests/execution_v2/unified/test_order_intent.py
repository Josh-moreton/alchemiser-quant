"""Business Unit: execution | Status: current.

Unit tests for OrderIntent abstraction.
"""

import pytest
from decimal import Decimal

from the_alchemiser.execution_v2.unified import (
    OrderIntent,
    OrderSide,
    CloseType,
    Urgency,
)


class TestOrderIntent:
    """Test cases for OrderIntent abstraction."""

    def test_valid_buy_order(self):
        """Test creating a valid buy order."""
        intent = OrderIntent(
            side=OrderSide.BUY,
            close_type=CloseType.NONE,
            symbol="AAPL",
            quantity=Decimal("10"),
            urgency=Urgency.MEDIUM,
        )

        assert intent.is_buy
        assert not intent.is_sell
        assert not intent.is_full_close
        assert not intent.is_partial_close
        assert intent.side == OrderSide.BUY
        assert intent.close_type == CloseType.NONE

    def test_valid_sell_partial(self):
        """Test creating a valid partial sell order."""
        intent = OrderIntent(
            side=OrderSide.SELL,
            close_type=CloseType.PARTIAL,
            symbol="AAPL",
            quantity=Decimal("5"),
            urgency=Urgency.LOW,
        )

        assert not intent.is_buy
        assert intent.is_sell
        assert not intent.is_full_close
        assert intent.is_partial_close

    def test_valid_sell_full(self):
        """Test creating a valid full close order."""
        intent = OrderIntent(
            side=OrderSide.SELL,
            close_type=CloseType.FULL,
            symbol="AAPL",
            quantity=Decimal("10"),
            urgency=Urgency.HIGH,
        )

        assert not intent.is_buy
        assert intent.is_sell
        assert intent.is_full_close
        assert not intent.is_partial_close

    def test_invalid_close_with_buy(self):
        """Test that close operations require SELL side."""
        with pytest.raises(ValueError, match="Close operations must use SELL side"):
            OrderIntent(
                side=OrderSide.BUY,
                close_type=CloseType.FULL,
                symbol="AAPL",
                quantity=Decimal("10"),
                urgency=Urgency.MEDIUM,
            )

    def test_invalid_negative_quantity(self):
        """Test that negative quantities are rejected."""
        with pytest.raises(ValueError, match="Quantity must be positive"):
            OrderIntent(
                side=OrderSide.BUY,
                close_type=CloseType.NONE,
                symbol="AAPL",
                quantity=Decimal("-10"),
                urgency=Urgency.MEDIUM,
            )

    def test_invalid_zero_quantity(self):
        """Test that zero quantities are rejected."""
        with pytest.raises(ValueError, match="Quantity must be positive"):
            OrderIntent(
                side=OrderSide.BUY,
                close_type=CloseType.NONE,
                symbol="AAPL",
                quantity=Decimal("0"),
                urgency=Urgency.MEDIUM,
            )

    def test_invalid_empty_symbol(self):
        """Test that empty symbols are rejected."""
        with pytest.raises(ValueError, match="Symbol cannot be empty"):
            OrderIntent(
                side=OrderSide.BUY,
                close_type=CloseType.NONE,
                symbol="",
                quantity=Decimal("10"),
                urgency=Urgency.MEDIUM,
            )

    def test_to_alpaca_params_buy(self):
        """Test conversion to Alpaca API params for buy."""
        intent = OrderIntent(
            side=OrderSide.BUY,
            close_type=CloseType.NONE,
            symbol="AAPL",
            quantity=Decimal("10"),
            urgency=Urgency.MEDIUM,
        )

        params = intent.to_alpaca_params()
        assert params["symbol"] == "AAPL"
        assert params["side"] == "buy"
        assert params["qty"] == 10.0
        assert params["is_complete_exit"] is False

    def test_to_alpaca_params_sell_full(self):
        """Test conversion to Alpaca API params for full close."""
        intent = OrderIntent(
            side=OrderSide.SELL,
            close_type=CloseType.FULL,
            symbol="AAPL",
            quantity=Decimal("10"),
            urgency=Urgency.HIGH,
        )

        params = intent.to_alpaca_params()
        assert params["symbol"] == "AAPL"
        assert params["side"] == "sell"
        assert params["qty"] == 10.0
        assert params["is_complete_exit"] is True

    def test_describe_buy(self):
        """Test human-readable description for buy order."""
        intent = OrderIntent(
            side=OrderSide.BUY,
            close_type=CloseType.NONE,
            symbol="AAPL",
            quantity=Decimal("10"),
            urgency=Urgency.MEDIUM,
        )

        desc = intent.describe()
        assert "BUY" in desc
        assert "10" in desc
        assert "AAPL" in desc

    def test_describe_sell_partial(self):
        """Test human-readable description for partial sell."""
        intent = OrderIntent(
            side=OrderSide.SELL,
            close_type=CloseType.PARTIAL,
            symbol="AAPL",
            quantity=Decimal("5"),
            urgency=Urgency.LOW,
        )

        desc = intent.describe()
        assert "REDUCE" in desc
        assert "5" in desc
        assert "AAPL" in desc

    def test_describe_sell_full(self):
        """Test human-readable description for full close."""
        intent = OrderIntent(
            side=OrderSide.SELL,
            close_type=CloseType.FULL,
            symbol="AAPL",
            quantity=Decimal("10"),
            urgency=Urgency.HIGH,
        )

        desc = intent.describe()
        assert "CLOSE" in desc
        assert "full exit" in desc
        assert "AAPL" in desc

    def test_order_side_enum(self):
        """Test OrderSide enum values."""
        assert OrderSide.BUY.value == "BUY"
        assert OrderSide.SELL.value == "SELL"
        assert OrderSide.BUY.to_alpaca() == "buy"
        assert OrderSide.SELL.to_alpaca() == "sell"

    def test_close_type_enum(self):
        """Test CloseType enum values."""
        assert CloseType.NONE.value == "NONE"
        assert CloseType.PARTIAL.value == "PARTIAL"
        assert CloseType.FULL.value == "FULL"
        assert not CloseType.NONE.is_closing()
        assert CloseType.PARTIAL.is_closing()
        assert CloseType.FULL.is_closing()

    def test_urgency_enum(self):
        """Test Urgency enum values."""
        assert Urgency.LOW.value == "LOW"
        assert Urgency.MEDIUM.value == "MEDIUM"
        assert Urgency.HIGH.value == "HIGH"
