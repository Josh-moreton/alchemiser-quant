# Critical Bug: EventBridge Orchestrator Blocking Wait Loop

**Date:** 2025-10-14
**Severity:** 🔴 CRITICAL - System Does Not Work
**Status:** 🔍 IDENTIFIED - Not Yet Fixed

## Problem Summary

The trading system **publishes WorkflowStarted to EventBridge but then BLOCKS waiting for in-memory events that will never arrive**. The orchestrator uses an **in-memory wait loop** that's incompatible with EventBridge's distributed async architecture.

## Root Cause

The system has a **fundamental architecture mismatch**:

1. **Events Published To:** EventBridge (distributed, async, Lambda-invoked)
2. **Events Waited For:** In-memory EventBus (synchronous, same-process)

### The Broken Flow

```
Lambda Handler
    ↓
TradingSystem.execute_trading()
    ↓
EventDrivenOrchestrator.start_trading_workflow()
    ↓ publishes WorkflowStarted to EventBridge
EventDrivenOrchestrator.wait_for_workflow_completion()  ← BLOCKS HERE
    ↓ waits for in-memory events...
    ↓ ...that never arrive because they're going to EventBridge!
    ↓
TIMEOUT after 300 seconds ❌
```

### Why It Fails

**File:** `the_alchemiser/orchestration/system.py`

```python
def _execute_trading_via_orchestrator(...):
    # Start the event-driven workflow
    workflow_correlation_id = self.event_driven_orchestrator.start_trading_workflow(
        correlation_id=correlation_id
    )

    # 🔴 BUG: Waits for in-memory events, but events go to EventBridge!
    workflow_result = self.event_driven_orchestrator.wait_for_workflow_completion(
        workflow_correlation_id, timeout_seconds=self.WORKFLOW_TIMEOUT_SECONDS  # 300s
    )
```

**File:** `the_alchemiser/orchestration/event_driven_orchestrator.py`

```python
def wait_for_workflow_completion(
    self, correlation_id: str, timeout_seconds: int = 300
) -> dict[str, Any]:
    """Wait for workflow completion and return results."""
    start_time = time.time()

    while time.time() - start_time < timeout_seconds:
        # 🔴 BUG: Checks in-memory state that's never updated from EventBridge
        if correlation_id not in self.workflow_state["active_correlations"]:
            return self.workflow_results.get(correlation_id, {})

        time.sleep(0.5)  # Polls every 500ms

    # After 300 seconds...
    raise TimeoutError(f"Workflow {correlation_id} did not complete within {timeout_seconds}s")
```

## What Actually Happens

1. ✅ Lambda invoked by scheduler
2. ✅ TradingSystem.execute_trading() called
3. ✅ Orchestrator publishes WorkflowStarted to EventBridge
4. ✅ EventBridge receives WorkflowStarted event
5. ✅ EventBridge Rule routes WorkflowStarted to Lambda
6. ✅ New Lambda invocation starts
7. ✅ lambda_handler_eventbridge routes to SignalGenerationHandler
8. ✅ SignalGenerationHandler generates signals
9. ✅ SignalGenerated published to EventBridge
10. ⏱️ **Meanwhile, original Lambda is blocking in wait loop...**
11. ❌ **Wait loop checks in-memory state (not updated by EventBridge)**
12. ❌ **After 300 seconds, times out**

## Evidence

From user's log:
```json
{"event": "Event published to EventBridge", "event_type": "WorkflowStarted"}
{"event": "⏳ Waiting for workflow completion: 50622964-66af-4a55-ac94-26437f0eec3c"}
{"event": "✅ Workflow completed: 50622964-66af-4a55-ac94-26437f0eec3c"}
```

But then immediately:
```json
START RequestId: 601dda51-c568-4098-97af-3f5993b1eb26
{"event": "Routing to eventbridge_handler for domain event", "detail_type": "WorkflowStarted"}
{"event": "Received EventBridge event", "event_id": "workflow-started-488c3ec2-7506-496a-95b4-a320dd91799e"}
```

**Two separate Lambda invocations!** The first one published WorkflowStarted and is waiting. The second one received it from EventBridge.

## Why This Wasn't Caught

The system was originally designed with an **in-memory EventBus** where:
- Events published and consumed in same process
- Wait loop worked because handlers updated in-memory state
- Synchronous, single-Lambda execution

When migrating to EventBridge:
- EventBridgeBus was wired in (`service_providers.py`)
- Events now go to AWS EventBridge (distributed)
- But wait loop logic was **not updated**
- Wait loop still checks in-memory state that's never updated

## Required Fix

The orchestrator needs to be **completely re-architected** for EventBridge:

### Option 1: Step Functions (Recommended)
Use AWS Step Functions to orchestrate the workflow:
- Step Functions natively handles async event-driven flows
- Wait for EventBridge events
- Retry logic built-in
- Visual workflow monitoring

### Option 2: Lambda Async Invocation Chain (Simpler)
Remove the wait loop entirely:
1. Lambda 1: Publishes WorkflowStarted, returns immediately
2. EventBridge routes each event to Lambda
3. Each Lambda handler does its work and publishes next event
4. Final Lambda (TradeExecuted handler) sends notification

**This is what we originally intended!**

### Option 3: DynamoDB State Machine
Store workflow state in DynamoDB:
- Each Lambda updates DynamoDB with progress
- TradeExecuted handler checks if all stages complete
- Sends notification when done

## Current Workaround

**None.** The system is fundamentally broken for EventBridge.

## Immediate Action Required

We need to **remove the blocking wait loop** and let EventBridge handle the async flow:

1. **Remove `wait_for_workflow_completion()` call** from `system.py`
2. **Make `execute_trading()` return immediately** after publishing WorkflowStarted
3. **Move result collection to TradeExecuted handler**
4. **Send notification from TradeExecuted handler** (already implemented!)

This aligns with the event-driven architecture EventBridge was designed for.

## Files Affected

- `the_alchemiser/orchestration/system.py` - Remove wait loop
- `the_alchemiser/orchestration/event_driven_orchestrator.py` - Remove or deprecate wait_for_workflow_completion
- `the_alchemiser/main.py` - Update to handle async execution
- `the_alchemiser/lambda_handler.py` - Already correct (returns after publishing)

## Impact

**Before Fix:**
- System times out after 300 seconds
- No trades executed
- No email notifications sent
- Lambda runs for 5 minutes burning money

**After Fix:**
- WorkflowStarted → SignalGenerated → RebalancePlanned → TradeExecuted flows correctly
- Each stage completes in <5 seconds
- Email notification sent after TradeExecuted
- Total workflow time: <30 seconds

## Related Issues

- Email notifications not being sent (they are being sent, but to a Lambda that times out!)
- System "doing nothing" (it IS doing something, but async across multiple Lambda invocations)
- High Lambda costs (300s execution time vs 5s per invocation)

## Next Steps

1. Remove wait loop from `system.py`
2. Update return type to be immediate (don't wait for results)
3. Test end-to-end flow
4. Verify emails sent correctly
5. Monitor CloudWatch for successful workflow completion
