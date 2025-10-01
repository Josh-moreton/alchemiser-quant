# Fix for No-Op Rebalancing False Failures

## Problem Statement

When portfolio was already balanced (7 positions at target allocations), the system incorrectly reported workflow failure:

```
📊 Execution plan: 0 SELLs, 0 BUYs, 7 HOLDs
❌ Rebalance plan completed: 0/0 orders succeeded (status: failure)
ERROR - Trade execution failed: No orders were placed
```

## Root Cause

The portfolio analysis handler was incorrectly determining `trades_required`:

```python
# INCORRECT (before)
trades_required = (
    rebalance_plan is not None and len(rebalance_plan.items) > 0
)
# Returns True even when items are all HOLDs!
```

This caused plans with only HOLD items to be sent to execution, which then:
1. Received plan with items (7 HOLDs)
2. Tried to execute but found no BUY/SELL actions
3. Placed 0 orders
4. Classified as FAILURE

## The Fix

Changed portfolio handler to check for actual trading actions:

```python
# CORRECT (after)
trades_required = False
if rebalance_plan and rebalance_plan.items:
    trades_required = any(
        item.action in ["BUY", "SELL"] for item in rebalance_plan.items
    )
# Only returns True when actual trades (BUY/SELL) are needed
```

### Why This is the Right Approach

1. **Fixes at the correct layer**: Portfolio analysis determines if trades are needed
2. **Preserves error detection**: Real execution failures still detected
3. **Clean separation of concerns**: Portfolio decides "what to do", execution does "how"

### Rejected Approach

Initially tried fixing at execution result classification level (treating 0 orders as SUCCESS). This was incorrect because:

❌ Too late in business flow
❌ Would mask real failures where we tried but failed to place orders
❌ Conflates "no trades needed" with "execution failed"

## Expected Behavior After Fix

### Scenario 1: Portfolio Already Balanced (HOLD-only)

```
📊 Execution plan: 0 SELLs, 0 BUYs, 7 HOLDs
trades_required = False
📊 No significant trades needed - portfolio already balanced
✅ Execution complete: True (0 orders)
✅ Workflow completed successfully
```

### Scenario 2: Real Execution Failure (tried but failed)

```
📊 Execution plan: 2 SELLs, 3 BUYs, 2 HOLDs
trades_required = True
[Execution attempts but all orders fail due to validation/market issues]
❌ Rebalance plan completed: 0/5 orders succeeded (status: failure)
ERROR - Trade execution failed
```

## Files Changed

- `the_alchemiser/portfolio_v2/handlers/portfolio_analysis_handler.py` (+10, -6 lines)
  - Lines 521-526: Added correct `trades_required` determination logic
- `tests/portfolio_v2/test_trades_required_logic.py` (new, 230 lines)
  - Tests for HOLD-only, BUY-only, SELL-only, mixed, and empty scenarios

## How Execution Handler Already Works

The execution handler already had correct logic to handle `trades_required=False`:

```python
# execution_v2/handlers/trading_execution_handler.py:111-134
if not event.trades_required or not rebalance_plan_data.items:
    self.logger.info("📊 No significant trades needed - portfolio already balanced")
    
    # Create empty execution result
    execution_result = ExecutionResult(
        success=True,
        status=ExecutionStatus.SUCCESS,
        plan_id=rebalance_plan_data.plan_id,
        correlation_id=event.correlation_id,
        orders=[],
        orders_placed=0,
        orders_succeeded=0,
        total_trade_value=DECIMAL_ZERO,
        execution_timestamp=datetime.now(UTC),
        metadata={"scenario": "no_trades_needed"},
    )
    
    # Emit successful trade executed event
    self._emit_trade_executed_event(execution_result, success=True)
    
    # Emit workflow completed event
    self._emit_workflow_completed_event(event.correlation_id, execution_result)
    
    return  # Exit early without attempting execution
```

The fix ensures this code path is taken for HOLD-only plans.

## Summary

✅ **Fixed**: HOLD-only plans now correctly identified as not requiring trades
✅ **Preserved**: Real execution failures still properly detected
✅ **Correct layer**: Fix at portfolio analysis stage, not execution classification
✅ **No masking**: Distinguishes "no trades needed" from "trades failed"
