"""Business Unit: portfolio | Status: current

Test specifically for the weight calculation fix in RebalancePlanCalculator.

This test validates that current_weight and target_weight are correctly calculated
rather than being hardcoded to 0, which was causing all SELL orders to be treated
as liquidations.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from the_alchemiser.portfolio_v2.core.planner import RebalancePlanCalculator
from the_alchemiser.portfolio_v2.models.portfolio_snapshot import PortfolioSnapshot
from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocation


class TestRebalancePlanCalculatorWeightFix:
    """Test rebalance plan calculator weight calculation fix."""

    @pytest.fixture
    def calculator(self):
        """Create rebalance plan calculator."""
        return RebalancePlanCalculator()

    def test_sell_partial_position_not_liquidation(self, calculator):
        """Test that reducing position size doesn't treat it as full liquidation.

        This addresses the issue where all SELL orders incorrectly liquidated
        the entire position because target_weight was hardcoded to 0.
        """
        # Scenario: Hold 10% AAPL, want to reduce to 5%
        portfolio = PortfolioSnapshot(
            positions={"AAPL": Decimal("10")},  # 10 shares @ $100 = $1000 (10% of $10k)
            prices={"AAPL": Decimal("100.00")},
            cash=Decimal("9000.00"),
            total_value=Decimal("10000.00"),
        )

        strategy = StrategyAllocation(
            target_weights={
                "AAPL": Decimal("0.05"),  # Target 5%
                "CASH": Decimal("0.95"),  # 95% cash
            },
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={},
        )

        plan = calculator.build_plan(strategy, portfolio, str(uuid.uuid4()))

        # Find AAPL item
        aapl_item = next(item for item in plan.items if item.symbol == "AAPL")

        # Validate the fix: weights should be calculated, not hardcoded to 0
        assert aapl_item.current_weight > Decimal("0"), "Current weight should be calculated, not 0"
        assert aapl_item.target_weight > Decimal("0"), "Target weight should be calculated, not 0"

        # Validate specific values
        assert aapl_item.target_weight == Decimal("0.05"), "Target weight should be 5%"
        assert abs(aapl_item.current_weight - Decimal("0.101")) < Decimal("0.01"), (
            "Current weight should be ~10.1% (accounting for cash reserve)"
        )

        # Validate action is SELL (partial reduction, not liquidation)
        assert aapl_item.action == "SELL", "Should be SELL action for partial reduction"

        # Validate trade amount is negative (selling) but not full liquidation
        assert aapl_item.trade_amount < Decimal("0"), "Trade amount should be negative (selling)"
        assert aapl_item.trade_amount > Decimal("-1000"), "Should not liquidate full $1000 position"
        assert abs(aapl_item.trade_amount - Decimal("-505")) < Decimal("10"), (
            "Should sell approximately $505 worth"
        )

    def test_full_liquidation_still_works(self, calculator):
        """Test that full liquidation (target weight 0%) still works correctly."""
        # Scenario: Hold 10% AAPL, want to liquidate completely (0%)
        portfolio = PortfolioSnapshot(
            positions={"AAPL": Decimal("10")},  # 10 shares @ $100 = $1000 (10% of $10k)
            prices={"AAPL": Decimal("100.00")},
            cash=Decimal("9000.00"),
            total_value=Decimal("10000.00"),
        )

        strategy = StrategyAllocation(
            target_weights={
                "CASH": Decimal("1.0"),  # 100% cash (0% AAPL)
            },
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={},
        )

        plan = calculator.build_plan(strategy, portfolio, str(uuid.uuid4()))

        # Find AAPL item
        aapl_item = next(item for item in plan.items if item.symbol == "AAPL")

        # Validate liquidation scenario
        assert aapl_item.current_weight > Decimal("0"), "Current weight should be calculated, not 0"
        assert aapl_item.target_weight == Decimal("0"), "Target weight should be 0 for liquidation"

        # Validate action is SELL (full liquidation)
        assert aapl_item.action == "SELL", "Should be SELL action for liquidation"

        # Validate trade amount is full liquidation
        assert abs(aapl_item.trade_amount - Decimal("-1000")) < Decimal("0.01"), (
            "Should liquidate full $1000 position"
        )

    def test_buy_position_weights_calculated(self, calculator):
        """Test that BUY orders also have correctly calculated weights."""
        # Scenario: Hold 5% AAPL, want to increase to 15%
        portfolio = PortfolioSnapshot(
            positions={"AAPL": Decimal("5")},  # 5 shares @ $100 = $500 (5% of $10k)
            prices={"AAPL": Decimal("100.00")},
            cash=Decimal("9500.00"),
            total_value=Decimal("10000.00"),
        )

        strategy = StrategyAllocation(
            target_weights={
                "AAPL": Decimal("0.15"),  # Target 15%
                "CASH": Decimal("0.85"),  # 85% cash
            },
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={},
        )

        plan = calculator.build_plan(strategy, portfolio, str(uuid.uuid4()))

        # Find AAPL item
        aapl_item = next(item for item in plan.items if item.symbol == "AAPL")

        # Validate weights are calculated correctly
        assert aapl_item.current_weight > Decimal("0"), "Current weight should be calculated, not 0"
        assert aapl_item.target_weight > Decimal("0"), "Target weight should be calculated, not 0"

        # Validate specific values
        assert aapl_item.target_weight == Decimal("0.15"), "Target weight should be 15%"
        assert abs(aapl_item.current_weight - Decimal("0.0505")) < Decimal("0.01"), (
            "Current weight should be ~5.05%"
        )

        # Validate action is BUY
        assert aapl_item.action == "BUY", "Should be BUY action for position increase"

        # Validate trade amount is positive (buying)
        assert aapl_item.trade_amount > Decimal("0"), "Trade amount should be positive (buying)"

    def test_weight_diff_calculation(self, calculator):
        """Test that weight_diff is calculated correctly as target - current."""
        portfolio = PortfolioSnapshot(
            positions={"AAPL": Decimal("10")},  # 10 shares @ $100 = $1000 (10% of $10k)
            prices={"AAPL": Decimal("100.00")},
            cash=Decimal("9000.00"),
            total_value=Decimal("10000.00"),
        )

        strategy = StrategyAllocation(
            target_weights={
                "AAPL": Decimal("0.05"),  # Target 5%
                "CASH": Decimal("0.95"),  # 95% cash
            },
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={},
        )

        plan = calculator.build_plan(strategy, portfolio, str(uuid.uuid4()))

        # Find AAPL item
        aapl_item = next(item for item in plan.items if item.symbol == "AAPL")

        # Validate weight_diff is calculated correctly
        expected_weight_diff = aapl_item.target_weight - aapl_item.current_weight
        assert abs(aapl_item.weight_diff - expected_weight_diff) < Decimal("0.0001"), (
            "weight_diff should equal target_weight - current_weight"
        )

        # Since target (5%) < current (~10%), weight_diff should be negative
        assert aapl_item.weight_diff < Decimal("0"), (
            "weight_diff should be negative when reducing position"
        )
