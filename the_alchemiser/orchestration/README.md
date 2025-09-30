# Orchestration Module

**Business Unit: orchestration | Status: current**

## Overview

The orchestration module provides event-driven coordination between business modules (strategy, portfolio, execution, notifications). It acts as the "conductor" for complex workflows that span multiple modules, managing workflow state, cross-cutting concerns, and ensuring proper event sequencing without violating module boundaries.

This module implements pure event-driven orchestration using the EventBus, enabling decoupled, extensible, and testable workflows.

## Core Responsibilities

- **Workflow Coordination**: Orchestrate complete trading workflows via events
- **Event Bus Management**: Register and coordinate domain event handlers
- **State Tracking**: Monitor workflow progress and completion
- **Cross-Cutting Concerns**: Handle notifications, reconciliation, and recovery
- **Module Boundary Enforcement**: Coordinate without direct cross-module imports

## Architecture

```
orchestration/
├── __init__.py                      # Public API exports
├── event_driven_orchestrator.py    # Primary event-driven orchestrator
├── system.py                        # System initialization and setup
├── trading_orchestrator.py          # Legacy direct-call orchestrator
└── display_utils.py                 # Output formatting utilities
```

### Event-Driven Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    EventDrivenOrchestrator                   │
│  - Registers domain handlers via module APIs                │
│  - Tracks workflow state and correlation IDs                │
│  - Handles cross-cutting concerns (monitoring, recovery)    │
└─────────────────────────────────────────────────────────────┘
                              │
                        ┌─────▼─────┐
                        │  EventBus │
                        └───────────┘
                              │
    ┌─────────────────────────┼─────────────────────────┐
    │                         │                         │
┌───▼───────┐        ┌────────▼────────┐      ┌────────▼────────┐
│ Strategy  │        │   Portfolio     │      │   Execution     │
│ Handlers  │        │   Handlers      │      │   Handlers      │
└───────────┘        └─────────────────┘      └─────────────────┘
    │                         │                         │
    │ SignalGenerated        │ RebalancePlanned       │ TradeExecuted
    └────────────────────────┴─────────────────────────┴──────────►
                        Events published to EventBus
```

## Core Design Principles

### Event-Driven Communication
- **No direct imports** of business module implementations
- **Module registration functions** wire handlers to event bus
- **Event-based coordination** replaces direct method calls
- **Idempotent handlers** tolerate event replay

### Workflow State Management
- Track active workflows by correlation ID
- Monitor workflow progression through lifecycle events
- Collect results across multiple events
- Provide timeout and recovery mechanisms

### Module Boundaries
- **Imports from**: `shared/` (events, config, logging) and module registration APIs
- **No imports from**: Business module internals (strategy/engines, portfolio/core, etc.)
- **Communication**: Via EventBus only; coordinate through event subscription

## Usage

### Starting a Trading Workflow

```python
from the_alchemiser.orchestration import EventDrivenOrchestrator
from the_alchemiser.shared.config.container import ApplicationContainer

# Initialize container and orchestrator
container = ApplicationContainer()
orchestrator = EventDrivenOrchestrator(container)

# Start workflow (non-blocking)
correlation_id = orchestrator.start_trading_workflow()
print(f"Started workflow: {correlation_id}")

# Wait for completion with timeout
results = orchestrator.wait_for_workflow_completion(
    correlation_id,
    timeout_seconds=300
)

# Check results
if results["success"]:
    print(f"Workflow completed in {results['duration_seconds']:.2f}s")
    print(f"Orders executed: {len(results['orders_executed'])}")
else:
    print(f"Workflow failed: {results['completion_status']}")
```

### Event Workflow Sequence

A typical trading workflow follows this event sequence:

1. **WorkflowStarted** → Orchestrator initiates workflow
2. **SignalGenerated** → Strategy module emits allocation signals
3. **RebalancePlanned** → Portfolio module emits rebalance plan
4. **TradeExecuted** → Execution module emits per-order results
5. **WorkflowCompleted** or **WorkflowFailed** → Final status

```python
# The orchestrator coordinates this automatically:
correlation_id = orchestrator.start_trading_workflow()

# Behind the scenes:
# 1. Publishes WorkflowStarted event
# 2. Strategy handler responds with SignalGenerated
# 3. Portfolio handler responds with RebalancePlanned
# 4. Execution handler responds with TradeExecuted (multiple)
# 5. Execution handler publishes WorkflowCompleted
```

### Monitoring Workflow State

```python
# Check active workflows
active_correlations = orchestrator.workflow_state["active_correlations"]
print(f"Active workflows: {len(active_correlations)}")

# Check if specific workflow is active
if correlation_id in active_correlations:
    print(f"Workflow {correlation_id} is in progress")

# Get workflow stage
if orchestrator.workflow_state["signal_generation_in_progress"]:
    print("Currently generating signals...")
elif orchestrator.workflow_state["rebalancing_in_progress"]:
    print("Currently planning rebalance...")
elif orchestrator.workflow_state["trading_in_progress"]:
    print("Currently executing trades...")
```

## Event Bus Integration

### Handler Registration

The orchestrator registers all domain handlers at initialization:

```python
def _register_domain_handlers(self) -> None:
    """Register domain event handlers using module registration functions."""
    from the_alchemiser.strategy_v2 import register_strategy_handlers
    from the_alchemiser.portfolio_v2 import register_portfolio_handlers
    from the_alchemiser.execution_v2 import register_execution_handlers
    from the_alchemiser.notifications_v2 import register_notification_handlers
    
    # Each module registers its own handlers
    register_strategy_handlers(self.container)
    register_portfolio_handlers(self.container)
    register_execution_handlers(self.container)
    register_notification_handlers(self.container)
```

### Event Types Handled

The orchestrator subscribes to these events for cross-cutting concerns:

- **StartupEvent**: System initialization and readiness
- **WorkflowStarted**: Workflow initiation and tracking
- **SignalGenerated**: Signal completion monitoring
- **RebalancePlanned**: Rebalance plan monitoring
- **TradeExecuted**: Trade execution monitoring
- **WorkflowCompleted**: Success path finalization
- **WorkflowFailed**: Error path handling

## Integration Points

### Module Registration APIs

Each business module exposes a registration function that the orchestrator calls:

```python
# Strategy module
from the_alchemiser.strategy_v2 import register_strategy_handlers
register_strategy_handlers(container)

# Portfolio module
from the_alchemiser.portfolio_v2 import register_portfolio_handlers
register_portfolio_handlers(container)

# Execution module
from the_alchemiser.execution_v2 import register_execution_handlers
register_execution_handlers(container)

# Notifications module
from the_alchemiser.notifications_v2 import register_notification_handlers
register_notification_handlers(container)
```

### Dependencies

- **shared/events**: EventBus and event schemas
- **shared/config**: ApplicationContainer for dependency injection
- **shared/logging**: Structured logging utilities

### Module Boundaries

- ✅ **Only imports** module registration functions (public API)
- ✅ **No imports** of internal module implementations
- ✅ **Event-driven** coordination; no direct method calls
- ✅ **Clean separation** of orchestration from domain logic

## Workflow State Tracking

The orchestrator maintains workflow state for monitoring and recovery:

```python
workflow_state = {
    "startup_completed": False,           # System initialization complete
    "signal_generation_in_progress": False,  # Strategy running
    "rebalancing_in_progress": False,     # Portfolio calculation running
    "trading_in_progress": False,         # Execution running
    "last_successful_workflow": None,     # Last completed correlation ID
    "active_correlations": set(),         # Currently active workflows
    "workflow_start_times": {},           # Start timestamps by correlation ID
    "completed_correlations": set(),      # Completed/failed workflows
}
```

### Result Collection

Results are collected across events and stored by correlation ID:

```python
workflow_results = {
    "correlation-123": {
        "strategy_signals": {...},        # From SignalGenerated event
        "rebalance_plan": {...},          # From RebalancePlanned event
        "orders_executed": [...],         # From TradeExecuted events
        "execution_summary": {...},       # From WorkflowCompleted event
    }
}
```

## Error Handling

The orchestrator handles errors at the workflow level:

### Workflow Failure Events

```python
def _handle_workflow_failed(self, event: WorkflowFailed) -> None:
    """Handle workflow failure for recovery and notifications."""
    
    # Log failure
    logger.error(
        f"Workflow failed: {event.failure_reason}",
        extra={
            "correlation_id": event.correlation_id,
            "error_code": event.error_code,
        }
    )
    
    # Update state
    self.workflow_state["active_correlations"].discard(event.correlation_id)
    
    # Store failure details for result collection
    self.workflow_results[event.correlation_id] = {
        "failure_reason": event.failure_reason,
        "error_code": event.error_code,
    }
```

### Timeout Handling

```python
# Wait for workflow with timeout
results = orchestrator.wait_for_workflow_completion(
    correlation_id,
    timeout_seconds=300  # 5 minutes
)

if results["completion_status"] == "timeout":
    # Handle timeout (manual intervention, retry, alert)
    logger.error(f"Workflow {correlation_id} timed out")
```

### Error Recovery

Workflows can be restarted with the same correlation ID for idempotent retry:

```python
# Retry failed workflow
try:
    correlation_id = orchestrator.start_trading_workflow(
        correlation_id="retry-previous-workflow"
    )
    results = orchestrator.wait_for_workflow_completion(correlation_id)
except Exception as e:
    logger.error(f"Retry failed: {e}")
```

## Performance Considerations

### Asynchronous Coordination
- Event-driven architecture is inherently asynchronous
- Workflows proceed as events are processed
- No blocking waits between stages (except in `wait_for_completion`)

### Memory Management
- Workflow results are stored in memory during execution
- Results are cleaned up after retrieval to prevent leaks
- Completed correlation IDs are tracked to prevent duplicate starts

### Scalability
- Multiple workflows can run concurrently (tracked by correlation ID)
- EventBus handles concurrent event processing
- State is isolated per correlation ID

## Logging

Structured logging with correlation IDs throughout:

```json
{
  "timestamp": "2024-01-01T10:00:00Z",
  "level": "INFO",
  "message": "🚀 Starting event-driven trading workflow: abc-123",
  "correlation_id": "abc-123",
  "module": "orchestration.event_driven_orchestrator"
}
```

Key log points:
- Workflow start/completion
- Event handler registration
- State transitions
- Error conditions
- Timeout warnings

## Testing and Validation

### Unit Tests
```bash
# Run orchestration module tests
poetry run pytest tests/orchestration/ -v

# Test with coverage
poetry run pytest tests/orchestration/ --cov=the_alchemiser.orchestration
```

### Integration Testing
```bash
# Test complete workflow
poetry run python scripts/test_event_driven_workflow.py
```

### Manual Testing
```python
# Test workflow coordination
from the_alchemiser.orchestration import EventDrivenOrchestrator
from the_alchemiser.shared.config.container import ApplicationContainer

container = ApplicationContainer()
orchestrator = EventDrivenOrchestrator(container)

# Start and monitor workflow
correlation_id = orchestrator.start_trading_workflow()
results = orchestrator.wait_for_workflow_completion(correlation_id, timeout_seconds=60)

print(f"Workflow result: {results['success']}")
print(f"Duration: {results['duration_seconds']:.2f}s")
```

### Type Checking
```bash
# Verify type correctness
make type-check
```

## Migration Status

The orchestration module is fully operational with event-driven architecture.

### Completed
- ✅ Event-driven orchestrator implementation
- ✅ Domain handler registration via module APIs
- ✅ Workflow state tracking and monitoring
- ✅ Timeout and error handling
- ✅ Result collection across events
- ✅ Clean module boundaries

### Legacy Components
- ⚠️ `trading_orchestrator.py`: Legacy direct-call orchestrator (deprecated)
  - Use `EventDrivenOrchestrator` instead
  - Kept for backward compatibility only

### Future Enhancements
- ⏳ Workflow persistence for recovery after restarts
- ⏳ Advanced retry strategies with exponential backoff
- ⏳ Workflow visualization and monitoring UI
- ⏳ Distributed orchestration across multiple Lambda functions

## CLI Integration

The orchestration module is used by CLI commands for interactive workflows:

```bash
# Run trading workflow via CLI
poetry run python -m the_alchemiser

# The CLI uses orchestration internally:
# - Initializes EventDrivenOrchestrator
# - Starts workflow
# - Monitors progress
# - Displays results
```

See CLI documentation for usage details.

## Best Practices

### Always Use Event-Driven Patterns
```python
# ✅ Good: Event-driven coordination
orchestrator = EventDrivenOrchestrator(container)
correlation_id = orchestrator.start_trading_workflow()

# ❌ Bad: Direct cross-module calls
from the_alchemiser.strategy_v2.core.orchestrator import SingleStrategyOrchestrator
strategy_result = orchestrator.run(...)  # Violates boundaries
```

### Track Workflows by Correlation ID
```python
# ✅ Good: Use correlation IDs for tracking
correlation_id = orchestrator.start_trading_workflow()
results = orchestrator.wait_for_workflow_completion(correlation_id)

# ❌ Bad: Assume single workflow
orchestrator.start_trading_workflow()
# Can't track or retrieve results
```

### Handle Timeouts Gracefully
```python
# ✅ Good: Handle timeout case
results = orchestrator.wait_for_workflow_completion(
    correlation_id,
    timeout_seconds=300
)
if results["completion_status"] == "timeout":
    handle_timeout(correlation_id)

# ❌ Bad: Infinite wait
results = orchestrator.wait_for_workflow_completion(
    correlation_id,
    timeout_seconds=999999
)
```
