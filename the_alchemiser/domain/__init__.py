"""
Domain Layer

The domain layer contains the core business logic, interfaces, and models
that define the contracts for our trading system.

This layer is independent of external concerns like databases, APIs, or UI,
and represents the heart of our business logic.

Following our eventual architecture vision:
- Interfaces define contracts that infrastructure adapters implement
- Models represent core business entities and value objects
- Business rules and validation logic live here

Current modules:
- interfaces: Protocol definitions for repositories and services
"""

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
