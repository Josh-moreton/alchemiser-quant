#!/usr/bin/env python3
"""Business Unit: strategy | Status: current.

Strategy execution context.

Immutable dataclass holding inputs for strategy engine execution.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from errors import ConfigurationError


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

    params: dict[str, str | int | float | bool] | None = None
    """Optional strategy-specific parameters (configuration metadata)"""

    def __post_init__(self) -> None:
        """Validate context after initialization.

        Raises:
            ConfigurationError: If validation fails (empty symbols/timeframe, duplicate symbols).

        """
        if not self.symbols:
            raise ConfigurationError(
                "symbols cannot be empty",
                field="symbols",
                value=str(self.symbols),
            )

        if not self.timeframe:
            raise ConfigurationError(
                "timeframe cannot be empty",
                field="timeframe",
                value=self.timeframe,
            )

        # Convert symbols to uppercase and check uniqueness
        upper_symbols = [symbol.upper() for symbol in self.symbols]
        if len(set(upper_symbols)) != len(upper_symbols):
            raise ConfigurationError(
                "symbols must be unique (case-insensitive)",
                field="symbols",
                value=str(self.symbols),
            )

        # Replace symbols with uppercase versions, preserving order
        object.__setattr__(self, "symbols", upper_symbols)
