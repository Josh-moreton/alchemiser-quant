#!/usr/bin/env python3
"""Business Unit: strategy | Status: current

Strategy execution context.

Immutable dataclass holding inputs for strategy engine execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


@dataclass(frozen=True)
class StrategyContext:
    """Immutable context for strategy execution.
    
    Contains all necessary inputs for running a strategy engine
    without side effects or mutable state.
    """
    
    symbols: list[str]
    """List of symbols to analyze"""
    
    timeframe: str
    """Timeframe for data (e.g., '1D', '1H', '15Min')"""
    
    as_of: datetime | None = None
    """Optional timestamp for strategy calculation (defaults to current time)"""
    
    params: dict[str, Any] | None = None
    """Optional strategy-specific parameters"""
    
    def __post_init__(self) -> None:
        """Validate context after initialization."""
        if not self.symbols:
            raise ValueError("symbols cannot be empty")
        
        if not self.timeframe:
            raise ValueError("timeframe cannot be empty")
        
        # Ensure symbols are unique and uppercase
        symbols_set = set(symbol.upper() for symbol in self.symbols)
        if len(symbols_set) != len(self.symbols):
            raise ValueError("symbols must be unique")
        
        # Replace symbols with uppercase versions
        object.__setattr__(self, 'symbols', list(symbols_set))