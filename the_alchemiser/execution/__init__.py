"""Business Unit: execution | Status: current.

Broker API integrations and order placement.

This module contains order routing, broker connectors, execution strategies,
and order lifecycle management.

DESIGN INTENT: Thin wrapper around alpaca-py with institutional-grade business logic
for limit order placement, re-pegging, and WebSocket monitoring.

RECOMMENDED USAGE:
- AlpacaManager: Primary broker integration (now re-exported from shared.brokers)
- TradingServicesFacade: Broker/account/position operations facade
- ExecutionManager: Multi-strategy execution orchestration
- SmartExecution: Execution strategies with re-pegging logic

ARCHITECTURE NOTES:
- TradingServicesFacade: Broker operations facade (recommended for account/order/position ops)
- ExecutionManager: Multi-strategy orchestration (recommended for strategy coordination)
- AlpacaManager: Primary broker integration (moved to shared.brokers for architectural compliance)
- Focus on thin-wrapper design around alpaca-py APIs

EXECUTION FLOW:
- For multi-strategy execution: TradingEngine → ExecutionManager → strategy coordination
- For broker operations: Services → TradingServicesFacade → broker APIs

NOTE: AlpacaManager has been moved to shared.brokers to resolve architectural boundary
violations. It is re-exported here for backward compatibility.
"""

from __future__ import annotations

# DEPRECATED: Import AlpacaManager from the_alchemiser.shared.brokers instead
# Re-exports have been removed to resolve circular import issues
# Expose preferred service managers
from .core import TradingServicesFacade

__all__ = [
    "TradingServicesFacade",
]
