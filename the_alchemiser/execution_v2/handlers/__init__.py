#!/usr/bin/env python3
"""Business Unit: execution | Status: current.

Event handlers for trade execution.

Provides event-driven handlers for processing execution-related events
in the event-driven architecture.

Handlers:
    TradingExecutionHandler: Legacy batched execution handler (processes full RebalancePlan)
    SingleTradeHandler: Per-trade execution handler (processes individual TradeMessage from FIFO)
"""

from __future__ import annotations

from .single_trade_handler import SingleTradeHandler
from .trading_execution_handler import TradingExecutionHandler

__all__ = [
    "SingleTradeHandler",
    "TradingExecutionHandler",
]
