#!/usr/bin/env python3
"""Business Unit: order execution/placement; Status: current.

Execution Configuration.

Configuration settings for the professional execution system.
Loads settings from the global application configuration.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from the_alchemiser.shared.config.config import load_settings

if TYPE_CHECKING:  # pragma: no cover - hint for type checkers only
    from the_alchemiser.execution.config.execution_config import StrategyConfig


@dataclass
class ExecutionConfig:
    """Configuration for professional execution system."""

    # Risk management settings
    max_slippage_bps: float = 20.0
    aggressive_timeout_seconds: float = 2.5
    max_repegs: int = 2

    # Market timing settings
    enable_premarket_assessment: bool = True
    market_open_fast_execution: bool = True

    # Spread thresholds (in cents)
    tight_spread_threshold: float = 3.0
    wide_spread_threshold: float = 5.0

    # Symbol classification
    leveraged_etf_symbols: list[str] | None = None
    high_volume_etfs: list[str] | None = None

    # Adaptive re-pegging configuration (Phase 2 enhancement)
    enable_adaptive_repegging: bool = True
    repeg_timeout_multiplier: float = 1.5  # Multiply timeout by this factor each re-peg
    repeg_price_improvement_ticks: int = 1  # Ticks to improve price each re-peg
    min_repeg_interval_seconds: float = 0.5  # Minimum time between re-pegs
    volatility_pause_threshold_bps: float = 100.0  # Pause re-pegging if volatility spikes

    @classmethod
    def from_settings(cls) -> ExecutionConfig:
        """Load configuration from application settings."""
        try:
            execution = load_settings().execution
            return cls(
                max_slippage_bps=execution.max_slippage_bps,
                aggressive_timeout_seconds=execution.aggressive_timeout_seconds,
                max_repegs=execution.max_repegs,
                enable_premarket_assessment=execution.enable_premarket_assessment,
                market_open_fast_execution=execution.market_open_fast_execution,
                tight_spread_threshold=execution.tight_spread_threshold,
                wide_spread_threshold=execution.wide_spread_threshold,
                leveraged_etf_symbols=execution.leveraged_etf_symbols,
                high_volume_etfs=execution.high_volume_etfs,
                # Adaptive re-pegging settings with safe fallbacks
                enable_adaptive_repegging=getattr(execution, "enable_adaptive_repegging", True),
                repeg_timeout_multiplier=getattr(execution, "repeg_timeout_multiplier", 1.5),
                repeg_price_improvement_ticks=getattr(
                    execution, "repeg_price_improvement_ticks", 1
                ),
                min_repeg_interval_seconds=getattr(execution, "min_repeg_interval_seconds", 0.5),
                volatility_pause_threshold_bps=getattr(
                    execution, "volatility_pause_threshold_bps", 100.0
                ),
            )
        except Exception as e:
            logging.error(f"Error loading execution config: {e}")
            return cls()

    def get_slippage_tolerance(self, symbol: str) -> float:
        """Get slippage tolerance for a symbol.

        Args:
            symbol: The symbol to check

        Returns:
            float: Slippage tolerance in basis points

        """
        # Use standard slippage for all symbols
        return self.max_slippage_bps

    def is_leveraged_etf(self, symbol: str) -> bool:
        """Check if symbol is a leveraged ETF."""
        return bool(self.leveraged_etf_symbols and symbol in self.leveraged_etf_symbols)

    def is_high_volume_etf(self, symbol: str) -> bool:
        """Check if symbol is a high-volume ETF."""
        return bool(self.high_volume_etfs and symbol in self.high_volume_etfs)

    def get_adaptive_timeout(self, attempt: int, base_timeout: float) -> float:
        """Calculate adaptive timeout for re-pegging attempts.

        Args:
            attempt: Current attempt number (0-based)
            base_timeout: Base timeout in seconds

        Returns:
            Adjusted timeout with exponential backoff

        """
        if not self.enable_adaptive_repegging:
            return base_timeout

        # Apply exponential backoff: base_timeout * multiplier^attempt
        return base_timeout * (self.repeg_timeout_multiplier**attempt)

    def should_pause_for_volatility(
        self, original_spread_cents: float, current_spread_cents: float
    ) -> bool:
        """Check if re-pegging should be paused due to spread volatility.

        Args:
            original_spread_cents: Original spread in cents
            current_spread_cents: Current spread in cents

        Returns:
            True if volatility is too high to continue re-pegging

        """
        if not self.enable_adaptive_repegging or original_spread_cents <= 0:
            return False

        # Calculate spread degradation in basis points
        spread_degradation_pct = (
            current_spread_cents - original_spread_cents
        ) / original_spread_cents
        spread_degradation_bps = spread_degradation_pct * 10000  # Convert to basis points

        return spread_degradation_bps > self.volatility_pause_threshold_bps

    def calculate_adaptive_limit_price(
        self, side: str, bid: float, ask: float, attempt: int, tick_size: float = 0.01
    ) -> float:
        """Calculate adaptive limit price that improves with each re-peg attempt.

        Args:
            side: "buy" or "sell"
            bid: Current bid price
            ask: Current ask price
            attempt: Current attempt number (0-based)
            tick_size: Minimum price increment

        Returns:
            Adaptive limit price

        """
        if not self.enable_adaptive_repegging:
            # Use original aggressive pricing
            if side.lower() == "buy":
                return ask + tick_size
            return bid - tick_size

        # Calculate price improvement based on attempt number
        price_improvement = self.repeg_price_improvement_ticks * tick_size * attempt

        if side.lower() == "buy":
            # Buy orders: start at ask + 1 tick, improve (increase) each attempt
            return ask + tick_size + price_improvement
        # Sell orders: start at bid - 1 tick, improve (decrease) each attempt
        return bid - tick_size - price_improvement


# Global config instance
_config_instance: ExecutionConfig | None = None


def get_execution_config() -> ExecutionConfig:
    """Get the global execution configuration."""
    global _config_instance
    if _config_instance is None:
        _config_instance = ExecutionConfig.from_settings()
    return _config_instance


def reload_execution_config() -> None:
    """Reload the execution configuration from settings."""
    global _config_instance
    _config_instance = ExecutionConfig.from_settings()


def create_strategy_config() -> StrategyConfig:  # forward ref for static typing
    """Create a StrategyConfig from current ExecutionConfig."""
    from decimal import Decimal

    from the_alchemiser.execution.config.execution_config import StrategyConfig

    config = get_execution_config()
    return StrategyConfig(
        max_attempts=config.max_repegs + 1,
        base_timeout_seconds=config.aggressive_timeout_seconds,
        tick_size=Decimal("0.01"),
        timeout_multiplier=config.repeg_timeout_multiplier,
        price_improvement_ticks=config.repeg_price_improvement_ticks,
        min_repeg_interval_seconds=config.min_repeg_interval_seconds,
        volatility_pause_threshold_bps=Decimal(str(config.volatility_pause_threshold_bps)),
        enable_adaptive_pricing=config.enable_adaptive_repegging,
        enable_volatility_pause=config.enable_adaptive_repegging,
    )
