"""Business Unit: orchestration | Status: current.

Cross-module orchestration components.

This module provides orchestration logic that coordinates between business units
(strategy, portfolio, execution) without belonging to any specific one. The orchestration
layer acts as the "conductor" for complex workflows that span multiple modules.

Uses fully event-driven architecture for loose coupling and extensible workflows.

Exports:
    - SignalOrchestrator: Signal analysis workflow orchestration
    - TradingOrchestrator: Event-driven trading execution workflow orchestration
    - StrategyOrchestrator: Multi-strategy coordination
    - PortfolioOrchestrator: Portfolio rebalancing workflow orchestration
    - EventDrivenOrchestrator: Event-driven workflow orchestration
    - PortfolioEventHandler: Event-driven portfolio analysis handler
"""

from .event_driven_orchestrator import EventDrivenOrchestrator
from .portfolio_event_handler import PortfolioEventHandler
from .portfolio_orchestrator import PortfolioOrchestrator
from .signal_orchestrator import SignalOrchestrator
from .strategy_orchestrator import StrategyOrchestrator
from .trading_orchestrator import TradingOrchestrator

__all__ = [
    "EventDrivenOrchestrator",
    "PortfolioEventHandler",
    "PortfolioOrchestrator",
    "SignalOrchestrator",
    "StrategyOrchestrator",
    "TradingOrchestrator",
]
