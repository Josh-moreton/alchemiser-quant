#!/usr/bin/env python3
"""
Repeg Strategy

Stateless strategy for planning and executing re-pegging attempts with
adaptive pricing and timeout logic.
"""

from dataclasses import dataclass
from typing import NamedTuple

from alpaca.trading.enums import OrderSide

from .config import StrategyConfig


class AttemptResult(NamedTuple):
    """Result of a single attempt calculation."""
    price: float
    timeout_seconds: float
    reason: str
    attempt_index: int


@dataclass(frozen=True)
class AttemptState:
    """Current state for an attempt sequence."""
    bid: float
    ask: float
    original_spread_cents: float
    last_attempt_time: float
    side: OrderSide


class RepegStrategy:
    """Stateless strategy for adaptive re-pegging logic.

    This strategy handles the pricing and timing logic for re-pegging
    attempts while maintaining no internal state. All state is passed
    explicitly through method parameters.
    """

    def __init__(self, config: StrategyConfig, strategy_name: str = "RepegStrategy") -> None:
        """Initialize repeg strategy with configuration.

        Args:
            config: Strategy configuration parameters
            strategy_name: Name for logging identification
        """
        self.config = config
        self.strategy_name = strategy_name

    def plan_attempts(self) -> list[dict[str, int | float | str]]:
        """Plan all attempts for a repeg sequence.

        Returns:
            List of attempt plans with timeout and pricing parameters
        """
        attempts: list[dict[str, int | float | str]] = []

        for attempt_index in range(self.config.max_attempts):
            timeout = self._calculate_timeout(attempt_index)

            attempts.append({
                "attempt_index": attempt_index,
                "timeout_seconds": timeout,
                "price_improvement_ticks": attempt_index * self.config.price_improvement_ticks,
                "reason": "initial" if attempt_index == 0 else f"repeg_{attempt_index}",
            })

        return attempts

    def next_attempt(self, previous_state: AttemptState, attempt_index: int) -> AttemptResult:
        """Calculate next attempt parameters.

        Args:
            previous_state: Current market and attempt state
            attempt_index: Zero-based attempt index

        Returns:
            AttemptResult with price, timeout, reason, and attempt_index
        """
        # Calculate adaptive timeout
        timeout = self._calculate_timeout(attempt_index)

        # Calculate adaptive pricing
        price = self._calculate_price(previous_state, attempt_index)

        # Generate reason
        if attempt_index == 0:
            reason = "initial_aggressive_limit"
        else:
            reason = f"repeg_attempt_{attempt_index}"

        return AttemptResult(
            price=price,
            timeout_seconds=timeout,
            reason=reason,
            attempt_index=attempt_index,
        )

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
        if not self.config.enable_volatility_pause or original_spread_cents <= 0:
            return False

        # Calculate spread degradation in basis points
        spread_degradation_pct = (
            current_spread_cents - original_spread_cents
        ) / original_spread_cents
        spread_degradation_bps = spread_degradation_pct * 10000  # Convert to basis points

        return spread_degradation_bps > self.config.volatility_pause_threshold_bps

    def _calculate_timeout(self, attempt_index: int) -> float:
        """Calculate adaptive timeout for attempt.

        Args:
            attempt_index: Zero-based attempt index

        Returns:
            Timeout in seconds with exponential backoff
        """
        return self.config.base_timeout_seconds * (self.config.timeout_multiplier ** attempt_index)

    def _calculate_price(self, state: AttemptState, attempt_index: int) -> float:
        """Calculate adaptive limit price for attempt.

        Args:
            state: Current market state
            attempt_index: Zero-based attempt index

        Returns:
            Calculated limit price
        """
        if not self.config.enable_adaptive_pricing:
            # Use original aggressive pricing
            if state.side == OrderSide.BUY:
                return state.ask + self.config.tick_size
            else:
                return state.bid - self.config.tick_size

        # Calculate price improvement based on attempt number
        price_improvement = self.config.price_improvement_ticks * self.config.tick_size * attempt_index

        if state.side == OrderSide.BUY:
            # Buy orders: start at ask + 1 tick, improve (increase) each attempt
            return state.ask + self.config.tick_size + price_improvement
        else:
            # Sell orders: start at bid - 1 tick, improve (decrease) each attempt
            return state.bid - self.config.tick_size - price_improvement
