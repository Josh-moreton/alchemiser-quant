"""Business Unit: execution | Status: current

Test execution result classification logic.

Tests the classification of execution outcomes to ensure proper distinction between:
- Success with no orders (portfolio already balanced)
- Success with all orders succeeded
- Partial success (some orders succeeded, some failed)
- Failure (no orders succeeded, or errors occurred)
"""

import pytest

from the_alchemiser.execution_v2.models.execution_result import (
    ExecutionResult,
    ExecutionStatus,
)


class TestExecutionResultClassification:
    """Test execution result status classification logic."""

    def test_classify_no_orders_as_success(self):
        """Test that 0 orders placed is classified as SUCCESS (portfolio already balanced)."""
        success, status = ExecutionResult.classify_execution_status(
            orders_placed=0, orders_succeeded=0
        )

        assert success is True, "No orders needed should be classified as success"
        assert (
            status == ExecutionStatus.SUCCESS
        ), "Status should be SUCCESS when portfolio is already balanced"

    def test_classify_all_orders_succeeded(self):
        """Test that all orders succeeded is classified as SUCCESS."""
        success, status = ExecutionResult.classify_execution_status(
            orders_placed=5, orders_succeeded=5
        )

        assert success is True
        assert status == ExecutionStatus.SUCCESS

    def test_classify_partial_success(self):
        """Test that some orders succeeded is classified as PARTIAL_SUCCESS."""
        success, status = ExecutionResult.classify_execution_status(
            orders_placed=5, orders_succeeded=3
        )

        assert success is False, "Partial success should have success=False"
        assert status == ExecutionStatus.PARTIAL_SUCCESS

    def test_classify_all_orders_failed(self):
        """Test that no orders succeeded is classified as FAILURE."""
        success, status = ExecutionResult.classify_execution_status(
            orders_placed=5, orders_succeeded=0
        )

        assert success is False
        assert status == ExecutionStatus.FAILURE

    def test_classify_single_order_success(self):
        """Test single order success."""
        success, status = ExecutionResult.classify_execution_status(
            orders_placed=1, orders_succeeded=1
        )

        assert success is True
        assert status == ExecutionStatus.SUCCESS

    def test_classify_single_order_failure(self):
        """Test single order failure."""
        success, status = ExecutionResult.classify_execution_status(
            orders_placed=1, orders_succeeded=0
        )

        assert success is False
        assert status == ExecutionStatus.FAILURE

    def test_success_rate_with_no_orders(self):
        """Test that success_rate returns 1.0 when no orders were placed."""
        from datetime import UTC, datetime
        from decimal import Decimal

        result = ExecutionResult(
            success=True,
            status=ExecutionStatus.SUCCESS,
            plan_id="test-plan",
            correlation_id="test-corr",
            orders=[],
            orders_placed=0,
            orders_succeeded=0,
            total_trade_value=Decimal("0"),
            execution_timestamp=datetime.now(UTC),
        )

        assert result.success_rate == 1.0, "Success rate should be 1.0 when no orders needed"
        assert result.failure_count == 0

    def test_success_rate_with_all_succeeded(self):
        """Test success_rate when all orders succeeded."""
        from datetime import UTC, datetime
        from decimal import Decimal

        result = ExecutionResult(
            success=True,
            status=ExecutionStatus.SUCCESS,
            plan_id="test-plan",
            correlation_id="test-corr",
            orders=[],
            orders_placed=5,
            orders_succeeded=5,
            total_trade_value=Decimal("1000"),
            execution_timestamp=datetime.now(UTC),
        )

        assert result.success_rate == 1.0
        assert result.failure_count == 0

    def test_success_rate_with_partial_success(self):
        """Test success_rate with partial success."""
        from datetime import UTC, datetime
        from decimal import Decimal

        result = ExecutionResult(
            success=False,
            status=ExecutionStatus.PARTIAL_SUCCESS,
            plan_id="test-plan",
            correlation_id="test-corr",
            orders=[],
            orders_placed=5,
            orders_succeeded=3,
            total_trade_value=Decimal("600"),
            execution_timestamp=datetime.now(UTC),
        )

        assert result.success_rate == 0.6
        assert result.failure_count == 2
        assert result.is_partial_success is True
