#!/usr/bin/env python3
"""Business Unit: execution | Status: current.

Event handlers for trade execution.

Provides event-driven handlers for processing execution-related events
in the event-driven architecture.
"""

from __future__ import annotations

from .trading_execution_handler import TradingExecutionHandler

__all__ = [
    "TradingExecutionHandler",
]
