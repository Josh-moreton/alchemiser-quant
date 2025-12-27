#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Core strategy orchestration and registry components.

Provides the main orchestration logic for running strategies and
mapping strategy names to their implementations.

Note: Factory functions (create_orchestrator, create_orchestrator_with_adapter)
are lazily imported because they depend on alpaca-py, which is not available
in the Strategy Lambda runtime (uses cached S3 data instead).
"""

from __future__ import annotations

# Eagerly import these - they don't depend on alpaca-py
from .orchestrator import SingleStrategyOrchestrator
from .registry import get_strategy, list_strategies, register_strategy

__all__ = [
    "SingleStrategyOrchestrator",
    "create_orchestrator",
    "create_orchestrator_with_adapter",
    "get_strategy",
    "list_strategies",
    "register_strategy",
]


def __getattr__(name: str) -> object:
    """Lazy import for factory functions that depend on alpaca-py."""
    if name == "create_orchestrator":
        from .factory import create_orchestrator

        return create_orchestrator
    if name == "create_orchestrator_with_adapter":
        from .factory import create_orchestrator_with_adapter

        return create_orchestrator_with_adapter
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
