#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Strategy_v2 module for signal generation and indicator calculation.

This module provides a clean, boundary-enforcing strategy system that:
- Consumes market data via shared Alpaca capabilities
- Outputs pure strategy signal DTOs (StrategyAllocation)
- Maintains strict separation from portfolio and execution concerns
- Communicates via events in the event-driven architecture

Architecture:
- Strategy Worker Lambda (lambda_handler.py) processes single DSL files
- Each worker evaluates DSL, calculates its own rebalance plan,
    and enqueues trades independently (per-strategy books)
- No aggregation step -- each strategy operates as an independent book

Note:
- Legacy registration helpers and deprecated handler aliases have been
    removed from public documentation; register handlers via the
    application's dependency injection container.

"""

from __future__ import annotations


def __getattr__(name: str) -> object:
    if name == "SingleStrategyOrchestrator":
        from core.orchestrator import (
            SingleStrategyOrchestrator as _SingleStrategyOrchestrator,
        )

        return _SingleStrategyOrchestrator
    if name in {"get_strategy", "list_strategies", "register_strategy"}:
        from core import registry as _registry

        return getattr(_registry, name)
    if name == "StrategyContext":
        from models.context import StrategyContext as _StrategyContext

        return _StrategyContext

    # Provide helpful error message with available attributes
    available = ", ".join(sorted(__all__))
    raise AttributeError(
        f"module {__name__!r} has no attribute {name!r}. Available attributes: {available}"
    )


# Public API exports (transitioning to event-driven only)
__all__ = [
    "SingleStrategyOrchestrator",
    "StrategyContext",
    "get_strategy",
    "list_strategies",
    "register_strategy",
]

# Version for compatibility tracking
__version__ = "2.0.0"
