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
    - MultiStrategyOrchestrator: Multi-strategy coordination
    - PortfolioOrchestrator: Portfolio rebalancing workflow orchestration
    - EventDrivenOrchestrator: Event-driven workflow orchestration (NEW)
"""

from .event_driven_orchestrator import EventDrivenOrchestrator
from .portfolio_orchestrator import PortfolioOrchestrator
from .signal_orchestrator import SignalOrchestrator
from .strategy_orchestrator import MultiStrategyOrchestrator
from .trading_orchestrator import TradingOrchestrator

__all__ = [
    "EventDrivenOrchestrator",
    "MultiStrategyOrchestrator",
    "PortfolioOrchestrator",
    "SignalOrchestrator",
    "TradingOrchestrator",
]
