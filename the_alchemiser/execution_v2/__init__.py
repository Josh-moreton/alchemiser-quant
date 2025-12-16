#!/usr/bin/env python3
"""Business Unit: execution | Status: current.

Execution module for trade execution via Alpaca.

This module provides a clean, minimal execution system that:
- Consumes TradeMessage DTOs from SQS FIFO queue
- Delegates order placement to shared AlpacaManager
- Focuses solely on order execution
- Maintains clean module boundaries
- Communicates via events in the event-driven architecture

Architecture:
- Execution Lambda (lambda_handler.py) processes one trade at a time from SQS FIFO
- Execution handlers live under `execution_v2.handlers` and process trade
    messages to produce `TradeExecuted` events

Note:
- Legacy registration helpers and deprecated handler aliases have been
    removed from public documentation; register handlers via the
    application's dependency injection container.

"""

from __future__ import annotations


def __getattr__(name: str) -> object:
    """Lazy attribute access for legacy exports.

    Avoids importing heavy legacy modules at import time while preserving the
    public API during the migration period.
    """
    if name == "ExecutionManager":
        from .core.execution_manager import ExecutionManager as _ExecutionManager

        return _ExecutionManager
    if name == "ExecutionResult":
        from .models.execution_result import ExecutionResult as _ExecutionResult

        return _ExecutionResult
    if name == "TradeLedgerService":
        from .services.trade_ledger import TradeLedgerService as _TradeLedgerService

        return _TradeLedgerService
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "ExecutionManager",
    "ExecutionResult",
    "TradeLedgerService",
]

# Version for compatibility tracking
__version__ = "2.0.0"
