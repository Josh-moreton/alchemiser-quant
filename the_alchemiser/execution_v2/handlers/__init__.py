#!/usr/bin/env python3
"""Business Unit: execution | Status: current.

Event handlers for trade execution.

Provides the SingleTradeHandler for processing individual TradeMessage
events from the SQS FIFO queue in the per-trade execution architecture.
"""

from __future__ import annotations

from .single_trade_handler import SingleTradeHandler

__all__ = [
    "SingleTradeHandler",
]
