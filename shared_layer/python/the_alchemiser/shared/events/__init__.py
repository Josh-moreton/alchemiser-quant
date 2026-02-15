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
    AllocationComparisonCompleted,
    AllStrategiesCompleted,
    AllTradesCompleted,
    BulkSettlementCompleted,
    DataLakeUpdateCompleted,
    ErrorNotificationRequested,
    ExecutionPhaseCompleted,
    GroupBackfillCompleted,
    GroupBackfillRequested,
    GroupBackfillTarget,
    MarketDataFetchCompleted,
    MarketDataFetchRequested,
    OrderSettlementCompleted,
    PortfolioStateChanged,
    ScheduleCreated,
    StartupEvent,
    SystemNotificationRequested,
    TradeExecuted,
    TradeExecutionStarted,
    TradingNotificationRequested,
    WorkflowCompleted,
    WorkflowFailed,
    WorkflowStarted,
)

__all__ = [
    "AllStrategiesCompleted",
    "AllTradesCompleted",
    "AllocationComparisonCompleted",
    "BaseEvent",
    "BulkSettlementCompleted",
    "DataLakeUpdateCompleted",
    "ErrorNotificationRequested",
    "EventBus",
    "EventHandler",
    "ExecutionPhaseCompleted",
    "GroupBackfillCompleted",
    "GroupBackfillRequested",
    "GroupBackfillTarget",
    "MarketDataFetchCompleted",
    "MarketDataFetchRequested",
    "OrderSettlementCompleted",
    "PortfolioStateChanged",
    "ScheduleCreated",
    "StartupEvent",
    "SystemNotificationRequested",
    "TradeExecuted",
    "TradeExecutionStarted",
    "TradingNotificationRequested",
    "WorkflowCompleted",
    "WorkflowFailed",
    "WorkflowStarted",
]
