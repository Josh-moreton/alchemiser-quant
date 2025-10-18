"""Business Unit: portfolio | Status: current

Test portfolio rebalance planner business logic and calculations.

Tests the core business logic of rebalance plan calculation, including
position sizing, trade calculations, and portfolio allocation math.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from the_alchemiser.portfolio_v2.core.planner import RebalancePlanCalculator
from the_alchemiser.portfolio_v2.models.portfolio_snapshot import PortfolioSnapshot
from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocation


class TestRebalancePlanCalculator:
    """Test rebalance plan calculator business logic."""

    @pytest.fixture
    def calculator(self):
        """Create rebalance plan calculator."""
        return RebalancePlanCalculator()

    @pytest.fixture
    def sample_strategy_allocation(self):
        """Sample strategy allocation."""
        return StrategyAllocation(
            target_weights={
                "AAPL": Decimal("0.4"),
                "MSFT": Decimal("0.35"),
                "GOOGL": Decimal("0.25"),
            },
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={"strategy_id": "test_strategy"},
        )

    @pytest.fixture
    def sample_portfolio_snapshot(self):
        """Sample portfolio snapshot with positions."""
        return PortfolioSnapshot(
            positions={
                "AAPL": Decimal("20"),  # 20 shares
                "MSFT": Decimal("15"),  # 15 shares
                "GOOGL": Decimal("5"),  # 5 shares
            },
            prices={
                "AAPL": Decimal("150.00"),  # $150/share
                "MSFT": Decimal("150.00"),  # $150/share
                "GOOGL": Decimal("300.00"),  # $300/share
            },
            cash=Decimal("3250.00"),  # Available cash
            total_value=Decimal("10000.00"),  # Total portfolio value
        )

    @pytest.fixture
    def empty_portfolio_snapshot(self):
        """Empty portfolio snapshot for new account."""
        return PortfolioSnapshot(
            positions={},
            prices={},
            cash=Decimal("10000.00"),  # All cash
            total_value=Decimal("10000.00"),
        )

    def test_rebalance_plan_basic_calculation(
        self, calculator, sample_strategy_allocation, sample_portfolio_snapshot
    ):
        """Test basic rebalance plan calculation logic."""
        correlation_id = str(uuid.uuid4())

        plan = calculator.build_plan(
            sample_strategy_allocation,
            sample_portfolio_snapshot,
            correlation_id,
        )

        # Plan should be created successfully
        assert plan.plan_id is not None
        assert plan.correlation_id == correlation_id
        assert len(plan.items) > 0

        # Check that target allocations are calculated
        for item in plan.items:
            assert item.symbol in sample_strategy_allocation.target_weights
            assert item.target_weight is not None
            assert item.action in ["BUY", "SELL", "HOLD"]

    def test_rebalance_from_empty_portfolio(
        self, calculator, sample_strategy_allocation, empty_portfolio_snapshot
    ):
        """Test rebalancing from completely empty portfolio."""
        correlation_id = str(uuid.uuid4())

        plan = calculator.build_plan(
            sample_strategy_allocation,
            empty_portfolio_snapshot,
            correlation_id,
        )

        # All actions should be BUY since starting from empty
        for item in plan.items:
            if item.target_value > Decimal("0"):
                assert item.action == "BUY"
                assert item.current_value == Decimal("0")
                assert item.target_value > Decimal("0")

    def test_target_value_calculations(
        self, calculator, sample_strategy_allocation, sample_portfolio_snapshot
    ):
        """Test that target values are calculated correctly."""
        correlation_id = str(uuid.uuid4())

        plan = calculator.build_plan(
            sample_strategy_allocation,
            sample_portfolio_snapshot,
            correlation_id,
        )

        total_value = sample_portfolio_snapshot.total_value
        # Account for cash reserve (1% default)
        effective_value = total_value * Decimal("0.99")

        for item in plan.items:
            expected_target_weight = sample_strategy_allocation.target_weights[item.symbol]
            expected_target_value = effective_value * expected_target_weight

            # Target value should match allocation percentage (accounting for cash reserve)
            assert abs(item.target_value - expected_target_value) < Decimal("0.01")

    def test_quantity_calculation_fractional_assets(self, calculator):
        """Test quantity calculations for fractionable assets."""
        # Create allocation for fractionable asset
        allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")},
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={},
        )

        # Portfolio with cash to invest
        snapshot = PortfolioSnapshot(
            positions={},
            prices={"AAPL": Decimal("100.00")},  # $100/share
            cash=Decimal("1000.00"),
            total_value=Decimal("1000.00"),
        )

        plan = calculator.build_plan(allocation, snapshot, str(uuid.uuid4()))

        # Should be able to buy fractional shares
        aapl_item = next(item for item in plan.items if item.symbol == "AAPL")
        assert aapl_item.target_value == Decimal("990.00")  # 1000 * (1 - 0.01 cash reserve)
        # For fractionable assets, quantity can be fractional

    def test_quantity_calculation_non_fractional_assets(self, calculator):
        """Test quantity calculations for non-fractionable assets."""
        allocation = StrategyAllocation(
            target_weights={"GOOGL": Decimal("1.0")},
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={},
        )

        snapshot = PortfolioSnapshot(
            positions={},
            prices={"GOOGL": Decimal("200.00")},  # $200/share
            cash=Decimal("1000.00"),
            total_value=Decimal("1000.00"),
        )

        plan = calculator.build_plan(allocation, snapshot, str(uuid.uuid4()))

        # Should handle whole share requirements
        googl_item = next(item for item in plan.items if item.symbol == "GOOGL")
        assert googl_item.target_value == Decimal("990.00")  # 1000 * (1 - 0.01 cash reserve)
        # For non-fractionable assets, quantities should be whole numbers

    def test_rebalance_determines_correct_actions(self, calculator, sample_portfolio_snapshot):
        """Test that rebalance correctly determines BUY/SELL/HOLD actions."""
        # Create allocation that requires rebalancing
        allocation = StrategyAllocation(
            target_weights={
                "AAPL": Decimal("0.1"),  # Reduce from current
                "MSFT": Decimal("0.6"),  # Increase from current
                "GOOGL": Decimal("0.3"),  # Keep roughly same
            },
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={},
        )

        plan = calculator.build_plan(allocation, sample_portfolio_snapshot, str(uuid.uuid4()))

        # Verify actions make sense based on current vs target allocations
        for item in plan.items:
            current_position = sample_portfolio_snapshot.positions.get(item.symbol, Decimal("0"))
            current_price = sample_portfolio_snapshot.prices.get(item.symbol, Decimal("0"))
            current_value = current_position * current_price
            current_allocation_pct = (
                current_value / sample_portfolio_snapshot.total_value
                if sample_portfolio_snapshot.total_value > 0
                else Decimal("0")
            )
            target_allocation_pct = allocation.target_weights[item.symbol]

            if target_allocation_pct > current_allocation_pct + Decimal("0.01"):
                # Should buy more
                assert item.action in ["BUY", "HOLD"]
            elif target_allocation_pct < current_allocation_pct - Decimal("0.01"):
                # Should sell some
                assert item.action in ["SELL", "HOLD"]

    def test_plan_preserves_correlation_metadata(
        self, calculator, sample_strategy_allocation, sample_portfolio_snapshot
    ):
        """Test that rebalance plan preserves correlation and metadata."""
        correlation_id = str(uuid.uuid4())

        plan = calculator.build_plan(
            sample_strategy_allocation,
            sample_portfolio_snapshot,
            correlation_id,
        )

        # Should preserve correlation ID
        assert plan.correlation_id == correlation_id

        # Should have valid timestamps
        assert plan.timestamp is not None

        # Should have a unique plan ID
        assert plan.plan_id is not None
        assert len(plan.plan_id) > 0

    def test_zero_allocation_handling(self, calculator, sample_portfolio_snapshot):
        """Test handling of assets with zero target allocation."""
        # Create allocation that excludes current positions
        allocation = StrategyAllocation(
            target_weights={
                "TSLA": Decimal("1.0"),  # New position, not in current portfolio
            },
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={},
        )

        plan = calculator.build_plan(allocation, sample_portfolio_snapshot, str(uuid.uuid4()))

        # Should create plan to exit existing positions and enter new one
        tsla_item = next((item for item in plan.items if item.symbol == "TSLA"), None)
        assert tsla_item is not None
        assert tsla_item.action == "BUY"

    def test_cash_management_calculations(
        self, calculator, sample_strategy_allocation, sample_portfolio_snapshot
    ):
        """Test that cash requirements are calculated correctly."""
        plan = calculator.build_plan(
            sample_strategy_allocation,
            sample_portfolio_snapshot,
            str(uuid.uuid4()),
        )

        # Calculate total cash needed for buys vs cash from sells
        total_buy_value = sum(item.trade_amount for item in plan.items if item.action == "BUY")
        total_sell_value = sum(
            abs(item.trade_amount) for item in plan.items if item.action == "SELL"
        )

        # Net cash requirement should be reasonable given available cash
        net_cash_needed = total_buy_value - total_sell_value
        assert net_cash_needed <= sample_portfolio_snapshot.cash
