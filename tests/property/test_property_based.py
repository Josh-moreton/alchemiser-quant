"""
Property-based tests using Hypothesis for the Alchemiser trading system.

Tests mathematical properties, invariants, and edge cases using generated data.
"""

import pytest
from hypothesis import given, strategies as st, assume, settings
from hypothesis.stateful import RuleBasedStateMachine, rule, invariant
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta
import math

from the_alchemiser.domain.models.account_models import AccountInfo
from the_alchemiser.domain.models.order_models import OrderRequest
from the_alchemiser.domain.models.position_models import PositionInfo
from the_alchemiser.domain.models.market_data_models import BarData, QuoteData
from the_alchemiser.utils.math_utils import calculate_percentage_change, calculate_sharpe_ratio
from the_alchemiser.utils.validators import validate_symbol, validate_quantity, validate_price
from the_alchemiser.application.portfolio_rebalancer.portfolio_rebalancer import PortfolioRebalancer


class TestMathematicalProperties:
    """Test mathematical properties and invariants."""

    @given(st.decimals(min_value=0, max_value=1000000, places=2))
    def test_percentage_change_identity(self, value):
        """Test that percentage change with same values is zero."""
        old_value = value
        new_value = value

        if old_value > 0:
            change = calculate_percentage_change(old_value, new_value)
            assert abs(change) < Decimal("0.0001")  # Should be approximately zero

    @given(
        st.decimals(min_value=Decimal("0.01"), max_value=1000000, places=2),
        st.decimals(min_value=Decimal("0.01"), max_value=1000000, places=2),
    )
    def test_percentage_change_properties(self, old_value, new_value):
        """Test percentage change mathematical properties."""
        change = calculate_percentage_change(old_value, new_value)

        # Property: percentage change should be finite
        assert not math.isinf(float(change))
        assert not math.isnan(float(change))

        # Property: if new_value > old_value, change should be positive
        if new_value > old_value:
            assert change > 0
        elif new_value < old_value:
            assert change < 0

    @given(
        st.lists(st.decimals(min_value=-1, max_value=1, places=4), min_size=10, max_size=252),
        st.decimals(min_value=Decimal("0.01"), max_value=Decimal("0.10"), places=4),
    )
    def test_sharpe_ratio_properties(self, returns, risk_free_rate):
        """Test Sharpe ratio mathematical properties."""
        # Skip if all returns are zero (would cause division by zero)
        assume(not all(r == 0 for r in returns))
        assume(len(set(returns)) > 1)  # Need some variance

        sharpe = calculate_sharpe_ratio(returns, risk_free_rate)

        # Property: Sharpe ratio should be finite
        assert not math.isinf(float(sharpe))
        assert not math.isnan(float(sharpe))

        # Property: Higher average returns should generally lead to higher Sharpe
        # (given same volatility and risk-free rate)

    @given(
        st.decimals(min_value=0, max_value=1000000, places=2),
        st.decimals(min_value=0, max_value=1, places=4),
    )
    def test_portfolio_allocation_sum(self, portfolio_value, allocation_pct):
        """Test that portfolio allocations maintain mathematical consistency."""
        assume(portfolio_value > 0)

        # Calculate allocated amount
        allocated_amount = portfolio_value * allocation_pct

        # Property: allocated amount should not exceed portfolio value
        assert allocated_amount <= portfolio_value

        # Property: allocation percentage should be preserved
        if portfolio_value > 0:
            calculated_pct = allocated_amount / portfolio_value
            assert abs(calculated_pct - allocation_pct) < Decimal("0.0001")


class TestDataValidationProperties:
    """Test data validation properties across different inputs."""

    @given(st.text(min_size=1, max_size=10))
    def test_symbol_validation_properties(self, symbol):
        """Test symbol validation properties."""
        is_valid = validate_symbol(symbol)

        # Property: Valid symbols should be uppercase alphanumeric
        if is_valid:
            assert symbol.isupper()
            assert symbol.isalnum()
            assert len(symbol) >= 1
            assert len(symbol) <= 6  # Typical stock symbol length

    @given(st.decimals(min_value=-1000000, max_value=1000000, places=8))
    def test_quantity_validation_properties(self, quantity):
        """Test quantity validation properties."""
        is_valid = validate_quantity(quantity)

        # Property: Valid quantities should be positive
        if is_valid:
            assert quantity > 0

        # Property: Negative quantities should be invalid
        if quantity <= 0:
            assert not is_valid

    @given(st.decimals(min_value=-10000, max_value=10000, places=4))
    def test_price_validation_properties(self, price):
        """Test price validation properties."""
        is_valid = validate_price(price)

        # Property: Valid prices should be positive
        if is_valid:
            assert price > 0

        # Property: Negative or zero prices should be invalid
        if price <= 0:
            assert not is_valid


class TestOrderModelProperties:
    """Test order model properties with generated data."""

    @given(
        st.text(min_size=1, max_size=6, alphabet=st.characters(whitelist_categories=["Lu", "Nd"])),
        st.decimals(min_value=Decimal("0.01"), max_value=10000, places=2),
        st.sampled_from(["buy", "sell"]),
        st.sampled_from(["market", "limit", "stop"]),
    )
    def test_order_request_creation(self, symbol, quantity, side, order_type):
        """Test OrderRequest creation with various inputs."""
        try:
            order = OrderRequest(
                symbol=symbol,
                quantity=quantity,
                side=side,
                order_type=order_type,
                limit_price=None if order_type == "market" else quantity + Decimal("10"),
            )

            # Property: Created order should preserve input values
            assert order.symbol == symbol
            assert order.quantity == quantity
            assert order.side == side
            assert order.order_type == order_type

            # Property: Order should be valid according to business rules
            assert len(order.symbol) <= 6
            assert order.quantity > 0
            assert order.side in ["buy", "sell"]

        except (ValueError, InvalidOperation):
            # Some inputs may be invalid, which is expected
            pass

    @given(
        st.text(min_size=1, max_size=6, alphabet=st.characters(whitelist_categories=["Lu", "Nd"])),
        st.decimals(min_value=1, max_value=1000000, places=0),
        st.decimals(min_value=Decimal("0.01"), max_value=10000, places=2),
        st.decimals(min_value=-50000, max_value=50000, places=2),
    )
    def test_position_info_properties(self, symbol, qty, market_value, unrealized_pl):
        """Test PositionInfo properties."""
        try:
            position = PositionInfo(
                symbol=symbol,
                qty=str(qty),
                market_value=str(market_value),
                unrealized_pl=str(unrealized_pl),
                unrealized_plpc=str(unrealized_pl / market_value) if market_value != 0 else "0.0",
            )

            # Property: Position quantities should be consistent
            assert Decimal(position.qty) > 0
            assert Decimal(position.market_value) > 0

            # Property: Unrealized P&L percentage should match calculation
            calculated_plpc = Decimal(position.unrealized_pl) / Decimal(position.market_value)
            actual_plpc = Decimal(position.unrealized_plpc)
            assert abs(calculated_plpc - actual_plpc) < Decimal("0.0001")

        except (ValueError, InvalidOperation, ZeroDivisionError):
            # Some combinations may be invalid
            pass


class TestMarketDataProperties:
    """Test market data model properties."""

    @given(
        st.decimals(min_value=Decimal("0.01"), max_value=10000, places=2),
        st.decimals(min_value=Decimal("0.01"), max_value=10000, places=2),
        st.decimals(min_value=Decimal("0.01"), max_value=10000, places=2),
        st.decimals(min_value=Decimal("0.01"), max_value=10000, places=2),
        st.integers(min_value=1, max_value=100000000),
    )
    def test_bar_data_ohlc_properties(self, open_price, high_price, low_price, close_price, volume):
        """Test OHLC bar data properties."""
        # Ensure valid OHLC relationships
        assume(high_price >= max(open_price, close_price))
        assume(low_price <= min(open_price, close_price))
        assume(high_price >= low_price)

        try:
            bar = BarData(
                timestamp=datetime.now(),
                open=open_price,
                high=high_price,
                low=low_price,
                close=close_price,
                volume=volume,
            )

            # Property: High should be >= Open and Close
            assert bar.high >= bar.open
            assert bar.high >= bar.close

            # Property: Low should be <= Open and Close
            assert bar.low <= bar.open
            assert bar.low <= bar.close

            # Property: High should be >= Low
            assert bar.high >= bar.low

            # Property: Volume should be positive
            assert bar.volume > 0

        except (ValueError, InvalidOperation):
            # Some price combinations may be invalid
            pass

    @given(
        st.decimals(min_value=Decimal("0.01"), max_value=10000, places=2),
        st.decimals(min_value=Decimal("0.01"), max_value=10000, places=2),
        st.integers(min_value=1, max_value=1000000),
        st.integers(min_value=1, max_value=1000000),
    )
    def test_quote_data_properties(self, bid_price, ask_price, bid_size, ask_size):
        """Test quote data properties."""
        # Ensure ask >= bid (normal market conditions)
        assume(ask_price >= bid_price)

        try:
            quote = QuoteData(
                timestamp=datetime.now(),
                bid=bid_price,
                ask=ask_price,
                bid_size=bid_size,
                ask_size=ask_size,
            )

            # Property: Ask should be >= Bid
            assert quote.ask >= quote.bid

            # Property: Sizes should be positive
            assert quote.bid_size > 0
            assert quote.ask_size > 0

            # Property: Spread should be non-negative
            spread = quote.ask - quote.bid
            assert spread >= 0

        except (ValueError, InvalidOperation):
            pass


class TestAccountModelProperties:
    """Test account model properties."""

    @given(
        st.decimals(min_value=0, max_value=10000000, places=2),
        st.decimals(min_value=0, max_value=1000000, places=2),
        st.decimals(min_value=0, max_value=2000000, places=2),
    )
    def test_account_info_properties(self, portfolio_value, cash, buying_power):
        """Test AccountInfo model properties."""
        # Ensure logical relationships
        assume(cash <= portfolio_value)  # Cash shouldn't exceed portfolio value
        assume(buying_power >= cash)  # Buying power should be at least cash (margin)

        try:
            account = AccountInfo(
                portfolio_value=str(portfolio_value),
                cash=str(cash),
                buying_power=str(buying_power),
                equity=str(portfolio_value),  # Simplified assumption
            )

            # Property: Portfolio value should be positive or zero
            assert Decimal(account.portfolio_value) >= 0

            # Property: Cash should not exceed portfolio value
            assert Decimal(account.cash) <= Decimal(account.portfolio_value)

            # Property: Buying power should be at least cash amount
            assert Decimal(account.buying_power) >= Decimal(account.cash)

        except (ValueError, InvalidOperation):
            pass


class PortfolioRebalancingStateMachine(RuleBasedStateMachine):
    """Stateful testing for portfolio rebalancing logic."""

    def __init__(self):
        super().__init__()
        self.portfolio_value = Decimal("100000.00")
        self.positions = {}
        self.cash = Decimal("10000.00")
        self.allocations = {}

    @rule(
        symbol=st.text(min_size=1, max_size=5, alphabet=st.characters(whitelist_categories=["Lu"])),
        allocation=st.decimals(min_value=0, max_value=Decimal("0.5"), places=3),
    )
    def add_target_allocation(self, symbol, allocation):
        """Add a target allocation for a symbol."""
        self.allocations[symbol] = allocation

    @rule()
    def check_allocation_constraints(self):
        """Verify allocation constraints are maintained."""
        total_allocation = sum(self.allocations.values())

        # Invariant: Total allocation should not exceed 100%
        assert total_allocation <= Decimal("1.0")

    @rule(
        symbol=st.text(min_size=1, max_size=5, alphabet=st.characters(whitelist_categories=["Lu"])),
        quantity=st.decimals(min_value=1, max_value=1000, places=0),
        price=st.decimals(min_value=Decimal("1.00"), max_value=Decimal("1000.00"), places=2),
    )
    def add_position(self, symbol, quantity, price):
        """Add a position to the portfolio."""
        market_value = quantity * price

        # Don't exceed portfolio value
        assume(market_value <= self.portfolio_value)

        self.positions[symbol] = {
            "quantity": quantity,
            "price": price,
            "market_value": market_value,
        }

    @invariant()
    def portfolio_value_consistency(self):
        """Portfolio value should equal sum of positions plus cash."""
        total_position_value = sum(pos["market_value"] for pos in self.positions.values())

        # Allow for small rounding differences
        calculated_portfolio = total_position_value + self.cash
        assert abs(calculated_portfolio - self.portfolio_value) < Decimal("1.00")

    @invariant()
    def position_values_positive(self):
        """All position values should be positive."""
        for position in self.positions.values():
            assert position["quantity"] > 0
            assert position["price"] > 0
            assert position["market_value"] > 0


class TestStateMachineProperties:
    """Test using state machine for complex scenarios."""

    @settings(max_examples=50, stateful_step_count=20)
    def test_portfolio_rebalancing_properties(self):
        """Test portfolio rebalancing maintains invariants."""
        # Run the state machine
        state_machine = PortfolioRebalancingStateMachine()
        state_machine.run()


class TestEdgeCaseProperties:
    """Test edge cases and boundary conditions."""

    @given(st.decimals(min_value=Decimal("0.0001"), max_value=Decimal("0.01"), places=4))
    def test_very_small_values(self, small_value):
        """Test behavior with very small values."""
        # Property: Small positive values should still be valid
        assert small_value > 0

        # Property: Calculations should not underflow
        result = small_value * Decimal("1000000")
        assert result > 0

    @given(st.decimals(min_value=Decimal("1000000"), max_value=Decimal("10000000"), places=2))
    def test_very_large_values(self, large_value):
        """Test behavior with very large values."""
        # Property: Large values should still be manageable
        assert large_value > 0

        # Property: Percentage calculations should remain accurate
        percentage = large_value * Decimal("0.01")  # 1%
        assert percentage == large_value / Decimal("100")

    @given(st.lists(st.decimals(min_value=0, max_value=1, places=4), min_size=2, max_size=20))
    def test_allocation_normalization(self, raw_allocations):
        """Test allocation normalization properties."""
        assume(sum(raw_allocations) > 0)  # Avoid division by zero

        # Normalize allocations to sum to 1.0
        total = sum(raw_allocations)
        normalized = [alloc / total for alloc in raw_allocations]

        # Property: Normalized allocations should sum to 1.0
        assert abs(sum(normalized) - 1.0) < 1e-10

        # Property: Each normalized allocation should be between 0 and 1
        for alloc in normalized:
            assert 0 <= alloc <= 1

    @given(st.integers(min_value=1, max_value=1000))
    def test_scaling_properties(self, scale_factor):
        """Test that calculations scale properly."""
        base_value = Decimal("100.00")
        scaled_value = base_value * scale_factor

        # Property: Scaling should preserve ratios
        ratio = scaled_value / base_value
        assert abs(ratio - scale_factor) < Decimal("0.0001")

    @given(st.datetimes(min_value=datetime(2020, 1, 1), max_value=datetime(2030, 12, 31)))
    def test_timestamp_properties(self, timestamp):
        """Test timestamp handling properties."""
        # Property: Timestamps should be within reasonable bounds
        assert datetime(2020, 1, 1) <= timestamp <= datetime(2030, 12, 31)

        # Property: Timestamp arithmetic should work correctly
        one_day_later = timestamp + timedelta(days=1)
        assert one_day_later > timestamp

        # Property: Time differences should be calculable
        time_diff = one_day_later - timestamp
        assert time_diff == timedelta(days=1)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
