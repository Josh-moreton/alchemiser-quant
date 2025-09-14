"""Business Unit: orchestration | Status: current.

Cross-module orchestration components.

This module provides orchestration logic that coordinates between business units
(strategy, portfolio, execution) without belonging to any specific one. The orchestration
layer acts as the "conductor" for complex workflows that span multiple modules.

Now includes event-driven orchestration alongside traditional direct-call orchestrators
for a modern, decoupled, and extensible architecture.

The module is in migration from hybrid (event-driven + direct-call) patterns to
fully event-driven orchestration as documented in EVENT_DRIVEN_MIGRATION_PLAN.md.

Exports:
    - SignalOrchestrator: Signal analysis workflow orchestration
    - TradingOrchestrator: Trading execution workflow orchestration (MIGRATING)
    - StrategyOrchestrator: Multi-strategy coordination
    - PortfolioOrchestrator: Portfolio rebalancing workflow orchestration (MIGRATING)
    - EventDrivenOrchestrator: Event-driven workflow orchestration
    - PortfolioEventHandler: Event-driven portfolio analysis workflows (NEW)
    - TradingWorkflowHandler: Event-driven trading workflow coordination (NEW)
"""

from .event_driven_orchestrator import EventDrivenOrchestrator
from .portfolio_event_handler import PortfolioEventHandler
from .portfolio_orchestrator import PortfolioOrchestrator
from .signal_orchestrator import SignalOrchestrator
from .strategy_orchestrator import StrategyOrchestrator
from .trading_orchestrator import TradingOrchestrator
from .trading_workflow_handler import TradingWorkflowHandler

__all__ = [
    "EventDrivenOrchestrator",
    "PortfolioEventHandler",
    "PortfolioOrchestrator",
    "SignalOrchestrator",
    "StrategyOrchestrator",
    "TradingOrchestrator",
    "TradingWorkflowHandler",
]
