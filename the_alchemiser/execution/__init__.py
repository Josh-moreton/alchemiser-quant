"""Business Unit: execution | Status: current.

Broker API integrations and order placement.

This module contains order routing, broker connectors, execution strategies,
and order lifecycle management.

DESIGN INTENT: Thin wrapper around alpaca-py with institutional-grade business logic
for limit order placement, re-pegging, and WebSocket monitoring.

RECOMMENDED USAGE:
- AlpacaManager: Primary broker integration (now re-exported from shared.brokers)
- RefactoredTradingServiceManager: Simplified service manager (when available)
- SmartExecution: Execution strategies with re-pegging logic

ARCHITECTURE NOTES:
- 64 Python files across 17 directories (simplified from original 67 files, 20+ directories)
- RefactoredTradingServiceManager: Main service manager (recommended)
- AlpacaManager: Primary broker integration (moved to shared.brokers for architectural compliance)
- Focus on thin-wrapper design around alpaca-py APIs

NOTE: AlpacaManager has been moved to shared.brokers to resolve architectural boundary
violations. It is re-exported here for backward compatibility.
"""

from __future__ import annotations

# DEPRECATED: Import AlpacaManager from the_alchemiser.shared.brokers instead
# Re-exports have been removed to resolve circular import issues
# Expose preferred service managers
from .core import RefactoredTradingServiceManager

__all__ = [
    "RefactoredTradingServiceManager",
]
