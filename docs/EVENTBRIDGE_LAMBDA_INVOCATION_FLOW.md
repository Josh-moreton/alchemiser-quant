# EventBridge Lambda Invocation Flow

**Date:** 2025-10-14
**Version:** v2.27.3+
**Status:** ✅ DOCUMENTED - Current Architecture

## Executive Summary

The Alchemiser trading system uses **one Lambda function** with **multiple event-driven invocations** to execute trading workflows. Each EventBridge event triggers a **new, independent Lambda invocation** that runs **different code** based on the event type.

This is the **correct serverless event-driven architecture**: fast, cheap, scalable, and observable.

## Core Concept

**One Lambda Function** → **Multiple Invocations** → **Different Code Paths**

```
Same Lambda: TradingSystemFunction
├─ Invocation #1: Scheduler event → TradingSystem.execute_trading()
├─ Invocation #2: WorkflowStarted → SignalGenerationHandler
├─ Invocation #3: SignalGenerated → PortfolioAnalysisHandler
├─ Invocation #4: RebalancePlanned → TradingExecutionHandler
├─ Invocation #5: TradeExecuted → Orchestrator (monitoring)
└─ Invocation #6: TradingNotificationRequested → NotificationService
```

## Lambda Invocation Map

| # | Trigger | Event Type | Entry Point | Code Path | Handler | Action | Duration |
|---|---------|------------|-------------|-----------|---------|--------|----------|
| 1 | EventBridge Scheduler | Scheduled Event (cron) | `lambda_handler` | `main()` → `TradingSystem.execute_trading()` | Orchestrator Start | Publish WorkflowStarted, return immediately | ~500ms |
| 2 | EventBridge Rule | WorkflowStarted | `lambda_handler` → `lambda_handler_eventbridge` | `SignalGenerationHandler.handle_event()` | Strategy Signal Generation | Pull market data, generate signals, publish SignalGenerated | ~2-3s |
| 3 | EventBridge Rule | SignalGenerated | `lambda_handler` → `lambda_handler_eventbridge` | `PortfolioAnalysisHandler.handle_event()` | Portfolio Rebalancing | Create rebalance plan, publish RebalancePlanned | ~1-2s |
| 4 | EventBridge Rule | RebalancePlanned | `lambda_handler` → `lambda_handler_eventbridge` | `TradingExecutionHandler.handle_event()` | Trade Execution | Execute orders via Alpaca, publish TradeExecuted | ~3-5s |
| 5 | EventBridge Rule | TradeExecuted | `lambda_handler` → `lambda_handler_eventbridge` | Orchestrator monitoring | Monitoring/Audit | Publish TradingNotificationRequested | ~200ms |
| 6 | EventBridge Rule | TradingNotificationRequested | `lambda_handler` → `lambda_handler_eventbridge` | `NotificationService.handle_event()` | Email Notification | Send email via SMTP | ~1-2s |

**Total Workflow Time:** ~10-15 seconds across 6 independent Lambda invocations

## Detailed Flow

### Invocation #1: Workflow Start (Scheduler → Lambda)

**Trigger:**
```yaml
# EventBridge Scheduler Rule (cron)
ScheduleExpression: rate(5 minutes)
Input: {"mode": "trade"}
```

**Code Path:**
```python
lambda_handler(event={"mode": "trade"}, context)
  ↓
main(["trade"])
  ↓
TradingSystem.execute_trading()
  ↓
EventDrivenOrchestrator.start_trading_workflow()
  ↓
event_bus.publish(WorkflowStarted)  # → EventBridge
  ↓
return {"status": "success", "workflow_started": True}  # Returns immediately!
```

**Duration:** ~500ms
**Result:** WorkflowStarted event published to EventBridge, Lambda exits

---

### Invocation #2: Signal Generation (WorkflowStarted → Lambda)

**Trigger:**
```yaml
# EventBridge Rule: WorkflowStarted
EventPattern:
  source: [alchemiser.orchestration]
  detail-type: [WorkflowStarted]
Target: TradingSystemFunction
```

**Code Path:**
```python
lambda_handler(event={EventBridge envelope with WorkflowStarted}, context)
  ↓
_is_domain_event(event) = True  # Has detail-type and source
  ↓
lambda_handler_eventbridge(event, context)
  ↓
_get_event_class("WorkflowStarted") → WorkflowStarted
  ↓
_get_handler_for_event("WorkflowStarted") → SignalGenerationHandler
  ↓
SignalGenerationHandler.handle_event(WorkflowStarted)
  ↓
# Pull market data from Alpaca
# Run DSL strategies (EDZ, MSFT, NVDA)
# Generate allocation signals
  ↓
event_bus.publish(SignalGenerated)  # → EventBridge
  ↓
return {"statusCode": 200, "body": "Event processed successfully"}
```

**Duration:** ~2-3s (depends on market data API)
**Result:** SignalGenerated event published to EventBridge, Lambda exits

---

### Invocation #3: Portfolio Analysis (SignalGenerated → Lambda)

**Trigger:**
```yaml
# EventBridge Rule: SignalGenerated
EventPattern:
  source: [alchemiser.strategy]
  detail-type: [SignalGenerated]
Target: TradingSystemFunction
```

**Code Path:**
```python
lambda_handler(event={EventBridge envelope with SignalGenerated}, context)
  ↓
_is_domain_event(event) = True
  ↓
lambda_handler_eventbridge(event, context)
  ↓
_get_event_class("SignalGenerated") → SignalGenerated
  ↓
_get_handler_for_event("SignalGenerated") → PortfolioAnalysisHandler
  ↓
PortfolioAnalysisHandler.handle_event(SignalGenerated)
  ↓
# Get current Alpaca positions
# Compare with strategy signals
# Calculate deltas (buy/sell/hold)
# Create rebalance plan
  ↓
event_bus.publish(RebalancePlanned)  # → EventBridge
  ↓
return {"statusCode": 200, "body": "Event processed successfully"}
```

**Duration:** ~1-2s
**Result:** RebalancePlanned event published to EventBridge, Lambda exits

---

### Invocation #4: Trade Execution (RebalancePlanned → Lambda)

**Trigger:**
```yaml
# EventBridge Rule: RebalancePlanned
EventPattern:
  source: [alchemiser.portfolio]
  detail-type: [RebalancePlanned]
Target: TradingSystemFunction
```

**Code Path:**
```python
lambda_handler(event={EventBridge envelope with RebalancePlanned}, context)
  ↓
_is_domain_event(event) = True
  ↓
lambda_handler_eventbridge(event, context)
  ↓
_get_event_class("RebalancePlanned") → RebalancePlanned
  ↓
_get_handler_for_event("RebalancePlanned") → TradingExecutionHandler
  ↓
TradingExecutionHandler.handle_event(RebalancePlanned)
  ↓
# Submit orders to Alpaca (limit orders)
# Poll for order fills
# Settle completed orders
# Handle failures
  ↓
event_bus.publish(TradeExecuted)  # → EventBridge
  ↓
return {"statusCode": 200, "body": "Event processed successfully"}
```

**Duration:** ~3-5s (depends on order fills)
**Result:** TradeExecuted event published to EventBridge, Lambda exits

---

### Invocation #5: Monitoring (TradeExecuted → Lambda)

**Trigger:**
```yaml
# EventBridge Rule: TradeExecuted
EventPattern:
  source: [alchemiser.execution]
  detail-type: [TradeExecuted]
Target: TradingSystemFunction
```

**Code Path:**
```python
lambda_handler(event={EventBridge envelope with TradeExecuted}, context)
  ↓
_is_domain_event(event) = True
  ↓
lambda_handler_eventbridge(event, context)
  ↓
_get_event_class("TradeExecuted") → TradeExecuted
  ↓
_get_handler_for_event("TradeExecuted") → None (orchestrator-only event)
  ↓
# Orchestrator monitoring: marked as orchestrator-only, returns success
# BUT orchestrator is subscribed via in-memory EventBus
# (EventBridgeBus publishes to both EventBridge AND in-memory subscribers)
  ↓
Orchestrator._handle_trade_executed(TradeExecuted)
  ↓
# Build trading notification payload
  ↓
event_bus.publish(TradingNotificationRequested)  # → EventBridge
  ↓
return {"statusCode": 200, "body": "Orchestrator-only event: TradeExecuted"}
```

**Duration:** ~200ms
**Result:** TradingNotificationRequested event published to EventBridge, Lambda exits

---

### Invocation #6: Email Notification (TradingNotificationRequested → Lambda)

**Trigger:**
```yaml
# EventBridge Rule: TradingNotificationRequested
EventPattern:
  source: [alchemiser.orchestration]
  detail-type: [TradingNotificationRequested]
Target: TradingSystemFunction
```

**Code Path:**
```python
lambda_handler(event={EventBridge envelope with TradingNotificationRequested}, context)
  ↓
_is_domain_event(event) = True
  ↓
lambda_handler_eventbridge(event, context)
  ↓
_get_event_class("TradingNotificationRequested") → TradingNotificationRequested
  ↓
_get_handler_for_event("TradingNotificationRequested") → NotificationService
  ↓
NotificationService.handle_event(TradingNotificationRequested)
  ↓
# Build email content (HTML + text)
# Send via SMTP (smtp.mail.me.com:587)
  ↓
return {"statusCode": 200, "body": "Event processed successfully"}
```

**Duration:** ~1-2s
**Result:** Email delivered to josh@rwxt.org, Lambda exits

---

## Event Routing Logic

### `lambda_handler.py` - Entry Point & Smart Routing

```python
def lambda_handler(event, context):
    """Main Lambda entry point - routes to correct handler based on event type."""

    # Circuit breaker: Skip error notification events
    if event.get("detail-type") == "ErrorNotificationRequested":
        return {"status": "skipped", "message": "Circuit breaker"}

    # Smart routing: Detect domain events vs command events
    if _is_domain_event(event):
        # Domain event (WorkflowStarted, SignalGenerated, etc.)
        # Route to lambda_handler_eventbridge for event-specific handling
        return lambda_handler_eventbridge(event, context)

    # Command event (Scheduler, direct invocation)
    # Parse and execute via main()
    command_args = parse_event_mode(event)
    result = main(command_args)
    return build_response(result)
```

### `lambda_handler_eventbridge.py` - Event-Specific Routing

```python
def eventbridge_handler(event, context):
    """Route EventBridge domain events to appropriate handlers."""

    # Extract event metadata
    detail_type = event["detail-type"]  # e.g., "SignalGenerated"
    detail = event["detail"]            # Event payload

    # Map event type to event class
    event_class = _get_event_class(detail_type)
    event_obj = event_class.model_validate(detail)

    # Map event type to handler
    handler = _get_handler_for_event(container, detail_type)

    if handler:
        # Invoke handler (different code runs here!)
        handler.handle_event(event_obj)
        return {"statusCode": 200, "body": "Event processed successfully"}

    # Orchestrator-only events (TradeExecuted, WorkflowCompleted, WorkflowFailed)
    # These are for monitoring/audit, no handler needed
    if detail_type in ["TradeExecuted", "WorkflowCompleted", "WorkflowFailed"]:
        return {"statusCode": 200, "body": f"Orchestrator-only event: {detail_type}"}

    # Unknown event type
    return {"statusCode": 404, "body": f"No handler for: {detail_type}"}
```

### Event-to-Handler Mapping

```python
# File: lambda_handler_eventbridge.py

# Event class mapping (for deserialization)
event_map: dict[str, type[BaseEvent]] = {
    "WorkflowStarted": WorkflowStarted,
    "SignalGenerated": SignalGenerated,
    "RebalancePlanned": RebalancePlanned,
    "TradeExecuted": TradeExecuted,
    "WorkflowCompleted": WorkflowCompleted,
    "WorkflowFailed": WorkflowFailed,
    "TradingNotificationRequested": TradingNotificationRequested,
}

# Handler mapping (different code for each event!)
handler_map: dict[str, Callable[[], EventHandler]] = {
    "WorkflowStarted": lambda: SignalGenerationHandler(container),
    "SignalGenerated": lambda: PortfolioAnalysisHandler(container),
    "RebalancePlanned": lambda: TradingExecutionHandler(container),
    "TradingNotificationRequested": lambda: NotificationService(container),
}

# Orchestrator-only events (no handler, just monitoring)
orchestrator_only_events = {
    "TradeExecuted",
    "WorkflowCompleted",
    "WorkflowFailed",
}
```

## Complete Timeline Example

**Scenario:** Scheduled trading run at 10:00:00 UTC

```
TIME         | INVOCATION | EVENT TYPE                     | HANDLER                  | ACTION
-------------|------------|--------------------------------|--------------------------|----------------------------------
10:00:00.000 | #1         | Scheduled Event (cron)         | TradingSystem            | Publish WorkflowStarted → return
10:00:00.500 | #2         | WorkflowStarted                | SignalGenerationHandler  | Generate signals → publish SignalGenerated
10:00:03.200 | #3         | SignalGenerated                | PortfolioAnalysisHandler | Create plan → publish RebalancePlanned
10:00:04.800 | #4         | RebalancePlanned               | TradingExecutionHandler  | Execute orders → publish TradeExecuted
10:00:09.500 | #5         | TradeExecuted                  | Orchestrator (monitoring)| Publish TradingNotificationRequested
10:00:09.700 | #6         | TradingNotificationRequested   | NotificationService      | Send email ✅
-------------|------------|--------------------------------|--------------------------|----------------------------------
TOTAL TIME: ~10 seconds across 6 Lambda invocations
```

## CloudWatch Logs View

Each Lambda invocation creates **separate log streams** with the **same correlation_id**:

```
# Invocation #1 (Scheduler)
2025-10-14 10:00:00.123 REQUEST_ID_1 {"event": "Lambda invoked", "correlation_id": "abc-123"}
2025-10-14 10:00:00.456 REQUEST_ID_1 {"event": "Event published to EventBridge", "event_type": "WorkflowStarted"}
2025-10-14 10:00:00.500 REQUEST_ID_1 END

# Invocation #2 (WorkflowStarted)
2025-10-14 10:00:00.550 REQUEST_ID_2 {"event": "Lambda invoked", "correlation_id": "abc-123"}
2025-10-14 10:00:00.560 REQUEST_ID_2 {"event": "Routing to eventbridge_handler", "detail_type": "WorkflowStarted"}
2025-10-14 10:00:03.100 REQUEST_ID_2 {"event": "Event published to EventBridge", "event_type": "SignalGenerated"}
2025-10-14 10:00:03.200 REQUEST_ID_2 END

# Invocation #3 (SignalGenerated)
2025-10-14 10:00:03.250 REQUEST_ID_3 {"event": "Lambda invoked", "correlation_id": "abc-123"}
...
```

**Search across all invocations:**
```bash
aws logs filter-pattern "abc-123" --log-group-name /aws/lambda/the-alchemiser-v2-lambda-dev
```

## Cost Analysis

### Before Fix (Blocking Wait Loop)

| Invocation | Duration | Memory | Cost Factor |
|------------|----------|--------|-------------|
| 1 (blocking) | 300s | 512MB | **150 GB-seconds** |
| **TOTAL** | **300s** | | **💰💰💰 EXPENSIVE** |

### After Fix (Async EventBridge)

| Invocation | Duration | Memory | Cost Factor |
|------------|----------|--------|-------------|
| 1 (start) | 0.5s | 512MB | 0.25 GB-seconds |
| 2 (signals) | 2.5s | 512MB | 1.25 GB-seconds |
| 3 (portfolio) | 1.5s | 512MB | 0.75 GB-seconds |
| 4 (execution) | 4s | 512MB | 2 GB-seconds |
| 5 (monitoring) | 0.2s | 512MB | 0.1 GB-seconds |
| 6 (notification) | 1.5s | 512MB | 0.75 GB-seconds |
| **TOTAL** | **10.2s** | | **5.1 GB-seconds** |

**Cost Reduction: ~30x cheaper!** (150 → 5.1 GB-seconds)

## Benefits

### 1. Performance
- **Fast:** Each invocation completes in seconds, not minutes
- **Parallel:** Multiple workflows can run simultaneously without blocking
- **Scalable:** EventBridge automatically scales to handle burst traffic

### 2. Reliability
- **Retry:** EventBridge retries failed invocations (2-3 attempts)
- **DLQ:** Failed events routed to Dead Letter Queue for analysis
- **Timeout:** Each invocation has independent 30s timeout (not 300s!)

### 3. Observability
- **Tracing:** Correlation ID tracks workflow across all invocations
- **Logs:** Each step visible in CloudWatch with clear boundaries
- **Metrics:** Lambda invocations, durations, errors tracked per event type

### 4. Cost
- **~30x cheaper** than blocking wait loop
- Pay only for actual compute time (10s vs 300s)
- No wasted cycles waiting for events

### 5. Maintainability
- **Separation of concerns:** Each handler focuses on one responsibility
- **Testable:** Each handler can be tested independently
- **Debuggable:** Clear log boundaries between invocations

## Common Pitfalls (Avoided)

### ❌ DON'T: Block and wait for events
```python
# WRONG - This is what we had before
workflow_id = start_workflow()
result = wait_for_completion(workflow_id, timeout=300)  # ❌ Blocks for 5 minutes!
return result
```

### ✅ DO: Publish and return immediately
```python
# RIGHT - This is what we have now
workflow_id = start_workflow()
event_bus.publish(WorkflowStarted)  # ✅ Published to EventBridge
return {"workflow_started": True}  # ✅ Returns immediately!
# EventBridge handles the rest asynchronously
```

### ❌ DON'T: Try to collect results in original invocation
```python
# WRONG - Original Lambda can't see results from other invocations
result = {
    "signals": ...,      # ❌ Not available yet!
    "orders": ...,       # ❌ Not available yet!
    "email_sent": ...    # ❌ Not available yet!
}
```

### ✅ DO: Send results via final notification
```python
# RIGHT - Email contains full workflow results
# Final Lambda invocation (NotificationService) has all context
email_body = f"""
Trading Summary:
- Signals: {event.strategy_signals}
- Orders: {event.orders_executed}
- Status: {event.success}
"""
send_email(email_body)  # ✅ Results delivered asynchronously
```

## Debugging Tips

### 1. Find All Invocations for a Workflow
```bash
# Search CloudWatch logs by correlation_id
aws logs filter-pattern "50622964-66af-4a55-ac94-26437f0eec3c" \
  --log-group-name /aws/lambda/the-alchemiser-v2-lambda-dev \
  --start-time $(date -u -d '10 minutes ago' +%s)000
```

### 2. Check Which Handler Processed an Event
```bash
# Search for routing logs
aws logs filter-pattern "Routing to eventbridge_handler" \
  --log-group-name /aws/lambda/the-alchemiser-v2-lambda-dev
```

### 3. Verify Event Published to EventBridge
```bash
# Search for published events
aws logs filter-pattern "Event published to EventBridge" \
  --log-group-name /aws/lambda/the-alchemiser-v2-lambda-dev
```

### 4. Check EventBridge Rule Invocations
```bash
# Get EventBridge metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Events \
  --metric-name Invocations \
  --dimensions Name=RuleName,Value=alchemiser-signal-generated-dev \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --period 300 \
  --statistics Sum
```

## Related Documentation

- `docs/BUG_FIX_EVENTBRIDGE_ORCHESTRATOR_BLOCKING.md` - The critical bug we fixed
- `docs/EVENTBRIDGE_READY_FOR_DEPLOYMENT.md` - Deployment guide
- `docs/EVENTBRIDGE_QUICK_REFERENCE.md` - Quick reference
- `template.yaml` - EventBridge Rules and Lambda configuration
- `the_alchemiser/lambda_handler.py` - Main entry point
- `the_alchemiser/lambda_handler_eventbridge.py` - Event routing

## Summary

The Alchemiser trading system uses **one Lambda function** with **multiple event-driven invocations** to execute trading workflows asynchronously via EventBridge. Each event triggers a new Lambda invocation that runs different code based on the event type.

This architecture is:
- ✅ **Fast** - 10 seconds total (vs 300s blocking)
- ✅ **Cheap** - ~30x cost reduction
- ✅ **Scalable** - EventBridge handles concurrency
- ✅ **Observable** - Clear logs and metrics per step
- ✅ **Reliable** - Retry policies and DLQ support

**Key Insight:** Don't wait for async events in a serverless architecture. Publish and return immediately. Let EventBridge orchestrate the flow.
