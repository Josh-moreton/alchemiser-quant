#!/usr/bin/env python3
"""Business Unit: execution | Status: current.

Event handlers for trade execution.

Provides the SingleTradeHandler for processing individual TradeMessage
events from the SQS Standard queue. Multiple Lambdas process trades in
parallel (up to 10 concurrent via ReservedConcurrentExecutions).

Two-phase ordering (sells before buys) is achieved via enqueue timing:
1. Portfolio Lambda enqueues only SELL trades initially
2. When all SELLs complete, the last Lambda enqueues BUY trades
3. BUYs then execute in parallel
"""

from __future__ import annotations

from .single_trade_handler import SingleTradeHandler

__all__ = [
    "SingleTradeHandler",
]
