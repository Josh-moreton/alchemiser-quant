# EventBridge Integration - Phase 2 Implementation

## Overview

This document describes the Phase 2 implementation of Amazon EventBridge integration for the Alchemiser trading system, as specified in issue #[issue-number].

## What Was Implemented

### 1. EventBridgeBus Class (`the_alchemiser/shared/events/eventbridge_bus.py`)

A new event bus implementation that publishes events to Amazon EventBridge while maintaining backward compatibility with the existing EventBus interface.

**Key Features:**
- Publishes events to EventBridge with proper source, detail-type, and detail structure
- Supports correlation and causation ID tracking via EventBridge Resources field
- Lazy initialization of boto3 EventBridge client
- Optional local handler support for testing/hybrid mode
- Error handling that logs but doesn't raise to avoid disrupting workflows
- Tracks event count like the in-memory EventBus

**Usage:**
```python
from the_alchemiser.shared.events import EventBridgeBus, SignalGenerated

# Create EventBridge bus
bus = EventBridgeBus(
    event_bus_name="alchemiser-trading-events-dev",
    source_prefix="alchemiser"
)

# Publish event
event = SignalGenerated(...)
bus.publish(event)  # Published to EventBridge
```

### 2. Lambda EventBridge Handler (`the_alchemiser/lambda_handler_eventbridge.py`)

Entry point for AWS Lambda functions triggered by EventBridge events.

**Key Features:**
- Extracts event details from EventBridge payload
- Parses timestamp strings to datetime objects
- Reconstructs event objects from JSON detail
- Routes events to appropriate handlers (Portfolio, Execution, etc.)
- Returns proper HTTP response codes for Lambda
- Re-raises exceptions to trigger Lambda retry mechanism

**Handler Mapping:**
- `SignalGenerated` → `PortfolioAnalysisHandler`
- `RebalancePlanned` → `TradingExecutionHandler`
- `TradeExecuted`, `WorkflowCompleted`, `WorkflowFailed` → Orchestrator only (returns None)

### 3. Service Provider Integration (`the_alchemiser/shared/config/service_providers.py`)

Updated to support environment-based event bus selection.

**Factory Function:**
```python
def create_event_bus() -> EventBus | EventBridgeBus:
    """Create appropriate event bus based on environment.
    
    Returns EventBridgeBus if USE_EVENTBRIDGE=true, otherwise EventBus.
    """
```

**Environment Variable:**
- `USE_EVENTBRIDGE=true` - Use EventBridge for event publishing
- `USE_EVENTBRIDGE=false` (default) - Use in-memory EventBus

**EventBridge Bus Name:**
- `EVENTBRIDGE_BUS_NAME` environment variable
- Default: `alchemiser-trading-events-dev`

### 4. Comprehensive Test Suite

**EventBridgeBus Tests** (`tests/shared/events/test_eventbridge_bus.py`):
- 16 tests covering:
  - Initialization with various configurations
  - Event publishing to EventBridge
  - Error handling and failure scenarios
  - Local handler support
  - Inheritance from EventBus
  - Event count tracking

**Lambda Handler Tests** (`tests/unit/test_lambda_handler_eventbridge.py`):
- 16 tests covering:
  - Event routing to correct handlers
  - Event deserialization from EventBridge payload
  - String detail parsing
  - Unknown event type handling
  - Handler instantiation
  - Error propagation for retries

**All Tests Pass:**
- 32 new tests (16 + 16)
- 134 tests in shared/events module
- Type checking passes (mypy strict mode)
- Code formatting and linting pass (ruff)

## Architecture

### Event Flow

```
Source Module (Strategy) 
    ↓
EventBridgeBus.publish()
    ↓
boto3.events.put_events()
    ↓
Amazon EventBridge
    ↓
EventBridge Rules (Phase 1)
    ↓
Target Lambda (Portfolio/Execution)
    ↓
lambda_handler_eventbridge()
    ↓
Appropriate Handler
```

### EventBridge Entry Structure

```python
{
    "Time": datetime.now(UTC),
    "Source": "alchemiser.strategy",  # {prefix}.{source_module}
    "DetailType": "SignalGenerated",  # event.event_type
    "Detail": json.dumps(event_dict),  # Full event serialized
    "EventBusName": "alchemiser-trading-events-dev",
    "Resources": [
        "correlation:corr-123",
        "causation:cause-456"
    ]
}
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_EVENTBRIDGE` | `false` | Enable EventBridge bus |
| `EVENTBRIDGE_BUS_NAME` | `alchemiser-trading-events-dev` | EventBridge bus name |

### IAM Permissions Required

Lambda execution role needs:
```json
{
    "Effect": "Allow",
    "Action": [
        "events:PutEvents"
    ],
    "Resource": "arn:aws:events:region:account:event-bus/alchemiser-trading-events-*"
}
```

## Testing

### Unit Tests
```bash
# Test EventBridgeBus
poetry run pytest tests/shared/events/test_eventbridge_bus.py -v

# Test Lambda handler
poetry run pytest tests/unit/test_lambda_handler_eventbridge.py -v

# Test all event module
poetry run pytest tests/shared/events/ -v
```

### Type Checking
```bash
# Check new files
poetry run mypy the_alchemiser/shared/events/eventbridge_bus.py \
    the_alchemiser/lambda_handler_eventbridge.py \
    the_alchemiser/shared/config/service_providers.py
```

### Linting
```bash
poetry run ruff check the_alchemiser/shared/events/eventbridge_bus.py \
    the_alchemiser/lambda_handler_eventbridge.py \
    the_alchemiser/shared/config/service_providers.py
```

## Integration with Phase 1

Phase 1 (already completed) created:
- EventBridge event bus: `alchemiser-trading-events-{Stage}`
- Event archive for replay (365-day retention)
- Dead-letter queue for failed events
- Event rules (currently DISABLED)

Phase 2 (this implementation) adds:
- EventBridgeBus class for publishing events
- Lambda handler for receiving events
- Service provider integration

**Next Steps (Phase 3 - Not in Scope):**
- Enable EventBridge rules in CloudFormation
- Split Lambda into separate functions per handler
- Add CloudWatch dashboards and alarms
- Test event replay from archive
- Implement event transformation rules

## Breaking Changes

None. This is a backward-compatible addition.

- Default behavior remains in-memory EventBus
- EventBridge enabled via environment variable
- Existing tests continue to pass

## Version

Version bumped from **2.24.0** to **2.25.0** (minor version) per semantic versioning:
- New features added (EventBridge support)
- Backward compatible
- No breaking changes

## Files Changed

### New Files
- `the_alchemiser/shared/events/eventbridge_bus.py` (211 lines)
- `the_alchemiser/lambda_handler_eventbridge.py` (175 lines)
- `tests/shared/events/test_eventbridge_bus.py` (355 lines)
- `tests/unit/test_lambda_handler_eventbridge.py` (281 lines)

### Modified Files
- `the_alchemiser/shared/events/__init__.py` - Export EventBridgeBus
- `the_alchemiser/shared/config/service_providers.py` - Add factory function
- `tests/shared/events/test_events_init.py` - Update tests for EventBridgeBus
- `pyproject.toml` - Add boto3 dependency, bump version
- `poetry.lock` - Update lock file

## Dependencies

Added: **boto3** ^1.40.51
- Required for EventBridge client
- AWS SDK for Python
- Includes botocore, jmespath, s3transfer

## Documentation

This README serves as the implementation documentation for Phase 2.

For usage examples and API reference, see:
- EventBridgeBus docstrings
- Lambda handler docstrings
- Test files for examples

## Future Work

Phase 3 (not implemented):
- Enable EventBridge rules in template.yaml
- Split Lambda into separate functions
- Add event transformation rules
- Implement event replay scripts
- Add CloudWatch monitoring
- Create runbooks for operational scenarios

## References

- Issue: Migrate to Amazon EventBridge for Event-Driven Architecture
- Phase 1 PR: #2451 (merged)
- AWS EventBridge Documentation: https://docs.aws.amazon.com/eventbridge/
