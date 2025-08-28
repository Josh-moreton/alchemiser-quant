"""Business Unit: utilities; Status: current.

Domain layer root package.

This package contains pure domain models, value objects, entities, and
protocols. Keep this layer free from framework and infrastructure dependencies.
"""

from __future__ import annotations

# Domain Layer notes
# - Interfaces define contracts that infrastructure adapters implement
# - Models represent core business entities and value objects
# - Business rules and validation logic live here
#
# Current modules:
# - interfaces: Protocol definitions for repositories and services
from .interfaces import (
    AccountRepository,
    MarketDataRepository,
    TradingRepository,
)

__all__ = [
    "AccountRepository",
    "MarketDataRepository",
    "TradingRepository",
]
