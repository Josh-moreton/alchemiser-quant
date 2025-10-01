# Workflow State Management Implementation Summary

## Problem Solved

Previously, when a workflow failed (e.g., due to negative cash balance), the event-driven system continued processing events in parallel, leading to confusing logs and wasted processing.

**Example from logs:**
```
12:51:12,224 - ERROR - Account has non-positive cash balance: $-7920.51
12:51:12,226 - ERROR - ❌ Workflow failed: portfolio_analysis
12:51:12,227 - INFO - ✅ Signal generation completed successfully  # ← MISLEADING!
```

The workflow **did** fail correctly, but other handlers continued processing the same `SignalGenerated` event in parallel, creating misleading "success" messages after the workflow had already failed.

## Solution Implemented

### 1. Workflow State Tracking

Added `WorkflowState` enum to track the execution state of each workflow:

```python
class WorkflowState(Enum):
    RUNNING = "running"      # Workflow is actively running
    FAILED = "failed"        # Workflow has failed - no further processing
    COMPLETED = "completed"  # Workflow completed successfully
```

### 2. State Management in EventDrivenOrchestrator

Added state tracking with thread-safe operations:

```python
# Track workflow states per correlation_id
self.workflow_states: dict[str, WorkflowState] = {}
self.workflow_states_lock = Lock()

def is_workflow_failed(self, correlation_id: str) -> bool:
    """Check if a workflow has failed."""
    with self.workflow_states_lock:
        return self.workflow_states.get(correlation_id) == WorkflowState.FAILED

def is_workflow_active(self, correlation_id: str) -> bool:
    """Check if a workflow is actively running."""
    with self.workflow_states_lock:
        return self.workflow_states.get(correlation_id) == WorkflowState.RUNNING
```

### 3. State Transitions

Updated workflow event handlers to set appropriate states:

- `_handle_workflow_started()` → Sets state to `RUNNING`
- `_handle_workflow_failed()` → Sets state to `FAILED` (blocks future processing)
- `_handle_workflow_completed()` → Sets state to `COMPLETED`

### 4. Handler Wrapping Pattern

Implemented `StateCheckingHandlerWrapper` to intercept events before they reach handlers:

```python
class StateCheckingHandlerWrapper:
    """Wrapper that checks workflow state before delegating to actual handler."""
    
    def handle_event(self, event: BaseEvent) -> None:
        # Check if workflow has failed before processing
        if self.orchestrator.is_workflow_failed(event.correlation_id):
            handler_name = type(self.wrapped_handler).__name__
            self.logger.info(
                f"🚫 Skipping {handler_name} - workflow {event.correlation_id} already failed"
            )
            return
        
        # Delegate to actual handler
        self.wrapped_handler.handle_event(event)
```

### 5. Automatic Handler Wrapping

The orchestrator automatically wraps critical event handlers after registration:

```python
def _wrap_handlers_with_state_checking(self) -> None:
    """Wrap registered handlers with workflow state checking."""
    state_checked_events = [
        "SignalGenerated",
        "RebalancePlanned",
    ]
    
    for event_type in state_checked_events:
        # Wrap all handlers for these event types
        # with state checking wrapper
```

## Benefits

### 1. Clearer Logs

**Before (confusing):**
```
12:51:12,226 - ERROR - ❌ Workflow failed: portfolio_analysis
12:51:12,227 - INFO - ✅ Signal generation completed successfully
```

**After (clear):**
```
12:51:12,226 - ERROR - ❌ Workflow failed: portfolio_analysis
12:51:12,226 - INFO - 🚫 Workflow 2e740e82-851a marked as FAILED - future events will be skipped
12:51:12,227 - INFO - 🚫 Skipping SignalGenerationHandler - workflow 2e740e82-851a already failed
```

### 2. Resource Efficiency

- Stop wasted processing immediately after critical failures
- Reduce unnecessary API calls when workflow already failed
- Faster failure propagation

### 3. Trading System Safety

- Immediate halt on critical failures (negative cash balance, API errors)
- Clear audit trail of what stopped when
- Prevent downstream operations that shouldn't execute

### 4. Better Debugging

- Obvious workflow state in logs
- No misleading "success" messages after failures
- Easier to trace failure propagation

## Implementation Architecture

### Thread Safety

All state checking operations are protected by a lock for concurrent access:

```python
with self.workflow_states_lock:
    return self.workflow_states.get(correlation_id) == WorkflowState.FAILED
```

### No Handler Modifications Required

The solution uses a **wrapper pattern** that doesn't require modifications to existing handlers:
- Handlers remain pure and focused on domain logic
- State checking is transparently added by the orchestrator
- Clean separation of concerns

### Independent Workflow States

Multiple workflows can run concurrently with independent states:
- Each workflow tracked by unique correlation_id
- Failure in one workflow doesn't affect others
- Thread-safe concurrent access

## Testing

### Unit Tests (`test_workflow_state_management.py`)

- ✅ Workflow state transitions (RUNNING → FAILED, RUNNING → COMPLETED)
- ✅ StateCheckingHandlerWrapper skips events for failed workflows
- ✅ StateCheckingHandlerWrapper allows events for active workflows
- ✅ Thread safety of state checking operations
- ✅ Multiple independent workflows maintain separate states

### Integration Tests (`test_workflow_failure_propagation.py`)

- ✅ Negative cash balance scenario prevents all downstream processing
- ✅ Multiple concurrent workflows maintain independent states
- ✅ Workflow can fail at any stage (signal, portfolio, execution)
- ✅ End-to-end failure propagation flow

### Demonstration Script (`scripts/demo_workflow_state_management.py`)

Interactive demonstration showing:
- How workflows transition through states
- How handlers are skipped after failure
- Before/after log message comparison
- Benefits of the feature

## Files Modified

### Core Implementation
- `the_alchemiser/orchestration/event_driven_orchestrator.py`
  - Added `WorkflowState` enum
  - Added `StateCheckingHandlerWrapper` class
  - Added state management methods
  - Updated workflow event handlers
  - Added handler wrapping functionality

### Documentation
- `the_alchemiser/orchestration/README.md`
  - Added detailed workflow state management section
  - Documented state transitions
  - Explained failure prevention mechanism
  - Provided examples and benefits

### Public API
- `the_alchemiser/orchestration/__init__.py`
  - Exported `WorkflowState` enum

### Tests
- `tests/orchestration/test_workflow_state_management.py` (NEW)
  - Comprehensive unit tests for state management

- `tests/orchestration/test_workflow_failure_propagation.py` (NEW)
  - Integration tests for failure propagation

### Demonstration
- `scripts/demo_workflow_state_management.py` (NEW)
  - Interactive demonstration script

## Backward Compatibility

✅ All existing functionality continues to work
✅ No breaking changes to event schemas
✅ Handlers remain unchanged (wrapping is transparent)
✅ Existing tests continue to pass

## Usage Example

```python
from the_alchemiser.orchestration import EventDrivenOrchestrator, WorkflowState

# Create orchestrator
orchestrator = EventDrivenOrchestrator(container)

# Check workflow state
if orchestrator.is_workflow_failed(correlation_id):
    print("Workflow has failed - skipping processing")
elif orchestrator.is_workflow_active(correlation_id):
    print("Workflow is running - continue processing")

# Get current state
state = orchestrator.workflow_states.get(correlation_id)
print(f"Workflow state: {state.value if state else 'unknown'}")
```

## Future Enhancements

Potential improvements for future iterations:

1. **State Cleanup**: Implement automatic cleanup of old workflow states
   ```python
   def cleanup_workflow_state(self, correlation_id: str, delay_minutes: int = 60):
       """Clean up workflow state after delay to prevent memory leaks"""
   ```

2. **State Persistence**: Persist workflow states for recovery after restarts

3. **State Metrics**: Track and expose metrics about workflow states
   - Number of failed vs successful workflows
   - Average workflow duration by state
   - Most common failure reasons

4. **State Callbacks**: Allow registration of callbacks for state transitions
   ```python
   orchestrator.on_workflow_failed(callback_function)
   ```

## Conclusion

This implementation successfully solves the race condition problem where handlers continued processing events after workflow failures. The solution:

- ✅ Prevents misleading log messages
- ✅ Stops wasted processing immediately
- ✅ Provides clear audit trail
- ✅ Maintains clean architecture
- ✅ Requires no handler modifications
- ✅ Is fully tested and documented
- ✅ Is backward compatible

The handler wrapper pattern ensures clean separation of concerns while providing the necessary failure prevention mechanism.
