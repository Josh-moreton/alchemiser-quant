# Integration Tests for Event-Driven Workflow

This directory contains comprehensive integration tests for validating the event-driven architecture of The Alchemiser trading system.

## Test Overview

### Event-Driven Workflow Tests (`test_event_driven_workflow.py`)

Validates the complete event chain through the system:

- **Full Event Chain**: `WorkflowStarted` → `SignalGenerated` → `RebalancePlanned` → `TradeExecuted` → `WorkflowCompleted`
- **Failure Scenarios**: Tests workflow failure handling with `WorkflowFailed` events
- **Replay Testing**: Validates idempotency behavior with duplicate event replay
- **Timeout Handling**: Ensures graceful handling of hanging workflows
- **Correlation Tracking**: Verifies correlation ID propagation throughout the chain

### Smoke Tests (`test_smoke_tests.py`)

End-to-end validation of system components:

- **Module Entry Point**: Validates `python -m the_alchemiser` functionality
- **Structured Logging**: Tests correlation metadata in log messages
- **Metrics Collection**: Validates event counters and performance metrics
- **OpenTelemetry Stubs**: Tests future tracing integration points
- **Import Boundaries**: Ensures architectural constraints are maintained

## Running the Tests

### Prerequisites

```bash
# Install test dependencies
pip install pytest pytest-asyncio pydantic pandas dependency-injector

# For full functionality (optional)
pip install alpaca-py boto3 requests PyYAML tqdm cachetools
```

### Running Tests

```bash
# Run all integration tests
pytest tests/integration/ -v

# Run specific test suites
pytest tests/integration/test_event_driven_workflow.py -v
pytest tests/integration/test_smoke_tests.py -v

# Run with markers
pytest tests/integration/ -m integration -v
```

### Test Markers

Tests are marked with appropriate pytest markers:

- `@pytest.mark.integration`: Integration tests requiring multiple components
- `@pytest.mark.skipif`: Conditional tests that skip based on environment

## Test Architecture

### Mock Handlers

The tests use mock event handlers that:

- Emit proper events following the schema
- Track correlation IDs throughout the chain
- Simulate both success and failure scenarios
- Support configurable behavior for different test cases

### Event Tracking

Tests include an `EventTracker` fixture that:

- Records all events published during test execution
- Provides counts and filtering by event type
- Validates event sequence and correlation propagation
- Enables assertion on event flow correctness

### Metrics Validation

Tests verify:

- Event counters increment correctly
- Handler latencies are recorded
- Workflow gauges reflect system state
- Metrics summary includes all expected data

## Expected Results

### Passing Tests

- **Full Event Chain Success**: Validates complete workflow execution
- **Full Event Chain Failure**: Validates error handling and `WorkflowFailed` emission
- **Timeout Handling**: Validates graceful timeout behavior
- **Smoke Tests**: Most smoke tests should pass (some may skip due to environment)

### Known Limitations

- **Idempotency Test**: May fail as full idempotency implementation is pending
- **End-to-End Test**: May skip due to dependency configuration in test environment
- **Configuration Tests**: May skip if settings cannot be loaded in test environment

## Observability Validation

The tests validate that the event-driven system provides:

1. **Structured Logging**: All events include correlation metadata
2. **Metrics Collection**: Event counters and handler latencies are tracked
3. **Error Handling**: Failures are properly logged and propagated
4. **Performance Monitoring**: Handler execution times are measured

## Future Enhancements

- **Persistent Idempotency Testing**: Once database-backed deduplication is implemented
- **External Broker Testing**: When Kafka/RabbitMQ integration is added
- **Performance Benchmarks**: Load testing for event processing throughput
- **Chaos Engineering**: Failure injection and recovery testing