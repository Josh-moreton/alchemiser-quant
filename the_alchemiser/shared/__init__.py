"""Business Unit: shared | Status: current.

DTOs, utilities, and cross-cutting concerns.

This module provides shared functionality used across the trading system:
- schemas: Data transfer objects and event schemas
- types: Common value objects (Money, Quantity, Percentage, etc.)
- utils: Utility functions and error handling
- config: Configuration management
- brokers: Broker integrations (AlpacaManager)
- events: Event-driven architecture components
- logging: Structured logging infrastructure
- protocols: Protocol definitions for dependency inversion
- value_objects: Core value objects and types
- math: Mathematical utilities
- errors: Error handling and exceptions
- services: Service layer components

Import from submodules directly:
    from the_alchemiser.shared.schemas import StrategySignal
    from the_alchemiser.shared.config import Settings
    from the_alchemiser.shared.brokers import AlpacaManager
"""

from __future__ import annotations

__all__: list[str] = []
