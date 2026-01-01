#!/usr/bin/env python3
"""Business Unit: execution | Status: current.

Execution module for trade execution via Alpaca.

This module provides a clean, minimal execution system that:
- Consumes TradeMessage DTOs from SQS Standard queue (parallel execution)
- Delegates order placement to shared AlpacaManager
- Focuses solely on order execution
- Maintains clean module boundaries
- Communicates via events in the event-driven architecture

Architecture (Two-Phase Parallel Execution):
- Portfolio Lambda enqueues SELL trades first (BUY trades stored in DynamoDB)
- Multiple Execution Lambdas (up to 10 concurrent) process SELLs in parallel
- When all SELLs complete, the last Lambda enqueues BUY trades
- BUY trades then execute in parallel via fresh Lambda invocations

Note: Despite env var name (EXECUTION_FIFO_QUEUE_URL), we use a Standard SQS queue
to enable parallel Lambda invocations. Two-phase ordering (sells before buys) is
controlled by enqueue timing, not FIFO queue guarantees.

Note:
- Legacy registration helpers and deprecated handler aliases have been
    removed from public documentation; register handlers via the
    application's dependency injection container.

"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .core.execution_manager import ExecutionManager as ExecutionManager
    from .models.execution_result import ExecutionResult as ExecutionResult
    from .services.trade_ledger import TradeLedgerService as TradeLedgerService


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
