"""Test the RebalancePlan value object."""

from decimal import Decimal

import pytest

from the_alchemiser.domain.portfolio.rebalancing.rebalance_plan import RebalancePlan


class TestRebalancePlan:
    """Test cases for RebalancePlan value object."""

    def test_rebalance_plan_creation(self):
        """Test basic RebalancePlan creation."""
        plan = RebalancePlan(
            symbol="AAPL",
            current_weight=Decimal("0.40"),
            target_weight=Decimal("0.30"),
            weight_diff=Decimal("-0.10"),
            target_value=Decimal("3000.00"),
            current_value=Decimal("4000.00"),
            trade_amount=Decimal("-1000.00"),
            needs_rebalance=True,
        )

        assert plan.symbol == "AAPL"
        assert plan.current_weight == Decimal("0.40")
        assert plan.target_weight == Decimal("0.30")
        assert plan.weight_diff == Decimal("-0.10")
        assert plan.target_value == Decimal("3000.00")
        assert plan.current_value == Decimal("4000.00")
        assert plan.trade_amount == Decimal("-1000.00")
        assert plan.needs_rebalance is True

    def test_trade_direction_sell(self):
        """Test trade_direction property for sell scenario."""
        plan = RebalancePlan(
            symbol="AAPL",
            current_weight=Decimal("0.40"),
            target_weight=Decimal("0.30"),
            weight_diff=Decimal("-0.10"),
            target_value=Decimal("3000.00"),
            current_value=Decimal("4000.00"),
            trade_amount=Decimal("-1000.00"),
            needs_rebalance=True,
        )

        assert plan.trade_direction == "SELL"

    def test_trade_direction_buy(self):
        """Test trade_direction property for buy scenario."""
        plan = RebalancePlan(
            symbol="MSFT",
            current_weight=Decimal("0.20"),
            target_weight=Decimal("0.30"),
            weight_diff=Decimal("0.10"),
            target_value=Decimal("3000.00"),
            current_value=Decimal("2000.00"),
            trade_amount=Decimal("1000.00"),
            needs_rebalance=True,
        )

        assert plan.trade_direction == "BUY"

    def test_trade_direction_hold(self):
        """Test trade_direction property for hold scenario."""
        plan = RebalancePlan(
            symbol="GOOGL",
            current_weight=Decimal("0.30"),
            target_weight=Decimal("0.30"),
            weight_diff=Decimal("0.00"),
            target_value=Decimal("3000.00"),
            current_value=Decimal("3000.00"),
            trade_amount=Decimal("0.00"),
            needs_rebalance=False,
        )

        assert plan.trade_direction == "HOLD"

    def test_trade_amount_abs(self):
        """Test trade_amount_abs property."""
        plan = RebalancePlan(
            symbol="AAPL",
            current_weight=Decimal("0.40"),
            target_weight=Decimal("0.30"),
            weight_diff=Decimal("-0.10"),
            target_value=Decimal("3000.00"),
            current_value=Decimal("4000.00"),
            trade_amount=Decimal("-1000.00"),
            needs_rebalance=True,
        )

        assert plan.trade_amount_abs == Decimal("1000.00")

    def test_weight_change_bps(self):
        """Test weight_change_bps property."""
        plan = RebalancePlan(
            symbol="AAPL",
            current_weight=Decimal("0.40"),
            target_weight=Decimal("0.30"),
            weight_diff=Decimal("-0.10"),
            target_value=Decimal("3000.00"),
            current_value=Decimal("4000.00"),
            trade_amount=Decimal("-1000.00"),
            needs_rebalance=True,
        )

        assert plan.weight_change_bps == -1000  # -0.10 * 10000 = -1000 bps

    def test_string_representation_sell(self):
        """Test string representation for sell scenario."""
        plan = RebalancePlan(
            symbol="AAPL",
            current_weight=Decimal("0.40"),
            target_weight=Decimal("0.30"),
            weight_diff=Decimal("-0.10"),
            target_value=Decimal("3000.00"),
            current_value=Decimal("4000.00"),
            trade_amount=Decimal("-1000.00"),
            needs_rebalance=True,
        )

        expected = "AAPL: SELL $1000.00 (40.0% → 30.0%)"
        assert str(plan) == expected

    def test_string_representation_buy(self):
        """Test string representation for buy scenario."""
        plan = RebalancePlan(
            symbol="MSFT",
            current_weight=Decimal("0.20"),
            target_weight=Decimal("0.30"),
            weight_diff=Decimal("0.10"),
            target_value=Decimal("3000.00"),
            current_value=Decimal("2000.00"),
            trade_amount=Decimal("1000.00"),
            needs_rebalance=True,
        )

        expected = "MSFT: BUY $1000.00 (20.0% → 30.0%)"
        assert str(plan) == expected

    def test_string_representation_hold(self):
        """Test string representation for hold scenario."""
        plan = RebalancePlan(
            symbol="GOOGL",
            current_weight=Decimal("0.30"),
            target_weight=Decimal("0.30"),
            weight_diff=Decimal("0.00"),
            target_value=Decimal("3000.00"),
            current_value=Decimal("3000.00"),
            trade_amount=Decimal("0.00"),
            needs_rebalance=False,
        )

        expected = "GOOGL: HOLD (within threshold)"
        assert str(plan) == expected

    def test_immutability(self):
        """Test that RebalancePlan is immutable."""
        plan = RebalancePlan(
            symbol="AAPL",
            current_weight=Decimal("0.40"),
            target_weight=Decimal("0.30"),
            weight_diff=Decimal("-0.10"),
            target_value=Decimal("3000.00"),
            current_value=Decimal("4000.00"),
            trade_amount=Decimal("-1000.00"),
            needs_rebalance=True,
        )

        # Attempting to modify should raise an error
        with pytest.raises(AttributeError):
            plan.symbol = "MSFT"
