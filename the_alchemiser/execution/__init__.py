"""Business Unit: execution | Status: current.

Broker API integrations and order placement.

This module contains order routing, broker connectors, execution strategies,
and order lifecycle management.
"""

from __future__ import annotations

# Expose key broker adapters
from .brokers.alpaca import AlpacaManager, create_alpaca_manager

__all__ = [
    "AlpacaManager",
    "create_alpaca_manager",
]
