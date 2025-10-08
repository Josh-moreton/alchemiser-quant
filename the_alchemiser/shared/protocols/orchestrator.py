#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Orchestrator protocols for type-safe interfaces.

Provides protocol definitions for orchestrator-like objects to enable
proper typing without tight coupling to concrete implementations.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

__all__ = ["TradingModeProvider"]


@runtime_checkable
class TradingModeProvider(Protocol):
    """Protocol for objects that can provide trading mode information.

    This protocol defines the minimal interface needed for determining
    whether trading operations should run in live or paper mode.
    """

    live_trading: bool
    """Whether live trading is enabled (True) or paper trading (False)."""
