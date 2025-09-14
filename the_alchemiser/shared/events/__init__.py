#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Event-driven architecture components.

Provides event bus implementation and base event definitions for
inter-module communication in an event-driven architecture.

Exports:
    - EventBus: Central event distribution mechanism
    - BaseEvent: Base class for all events
    - EventHandler: Protocol for event handlers
"""

from __future__ import annotations

from .base import BaseEvent
from .bus import EventBus
from .handlers import EventHandler
from .schemas import (
    PortfolioAnalysisCompleted,
    PortfolioAnalysisRequested,
    RebalancePlanned,
    SignalGenerated,
    SignalGenerationRequested,
    StartupEvent,
    TradeExecuted,
    TradingWorkflowRequested,
)

__all__ = [
    "BaseEvent",
    "EventBus",
    "EventHandler",
    "PortfolioAnalysisCompleted",
    "PortfolioAnalysisRequested",
    "RebalancePlanned",
    "SignalGenerated",
    "SignalGenerationRequested",
    "StartupEvent",
    "TradeExecuted",
    "TradingWorkflowRequested",
]
