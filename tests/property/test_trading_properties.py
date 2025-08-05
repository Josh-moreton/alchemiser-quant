"""
Property-based tests for trading mathematics and calculations.

These tests verify that our mathematical functions behave correctly
across a wide range of inputs and edge cases.
"""

import math
from decimal import Decimal

from hypothesis import HealthCheck, assume, given, settings
from hypothesis import strategies as st
from hypothesis.strategies import composite


# Custom strategies for trading-specific data types
@composite
def decimal_prices(draw, min_value=0.01, max_value=10000.0):
    """Generate realistic decimal prices."""
    price = draw(
        st.floats(min_value=min_value, max_value=max_value, allow_nan=False, allow_infinity=False)
    )
    return Decimal(str(round(price, 2)))


@composite
def price_sequences(draw, min_length=2, max_length=100):
    """Generate sequences of prices for technical analysis."""
    length = draw(st.integers(min_value=min_length, max_value=max_length))
    prices = draw(
        st.lists(decimal_prices(min_value=1.0, max_value=1000.0), min_size=length, max_size=length)
    )
    return prices


@composite
def portfolio_quantities(draw, min_qty=0, max_qty=10000):
    """Generate realistic portfolio quantities."""
    return draw(st.integers(min_value=min_qty, max_value=max_qty))


class TestTradingMathProperties:
    """Property-based tests for core trading mathematics."""

    @given(price_sequences())
    def test_moving_average_properties(self, prices):
        """Test mathematical properties of moving averages."""
        assume(len(prices) >= 2)

        def simple_moving_average(prices_list, period):
            if len(prices_list) < period:
                return None
            return sum(prices_list[-period:]) / period

        # Test different periods
        for period in [2, 5, min(10, len(prices))]:
            if len(prices) >= period:
                sma = simple_moving_average(prices, period)

                # Property: SMA should be between min and max of the period
                period_prices = prices[-period:]
                assert min(period_prices) <= sma <= max(period_prices)

                # Property: SMA should be a Decimal/float
                assert isinstance(sma, (Decimal, float))

                # Property: SMA should be positive for positive prices
                assert sma > 0

    @given(price_sequences())
    def test_price_change_calculations(self, prices):
        """Test price change percentage calculations."""
        assume(len(prices) >= 2)

        def price_change_percent(old_price, new_price):
            if old_price == 0:
                return Decimal("0")
            return ((new_price - old_price) / old_price) * 100

        for i in range(1, len(prices)):
            old_price = prices[i - 1]
            new_price = prices[i]

            assume(old_price > 0)  # Avoid division by zero

            change_pct = price_change_percent(old_price, new_price)

            # Property: 100% increase should double the price
            if change_pct == 100:
                assert abs(new_price - (old_price * 2)) < Decimal("0.01")

            # Property: -50% decrease should halve the price
            if change_pct == -50:
                assert abs(new_price - (old_price / 2)) < Decimal("0.01")

            # Property: 0% change means same price
            if change_pct == 0:
                assert new_price == old_price

    @given(
        st.integers(min_value=1, max_value=1000),  # quantity
        decimal_prices(min_value=0.01, max_value=1000.0),  # price
        decimal_prices(min_value=0.01, max_value=1000.0),  # existing_avg_price
    )
    def test_average_price_calculation_properties(self, quantity, price, existing_avg_price):
        """Test properties of average price calculations."""

        def calculate_new_average_price(existing_qty, existing_avg, new_qty, new_price):
            if existing_qty == 0:
                return new_price

            total_value = (existing_qty * existing_avg) + (new_qty * new_price)
            total_qty = existing_qty + new_qty

            if total_qty == 0:
                return Decimal("0")

            return total_value / total_qty

        existing_qty = quantity
        new_qty = quantity

        new_avg = calculate_new_average_price(existing_qty, existing_avg_price, new_qty, price)

        # Property: New average should be between the two input prices
        min_price = min(existing_avg_price, price)
        max_price = max(existing_avg_price, price)
        assert min_price <= new_avg <= max_price

        # Property: If buying at same price, average shouldn't change
        if price == existing_avg_price:
            assert abs(new_avg - existing_avg_price) < Decimal("0.0001")

        # Property: Average should be positive for positive inputs
        assert new_avg > 0

    @given(
        decimal_prices(min_value=100, max_value=10000),  # cash
        portfolio_quantities(min_qty=1, max_qty=100),  # quantity
        decimal_prices(min_value=1, max_value=1000),  # price
    )
    def test_order_validation_properties(self, cash, quantity, price):
        """Test properties of order validation logic."""

        def can_afford_order(available_cash, order_quantity, order_price):
            order_value = Decimal(str(order_quantity)) * order_price
            return available_cash >= order_value

        def calculate_order_value(qty, px):
            return Decimal(str(qty)) * px

        order_value = calculate_order_value(quantity, price)
        can_afford = can_afford_order(cash, quantity, price)

        # Property: If we can afford the order, cash should be >= order value
        if can_afford:
            assert cash >= order_value

        # Property: If we can't afford the order, cash should be < order value
        if not can_afford:
            assert cash < order_value

        # Property: Order value should always be positive
        assert order_value > 0

        # Property: Doubling quantity should double order value
        double_quantity = quantity * 2
        double_order_value = calculate_order_value(double_quantity, price)
        assert abs(double_order_value - (order_value * 2)) < Decimal("0.01")

    @given(price_sequences(min_length=14, max_length=100))
    def test_rsi_calculation_properties(self, prices):
        """Test properties of RSI calculations."""
        assume(len(prices) >= 14)

        def calculate_simple_rsi(price_list, period=14):
            """Simplified RSI calculation for testing."""
            if len(price_list) < period + 1:
                return None

            changes = []
            for i in range(1, len(price_list)):
                changes.append(price_list[i] - price_list[i - 1])

            if len(changes) < period:
                return None

            gains = [max(change, 0) for change in changes[-period:]]
            losses = [abs(min(change, 0)) for change in changes[-period:]]

            avg_gain = sum(gains) / period
            avg_loss = sum(losses) / period

            if avg_loss == 0:
                return 100.0  # RSI = 100 when no losses

            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))

            return rsi

        rsi = calculate_simple_rsi(prices)

        if rsi is not None:
            # Property: RSI should always be between 0 and 100
            assert 0 <= rsi <= 100

            # Property: RSI should be a number
            assert isinstance(rsi, (int, float, Decimal))

            # Property: If all price changes are positive, RSI should be high
            changes = [prices[i] - prices[i - 1] for i in range(1, len(prices))]
            if all(change >= 0 for change in changes[-14:]):
                assert rsi >= 50  # Should be above neutral

    @given(
        decimal_prices(min_value=1, max_value=1000),  # entry_price
        decimal_prices(min_value=1, max_value=1000),  # current_price
        portfolio_quantities(min_qty=1, max_qty=1000),  # quantity
    )
    def test_pnl_calculation_properties(self, entry_price, current_price, quantity):
        """Test properties of P&L calculations."""

        def calculate_unrealized_pnl(qty, entry_px, current_px):
            return Decimal(str(qty)) * (current_px - entry_px)

        def calculate_unrealized_pnl_percent(entry_px, current_px):
            if entry_px == 0:
                return Decimal("0")
            return ((current_px - entry_px) / entry_px) * 100

        pnl = calculate_unrealized_pnl(quantity, entry_price, current_price)
        pnl_percent = calculate_unrealized_pnl_percent(entry_price, current_price)

        # Property: If current price > entry price, P&L should be positive
        if current_price > entry_price:
            assert pnl > 0
            assert pnl_percent > 0

        # Property: If current price < entry price, P&L should be negative
        if current_price < entry_price:
            assert pnl < 0
            assert pnl_percent < 0

        # Property: If prices are equal, P&L should be zero
        if current_price == entry_price:
            assert pnl == 0
            assert pnl_percent == 0

        # Property: Doubling quantity should double absolute P&L
        double_pnl = calculate_unrealized_pnl(quantity * 2, entry_price, current_price)
        assert abs(double_pnl - (pnl * 2)) < Decimal("0.01")

    @given(
        st.lists(decimal_prices(min_value=1, max_value=1000), min_size=5, max_size=50),  # prices
        st.integers(min_value=2, max_value=10),  # period
    )
    def test_bollinger_bands_properties(self, prices, period):
        """Test properties of Bollinger Bands calculations."""
        assume(len(prices) >= period)

        # Assume we have some price variation (not all identical prices)
        recent_prices = prices[-period:]
        assume(len(set(recent_prices)) > 1)  # At least 2 different prices

        def calculate_bollinger_bands(price_list, period_len, std_dev=2):
            """Simple Bollinger Bands calculation."""
            if len(price_list) < period_len:
                return None, None, None

            # Get the last period_len prices
            recent_prices = price_list[-period_len:]

            # Calculate SMA
            sma = sum(recent_prices) / len(recent_prices)

            # Calculate standard deviation
            variance = sum((price - sma) ** 2 for price in recent_prices) / len(recent_prices)
            std = Decimal(str(math.sqrt(float(variance))))

            # Calculate bands
            upper_band = sma + (std * std_dev)
            lower_band = sma - (std * std_dev)

            return lower_band, sma, upper_band

        lower, middle, upper = calculate_bollinger_bands(prices, period)

        if all(band is not None for band in [lower, middle, upper]):
            # Property: Upper band should be above middle (SMA) when there's variance
            assert upper > middle

            # Property: Lower band should be below middle (SMA) when there's variance
            assert lower < middle

            # Property: Middle band should be between lower and upper
            assert lower < middle < upper


class TestPortfolioMathProperties:
    """Property-based tests for portfolio mathematics."""

    @given(
        st.lists(
            st.tuples(
                st.text(min_size=1, max_size=10).filter(lambda x: x.isalnum()),  # symbol
                portfolio_quantities(min_qty=0, max_qty=1000),  # quantity
                decimal_prices(min_value=1, max_value=1000),  # price
            ),
            min_size=1,
            max_size=10,
        )
    )
    def test_portfolio_value_calculation_properties(self, positions):
        """Test properties of portfolio value calculations."""

        def calculate_portfolio_value(position_list):
            total_value = Decimal("0")
            for symbol, qty, price in position_list:
                position_value = Decimal(str(qty)) * price
                total_value += position_value
            return total_value

        portfolio_value = calculate_portfolio_value(positions)

        # Property: Portfolio value should be non-negative
        assert portfolio_value >= 0

        # Property: If all positions have zero quantity, value should be zero
        zero_qty_positions = [(symbol, 0, price) for symbol, qty, price in positions]
        zero_value = calculate_portfolio_value(zero_qty_positions)
        assert zero_value == 0

        # Property: Doubling all quantities should double portfolio value
        double_qty_positions = [(symbol, qty * 2, price) for symbol, qty, price in positions]
        double_value = calculate_portfolio_value(double_qty_positions)

        if portfolio_value > 0:
            ratio = double_value / portfolio_value
            assert abs(ratio - 2) < Decimal("0.01")

    @given(
        decimal_prices(min_value=1000, max_value=100000),  # initial_cash
        st.lists(
            st.tuples(
                portfolio_quantities(min_qty=1, max_qty=100),  # quantity
                decimal_prices(min_value=1, max_value=1000),  # price
            ),
            min_size=0,
            max_size=5,
        ),
    )
    def test_cash_management_properties(self, initial_cash, trades):
        """Test properties of cash management."""

        def execute_trades(starting_cash, trade_list):
            remaining_cash = starting_cash
            total_spent = Decimal("0")
            executed_trades = []

            for qty, price in trade_list:
                trade_value = Decimal(str(qty)) * price
                if remaining_cash >= trade_value:
                    remaining_cash -= trade_value
                    total_spent += trade_value
                    executed_trades.append((qty, price))

            return remaining_cash, total_spent, executed_trades

        final_cash, spent, executed = execute_trades(initial_cash, trades)

        # Property: Final cash + spent should equal initial cash
        assert abs((final_cash + spent) - initial_cash) < Decimal("0.01")

        # Property: Final cash should be non-negative
        assert final_cash >= 0

        # Property: Spent amount should be non-negative
        assert spent >= 0

        # Property: Number of executed trades should not exceed total trades
        assert len(executed) <= len(trades)


# Configure Hypothesis settings for trading tests
hypothesis_settings = settings(
    max_examples=100,  # Run more examples for financial code
    deadline=None,  # No deadline for complex calculations
    suppress_health_check=[HealthCheck.too_slow],  # Allow slower tests for thorough coverage
)
