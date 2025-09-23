"""Business Unit: orchestration | Status: current.

Cross-module orchestration components.

This module provides orchestration logic that coordinates between business units
(strategy, portfolio, execution) without belonging to any specific one. The orchestration
layer acts as the "conductor" for complex workflows that span multiple modules.

Now includes event-driven orchestration alongside traditional direct-call orchestrators
for a modern, decoupled, and extensible architecture.

Also includes CLI components that orchestrate user interactions and coordinate
cross-module workflows through command-line interfaces.

Exports:
    - SignalOrchestrator: Signal analysis workflow orchestration
    - TradingOrchestrator: Trading execution workflow orchestration
    - PortfolioOrchestrator: Portfolio rebalancing workflow orchestration
    - EventDrivenOrchestrator: Event-driven workflow orchestration (NEW)
"""

# Lazy imports to avoid circular dependencies and missing dependencies during CLI operations
__all__ = [
    "EventDrivenOrchestrator",
    "PortfolioOrchestrator",
    "SignalOrchestrator",
    "TradingOrchestrator",
]


def __getattr__(name: str) -> object:
    """Lazy import for orchestration components."""
    if name == "EventDrivenOrchestrator":
        from .event_driven_orchestrator import EventDrivenOrchestrator

        return EventDrivenOrchestrator
    if name == "PortfolioOrchestrator":
        from .portfolio_orchestrator import PortfolioOrchestrator

        return PortfolioOrchestrator
    if name == "SignalOrchestrator":
        from .signal_orchestrator import SignalOrchestrator

        return SignalOrchestrator
    if name == "TradingOrchestrator":
        from .trading_orchestrator import TradingOrchestrator

        return TradingOrchestrator
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
