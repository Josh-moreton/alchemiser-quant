#!/usr/bin/env python3
"""Business Unit: execution; Status: current.

Strategy Configuration DTO.

Defines configuration parameters for execution strategies including
repeg attempts, timeouts, volatility thresholds, and pricing ticks.

Financial values (prices, ticks) use Decimal per project standards.
Temporal values (timeouts, intervals) remain float.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol


@dataclass(frozen=True)
class StrategyConfig:
    """Configuration for execution strategies.

    This DTO contains all the parameters needed for execution strategies
    to make pricing and timing decisions without coupling to the broader
    execution configuration.
    """

    # Basic execution parameters
    max_attempts: int = 3  # Maximum number of total attempts (initial + re-pegs)
    base_timeout_seconds: float = 2.5  # Base timeout for first attempt (time, not money)
    tick_size: Decimal = Decimal("0.01")  # Minimum price increment

    # Adaptive re-pegging parameters
    timeout_multiplier: float = 1.5  # Multiply timeout by this factor each re-peg
    price_improvement_ticks: int = 1  # Ticks to improve price each re-peg
    min_repeg_interval_seconds: float = 0.5  # Minimum time between re-pegs

    # Volatility control
    volatility_pause_threshold_bps: Decimal = Decimal("100")  # Basis points threshold
    enable_adaptive_pricing: bool = True  # Enable adaptive price improvement
    enable_volatility_pause: bool = True  # Enable volatility-based pause


class StrategyConfigProvider(Protocol):
    """Protocol for providing strategy configuration."""

    def get_strategy_config(self) -> StrategyConfig:
        """Get the current strategy configuration."""
        ...
