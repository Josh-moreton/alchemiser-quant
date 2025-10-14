# EventBridge Handler Fix Plan

## TL;DR

**Is it fucked?** Not really! 😅

**Good News:**
- ✅ `lambda_handler_eventbridge.py` **already exists** and is fully implemented
- ✅ Handles `SignalGenerated`, `RebalancePlanned`, `TradeExecuted`, `WorkflowCompleted`, `WorkflowFailed`
- ✅ Has idempotency checks with DynamoDB
- ✅ Routes to correct handlers (Portfolio, Execution)
- ✅ Has comprehensive tests

**Bad News:**
- ❌ SAM/CloudFormation doesn't know about it (not configured as Lambda handler)
- ❌ EventBridge Rules route to wrong handler (`lambda_handler` instead of `lambda_handler_eventbridge`)

**Fix Complexity:** **SMALL** - Just configuration, no code changes needed!

---

## Current Architecture Problem

### What We Have Now

```
┌─────────────────────────────────────────────────────────────┐
│              ONE Lambda Function (TradingSystemFunction)     │
│                                                              │
│  Handler: lambda_handler.lambda_handler                      │
│  (Only understands LambdaEvent schema)                       │
└──────────────────────┬───────────────────────────────────────┘
                       │
                       │ Invoked by BOTH:
                       │
         ┌─────────────┴────────────────┐
         │                              │
         ▼                              ▼
┌──────────────────┐         ┌──────────────────────┐
│ EventBridge      │         │ EventBridge Rules    │
│ Scheduler        │         │ (SignalGenerated,    │
│                  │         │  RebalancePlanned,   │
│ Sends:           │         │  WorkflowStarted)    │
│ {"mode":"trade"} │         │                      │
│ ✅ WORKS         │         │ ❌ BREAKS            │
└──────────────────┘         └──────────────────────┘
```

**Problem:** All EventBridge events route to the same Lambda handler, but:
- `lambda_handler` expects `LambdaEvent` schema (mode, action, pnl_type, etc.)
- Domain events have completely different schemas (event_id, event_type, timestamp, etc.)

### What Happens When It Breaks

```
1. Trading workflow executes: main(["trade"])
   ↓
2. Orchestrator publishes: WorkflowStarted event to EventBridge
   {
     "event_id": "workflow-started-123",
     "event_type": "WorkflowStarted",
     "timestamp": "2025-10-14T14:25:29Z",
     "source_module": "orchestration.event_driven_orchestrator",
     "workflow_type": "trading",
     "requested_by": "TradingSystem",
     "configuration": {"live_trading": false}
   }
   ↓
3. EventBridge Rule (AllEventsToOrchestratorRule) matches
   ↓
4. Routes to: lambda_handler.lambda_handler()
   ↓
5. lambda_handler tries: LambdaEvent(**event)
   ↓
6. Pydantic validation error: ❌
   "Extra inputs not permitted: event_id, event_type, timestamp, source_module..."
```

---

## What We Actually Need

### Two Different Invocation Paths

```
┌───────────────────────────────────────────────────────────────────┐
│                    OPTION A: Separate Lambda Functions            │
│                                                                    │
│  TradingSystemFunction            EventRoutingFunction            │
│  (lambda_handler)                 (lambda_handler_eventbridge)    │
│  ↑                                ↑                               │
│  │                                │                               │
│  EventBridge Scheduler            EventBridge Rules               │
│  (cron schedule)                  (event patterns)                │
└───────────────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────────────┐
│                    OPTION B: One Lambda, Dual Handler             │
│                                                                    │
│  TradingSystemFunction (with both handlers)                       │
│  ├─ lambda_handler (default)      ← EventBridge Scheduler         │
│  └─ lambda_handler_eventbridge    ← EventBridge Rules             │
│                                                                    │
│  Configure different handlers per invocation source               │
└───────────────────────────────────────────────────────────────────┘
```

---

## The Fix: Option B (Recommended)

**Why Option B?**
- ✅ No code duplication
- ✅ Single deployment artifact
- ✅ Shared dependencies (layer)
- ✅ Simpler IAM permissions
- ✅ Lower cold start overhead (Lambda reuse)

### Implementation Steps

#### Step 1: Update EventBridge Rules to Use Different Handler

**File:** `template.yaml`

**Change:** Update ALL EventBridge Rules targets to invoke `lambda_handler_eventbridge` instead of `lambda_handler`

**Before:**
```yaml
SignalGeneratedRule:
  Type: AWS::Events::Rule
  Properties:
    Targets:
      - Arn: !GetAtt TradingSystemFunction.Arn
        Id: PortfolioHandler
```

**After:**
```yaml
SignalGeneratedRule:
  Type: AWS::Events::Rule
  Properties:
    Targets:
      - Arn: !GetAtt TradingSystemFunction.Arn
        Id: PortfolioHandler
        # Specify the handler function to invoke
        Input: !Sub |
          {
            "handler": "lambda_handler_eventbridge"
          }
```

**Wait, that won't work!** EventBridge can't specify which handler function within a Lambda to invoke. Lambda only has ONE entry point.

#### Step 1 (Revised): Create Smart Router Handler

**The Real Solution:** Make `lambda_handler` detect which type of event it received and route accordingly!

**File:** `the_alchemiser/lambda_handler.py`

**Current Logic:**
```python
def lambda_handler(event, context):
    # 1. Extract correlation_id
    # 2. Circuit breaker for ErrorNotificationRequested
    # 3. Unwrap EventBridge envelope if present
    # 4. Parse as LambdaEvent
    # 5. Execute main()
```

**New Logic:**
```python
def lambda_handler(event, context):
    # 1. Extract correlation_id
    # 2. Circuit breaker for ErrorNotificationRequested

    # 3. Detect event type
    if _is_domain_event(event):
        # Route to eventbridge_handler
        from the_alchemiser.lambda_handler_eventbridge import eventbridge_handler
        return eventbridge_handler(event, context)

    # 4. Unwrap EventBridge envelope if present (for scheduler events)
    # 5. Parse as LambdaEvent
    # 6. Execute main()
```

**Detection Logic:**
```python
def _is_domain_event(event: dict[str, Any]) -> bool:
    """Detect if event is a domain event vs. command event.

    Domain events have:
    - detail-type matching known domain event types
    - source starting with "alchemiser."

    Command events have:
    - detail-type: "Scheduled Event" (scheduler)
    - OR no detail-type (direct invocation)
    """
    detail_type = event.get("detail-type", "")
    source = event.get("source", "")

    # Known domain event types
    domain_event_types = {
        "WorkflowStarted",
        "SignalGenerated",
        "RebalancePlanned",
        "TradeExecuted",
        "WorkflowCompleted",
        "WorkflowFailed",
        "ErrorNotificationRequested",
    }

    # Check if it's a domain event
    is_domain = (
        detail_type in domain_event_types
        and source.startswith("alchemiser.")
    )

    return is_domain
```

---

## Implementation Plan

### Phase 1: Add Smart Routing (10 minutes)

**File:** `the_alchemiser/lambda_handler.py`

**Changes:**

1. Add `_is_domain_event()` detection function
2. Add routing logic at top of `lambda_handler()`
3. Move circuit breaker BEFORE routing (applies to both paths)

**Code:**

```python
def _is_domain_event(event: dict[str, Any]) -> bool:
    """Detect if event is a domain event (vs. command/scheduler event).

    Args:
        event: Lambda event payload

    Returns:
        True if domain event (WorkflowStarted, SignalGenerated, etc.)
        False if command event (Scheduled Event, direct invocation)
    """
    if not isinstance(event, dict):
        return False

    detail_type = event.get("detail-type", "")
    source = event.get("source", "")

    # Known domain event types
    domain_event_types = {
        "WorkflowStarted",
        "SignalGenerated",
        "RebalancePlanned",
        "TradeExecuted",
        "WorkflowCompleted",
        "WorkflowFailed",
    }

    # Check if it's a domain event from alchemiser
    return detail_type in domain_event_types and source.startswith("alchemiser.")


def lambda_handler(event, context):
    """AWS Lambda entry point with smart routing."""

    # Extract request IDs
    request_id = getattr(context, "aws_request_id", "unknown") if context else "local"
    correlation_id = _extract_correlation_id(event)
    set_request_id(correlation_id)

    logger.info("Lambda invoked", ...)

    # Circuit breaker: Skip error notifications (applies to both handlers)
    if isinstance(event, dict):
        detail_type = event.get("detail-type")
        if detail_type == "ErrorNotificationRequested":
            logger.info("Skipping ErrorNotificationRequested event...")
            return {"status": "skipped", ...}

    # Smart routing: Detect domain events vs. command events
    if _is_domain_event(event):
        logger.info(
            "Routing to eventbridge_handler for domain event",
            detail_type=event.get("detail-type"),
            source=event.get("source"),
        )
        from the_alchemiser.lambda_handler_eventbridge import eventbridge_handler
        return eventbridge_handler(event, context)

    # Continue with command/scheduler event handling
    # (existing logic for parse_event_mode, main(), etc.)
    ...
```

### Phase 2: Re-enable EventBridge Rules (2 minutes)

**File:** `template.yaml`

**Change:** Set `State: ENABLED` for all rules

```yaml
SignalGeneratedRule:
  State: ENABLED  # Was: DISABLED

RebalancePlannedRule:
  State: ENABLED  # Was: DISABLED

TradeExecutedRule:
  State: ENABLED  # Was: DISABLED

AllEventsToOrchestratorRule:
  State: ENABLED  # Was: DISABLED
```

### Phase 3: Add Missing Event Type to Map (1 minute)

**File:** `the_alchemiser/lambda_handler_eventbridge.py`

**Change:** Add `WorkflowStarted` to event map

**Current:**
```python
event_map: dict[str, type[BaseEvent]] = {
    "SignalGenerated": SignalGenerated,
    "RebalancePlanned": RebalancePlanned,
    "TradeExecuted": TradeExecuted,
    "WorkflowCompleted": WorkflowCompleted,
    "WorkflowFailed": WorkflowFailed,
}
```

**After:**
```python
from the_alchemiser.shared.events import (
    RebalancePlanned,
    SignalGenerated,
    TradeExecuted,
    WorkflowCompleted,
    WorkflowFailed,
    WorkflowStarted,  # Add this
)

event_map: dict[str, type[BaseEvent]] = {
    "WorkflowStarted": WorkflowStarted,  # Add this
    "SignalGenerated": SignalGenerated,
    "RebalancePlanned": RebalancePlanned,
    "TradeExecuted": TradeExecuted,
    "WorkflowCompleted": WorkflowCompleted,
    "WorkflowFailed": WorkflowFailed,
}
```

### Phase 4: Test Locally (5 minutes)

**Test smart routing:**

```bash
# Test 1: Scheduler event (should use lambda_handler path)
sam local invoke TradingSystemFunction \
  --event test-events/eventbridge-scheduler-trade.json

# Test 2: Domain event (should route to eventbridge_handler)
sam local invoke TradingSystemFunction \
  --event test-events/eventbridge-workflow-started.json

# Test 3: Error notification (circuit breaker)
sam local invoke TradingSystemFunction \
  --event test-events/eventbridge-error-notification.json
```

**Expected logs:**
- Test 1: "Parsed event to command: trade"
- Test 2: "Routing to eventbridge_handler for domain event"
- Test 3: "Skipping ErrorNotificationRequested event..."

### Phase 5: Deploy & Monitor (10 minutes)

```bash
# Deploy to AWS
sam deploy --config-env dev

# Monitor CloudWatch Logs
aws logs tail /aws/lambda/the-alchemiser-v2-lambda-dev --follow

# Trigger scheduler manually to test end-to-end
# AWS Console → EventBridge → Schedules → the-alchemiser-daily-trading-dev → Invoke now
```

**Watch for:**
- ✅ Scheduler event: "Parsed event to command: trade"
- ✅ WorkflowStarted published
- ✅ WorkflowStarted routed to eventbridge_handler
- ✅ No validation errors
- ✅ Workflow completes successfully

---

## Complexity Assessment

### Code Changes Required

| File | Change | Lines | Complexity |
|------|--------|-------|------------|
| `lambda_handler.py` | Add `_is_domain_event()` | ~25 | Low |
| `lambda_handler.py` | Add routing logic | ~10 | Low |
| `lambda_handler_eventbridge.py` | Add `WorkflowStarted` to map | ~3 | Trivial |
| `template.yaml` | Re-enable rules | ~4 | Trivial |
| **Total** | | **~42 lines** | **LOW** |

### Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Routing logic breaks scheduler | Low | High | Test locally first |
| Domain events still fail validation | Low | Medium | Idempotency prevents duplicates |
| Performance overhead from routing | Very Low | Low | Single function call |
| Circuit breaker not applied | Very Low | High | Moved before routing |

**Overall Risk:** **LOW** ✅

### Time Estimate

| Phase | Time | Cumulative |
|-------|------|------------|
| 1. Add smart routing | 10 min | 10 min |
| 2. Re-enable rules | 2 min | 12 min |
| 3. Add WorkflowStarted | 1 min | 13 min |
| 4. Test locally | 5 min | 18 min |
| 5. Deploy & monitor | 10 min | 28 min |
| **Total** | **~30 minutes** | |

**Actual time with debugging:** **~1 hour** (being realistic)

---

## Alternative: Separate Lambda Functions (Option A)

If smart routing feels too clever, we can create two separate Lambda functions.

### Pros
- ✅ Clear separation of concerns
- ✅ Independent scaling
- ✅ Easier to debug (clear CloudWatch log groups)
- ✅ No routing logic needed

### Cons
- ❌ More AWS resources to manage
- ❌ Duplicate dependencies (larger deployment)
- ❌ Higher cold start frequency (two functions)
- ❌ More complex IAM permissions

### Implementation

**Add to `template.yaml`:**

```yaml
EventRoutingFunction:
  Type: AWS::Serverless::Function
  Properties:
    FunctionName: !Sub "the-alchemiser-event-router-${Stage}"
    PackageType: Zip
    Runtime: python3.12
    CodeUri: ./
    Handler: the_alchemiser.lambda_handler_eventbridge.eventbridge_handler
    Role: !GetAtt TradingSystemExecutionRole.Arn
    Layers:
      - !Ref DependenciesLayer
```

**Update all EventBridge Rules:**

```yaml
SignalGeneratedRule:
  Targets:
    - Arn: !GetAtt EventRoutingFunction.Arn  # Changed
      Id: PortfolioHandler
```

**Time estimate:** **~45 minutes** (more CloudFormation changes)

---

## Recommendation

**Use Option B (Smart Routing)** because:

1. **Simpler deployment** - one Lambda function, one deployment
2. **Lower cost** - single function warm, lower invocation count
3. **Already works** - `lambda_handler_eventbridge` is fully implemented
4. **Small code change** - ~42 lines, low risk
5. **Fast to implement** - ~30 minutes

**When to use Option A:**
- If smart routing feels too "magical"
- If you want strict separation for compliance/audit
- If you need independent scaling (unlikely for this workload)

---

## Testing Plan

### Unit Tests to Add

**File:** `tests/unit/test_lambda_handler.py`

```python
def test_is_domain_event_detects_workflow_started():
    """Test detection of WorkflowStarted domain event."""
    event = {
        "detail-type": "WorkflowStarted",
        "source": "alchemiser.orchestration",
        "detail": {...}
    }
    assert _is_domain_event(event) is True

def test_is_domain_event_detects_scheduler_event():
    """Test scheduler event is NOT detected as domain event."""
    event = {
        "detail-type": "Scheduled Event",
        "source": "aws.scheduler",
        "detail": {"mode": "trade"}
    }
    assert _is_domain_event(event) is False

def test_lambda_handler_routes_to_eventbridge_handler(mock_eventbridge_handler):
    """Test lambda_handler routes domain events to eventbridge_handler."""
    event = {
        "detail-type": "SignalGenerated",
        "source": "alchemiser.strategy",
        "detail": {...}
    }

    with patch("the_alchemiser.lambda_handler.eventbridge_handler") as mock:
        lambda_handler(event, None)

    mock.assert_called_once_with(event, None)
```

### Integration Tests

**File:** `tests/integration/test_eventbridge_routing.py`

1. Test scheduler event → lambda_handler → trading workflow
2. Test WorkflowStarted event → lambda_handler → eventbridge_handler
3. Test SignalGenerated event → lambda_handler → eventbridge_handler
4. Test circuit breaker for ErrorNotificationRequested

---

## Conclusion

**Is it fucked?** No! It's actually in great shape:

✅ **Code already exists** - `lambda_handler_eventbridge.py` is fully implemented
✅ **Tests already exist** - comprehensive test coverage
✅ **Small fix** - ~42 lines of code, ~30 minutes
✅ **Low risk** - simple routing logic, easy to test
✅ **Easy rollback** - just disable rules again if issues

**The problem:** Configuration mismatch between EventBridge Rules and Lambda handlers
**The solution:** Smart routing to detect event type and route to correct handler
**The effort:** **30 minutes to 1 hour**

Not fucked at all! Just needs a small config fix. 🎯
