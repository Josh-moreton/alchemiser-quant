"""Business Unit: execution | Status: current

Integration test for no-op rebalancing workflow.

Validates that when portfolio already matches target allocations,
the system correctly classifies the outcome as SUCCESS and does not
send failure notifications.
"""

from datetime import UTC, datetime
from decimal import Decimal

from the_alchemiser.execution_v2.models.execution_result import (
    ExecutionResult,
    ExecutionStatus,
)


def test_no_op_rebalancing_workflow_success():
    """
    Test that a no-op rebalancing (0 orders) is classified as successful.
    
    This validates the fix for the issue where portfolio already matching
    target allocations was incorrectly classified as workflow failure.
    
    Scenario:
    - Portfolio has 7 positions already at target allocations
    - Rebalance plan shows 7 HOLDs, 0 BUYs, 0 SELLs
    - Execution places 0 orders (no trades needed)
    - Expected: SUCCESS status, not FAILURE
    """
    # Create execution result with 0 orders (portfolio already balanced)
    result = ExecutionResult(
        success=True,
        status=ExecutionStatus.SUCCESS,
        plan_id="plan-balanced-portfolio",
        correlation_id="corr-no-trades-needed",
        orders=[],
        orders_placed=0,
        orders_succeeded=0,
        total_trade_value=Decimal("0.00"),
        execution_timestamp=datetime.now(UTC),
        metadata={"scenario": "no_trades_needed", "hold_positions": 7},
    )

    # Verify the result is correctly classified as success
    assert result.success is True, "No-op execution should be classified as success"
    assert (
        result.status == ExecutionStatus.SUCCESS
    ), "Status should be SUCCESS when portfolio is balanced"
    assert result.orders_placed == 0, "No orders should be placed"
    assert result.orders_succeeded == 0, "No orders to succeed"
    assert result.success_rate == 1.0, "Success rate should be 100% for balanced portfolio"
    assert result.failure_count == 0, "No failures in balanced portfolio"
    assert result.is_partial_success is False, "Should not be partial success"

    # Verify classification logic directly
    success_flag, status = ExecutionResult.classify_execution_status(
        orders_placed=0, orders_succeeded=0
    )
    assert success_flag is True, "Classification should return success=True for 0 orders"
    assert (
        status == ExecutionStatus.SUCCESS
    ), "Classification should return SUCCESS status for 0 orders"


def test_contrast_with_actual_failure():
    """
    Contrast no-op success with actual execution failure.
    
    This demonstrates that our fix correctly distinguishes between:
    - No orders needed (SUCCESS) - portfolio balanced
    - Orders failed (FAILURE) - execution problems
    """
    # Case 1: No orders needed (SUCCESS)
    no_orders_success, no_orders_status = ExecutionResult.classify_execution_status(
        orders_placed=0, orders_succeeded=0
    )
    assert no_orders_success is True
    assert no_orders_status == ExecutionStatus.SUCCESS

    # Case 2: Orders placed but all failed (FAILURE)
    all_failed_success, all_failed_status = ExecutionResult.classify_execution_status(
        orders_placed=5, orders_succeeded=0
    )
    assert all_failed_success is False
    assert all_failed_status == ExecutionStatus.FAILURE

    # Case 3: Partial success (some succeeded, some failed)
    partial_success, partial_status = ExecutionResult.classify_execution_status(
        orders_placed=5, orders_succeeded=3
    )
    assert partial_success is False
    assert partial_status == ExecutionStatus.PARTIAL_SUCCESS

    # Case 4: All orders succeeded (SUCCESS)
    all_success, all_status = ExecutionResult.classify_execution_status(
        orders_placed=5, orders_succeeded=5
    )
    assert all_success is True
    assert all_status == ExecutionStatus.SUCCESS


def test_workflow_logging_expectations():
    """
    Verify the expected log output for no-op rebalancing.
    
    After the fix, the logs should show:
    - ✅ emoji (success) instead of ❌ (failure)
    - status: success instead of status: failure
    - Execution complete: True instead of False
    """
    result = ExecutionResult(
        success=True,
        status=ExecutionStatus.SUCCESS,
        plan_id="test-plan",
        correlation_id="test-corr",
        orders=[],
        orders_placed=0,
        orders_succeeded=0,
        total_trade_value=Decimal("0.00"),
        execution_timestamp=datetime.now(UTC),
        metadata={"scenario": "no_trades_needed"},
    )

    # Simulate the logging logic from executor.py
    if result.status == ExecutionStatus.SUCCESS:
        status_emoji = "✅"
    elif result.status == ExecutionStatus.PARTIAL_SUCCESS:
        status_emoji = "⚠️"
    else:
        status_emoji = "❌"

    # Verify correct emoji is selected
    assert status_emoji == "✅", "Should use success emoji for no-op execution"

    # Verify log message format would be correct
    log_message = (
        f"{status_emoji} Rebalance plan {result.plan_id} completed: "
        f"{result.orders_succeeded}/{result.orders_placed} orders succeeded "
        f"(status: {result.status.value})"
    )
    
    expected_message = "✅ Rebalance plan test-plan completed: 0/0 orders succeeded (status: success)"
    assert log_message == expected_message, f"Log message should be: {expected_message}"

    # Verify execution summary shows 100% success rate
    success_rate = result.success_rate * 100
    assert success_rate == 100.0, "Success rate should be 100% for no-op execution"
