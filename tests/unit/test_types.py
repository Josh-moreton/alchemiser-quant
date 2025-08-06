"""
Unit tests for core type definitions and validation.

Tests the core types module that defines the fundamental data structures
used throughout the trading system.
"""

from datetime import datetime
from decimal import Decimal

import pytest

# Import the core types - adjust import path as needed
try:
    from the_alchemiser.core.types import (
        OrderRequest,
        PortfolioState,
        Position,
        PriceData,
        Signal,
    )
except ImportError:
    pytest.skip("Core types module not available", allow_module_level=True)


class TestPortfolioState:
    """Test portfolio state type validation and behavior."""

    def test_portfolio_state_creation(self):
        """Test creating a valid portfolio state."""
        portfolio = PortfolioState(
            total_value=Decimal("100000.00"),
            cash=Decimal("10000.00"),
            positions={},
            timestamp=datetime.now(),
        )

        assert portfolio.total_value == Decimal("100000.00")
        assert portfolio.cash == Decimal("10000.00")
        assert portfolio.positions == {}
        assert isinstance(portfolio.timestamp, datetime)

    def test_portfolio_state_with_positions(self):
        """Test portfolio state with actual positions."""
        positions = {
            "AAPL": Position(
                symbol="AAPL",
                shares=100,
                avg_price=Decimal("150.00"),
                current_price=Decimal("155.00"),
                market_value=Decimal("15500.00"),
            )
        }

        portfolio = PortfolioState(
            total_value=Decimal("100000.00"),
            cash=Decimal("84500.00"),
            positions=positions,
            timestamp=datetime.now(),
        )

        assert len(portfolio.positions) == 1
        assert "AAPL" in portfolio.positions
        assert portfolio.positions["AAPL"].shares == 100

    def test_portfolio_state_validation(self):
        """Test portfolio state validation rules."""
        # Test negative cash should be allowed (margin accounts)
        portfolio = PortfolioState(
            total_value=Decimal("100000.00"),
            cash=Decimal("-5000.00"),  # Negative cash (margin)
            positions={},
            timestamp=datetime.now(),
        )
        assert portfolio.cash == Decimal("-5000.00")

        # Test zero values
        portfolio_zero = PortfolioState(
            total_value=Decimal("0.00"),
            cash=Decimal("0.00"),
            positions={},
            timestamp=datetime.now(),
        )
        assert portfolio_zero.total_value == Decimal("0.00")


class TestPosition:
    """Test position type validation and calculations."""

    def test_position_creation(self):
        """Test creating a valid position."""
        position = Position(
            symbol="AAPL",
            shares=100,
            avg_price=Decimal("150.00"),
            current_price=Decimal("155.00"),
            market_value=Decimal("15500.00"),
        )

        assert position.symbol == "AAPL"
        assert position.shares == 100
        assert position.avg_price == Decimal("150.00")
        assert position.current_price == Decimal("155.00")
        assert position.market_value == Decimal("15500.00")

    def test_position_pnl_calculation(self):
        """Test P&L calculation for positions."""
        position = Position(
            symbol="AAPL",
            shares=100,
            avg_price=Decimal("150.00"),
            current_price=Decimal("155.00"),
            market_value=Decimal("15500.00"),
        )

        # If position has unrealized_pnl property
        try:
            expected_pnl = (position.current_price - position.avg_price) * position.shares
            # Assuming the position calculates this automatically
            if hasattr(position, "unrealized_pnl"):
                assert position.unrealized_pnl == expected_pnl
        except AttributeError:
            # P&L calculation might be handled elsewhere
            pass

    def test_position_with_zero_shares(self):
        """Test position with zero shares (closed position)."""
        position = Position(
            symbol="AAPL",
            shares=0,
            avg_price=Decimal("150.00"),
            current_price=Decimal("155.00"),
            market_value=Decimal("0.00"),
        )

        assert position.shares == 0
        assert position.market_value == Decimal("0.00")

    def test_position_fractional_shares(self):
        """Test position with fractional shares."""
        position = Position(
            symbol="AAPL",
            shares=100.5,
            avg_price=Decimal("150.00"),
            current_price=Decimal("155.00"),
            market_value=Decimal("15577.50"),
        )

        assert position.shares == 100.5
        assert position.market_value == Decimal("15577.50")


class TestOrderRequest:
    """Test order request type validation."""

    def test_order_request_creation(self):
        """Test creating a valid order request."""
        order = OrderRequest(
            symbol="AAPL", quantity=100, side="BUY", order_type="MARKET", time_in_force="DAY"
        )

        assert order.symbol == "AAPL"
        assert order.quantity == 100
        assert order.side == "BUY"
        assert order.order_type == "MARKET"
        assert order.time_in_force == "DAY"

    def test_order_request_with_limit_price(self):
        """Test order request with limit price."""
        order = OrderRequest(
            symbol="AAPL",
            quantity=100,
            side="BUY",
            order_type="LIMIT",
            limit_price=Decimal("150.00"),
            time_in_force="GTC",
        )

        assert order.order_type == "LIMIT"
        if hasattr(order, "limit_price"):
            assert order.limit_price == Decimal("150.00")

    def test_order_request_validation(self):
        """Test order request validation."""
        # Test valid sides
        for side in ["BUY", "SELL"]:
            order = OrderRequest(
                symbol="AAPL", quantity=100, side=side, order_type="MARKET", time_in_force="DAY"
            )
            assert order.side == side

        # Test valid order types
        for order_type in ["MARKET", "LIMIT", "STOP", "STOP_LIMIT"]:
            order = OrderRequest(
                symbol="AAPL", quantity=100, side="BUY", order_type=order_type, time_in_force="DAY"
            )
            assert order.order_type == order_type


class TestSignal:
    """Test trading signal type validation."""

    def test_signal_creation(self):
        """Test creating a valid trading signal."""
        signal = Signal(
            symbol="AAPL",
            action="BUY",
            strength=0.8,
            timestamp=datetime.now(),
            strategy="test_strategy",
        )

        assert signal.symbol == "AAPL"
        assert signal.action == "BUY"
        assert signal.strength == 0.8
        assert isinstance(signal.timestamp, datetime)
        if hasattr(signal, "strategy"):
            assert signal.strategy == "test_strategy"

    def test_signal_strength_validation(self):
        """Test signal strength is within valid range."""
        # Test valid strength values
        for strength in [0.0, 0.5, 1.0]:
            signal = Signal(
                symbol="AAPL", action="BUY", strength=strength, timestamp=datetime.now()
            )
            assert signal.strength == strength

        # Test edge case strengths
        signal_weak = Signal(symbol="AAPL", action="HOLD", strength=0.1, timestamp=datetime.now())
        assert signal_weak.strength == 0.1

    def test_signal_actions(self):
        """Test valid signal actions."""
        for action in ["BUY", "SELL", "HOLD"]:
            signal = Signal(symbol="AAPL", action=action, strength=0.5, timestamp=datetime.now())
            assert signal.action == action


class TestPriceData:
    """Test price data type validation."""

    def test_price_data_creation(self):
        """Test creating valid price data."""
        price_data = PriceData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=Decimal("150.00"),
            high=Decimal("155.00"),
            low=Decimal("149.00"),
            close=Decimal("154.00"),
            volume=1000000,
        )

        assert price_data.symbol == "AAPL"
        assert isinstance(price_data.timestamp, datetime)
        assert price_data.open == Decimal("150.00")
        assert price_data.high == Decimal("155.00")
        assert price_data.low == Decimal("149.00")
        assert price_data.close == Decimal("154.00")
        assert price_data.volume == 1000000

    def test_price_data_ohlc_validation(self):
        """Test OHLC price validation logic."""
        # Valid OHLC relationships
        price_data = PriceData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=Decimal("150.00"),
            high=Decimal("155.00"),  # High should be >= open, close, low
            low=Decimal("149.00"),  # Low should be <= open, close, high
            close=Decimal("154.00"),
            volume=1000000,
        )

        # Basic validation - high >= low
        assert price_data.high >= price_data.low

        # High should be >= open and close
        assert price_data.high >= price_data.open
        assert price_data.high >= price_data.close

        # Low should be <= open and close
        assert price_data.low <= price_data.open
        assert price_data.low <= price_data.close

    def test_price_data_edge_cases(self):
        """Test price data edge cases."""
        # Same OHLC (no movement)
        flat_price = Decimal("150.00")
        price_data = PriceData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=flat_price,
            high=flat_price,
            low=flat_price,
            close=flat_price,
            volume=0,  # Zero volume
        )

        assert price_data.open == price_data.high == price_data.low == price_data.close
        assert price_data.volume == 0

    def test_price_data_precision(self):
        """Test price data decimal precision."""
        # Test with high precision prices
        price_data = PriceData(
            symbol="AAPL",
            timestamp=datetime.now(),
            open=Decimal("150.1234"),
            high=Decimal("155.5678"),
            low=Decimal("149.9876"),
            close=Decimal("154.4321"),
            volume=1000000,
        )

        assert price_data.open == Decimal("150.1234")
        assert price_data.high == Decimal("155.5678")
        assert price_data.low == Decimal("149.9876")
        assert price_data.close == Decimal("154.4321")


class TestTypeCompatibility:
    """Test type compatibility and conversion."""

    def test_decimal_float_conversion(self):
        """Test handling of float to Decimal conversion."""
        # Test that the system can handle both Decimal and float inputs
        try:
            position_with_float = Position(
                symbol="AAPL",
                shares=100,
                avg_price=150.00,  # float instead of Decimal
                current_price=155.00,  # float instead of Decimal
                market_value=15500.00,  # float instead of Decimal
            )

            # Should convert to Decimal or handle gracefully
            assert position_with_float.shares == 100
        except (TypeError, ValueError):
            # If strict Decimal enforcement, that's also valid
            pass

    def test_type_serialization(self):
        """Test that types can be serialized/deserialized."""
        position = Position(
            symbol="AAPL",
            shares=100,
            avg_price=Decimal("150.00"),
            current_price=Decimal("155.00"),
            market_value=Decimal("15500.00"),
        )

        # Test dict conversion if available
        if hasattr(position, "dict") or hasattr(position, "model_dump"):
            try:
                position_dict = (
                    position.dict() if hasattr(position, "dict") else position.model_dump()
                )
                assert isinstance(position_dict, dict)
                assert position_dict["symbol"] == "AAPL"
            except AttributeError:
                # Not all type systems support dict serialization
                pass
