# EventBridge Lambda Handler Fix - 2025-10-14

## Problem Summary

The first attempt to run the new EventBridge system failed catastrophically with an infinite error loop. The system generated ~5 Lambda invocations, each failing with the same Pydantic validation error.

### Root Causes

1. **EventBridge Envelope Not Unwrapped**: When EventBridge invokes a Lambda function, it wraps the event in an envelope with metadata fields (`version`, `id`, `detail-type`, `source`, `account`, `time`, `region`, `resources`). The actual event data is nested in the `detail` field. The `lambda_handler` was trying to parse the entire envelope as a `LambdaEvent`, which has `extra="forbid"` in its Pydantic config.

2. **Infinite Error Loop**: When an error occurred, it published an `ErrorNotificationRequested` event to EventBridge. This event triggered the same Lambda function again, which failed with the same validation error, creating an infinite cascade of errors.

## Solution Implemented

### 1. EventBridge Envelope Unwrapping

**File**: `the_alchemiser/lambda_handler.py`
**Function**: `parse_event_mode()`

Added detection and unwrapping of EventBridge envelopes:

```python
# Unwrap EventBridge envelope if present
# EventBridge wraps events with metadata: version, id, detail-type, source, etc.
# The actual event data is nested in the 'detail' field
if isinstance(event, dict) and "detail-type" in event and "detail" in event:
    logger.debug(
        "Detected EventBridge envelope; extracting detail payload",
        detail_type=event.get("detail-type"),
        source=event.get("source"),
    )
    event = event["detail"]
```

### 2. Circuit Breaker for Error Notifications

**File**: `the_alchemiser/lambda_handler.py`
**Function**: `lambda_handler()`

Added early detection and skipping of `ErrorNotificationRequested` events:

```python
# Circuit breaker: Skip error notification events to prevent infinite error loops
# When an error occurs, it publishes ErrorNotificationRequested to EventBridge,
# which triggers this Lambda again. Without this check, one error creates a cascade.
if isinstance(event, dict):
    detail_type = event.get("detail-type")
    if detail_type == "ErrorNotificationRequested":
        logger.info(
            "Skipping ErrorNotificationRequested event to prevent error cascade",
            detail_type=detail_type,
        )
        return {
            "status": "skipped",
            "mode": "error_notification",
            "trading_mode": "n/a",
            "message": "Error notification event skipped (circuit breaker)",
            "request_id": request_id,
        }
```

### 3. Code Cleanup

- Removed dead code for `monthly_summary` action validation (now handled by Pydantic schema)
- Removed obsolete test for `monthly_summary` error handling

## Testing

Created test events and validated with SAM Local:

### Test Cases

1. **Direct Event (No Wrapper)**
   - File: `test-events/direct-trade-event.json`
   - Result: ✅ Success - trades execute normally

2. **EventBridge Scheduler Event**
   - File: `test-events/eventbridge-scheduler-trade.json`
   - Contains: EventBridge envelope with `LambdaEvent` schema in `detail`
   - Result: ✅ Success - envelope detected, unwrapped, trades execute

3. **ErrorNotificationRequested Event**
   - File: `test-events/eventbridge-error-notification.json`
   - Result: ✅ Success - circuit breaker activates, event skipped with clear message

### Test Commands

```bash
# Build the Lambda function
sam build TradingSystemFunction

# Test direct event
sam local invoke TradingSystemFunction \
  --event test-events/direct-trade-event.json \
  --skip-pull-image

# Test EventBridge scheduler event
sam local invoke TradingSystemFunction \
  --event test-events/eventbridge-scheduler-trade.json \
  --skip-pull-image

# Test circuit breaker
sam local invoke TradingSystemFunction \
  --event test-events/eventbridge-error-notification.json \
  --skip-pull-image
```

## Impact

- ✅ EventBridge Scheduler invocations now work correctly
- ✅ Error notifications no longer create infinite loops
- ✅ System degrades gracefully with clear logging
- ✅ Both direct and wrapped event formats supported

## Architecture Notes

### Lambda Handler Responsibilities

- **`lambda_handler`**: Handles direct invocations and EventBridge Scheduler events
  - Parses `LambdaEvent` schema (mode, trading_mode, pnl analysis)
  - Unwraps EventBridge envelopes when present
  - Circuit breaker for error notification events

- **`lambda_handler_eventbridge`**: Handles EventBridge event routing
  - Parses domain events (SignalGenerated, RebalancePlanned, TradeExecuted, etc.)
  - Routes events to appropriate handlers
  - Should NOT be invoked for scheduler events

### Event Flow

```
EventBridge Scheduler (cron)
  → Lambda (lambda_handler)
  → Unwraps envelope
  → Parses LambdaEvent
  → Executes trade workflow
  → Publishes WorkflowStarted to EventBridge

EventBridge Rule (event pattern)
  → Lambda (lambda_handler_eventbridge)
  → Routes to handler
  → Executes business logic
```

## Additional Fix: Smart Event Routing

After testing, discovered that EventBridge Rules were routing domain events (`WorkflowStarted`, `SignalGenerated`, etc.) back to `lambda_handler`, which only understands `LambdaEvent` schema. This caused validation errors.

**Solution:** Implemented smart routing in `lambda_handler` to detect event type and route appropriately:

1. **Detection Function (`_is_domain_event`)**: Detects domain events by checking:
   - `detail-type` matches known domain event types (WorkflowStarted, SignalGenerated, etc.)
   - `source` starts with "alchemiser."

2. **Smart Routing Logic**: Added early routing in `lambda_handler`:
   ```python
   if _is_domain_event(event):
       logger.info("Routing to eventbridge_handler for domain event")
       from the_alchemiser.lambda_handler_eventbridge import eventbridge_handler
       return eventbridge_handler(event, context)
   ```

3. **Added WorkflowStarted Support**: Updated `lambda_handler_eventbridge.py` to handle `WorkflowStarted` events

4. **Re-enabled EventBridge Rules**: All rules now ENABLED:
   - `SignalGeneratedRule` → ENABLED
   - `RebalancePlannedRule` → ENABLED
   - `TradeExecutedRule` → ENABLED
   - `AllEventsToOrchestratorRule` → ENABLED

**Effect:**
- EventBridge Scheduler events (Scheduled Event) → processed by `lambda_handler`
- Domain events (WorkflowStarted, SignalGenerated, etc.) → routed to `lambda_handler_eventbridge`
- No validation errors
- Circuit breaker still prevents ErrorNotificationRequested loops
- Events properly archived (365-day retention)

## Version Bump Required

Per project guidelines, this is a **MINOR** version bump:
- New feature (smart event routing)
- EventBridge Rules enabled (significant functionality change)
- Bug fixes (envelope handling, event routing)
- Backward compatible (existing scheduler invocations unchanged)

Command: `make bump-minor`
