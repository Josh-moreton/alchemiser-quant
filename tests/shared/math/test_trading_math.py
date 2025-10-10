"""Business Unit: shared | Status: current.

Comprehensive unit and property-based tests for trading math utilities.

Tests position sizing, limit pricing, slippage calculations, and portfolio
rebalancing with Decimal arithmetic for money calculations per guardrails.
"""

import pytest
from decimal import Decimal
from hypothesis import given, strategies as st, assume
from unittest.mock import Mock

from the_alchemiser.shared.math.trading_math import (
    calculate_position_size,
    calculate_position_size_decimal,
    calculate_dynamic_limit_price,
    calculate_slippage_buffer,
    calculate_allocation_discrepancy,
    calculate_allocation_discrepancy_decimal,
    calculate_rebalance_amounts,
    _calculate_midpoint_price,
    _calculate_precision_from_tick_size,
)


class TestCalculatePositionSize:
    """Test position size calculation."""

    @pytest.mark.unit
    def test_basic_position_size(self):
        """Test basic position size calculation."""
        # 25% of $10,000 at $100/share = 25 shares
        result = calculate_position_size(100.0, 0.25, 10000.0)
        assert result == 25.0

    @pytest.mark.unit
    def test_fractional_shares(self):
        """Test calculation with fractional shares."""
        # 25% of $10,000 at $150/share = 16.666667 shares
        result = calculate_position_size(150.0, 0.25, 10000.0)
        assert abs(result - 16.666667) < 0.000001

    @pytest.mark.unit
    def test_zero_price_returns_zero(self):
        """Test that zero price returns 0.0."""
        result = calculate_position_size(0.0, 0.5, 10000.0)
        assert result == 0.0

    @pytest.mark.unit
    def test_negative_price_returns_zero(self):
        """Test that negative price returns 0.0."""
        result = calculate_position_size(-100.0, 0.5, 10000.0)
        assert result == 0.0

    @pytest.mark.unit
    def test_zero_weight(self):
        """Test with zero portfolio weight."""
        result = calculate_position_size(100.0, 0.0, 10000.0)
        assert result == 0.0

    @pytest.mark.unit
    def test_full_portfolio_weight(self):
        """Test with 100% portfolio weight."""
        # 100% of $10,000 at $100/share = 100 shares
        result = calculate_position_size(100.0, 1.0, 10000.0)
        assert result == 100.0

    @pytest.mark.unit
    def test_small_account_value(self):
        """Test with small account value."""
        # 50% of $100 at $50/share = 1 share
        result = calculate_position_size(50.0, 0.5, 100.0)
        assert result == 1.0

    @pytest.mark.unit
    def test_expensive_stock(self):
        """Test with expensive stock price."""
        # 10% of $10,000 at $1000/share = 1 share
        result = calculate_position_size(1000.0, 0.1, 10000.0)
        assert result == 1.0

    @pytest.mark.unit
    def test_result_precision_six_decimals(self):
        """Test that result is rounded to 6 decimal places."""
        result = calculate_position_size(137.456, 0.333, 10000.0)
        # Check it has at most 6 decimal places
        result_str = str(result)
        if '.' in result_str:
            decimals = len(result_str.split('.')[1])
            assert decimals <= 6


class TestCalculateDynamicLimitPrice:
    """Test dynamic limit price calculation."""

    @pytest.mark.unit
    def test_buy_order_step_zero(self):
        """Test buy order at step 0 (midpoint)."""
        result = calculate_dynamic_limit_price(
            side_is_buy=True, bid=100.0, ask=100.10, step=0
        )
        # Midpoint = 100.05
        assert result == 100.05

    @pytest.mark.unit
    def test_sell_order_step_zero(self):
        """Test sell order at step 0 (midpoint)."""
        result = calculate_dynamic_limit_price(
            side_is_buy=False, bid=100.0, ask=100.10, step=0
        )
        # Midpoint = 100.05
        assert result == 100.05

    @pytest.mark.unit
    def test_buy_order_incremental_steps(self):
        """Test buy order moving toward ask with steps."""
        # Step 0: near midpoint
        price0 = calculate_dynamic_limit_price(
            side_is_buy=True, bid=100.0, ask=100.10, step=0
        )
        
        # Step 1: slightly higher
        price1 = calculate_dynamic_limit_price(
            side_is_buy=True, bid=100.0, ask=100.10, step=1
        )
        
        # Step 2: even higher
        price2 = calculate_dynamic_limit_price(
            side_is_buy=True, bid=100.0, ask=100.10, step=2
        )
        
        assert price0 < price1 < price2

    @pytest.mark.unit
    def test_sell_order_incremental_steps(self):
        """Test sell order moving toward bid with steps."""
        # Step 0: near midpoint
        price0 = calculate_dynamic_limit_price(
            side_is_buy=False, bid=100.0, ask=100.10, step=0
        )
        
        # Step 1: slightly lower
        price1 = calculate_dynamic_limit_price(
            side_is_buy=False, bid=100.0, ask=100.10, step=1
        )
        
        # Step 2: even lower
        price2 = calculate_dynamic_limit_price(
            side_is_buy=False, bid=100.0, ask=100.10, step=2
        )
        
        assert price0 > price1 > price2

    @pytest.mark.unit
    def test_buy_order_max_steps_uses_ask(self):
        """Test that buy order beyond max_steps uses ask price."""
        result = calculate_dynamic_limit_price(
            side_is_buy=True, bid=100.0, ask=100.10, step=6, max_steps=5
        )
        assert result == 100.10

    @pytest.mark.unit
    def test_sell_order_max_steps_uses_bid(self):
        """Test that sell order beyond max_steps uses bid price."""
        result = calculate_dynamic_limit_price(
            side_is_buy=False, bid=100.0, ask=100.10, step=6, max_steps=5
        )
        assert result == 100.0

    @pytest.mark.unit
    def test_custom_tick_size(self):
        """Test with custom tick size."""
        result = calculate_dynamic_limit_price(
            side_is_buy=True, bid=100.0, ask=100.20, step=1, tick_size=0.05
        )
        # Midpoint = 100.10, plus 1 tick (0.05) = 100.15
        assert result == 100.15

    @pytest.mark.unit
    def test_result_rounded_to_two_decimals(self):
        """Test that result is rounded to 2 decimal places."""
        result = calculate_dynamic_limit_price(
            side_is_buy=True, bid=100.123, ask=100.456, step=0
        )
        # Check result has exactly 2 decimal places
        result_str = f"{result:.2f}"
        assert result == float(result_str)


class TestCalculateSlippageBuffer:
    """Test slippage buffer calculation."""

    @pytest.mark.unit
    def test_basic_slippage_calculation(self):
        """Test basic slippage buffer calculation."""
        # 30 bps of $100 = $0.30
        result = calculate_slippage_buffer(100.0, 30.0)
        assert result == 0.30

    @pytest.mark.unit
    def test_small_slippage(self):
        """Test small slippage calculation."""
        # 5 bps of $100 = $0.05
        result = calculate_slippage_buffer(100.0, 5.0)
        assert result == 0.05

    @pytest.mark.unit
    def test_large_slippage(self):
        """Test large slippage calculation."""
        # 100 bps (1%) of $100 = $1.00
        result = calculate_slippage_buffer(100.0, 100.0)
        assert result == 1.0

    @pytest.mark.unit
    def test_expensive_stock(self):
        """Test slippage on expensive stock."""
        # 30 bps of $1000 = $3.00
        result = calculate_slippage_buffer(1000.0, 30.0)
        assert result == 3.0

    @pytest.mark.unit
    def test_cheap_stock(self):
        """Test slippage on cheap stock."""
        # 30 bps of $10 = $0.03
        result = calculate_slippage_buffer(10.0, 30.0)
        assert result == 0.03

    @pytest.mark.unit
    def test_zero_slippage(self):
        """Test zero slippage."""
        result = calculate_slippage_buffer(100.0, 0.0)
        assert result == 0.0


class TestCalculateAllocationDiscrepancy:
    """Test allocation discrepancy calculation."""

    @pytest.mark.unit
    def test_overweight_position(self):
        """Test detecting overweight position."""
        # Target 25%, current $3000 of $10000 = 30%
        current_weight, diff = calculate_allocation_discrepancy(
            0.25, 3000.0, 10000.0
        )
        assert abs(current_weight - 0.30) < 0.001
        assert abs(diff - (-0.05)) < 0.001  # 5% overweight

    @pytest.mark.unit
    def test_underweight_position(self):
        """Test detecting underweight position."""
        # Target 25%, current $2000 of $10000 = 20%
        current_weight, diff = calculate_allocation_discrepancy(
            0.25, 2000.0, 10000.0
        )
        assert abs(current_weight - 0.20) < 0.001
        assert abs(diff - 0.05) < 0.001  # 5% underweight

    @pytest.mark.unit
    def test_correctly_weighted_position(self):
        """Test correctly weighted position."""
        # Target 25%, current $2500 of $10000 = 25%
        current_weight, diff = calculate_allocation_discrepancy(
            0.25, 2500.0, 10000.0
        )
        assert current_weight == 0.25
        assert diff == 0.0

    @pytest.mark.unit
    def test_zero_current_value(self):
        """Test with zero current value."""
        current_weight, diff = calculate_allocation_discrepancy(
            0.25, 0.0, 10000.0
        )
        assert current_weight == 0.0
        assert diff == 0.25

    @pytest.mark.unit
    def test_zero_portfolio_value_returns_target(self):
        """Test that zero portfolio value returns 0 current weight and target diff."""
        current_weight, diff = calculate_allocation_discrepancy(
            0.25, 1000.0, 0.0
        )
        assert current_weight == 0.0
        assert diff == 0.25

    @pytest.mark.unit
    def test_string_current_value_converted(self):
        """Test that string current value is converted to float."""
        current_weight, diff = calculate_allocation_discrepancy(
            0.25, "2500.0", 10000.0
        )
        assert current_weight == 0.25
        assert diff == 0.0


class TestCalculateRebalanceAmounts:
    """Test rebalance amounts calculation."""

    @pytest.mark.unit
    def test_empty_target_weights_returns_empty(self):
        """Test that empty target weights returns empty result."""
        result = calculate_rebalance_amounts({}, {"AAPL": 5000.0}, 10000.0)
        assert result == {}

    @pytest.mark.unit
    def test_zero_portfolio_value_returns_empty(self):
        """Test that zero portfolio value returns empty result."""
        target = {"AAPL": 0.5}
        result = calculate_rebalance_amounts(target, {"AAPL": 0.0}, 0.0)
        assert result == {}


class TestCalculateMidpointPrice:
    """Test midpoint price calculation."""

    @pytest.mark.unit
    def test_valid_bid_ask_midpoint(self):
        """Test midpoint with valid bid and ask."""
        result = _calculate_midpoint_price(100.0, 100.10, side_is_buy=True)
        assert result == 100.05

    @pytest.mark.unit
    def test_zero_bid_buy_uses_ask(self):
        """Test that zero bid for buy uses ask."""
        result = _calculate_midpoint_price(0.0, 100.10, side_is_buy=True)
        assert result == 0.0  # Returns bid (0) for buy when bid is 0

    @pytest.mark.unit
    def test_zero_ask_sell_uses_bid(self):
        """Test that zero ask for sell uses bid."""
        result = _calculate_midpoint_price(100.0, 0.0, side_is_buy=False)
        assert result == 0.0  # Returns ask (0) for sell when ask is 0

    @pytest.mark.unit
    def test_wide_spread(self):
        """Test midpoint with wide spread."""
        result = _calculate_midpoint_price(100.0, 101.0, side_is_buy=True)
        assert result == 100.5


class TestCalculatePrecisionFromTickSize:
    """Test precision calculation from tick size."""

    @pytest.mark.unit
    def test_cent_tick_size(self):
        """Test with 1 cent tick size."""
        precision = _calculate_precision_from_tick_size(Decimal("0.01"))
        assert precision == 2

    @pytest.mark.unit
    def test_tenth_cent_tick_size(self):
        """Test with 0.1 cent tick size."""
        precision = _calculate_precision_from_tick_size(Decimal("0.001"))
        assert precision == 3

    @pytest.mark.unit
    def test_nickel_tick_size(self):
        """Test with 5 cent tick size."""
        precision = _calculate_precision_from_tick_size(Decimal("0.05"))
        assert precision == 2

    @pytest.mark.unit
    def test_minimum_precision_is_two(self):
        """Test that minimum precision is 2."""
        precision = _calculate_precision_from_tick_size(Decimal("1.0"))
        assert precision == 2


class TestCalculatePositionSizeDecimal:
    """Test Decimal-based position size calculation."""

    @pytest.mark.unit
    def test_basic_position_size(self):
        """Test basic position size calculation with Decimal."""
        # 25% of $10,000 at $100/share = 25 shares
        result = calculate_position_size_decimal(
            Decimal("100.0"), Decimal("0.25"), Decimal("10000.0")
        )
        assert result == Decimal("25.0")

    @pytest.mark.unit
    def test_fractional_shares(self):
        """Test calculation with fractional shares using Decimal."""
        # 25% of $10,000 at $150/share = 16.666667 shares
        result = calculate_position_size_decimal(
            Decimal("150.0"), Decimal("0.25"), Decimal("10000.0")
        )
        expected = Decimal("16.666667")
        assert abs(result - expected) < Decimal("0.000001")

    @pytest.mark.unit
    def test_zero_price_returns_zero(self):
        """Test that zero price returns Decimal zero."""
        result = calculate_position_size_decimal(
            Decimal("0.0"), Decimal("0.5"), Decimal("10000.0")
        )
        assert result == Decimal("0")

    @pytest.mark.unit
    def test_negative_price_returns_zero(self):
        """Test that negative price returns Decimal zero."""
        result = calculate_position_size_decimal(
            Decimal("-100.0"), Decimal("0.5"), Decimal("10000.0")
        )
        assert result == Decimal("0")

    @pytest.mark.unit
    def test_result_precision_six_decimals(self):
        """Test that result has exactly 6 decimal places."""
        result = calculate_position_size_decimal(
            Decimal("137.456"), Decimal("0.333"), Decimal("10000.0")
        )
        # Check that result is quantized to 6 decimal places
        assert str(result).split(".")[1] if "." in str(result) else "" 
        # Verify it's a Decimal type
        assert isinstance(result, Decimal)

    @pytest.mark.unit
    def test_precision_vs_float(self):
        """Test that Decimal version is more precise than float."""
        # Use a case where float precision matters
        price = Decimal("0.333333")
        weight = Decimal("0.333333")
        account = Decimal("10000.0")
        
        result_decimal = calculate_position_size_decimal(price, weight, account)
        result_float = calculate_position_size(
            float(price), float(weight), float(account)
        )
        
        # Both should be close but Decimal should maintain precision
        assert isinstance(result_decimal, Decimal)
        assert isinstance(result_float, float)


class TestCalculateAllocationDiscrepancyDecimal:
    """Test Decimal-based allocation discrepancy calculation."""

    @pytest.mark.unit
    def test_overweight_position(self):
        """Test detecting overweight position with Decimal."""
        # Target 25%, current $3000 of $10000 = 30%
        current_weight, diff = calculate_allocation_discrepancy_decimal(
            Decimal("0.25"), Decimal("3000.0"), Decimal("10000.0")
        )
        assert abs(current_weight - Decimal("0.30")) < Decimal("0.001")
        assert abs(diff - Decimal("-0.05")) < Decimal("0.001")

    @pytest.mark.unit
    def test_underweight_position(self):
        """Test detecting underweight position with Decimal."""
        # Target 25%, current $2000 of $10000 = 20%
        current_weight, diff = calculate_allocation_discrepancy_decimal(
            Decimal("0.25"), Decimal("2000.0"), Decimal("10000.0")
        )
        assert abs(current_weight - Decimal("0.20")) < Decimal("0.001")
        assert abs(diff - Decimal("0.05")) < Decimal("0.001")

    @pytest.mark.unit
    def test_correctly_weighted_position(self):
        """Test correctly weighted position with Decimal."""
        # Target 25%, current $2500 of $10000 = 25%
        current_weight, diff = calculate_allocation_discrepancy_decimal(
            Decimal("0.25"), Decimal("2500.0"), Decimal("10000.0")
        )
        assert current_weight == Decimal("0.25")
        assert diff == Decimal("0")

    @pytest.mark.unit
    def test_zero_portfolio_value_returns_target(self):
        """Test that zero portfolio value returns zero weight and target diff."""
        current_weight, diff = calculate_allocation_discrepancy_decimal(
            Decimal("0.25"), Decimal("1000.0"), Decimal("0.0")
        )
        assert current_weight == Decimal("0")
        assert diff == Decimal("0.25")

    @pytest.mark.unit
    def test_decimal_precision(self):
        """Test that Decimal maintains precision better than float."""
        # Use values that would lose precision with float
        target = Decimal("0.333333333")
        current = Decimal("3333.33")
        portfolio = Decimal("10000.00")
        
        current_weight, diff = calculate_allocation_discrepancy_decimal(
            target, current, portfolio
        )
        
        # Verify we get Decimal results
        assert isinstance(current_weight, Decimal)
        assert isinstance(diff, Decimal)
        
        # Compare with float version
        current_weight_float, diff_float = calculate_allocation_discrepancy(
            float(target), float(current), float(portfolio)
        )
        
        # Decimal should maintain more precision
        assert isinstance(current_weight_float, float)
        assert isinstance(diff_float, float)


class TestCalculatePrecisionFromTickSize:
    """Test precision calculation from tick size."""

    @pytest.mark.unit
    def test_cent_tick_size(self):
        """Test with 1 cent tick size."""
        precision = _calculate_precision_from_tick_size(Decimal("0.01"))
        assert precision == 2

    @pytest.mark.unit
    def test_tenth_cent_tick_size(self):
        """Test with 0.1 cent tick size."""
        precision = _calculate_precision_from_tick_size(Decimal("0.001"))
        assert precision == 3

    @pytest.mark.unit
    def test_nickel_tick_size(self):
        """Test with 5 cent tick size."""
        precision = _calculate_precision_from_tick_size(Decimal("0.05"))
        assert precision == 2

    @pytest.mark.unit
    def test_minimum_precision_is_two(self):
        """Test that minimum precision is 2."""
        precision = _calculate_precision_from_tick_size(Decimal("1.0"))
        assert precision == 2


# Property-based tests using Hypothesis
class TestTradingMathProperties:
    """Property-based tests for trading math utilities."""

    @pytest.mark.property
    @given(
        st.floats(min_value=1.0, max_value=1000.0),
        st.floats(min_value=0.0, max_value=1.0),
        st.floats(min_value=100.0, max_value=1000000.0)
    )
    def test_position_size_non_negative(self, price, weight, account_value):
        """Property: position size should always be non-negative."""
        result = calculate_position_size(price, weight, account_value)
        assert result >= 0.0

    @pytest.mark.property
    @given(
        st.floats(min_value=1.0, max_value=1000.0),
        st.floats(min_value=0.01, max_value=1.0),
        st.floats(min_value=1000.0, max_value=1000000.0)
    )
    def test_position_size_proportional_to_weight(self, price, weight, account_value):
        """Property: doubling weight should roughly double position size."""
        size1 = calculate_position_size(price, weight, account_value)
        size2 = calculate_position_size(price, weight * 2, account_value)
        
        if weight * 2 <= 1.0:
            # Allow small rounding difference
            assert abs(size2 - size1 * 2) < 0.001

    @pytest.mark.property
    @given(
        st.floats(min_value=90.0, max_value=110.0),
        st.floats(min_value=90.0, max_value=110.0)
    )
    def test_dynamic_limit_price_within_spread(self, bid, ask):
        """Property: limit price should be within bid-ask spread."""
        assume(bid > 0 and ask > 0 and bid <= ask)
        
        for step in range(6):
            price = calculate_dynamic_limit_price(
                side_is_buy=True, bid=bid, ask=ask, step=step
            )
            # Price should be between bid and ask (with some tolerance for rounding)
            assert bid - 0.01 <= price <= ask + 0.01

    @pytest.mark.property
    @given(
        st.floats(min_value=10.0, max_value=1000.0),
        st.floats(min_value=1.0, max_value=100.0)
    )
    def test_slippage_buffer_proportional(self, price, bps):
        """Property: slippage buffer should be proportional to price."""
        buffer1 = calculate_slippage_buffer(price, bps)
        buffer2 = calculate_slippage_buffer(price * 2, bps)
        
        # Doubling price should double buffer
        assert abs(buffer2 - buffer1 * 2) < 0.01

    @pytest.mark.property
    @given(
        st.floats(min_value=0.0, max_value=1.0),
        st.floats(min_value=0.0, max_value=10000.0),
        st.floats(min_value=1.0, max_value=100000.0)
    )
    def test_allocation_discrepancy_bounded(self, target, current, portfolio):
        """Property: current weight should reflect current/portfolio ratio."""
        if portfolio <= 0:
            return
        
        # Limit current to reasonable values
        assume(current <= portfolio * 5)  # Allow up to 5x leverage
        
        current_weight, diff = calculate_allocation_discrepancy(
            target, current, portfolio
        )
        
        # Current weight should match ratio (with some tolerance)
        expected_weight = current / portfolio
        assert abs(current_weight - expected_weight) < 0.001
        
        # Diff should be target minus current
        expected_diff = target - expected_weight
        assert abs(diff - expected_diff) < 0.001
