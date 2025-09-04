"""Business Unit: execution | Status: current.

Broker API integrations and order placement.

This module contains order routing, broker connectors, execution strategies,
and order lifecycle management.

DESIGN INTENT: Thin wrapper around alpaca-py with institutional-grade business logic
for limit order placement, re-pegging, and WebSocket monitoring.

RECOMMENDED USAGE:
- AlpacaManager: Primary broker integration (recommended for new code)
- RefactoredTradingServiceManager: Simplified service manager (when available)
- SmartExecution: Execution strategies with re-pegging logic

ARCHITECTURE NOTES:
- 64 Python files across 17 directories (simplified from original 67 files, 20+ directories)
- Core complexity concentrated in execution_manager.py (1185 lines) - use refactored version when possible
- Legacy alpaca_client.py (336 lines) marked for deprecation - migrate to AlpacaManager
- Focus on thin-wrapper design around alpaca-py APIs
"""

from __future__ import annotations

# Expose key broker adapters
from .brokers.alpaca import AlpacaManager, create_alpaca_manager

# Expose preferred service managers
from .core import RefactoredTradingServiceManager

__all__ = [
    "AlpacaManager",
    "RefactoredTradingServiceManager",
    "create_alpaca_manager",
]
