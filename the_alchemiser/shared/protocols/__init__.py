"""Business Unit: shared | Status: current.

Protocol definitions for type-safe interfaces.

This module exports protocols that define minimal interfaces for type-safe
interactions without tight coupling to concrete implementations.
"""

from __future__ import annotations

from the_alchemiser.shared.protocols.orchestrator import TradingModeProvider

__all__ = [
    "TradingModeProvider",
]
