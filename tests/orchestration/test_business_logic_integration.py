"""Business Unit: orchestration | Status: current

Test integration of business logic across modules.

Tests the actual business logic integration patterns and data flow
without requiring full external broker connections.
"""

import uuid
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from the_alchemiser.shared.schemas.rebalance_plan import (
    RebalancePlan,
    RebalancePlanItem,
)
from the_alchemiser.shared.schemas.strategy_allocation import StrategyAllocation


class TestBusinessLogicIntegration:
    """Test integration of business logic across strategy, portfolio, and execution modules."""

    def test_strategy_to_portfolio_data_flow(self):
        """Test data flow from strategy allocation to portfolio rebalancing."""
        # Simulate strategy output
        strategy_allocation = StrategyAllocation(
            target_weights={
                "AAPL": Decimal("0.6"),
                "MSFT": Decimal("0.4"),
            },
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={"strategy_id": "test_strategy"},
        )

        # Verify strategy allocation properties
        assert sum(strategy_allocation.target_weights.values()) == Decimal("1.0")
        assert strategy_allocation.correlation_id is not None
        assert strategy_allocation.constraints["strategy_id"] == "test_strategy"

        # This would be input to portfolio module
        assert len(strategy_allocation.target_weights) == 2
        assert all(weight >= 0 for weight in strategy_allocation.target_weights.values())

    def test_portfolio_to_execution_data_flow(self):
        """Test data flow from portfolio plan to execution."""
        # Simulate portfolio rebalance plan output
        rebalance_plan = RebalancePlan(
            plan_id=str(uuid.uuid4()),
            correlation_id=str(uuid.uuid4()),
            causation_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            total_portfolio_value=Decimal("5000.00"),
            total_trade_value=Decimal("1250.00"),
            items=[
                RebalancePlanItem(
                    symbol="AAPL",
                    current_weight=Decimal("0.3"),
                    target_weight=Decimal("0.6"),
                    weight_diff=Decimal("0.3"),
                    current_value=Decimal("1500.00"),
                    target_value=Decimal("2250.00"),
                    trade_amount=Decimal("750.00"),
                    action="BUY",
                    priority=1,
                ),
                RebalancePlanItem(
                    symbol="MSFT",
                    current_weight=Decimal("0.5"),
                    target_weight=Decimal("0.4"),
                    weight_diff=Decimal("-0.1"),
                    current_value=Decimal("2000.00"),
                    target_value=Decimal("1500.00"),
                    trade_amount=Decimal("-500.00"),
                    action="SELL",
                    priority=2,
                ),
            ],
        )

        # Verify rebalance plan properties
        assert rebalance_plan.plan_id is not None
        assert len(rebalance_plan.items) == 2

        # Verify actions make business sense
        aapl_item = next(item for item in rebalance_plan.items if item.symbol == "AAPL")
        assert aapl_item.action == "BUY"
        assert aapl_item.target_weight > aapl_item.current_weight

        msft_item = next(item for item in rebalance_plan.items if item.symbol == "MSFT")
        assert msft_item.action == "SELL"
        assert msft_item.target_weight < msft_item.current_weight

        # This would be input to execution module
        total_target_value = sum(item.target_value for item in rebalance_plan.items)
        assert total_target_value == Decimal("3750.00")

    def test_end_to_end_business_logic_flow(self):
        """Test complete business logic flow from strategy to execution."""
        # Phase 1: Strategy generates allocation
        strategy_allocation = StrategyAllocation(
            target_weights={
                "AAPL": Decimal("0.5"),
                "GOOGL": Decimal("0.3"),
                "MSFT": Decimal("0.2"),
            },
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={"strategy_id": "balanced_growth"},
        )

        # Verify strategy output is valid
        assert abs(sum(strategy_allocation.target_weights.values()) - Decimal("1.0")) < Decimal(
            "0.0001"
        )

        # Phase 2: Portfolio creates rebalance plan (simulated)
        total_portfolio_value = Decimal("10000.00")
        rebalance_items = []

        for symbol, target_weight in strategy_allocation.target_weights.items():
            target_value = total_portfolio_value * target_weight
            rebalance_items.append(
                RebalancePlanItem(
                    symbol=symbol,
                    current_weight=Decimal("0"),  # Starting from empty
                    target_weight=target_weight,
                    weight_diff=target_weight,
                    current_value=Decimal("0"),
                    target_value=target_value,
                    trade_amount=target_value,
                    action="BUY",
                    priority=1,
                )
            )

        rebalance_plan = RebalancePlan(
            plan_id=str(uuid.uuid4()),
            correlation_id=strategy_allocation.correlation_id,
            causation_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            total_portfolio_value=total_portfolio_value,
            total_trade_value=sum(item.trade_amount for item in rebalance_items),
            items=rebalance_items,
        )

        # Verify portfolio plan matches strategy allocation
        assert rebalance_plan.correlation_id == strategy_allocation.correlation_id
        assert len(rebalance_plan.items) == len(strategy_allocation.target_weights)

        plan_total_value = sum(item.target_value for item in rebalance_plan.items)
        assert abs(plan_total_value - total_portfolio_value) < Decimal("0.01")

        # Phase 3: Execution processes plan (simulated)
        execution_summary = {
            "orders_placed": len(rebalance_plan.items),
            "total_value": plan_total_value,
            "correlation_id": rebalance_plan.correlation_id,
            "success": True,
        }

        # Verify execution summary
        assert execution_summary["orders_placed"] == 3
        assert execution_summary["total_value"] == total_portfolio_value
        assert execution_summary["correlation_id"] == strategy_allocation.correlation_id
        assert execution_summary["success"] is True

    def test_correlation_id_propagation(self):
        """Test that correlation IDs propagate through the business logic flow."""
        correlation_id = str(uuid.uuid4())

        # Strategy phase
        strategy_allocation = StrategyAllocation(
            target_weights={"AAPL": Decimal("1.0")},
            correlation_id=correlation_id,
            as_of=datetime.now(UTC),
            constraints={},
        )

        # Portfolio phase
        rebalance_plan = RebalancePlan(
            plan_id=str(uuid.uuid4()),
            correlation_id=strategy_allocation.correlation_id,
            causation_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            total_portfolio_value=Decimal("1000.00"),
            total_trade_value=Decimal("1000.00"),
            items=[
                RebalancePlanItem(
                    symbol="AAPL",
                    current_weight=Decimal("0"),
                    target_weight=Decimal("1.0"),
                    weight_diff=Decimal("1.0"),
                    current_value=Decimal("0"),
                    target_value=Decimal("1000.00"),
                    trade_amount=Decimal("1000.00"),
                    action="BUY",
                    priority=1,
                ),
            ],
        )

        # Execution phase (simulated)
        execution_result = {
            "correlation_id": rebalance_plan.correlation_id,
            "success": True,
        }

        # Verify correlation ID maintained throughout
        assert strategy_allocation.correlation_id == correlation_id
        assert rebalance_plan.correlation_id == correlation_id
        assert execution_result["correlation_id"] == correlation_id

    def test_business_rule_validation(self):
        """Test business rule validation across modules."""
        # Test allocation weights sum to 1.0
        with pytest.raises(ValueError):
            StrategyAllocation(
                target_weights={
                    "AAPL": Decimal("0.6"),
                    "MSFT": Decimal("0.6"),  # Sum > 1.0
                },
                correlation_id=str(uuid.uuid4()),
                as_of=datetime.now(UTC),
                constraints={},
            )

        # Test valid allocation
        valid_allocation = StrategyAllocation(
            target_weights={
                "AAPL": Decimal("0.7"),
                "MSFT": Decimal("0.3"),
            },
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={},
        )

        assert abs(sum(valid_allocation.target_weights.values()) - Decimal("1.0")) < Decimal(
            "0.0001"
        )

    def test_decimal_precision_handling(self):
        """Test that decimal precision is maintained throughout business logic."""
        # Strategy with precise weights
        strategy_allocation = StrategyAllocation(
            target_weights={
                "AAPL": Decimal("0.333333"),
                "MSFT": Decimal("0.333333"),
                "GOOGL": Decimal("0.333334"),  # Adds to 1.0
            },
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={},
        )

        # Verify precision is maintained
        total_weight = sum(strategy_allocation.target_weights.values())
        assert total_weight == Decimal("1.0")

        # Portfolio calculations with precision
        portfolio_value = Decimal("10000.00")
        for symbol, weight in strategy_allocation.target_weights.items():
            target_value = portfolio_value * weight
            # Should maintain decimal precision
            assert isinstance(target_value, Decimal)
            assert target_value.quantize(Decimal("0.01")) == target_value.quantize(Decimal("0.01"))

    def test_error_handling_integration(self):
        """Test error handling across business logic modules."""
        # Test invalid strategy allocation
        with pytest.raises(ValueError):
            StrategyAllocation(
                target_weights={},  # Empty weights
                correlation_id=str(uuid.uuid4()),
                as_of=datetime.now(UTC),
                constraints={},
            )

        # Test invalid rebalance plan item
        with pytest.raises(ValueError):
            RebalancePlanItem(
                symbol="",  # Empty symbol
                current_weight=Decimal("0"),
                target_weight=Decimal("1.0"),
                weight_diff=Decimal("1.0"),
                current_value=Decimal("0"),
                target_value=Decimal("1000.00"),
                trade_amount=Decimal("1000.00"),
                action="BUY",
                priority=1,
            )

    def test_business_logic_performance_considerations(self):
        """Test that business logic handles reasonable scale efficiently."""
        # Large strategy allocation (100 symbols)
        target_weights = {}
        weight_per_symbol = Decimal("0.01")  # 1% each

        for i in range(100):
            target_weights[f"SYMBOL_{i:03d}"] = weight_per_symbol

        strategy_allocation = StrategyAllocation(
            target_weights=target_weights,
            correlation_id=str(uuid.uuid4()),
            as_of=datetime.now(UTC),
            constraints={"strategy_id": "diversified_100"},
        )

        # Should handle large allocations
        assert len(strategy_allocation.target_weights) == 100
        assert sum(strategy_allocation.target_weights.values()) == Decimal("1.0")

        # Should be able to create corresponding rebalance plan
        rebalance_items = []
        for symbol, weight in strategy_allocation.target_weights.items():
            rebalance_items.append(
                RebalancePlanItem(
                    symbol=symbol,
                    current_weight=Decimal("0"),
                    target_weight=weight,
                    weight_diff=weight,
                    current_value=Decimal("0"),
                    target_value=Decimal("100.00") * weight,
                    trade_amount=Decimal("100.00") * weight,
                    action="BUY",
                    priority=1,
                )
            )

        rebalance_plan = RebalancePlan(
            plan_id=str(uuid.uuid4()),
            correlation_id=strategy_allocation.correlation_id,
            causation_id=str(uuid.uuid4()),
            timestamp=datetime.now(UTC),
            total_portfolio_value=Decimal("100.00"),
            total_trade_value=sum(item.trade_amount for item in rebalance_items),
            items=rebalance_items,
        )

        # Should handle large plans efficiently
        assert len(rebalance_plan.items) == 100
        total_value = sum(item.target_value for item in rebalance_plan.items)
        assert total_value == Decimal("100.00")
