"""Business Unit: execution_v2 | Status: current.

Test execution status classification with skipped trades.

These tests verify the new classification logic that distinguishes between
failed trades (broker rejections) and skipped trades (intentionally not sent
due to bad market data or constraints).
"""

from datetime import UTC, datetime
from decimal import Decimal

import pytest

from the_alchemiser.execution_v2.models.execution_result import (
    ExecutionResult,
    ExecutionStatus,
    OrderResult,
)


class TestExecutionStatusClassification:
    """Test execution status classification with skipped trades."""

    def test_classify_all_succeeded_no_skips(self):
        """Test classification when all orders succeeded with no skips."""
        success, status = ExecutionResult.classify_execution_status(
            orders_placed=3, orders_succeeded=3, orders_skipped=0
        )

        assert success is True
        assert status == ExecutionStatus.SUCCESS

    def test_classify_all_succeeded_with_skips(self):
        """Test classification when all placed orders succeeded but some were skipped."""
        # TECL scenario: 3 planned, 1 skipped due to bad quote, 2 placed and succeeded
        success, status = ExecutionResult.classify_execution_status(
            orders_placed=2, orders_succeeded=2, orders_skipped=1
        )

        assert success is True
        assert status == ExecutionStatus.SUCCESS_WITH_SKIPS

    def test_classify_no_orders_placed_with_skips(self):
        """Test classification when no orders placed but all were skipped."""
        # All trades skipped due to bad market data
        success, status = ExecutionResult.classify_execution_status(
            orders_placed=0, orders_succeeded=0, orders_skipped=3
        )

        assert success is True
        assert status == ExecutionStatus.SUCCESS_WITH_SKIPS

    def test_classify_partial_success(self):
        """Test classification when some orders succeeded and some failed."""
        success, status = ExecutionResult.classify_execution_status(
            orders_placed=3, orders_succeeded=2, orders_skipped=0
        )

        assert success is False
        assert status == ExecutionStatus.PARTIAL_SUCCESS

    def test_classify_all_failed_no_skips(self):
        """Test classification when all orders failed."""
        success, status = ExecutionResult.classify_execution_status(
            orders_placed=3, orders_succeeded=0, orders_skipped=0
        )

        assert success is False
        assert status == ExecutionStatus.FAILURE

    def test_classify_no_activity(self):
        """Test classification when no orders placed and none skipped."""
        success, status = ExecutionResult.classify_execution_status(
            orders_placed=0, orders_succeeded=0, orders_skipped=0
        )

        assert success is False
        assert status == ExecutionStatus.FAILURE

    def test_classify_partial_success_with_skips(self):
        """Test classification when some succeeded, some failed, some skipped."""
        # Complex scenario: 5 planned, 1 skipped, 4 placed, 3 succeeded, 1 failed
        success, status = ExecutionResult.classify_execution_status(
            orders_placed=4, orders_succeeded=3, orders_skipped=1
        )

        assert success is False
        assert status == ExecutionStatus.PARTIAL_SUCCESS


class TestCreateSkippedOrder:
    """Test helper function for creating skipped order results."""

    def test_create_skipped_order_basic(self):
        """Test creating a basic skipped order."""
        result = OrderResult.create_skipped_order(
            symbol="TECL",
            action="BUY",
            shares=Decimal("10"),
            skip_reason="Invalid quote: bid=107.0, ask=0.0",
        )

        assert result.symbol == "TECL"
        assert result.action == "BUY"
        assert result.shares == Decimal("10")
        assert result.success is False
        assert result.skipped is True
        assert result.skip_reason == "Invalid quote: bid=107.0, ask=0.0"
        assert result.error_message == "Trade skipped: Invalid quote: bid=107.0, ask=0.0"
        assert result.price is None
        assert result.order_id is None
        assert result.trade_amount == Decimal("0")

    def test_create_skipped_order_minimum_notional(self):
        """Test creating skipped order due to minimum notional."""
        result = OrderResult.create_skipped_order(
            symbol="TEST",
            action="SELL",
            shares=Decimal("1"),
            skip_reason="Order notional ($0.01) below Alpaca minimum ($1.00)",
        )

        assert result.symbol == "TEST"
        assert result.action == "SELL"
        assert result.skipped is True
        assert "notional" in result.skip_reason
        assert "Alpaca minimum" in result.skip_reason

    def test_create_skipped_order_with_timestamp(self):
        """Test creating skipped order with explicit timestamp."""
        timestamp = datetime(2025, 1, 10, 12, 0, 0, tzinfo=UTC)
        result = OrderResult.create_skipped_order(
            symbol="AAPL",
            action="BUY",
            shares=Decimal("5"),
            skip_reason="Test reason",
            timestamp=timestamp,
        )

        assert result.timestamp == timestamp

    def test_create_skipped_order_case_insensitive_action(self):
        """Test that action is normalized to uppercase."""
        result = OrderResult.create_skipped_order(
            symbol="AAPL", action="buy", shares=Decimal("5"), skip_reason="Test"
        )

        assert result.action == "BUY"


class TestExecutionResultWithSkippedOrders:
    """Test ExecutionResult construction with skipped orders."""

    def test_execution_result_with_skipped_orders(self):
        """Test creating ExecutionResult with skipped orders."""
        timestamp = datetime.now(UTC)

        # Create a mix of successful and skipped orders
        orders = [
            OrderResult(
                symbol="AAPL",
                action="SELL",
                trade_amount=Decimal("1000"),
                shares=Decimal("10"),
                price=Decimal("100"),
                order_id="order-1",
                success=True,
                timestamp=timestamp,
            ),
            OrderResult.create_skipped_order(
                symbol="TECL",
                action="BUY",
                shares=Decimal("5"),
                skip_reason="Invalid quote",
                timestamp=timestamp,
            ),
            OrderResult(
                symbol="GOOG",
                action="BUY",
                trade_amount=Decimal("500"),
                shares=Decimal("5"),
                price=Decimal("100"),
                order_id="order-2",
                success=True,
                timestamp=timestamp,
            ),
        ]

        result = ExecutionResult(
            success=True,
            status=ExecutionStatus.SUCCESS_WITH_SKIPS,
            plan_id="plan-123",
            correlation_id="corr-456",
            orders=orders,
            orders_placed=2,  # Only AAPL and GOOG were placed
            orders_succeeded=2,
            orders_skipped=1,  # TECL was skipped
            total_trade_value=Decimal("1500"),
            execution_timestamp=timestamp,
        )

        assert result.orders_placed == 2
        assert result.orders_succeeded == 2
        assert result.orders_skipped == 1
        assert result.status == ExecutionStatus.SUCCESS_WITH_SKIPS
        assert result.success is True
        assert len(result.orders) == 3

        # Verify the skipped order is in the list
        skipped_orders = [o for o in result.orders if o.skipped]
        assert len(skipped_orders) == 1
        assert skipped_orders[0].symbol == "TECL"
