"""Business Unit: orchestration | Status: current.

Cross-module orchestration components.

This module provides orchestration logic that coordinates between business units
(strategy, portfolio, execution) without belonging to any specific one. The orchestration
layer acts as the "conductor" for complex workflows that span multiple modules.

Uses pure event-driven orchestration for modern, decoupled, and extensible architecture.
Traditional direct-call orchestrators have been removed in favor of event-driven patterns.

Also includes CLI components that orchestrate user interactions and coordinate
cross-module workflows through command-line interfaces.

Exports:
    - EventDrivenOrchestrator: Event-driven workflow orchestration
    - WorkflowState: Workflow execution state enum (RUNNING, FAILED, COMPLETED)
"""

# Lazy imports to avoid circular dependencies and missing dependencies during CLI operations
__all__ = [
    "EventDrivenOrchestrator",
    "WorkflowState",
]


def __getattr__(name: str) -> object:
    """Lazy import for orchestration components."""
    if name == "EventDrivenOrchestrator":
        from .event_driven_orchestrator import EventDrivenOrchestrator

        return EventDrivenOrchestrator
    if name == "WorkflowState":
        from .workflow_state import WorkflowState

        return WorkflowState
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
