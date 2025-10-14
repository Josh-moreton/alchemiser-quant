# EventBridge Migration - Complete Cutover (Phase 3)

## Overview

This document describes the complete migration to Amazon EventBridge for the Alchemiser trading system, completing the work started in Phases 1 and 2. As of version 2.26.0, the system now uses EventBridge exclusively for distributed event-driven architecture.

## What Changed

### 1. Default Event Bus is Now EventBridge

**File: `the_alchemiser/shared/config/service_providers.py`**

The `create_event_bus()` factory function now returns `EventBridgeBus` by default, removing the environment variable check that previously toggled between in-memory and EventBridge buses.

**Before (Phase 2):**
```python
def create_event_bus() -> EventBus | EventBridgeBus:
    """Create appropriate event bus based on environment."""
    use_eventbridge = os.environ.get("USE_EVENTBRIDGE", "false").lower() == "true"
    if use_eventbridge:
        return EventBridgeBus()
    return EventBus()
```

**After (Phase 3):**
```python
def create_event_bus() -> EventBridgeBus:
    """Create EventBridge bus for distributed event routing."""
    return EventBridgeBus()
```

### 2. Orchestrator Uses EventBridgeBus Type

**File: `the_alchemiser/orchestration/event_driven_orchestrator.py`**

Updated type hints to reflect that the event bus is now always an `EventBridgeBus` instance:

```python
from the_alchemiser.shared.events import (
    EventBridgeBus,  # Changed from EventBus
    # ... other imports
)

class EventDrivenOrchestrator:
    def __init__(self, container: ApplicationContainer) -> None:
        self.event_bus: EventBridgeBus = container.services.event_bus()  # Type updated
```

### 3. Test Infrastructure Updated

**File: `tests/conftest.py`**

Added new fixture for EventBridge-aware testing:

```python
@pytest.fixture
def eventbridge_bus_fixture():
    """Create an EventBridgeBus instance for testing with mocked boto3 client."""
    bus = EventBridgeBus(event_bus_name="test-bus", enable_local_handlers=True)
    # Mock the boto3 client to avoid actual AWS calls
    mock_client = Mock()
    mock_client.put_events.return_value = {
        "FailedEntryCount": 0,
        "Entries": [{"EventId": "test-event-id"}]
    }
    bus._events_client = mock_client
    return bus
```

**File: `tests/shared/config/test_service_providers.py`**

Updated tests to verify `EventBridgeBus` instances:

```python
def test_service_providers_event_bus_type() -> None:
    container = ServiceProviders()
    bus = container.event_bus()
    
    assert isinstance(bus, EventBridgeBus)
    # EventBridgeBus inherits from EventBus
    assert isinstance(bus, EventBus)
```

## Architecture

### Event Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        Lambda Invocation (Entry Points)                  │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                           │
│  ┌──────────────────┐         ┌──────────────────────────────────┐     │
│  │  Standard Lambda │         │  EventBridge Lambda Handler      │     │
│  │  (lambda_handler)│         │  (eventbridge_handler)           │     │
│  └────────┬─────────┘         └────────┬─────────────────────────┘     │
│           │                             │                                │
│           │ Creates events              │ Receives EventBridge events   │
│           │                             │                                │
└───────────┼─────────────────────────────┼────────────────────────────────┘
            │                             │
            ▼                             ▼
   ┌────────────────────────────────────────────────────┐
   │         EventBridgeBus (Service Provider)          │
   │  • Publishes to Amazon EventBridge                 │
   │  • Handles serialization & error logging           │
   │  • Tracks correlation/causation IDs                │
   └────────────────┬───────────────────────────────────┘
                    │
                    │ publish(event)
                    ▼
   ┌────────────────────────────────────────────────────┐
   │           Amazon EventBridge                        │
   │  • Durable event storage                           │
   │  • Automatic retries (up to 185x over 24h)         │
   │  • Dead-letter queue for failed events             │
   │  • CloudWatch metrics & logs                       │
   │  • Event archive for replay (365 days)             │
   └────────────────┬───────────────────────────────────┘
                    │
                    │ EventBridge Rules route by event type
                    │
        ┌───────────┼───────────┬───────────────────┐
        │           │           │                   │
        ▼           ▼           ▼                   ▼
   SignalGenerated  RebalancePlanned  TradeExecuted  WorkflowCompleted
        │               │              │               │
        │               │              │               │
        ▼               ▼              ▼               ▼
   Portfolio Lambda  Execution Lambda  Orchestrator   Orchestrator
```

### Event Routing via CloudFormation

Events are no longer routed via programmatic `subscribe()` calls. Instead, routing is managed by CloudFormation EventRules in `template.yaml`:

```yaml
SignalGeneratedRule:
  Type: AWS::Events::Rule
  Properties:
    EventBusName: !Ref AlchemiserEventBus
    EventPattern:
      source:
        - alchemiser.strategy
      detail-type:
        - SignalGenerated
    Targets:
      - Arn: !GetAtt PortfolioLambda.Arn
        Id: PortfolioHandler
        RetryPolicy:
          MaximumRetryAttempts: 3
          MaximumEventAge: 3600
        DeadLetterConfig:
          Arn: !GetAtt EventDLQ.Arn
```

## Handler Registration

While handler registration functions still call `event_bus.subscribe()`, these calls now log warnings and are ignored when `enable_local_handlers=False` (the default for EventBridgeBus):

```python
# In strategy_v2/__init__.py, portfolio_v2/__init__.py, etc.
def register_strategy_handlers(container: ApplicationContainer) -> None:
    event_bus = container.services.event_bus()
    signal_handler = SignalGenerationHandler(container)
    
    # This logs a warning but doesn't fail
    # Actual routing is via CloudFormation EventRules
    event_bus.subscribe("StartupEvent", signal_handler)
```

This maintains backward compatibility and allows the code to work with both EventBridge (production) and in-memory EventBus (testing).

## Testing Strategy

### Unit Tests
- Continue to use in-memory `EventBus` for fast, isolated unit tests
- Use `event_bus_fixture()` for tests that don't need EventBridge

### Integration Tests with Mocked EventBridge
- Use `eventbridge_bus_fixture()` for tests that need EventBridge behavior
- Mocked boto3 client prevents actual AWS API calls
- Tests verify event serialization and publishing logic

### End-to-End Tests
- Deploy to AWS test environment
- Test actual EventBridge event flow
- Verify Lambda invocations via EventBridge
- Monitor CloudWatch Logs for event tracing

## Backward Compatibility

### EventBridgeBus Inherits from EventBus

Since `EventBridgeBus(EventBus)`, all existing code expecting `EventBus` continues to work:
- All methods from `EventBus` are available
- `set_workflow_state_checker()` works as before
- `_handlers` dict access works (inherited from parent)
- Handler wrapping in orchestrator works unchanged

### Local Handler Support

EventBridgeBus supports `enable_local_handlers=True` for testing:

```python
# Test mode: events published to EventBridge AND local handlers
bus = EventBridgeBus(enable_local_handlers=True)
bus.subscribe("SignalGenerated", handler)
bus.publish(event)  # Publishes to EventBridge AND calls handler
```

### In-Memory Bus Still Available

For unit tests that need fast, isolated event flow:

```python
from the_alchemiser.shared.events.bus import EventBus

# Pure in-memory event bus (no AWS dependencies)
bus = EventBus()
```

## Benefits of EventBridge

### 1. Durability
- Events persisted to EventBridge before handler invocation
- Lambda crashes don't lose events
- Automatic retry on transient failures

### 2. Async Execution
- Handlers invoked asynchronously
- No blocking between workflow stages
- Independent Lambda timeouts per stage

### 3. Observability
- Every event logged to CloudWatch
- X-Ray tracing for end-to-end workflows
- Event history for auditing

### 4. Replay & Recovery
- 365-day event archive to S3
- Replay past events for testing
- Recover from bugs by reprocessing

### 5. Scalability
- Multiple Lambda instances per handler
- Automatic load balancing
- Rate limiting per target

### 6. Cost Efficiency
- ~$0.01-0.02/month for 100-200 events/day
- No idle cost
- Pay only for events published

## Environment Variables

### Required for EventBridge

- `EVENTBRIDGE_BUS_NAME` - Name of the EventBridge event bus
  - Default: `alchemiser-trading-events-dev`
  - Production: `alchemiser-trading-events-prod`

### No Longer Used

- `USE_EVENTBRIDGE` - Removed in Phase 3 (EventBridge is always used)

## Deployment Notes

### Prerequisites

1. EventBridge event bus created via CloudFormation
2. EventBridge rules configured for each event type
3. Lambda functions have EventBridge permissions
4. Dead-letter queue configured for failed events
5. Event archive enabled for replay capability

### CloudFormation Stack

Deploy the complete EventBridge infrastructure:

```bash
sam build
sam deploy --config-env production
```

This creates:
- EventBridge event bus
- Event rules for each event type
- Dead-letter queue (SQS)
- Event archive (S3)
- Lambda permissions

### Monitoring

**CloudWatch Dashboards:**
- EventBridge invocations and failures
- Lambda execution metrics
- DLQ message count

**Alarms:**
- High DLQ message count (> 5 messages)
- Failed EventBridge invocations
- Lambda errors

## Migration Checklist

- [x] Phase 1: EventBridge infrastructure (CloudFormation)
- [x] Phase 2: EventBridgeBus implementation
- [x] Phase 3: Complete cutover
  - [x] Remove in-memory EventBus as default
  - [x] Update type hints to EventBridgeBus
  - [x] Update tests for EventBridgeBus
  - [x] Remove USE_EVENTBRIDGE environment variable
  - [x] Update documentation
  - [x] Version bump to 2.26.0

## Rollback Plan

If issues arise after deployment, rollback is straightforward:

1. **Code Rollback:**
   ```bash
   git revert <commit-hash>
   sam deploy
   ```

2. **Database State:**
   - No database changes required
   - Event history preserved in EventBridge

3. **In-Flight Events:**
   - EventBridge continues processing queued events
   - DLQ captures any failures
   - Replay from archive if needed

## Future Enhancements

### Phase 4 (Optional)

1. **Schema Registry:**
   - Register event schemas with EventBridge Schema Registry
   - Enable code generation from schemas
   - Version management for event schemas

2. **Content-Based Routing:**
   - Route high-value trades to different handlers
   - Filter events by numeric thresholds
   - Complex event patterns

3. **Cross-Account Events:**
   - Publish events to other AWS accounts
   - Enable multi-tenant architecture
   - Centralized event bus

4. **Event Replay Automation:**
   - Scheduled replays for testing
   - Automated recovery workflows
   - Integration with CI/CD

## References

- [Amazon EventBridge Documentation](https://docs.aws.amazon.com/eventbridge/)
- [EventBridge Best Practices](https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-best-practices.html)
- [EVENTBRIDGE_PHASE2.md](./EVENTBRIDGE_PHASE2.md) - Phase 2 implementation details
- Issue #[issue-number] - Original feature request

## Version History

- **2.26.0** (2025-10-14) - Phase 3: Complete cutover to EventBridge
- **2.25.0** (2025-10-13) - Phase 2: EventBridgeBus implementation
- **2.24.0** (2025-10-12) - Phase 1: CloudFormation infrastructure

---

**Status:** ✅ Complete  
**Last Updated:** 2025-10-14  
**Author:** AI Copilot Agent
