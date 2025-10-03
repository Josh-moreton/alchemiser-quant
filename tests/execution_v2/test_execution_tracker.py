"""Business Unit: execution | Status: current

Test execution tracker functionality.

Tests logging and health check capabilities without external dependencies.
"""

from datetime import UTC, datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch
import uuid

import pytest

from the_alchemiser.execution_v2.core.execution_tracker import ExecutionTracker
from the_alchemiser.execution_v2.models.execution_result import (
    ExecutionResult,
    ExecutionStatus,
    OrderResult,
)
from the_alchemiser.shared.schemas.rebalance_plan import RebalancePlan, RebalancePlanItem


def _make_rebalance_plan_item(
    symbol: str = "AAPL",
    *,
    action: str = "BUY",
    trade_amount: Decimal = Decimal("1000.00"),
    target_weight: Decimal = Decimal("0.5"),
    current_weight: Decimal = Decimal("0.3"),
) -> RebalancePlanItem:
    """Create a test rebalance plan item."""
    weight_diff = target_weight - current_weight
    # Calculate values assuming $10,000 portfolio
    portfolio_value = Decimal("10000.00")
    target_value = portfolio_value * target_weight
    current_value = portfolio_value * current_weight
    
    return RebalancePlanItem(
        symbol=symbol,
        action=action,
        trade_amount=trade_amount,
        target_weight=target_weight,
        current_weight=current_weight,
        weight_diff=weight_diff,
        target_value=target_value,
        current_value=current_value,
        priority=1,
    )


def _make_rebalance_plan(
    items: list[RebalancePlanItem] | None = None, plan_id: str | None = None
) -> RebalancePlan:
    """Create a test rebalance plan."""
    if items is None:
        items = [_make_rebalance_plan_item()]
    
    total_trade_value = sum(abs(item.trade_amount) for item in items)
    
    return RebalancePlan(
        plan_id=plan_id or f"plan-{uuid.uuid4()}",
        items=items,
        total_trade_value=total_trade_value,
        total_portfolio_value=Decimal("10000.00"),
        correlation_id=f"corr-{uuid.uuid4()}",
        causation_id=f"cause-{uuid.uuid4()}",
        timestamp=datetime.now(UTC),
    )


def _make_order_result(
    symbol: str,
    *,
    action: str = "BUY",
    shares: Decimal = Decimal("10"),
    trade_amount: Decimal = Decimal("100.00"),
    success: bool = True,
    price: Decimal | None = Decimal("10.00"),
    order_id: str | None = None,
    error_message: str | None = None,
) -> OrderResult:
    """Create a test order result."""
    return OrderResult(
        symbol=symbol,
        action=action,
        trade_amount=trade_amount,
        shares=shares,
        price=price,
        order_id=order_id or f"order-{uuid.uuid4()}",
        success=success,
        error_message=error_message,
        timestamp=datetime.now(UTC),
    )


def _make_execution_result(
    *,
    success: bool = True,
    status: ExecutionStatus = ExecutionStatus.SUCCESS,
    orders: list[OrderResult] | None = None,
    plan_id: str | None = None,
) -> ExecutionResult:
    """Create a test execution result."""
    if orders is None:
        orders = []
    orders_placed = len(orders)
    orders_succeeded = sum(1 for o in orders if o.success)
    total_trade_value = sum(o.trade_amount for o in orders if o.success)

    return ExecutionResult(
        success=success,
        status=status,
        plan_id=plan_id or f"plan-{uuid.uuid4()}",
        correlation_id=f"corr-{uuid.uuid4()}",
        orders=orders,
        orders_placed=orders_placed,
        orders_succeeded=orders_succeeded,
        total_trade_value=Decimal(str(total_trade_value)),  # Ensure Decimal type
        execution_timestamp=datetime.now(UTC),
        metadata={},
    )


class TestExecutionTracker:
    """Test ExecutionTracker logging and health checking."""

    def test_log_plan_received_with_items(self):
        """Test logging when plan is received with multiple items."""
        items = [
            _make_rebalance_plan_item(
                symbol="AAPL",
                action="BUY",
                trade_amount=Decimal("1000.00"),
                target_weight=Decimal("0.5"),
                current_weight=Decimal("0.3"),
            ),
            _make_rebalance_plan_item(
                symbol="MSFT",
                action="SELL",
                trade_amount=Decimal("-500.00"),
                target_weight=Decimal("0.2"),
                current_weight=Decimal("0.4"),
            ),
        ]
        plan = _make_rebalance_plan(items=items)

        with patch("the_alchemiser.execution_v2.core.execution_tracker.logger") as mock_logger:
            ExecutionTracker.log_plan_received(plan)

            # Should log plan summary
            assert mock_logger.info.call_count >= 3  # Header + items
            mock_logger.info.assert_any_call(f"📋 Plan received: {plan.plan_id}")

    def test_log_plan_received_empty_plan(self):
        """Test logging when plan has minimal items."""
        plan = _make_rebalance_plan()  # Default single item plan

        with patch("the_alchemiser.execution_v2.core.execution_tracker.logger") as mock_logger:
            ExecutionTracker.log_plan_received(plan)

            # Should still log plan header
            mock_logger.info.assert_any_call(f"📋 Plan received: {plan.plan_id}")

    def test_log_execution_summary_all_success(self):
        """Test logging execution summary when all orders succeed."""
        orders = [
            _make_order_result("AAPL", success=True, trade_amount=Decimal("1000.00")),
            _make_order_result("MSFT", success=True, trade_amount=Decimal("500.00")),
        ]
        result = _make_execution_result(success=True, orders=orders)
        plan = _make_rebalance_plan(plan_id=result.plan_id)

        with patch("the_alchemiser.execution_v2.core.execution_tracker.logger") as mock_logger:
            ExecutionTracker.log_execution_summary(plan, result)

            # Check success rate logged (should be 100%)
            calls = [str(call) for call in mock_logger.info.call_args_list]
            assert any("100.0%" in str(call) for call in calls)

    def test_log_execution_summary_partial_success(self):
        """Test logging execution summary when some orders fail."""
        orders = [
            _make_order_result("AAPL", success=True, trade_amount=Decimal("1000.00")),
            _make_order_result(
                "MSFT",
                success=False,
                trade_amount=Decimal("0"),
                error_message="Insufficient funds",
            ),
        ]
        result = _make_execution_result(success=False, orders=orders)
        plan = _make_rebalance_plan(plan_id=result.plan_id)

        with patch("the_alchemiser.execution_v2.core.execution_tracker.logger") as mock_logger:
            ExecutionTracker.log_execution_summary(plan, result)

            # Should log failure count and details
            mock_logger.warning.assert_any_call("  Failed Orders: 1")
            # Should log the specific failure
            warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
            assert any("MSFT" in str(call) for call in warning_calls)

    def test_log_execution_summary_all_failures(self):
        """Test logging execution summary when all orders fail."""
        orders = [
            _make_order_result(
                "AAPL",
                success=False,
                trade_amount=Decimal("0"),
                error_message="Market closed",
            ),
            _make_order_result(
                "MSFT",
                success=False,
                trade_amount=Decimal("0"),
                error_message="Insufficient funds",
            ),
        ]
        result = _make_execution_result(success=False, orders=orders)
        plan = _make_rebalance_plan(plan_id=result.plan_id)

        with patch("the_alchemiser.execution_v2.core.execution_tracker.logger") as mock_logger:
            ExecutionTracker.log_execution_summary(plan, result)

            # Should log 0% success rate
            calls = [str(call) for call in mock_logger.info.call_args_list]
            assert any("0.0%" in str(call) for call in calls)

    def test_check_execution_health_all_success(self):
        """Test health check with 100% success rate."""
        orders = [
            _make_order_result("AAPL", success=True),
            _make_order_result("MSFT", success=True),
        ]
        result = _make_execution_result(success=True, orders=orders)

        with patch("the_alchemiser.execution_v2.core.execution_tracker.logger") as mock_logger:
            ExecutionTracker.check_execution_health(result)

            # Should log healthy status
            info_calls = [str(call) for call in mock_logger.info.call_args_list]
            assert any("✅ Healthy execution" in str(call) for call in info_calls)

    def test_check_execution_health_elevated_failure_rate(self):
        """Test health check with elevated failure rate (>20%)."""
        orders = [
            _make_order_result("AAPL", success=True),
            _make_order_result("MSFT", success=True),
            _make_order_result("GOOGL", success=False, trade_amount=Decimal("0")),
        ]
        result = _make_execution_result(success=False, orders=orders)

        with patch("the_alchemiser.execution_v2.core.execution_tracker.logger") as mock_logger:
            ExecutionTracker.check_execution_health(result)

            # Should log warning for elevated failure rate (33%)
            warning_calls = [str(call) for call in mock_logger.warning.call_args_list]
            assert any("⚠️ Elevated failure rate" in str(call) for call in warning_calls)

    def test_check_execution_health_high_failure_rate(self):
        """Test health check with high failure rate (>50%)."""
        orders = [
            _make_order_result("AAPL", success=False, trade_amount=Decimal("0")),
            _make_order_result("MSFT", success=False, trade_amount=Decimal("0")),
            _make_order_result("GOOGL", success=True),
        ]
        result = _make_execution_result(success=False, orders=orders)

        with patch("the_alchemiser.execution_v2.core.execution_tracker.logger") as mock_logger:
            ExecutionTracker.check_execution_health(result)

            # Should log critical alert (67% failure)
            critical_calls = [str(call) for call in mock_logger.critical.call_args_list]
            assert any("🚨 HIGH FAILURE RATE" in str(call) for call in critical_calls)

    def test_check_execution_health_zero_orders(self):
        """Test health check with no orders."""
        result = _make_execution_result(success=True, orders=[])

        with patch("the_alchemiser.execution_v2.core.execution_tracker.logger") as mock_logger:
            # Should not raise errors with empty orders
            ExecutionTracker.check_execution_health(result)

            # Should still produce some logging output
            assert mock_logger.info.called or mock_logger.warning.called or mock_logger.critical.called
