#!/usr/bin/env python3
"""Business Unit: order execution/placement; Status: current.

Progressive Order Execution Utilities.

This module provides intelligent order execution parameters based on market conditions:
- Volatility-aware timeout adjustments
- Spread-aware step sizing and timing
- Dynamic pricing strategies based on market microstructure
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any


@dataclass
class OrderExecutionParams:
    """Parameters for progressive order execution."""

    max_wait_seconds: int
    step_count: int
    step_percentages: list[float]  # Percentage of spread to step through
    tick_aggressiveness: float  # How aggressively to step (multiplier)

    def __str__(self) -> str:
        """Human readable representation used in logs."""
        return (
            f"OrderExecutionParams(wait={self.max_wait_seconds}s, "
            f"steps={self.step_count}, aggressiveness={self.tick_aggressiveness:.2f})"
        )


class ProgressiveOrderCalculator:
    """Calculate optimal order execution parameters based on market conditions.

    This class analyzes volatility, spreads, and urgency to determine:
    - How long to wait at each price level
    - How many steps to take through the spread
    - How aggressively to price orders
    """

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """Initialize with configuration."""
        self.config = config or {}

        # Base configuration - can be overridden by config
        self.base_wait_seconds = self.config.get("base_wait_seconds", 20)
        self.min_wait_seconds = self.config.get("min_wait_seconds", 5)
        self.max_wait_seconds = self.config.get("max_wait_seconds", 60)
        self.base_step_count = self.config.get("base_step_count", 3)

        # Volatility thresholds (as percentage of price)
        self.low_volatility_threshold = 0.005  # 0.5%
        self.high_volatility_threshold = 0.02  # 2.0%

        # Spread thresholds (in basis points)
        self.tight_spread_bps = 10  # 0.1%
        self.wide_spread_bps = 100  # 1.0%

    def calculate_volatility_metric(
        self,
        symbol: str,
        current_price: float,
        recent_high: float | None = None,
        recent_low: float | None = None,
    ) -> float:
        """Calculate a simple volatility metric.

        Args:
            symbol: Stock symbol
            current_price: Current price
            recent_high: Recent high price (optional)
            recent_low: Recent low price (optional)

        Returns:
            Volatility as percentage of current price (0.0 to 1.0+)

        """
        if recent_high is None or recent_low is None:
            # Default to medium volatility if we don't have range data
            return 0.01  # 1%

        if current_price <= 0:
            return 0.01

        # Calculate range as percentage of current price
        price_range = recent_high - recent_low
        volatility = price_range / current_price

        return max(0.001, volatility)  # Minimum 0.1% volatility

    def calculate_spread_metric(self, bid: float, ask: float) -> tuple[float, float]:
        """Calculate spread metrics.

        Args:
            bid: Bid price
            ask: Ask price

        Returns:
            Tuple of (spread_bps, spread_pct) where:
            - spread_bps: Spread in basis points
            - spread_pct: Spread as percentage of midpoint

        """
        if bid <= 0 or ask <= 0 or ask <= bid:
            return 50.0, 0.005  # Default to 50bps, 0.5%

        midpoint = (bid + ask) / 2.0
        spread = ask - bid
        spread_pct = spread / midpoint
        spread_bps = spread_pct * 10000  # Convert to basis points

        return spread_bps, spread_pct

    def calculate_execution_params(
        self,
        symbol: str,
        bid: float,
        ask: float,
        side: Any,  # BrokerOrderSide or compatible
        urgency_level: str = "normal",
        recent_high: float | None = None,
        recent_low: float | None = None,
    ) -> OrderExecutionParams:
        """Calculate optimal execution parameters based on market conditions.

        Args:
            symbol: Stock symbol
            bid: Current bid price
            ask: Current ask price
            side: Order side (BUY or SELL)
            urgency_level: "low", "normal", "high", or "urgent"
            recent_high: Recent high for volatility calculation
            recent_low: Recent low for volatility calculation

        Returns:
            OrderExecutionParams with optimized settings

        """
        current_price = (bid + ask) / 2.0

        # Calculate market condition metrics
        volatility = self.calculate_volatility_metric(
            symbol, current_price, recent_high, recent_low
        )
        spread_bps, spread_pct = self.calculate_spread_metric(bid, ask)

        logging.info(
            f"📊 Market conditions for {symbol}: volatility={volatility:.3f} ({volatility * 100:.1f}%), "
            f"spread={spread_bps:.1f}bps ({spread_pct * 100:.2f}%)"
        )

        # Determine urgency multiplier
        urgency_multipliers = {
            "low": 1.5,  # More patient
            "normal": 1.0,  # Base case
            "high": 0.7,  # More aggressive
            "urgent": 0.4,  # Very aggressive
        }
        urgency_mult = urgency_multipliers.get(urgency_level, 1.0)

        # Calculate wait time based on conditions
        wait_time = self.base_wait_seconds

        # Volatility adjustments
        if volatility < self.low_volatility_threshold:
            # Low volatility = stable prices = can wait longer
            wait_time = int(wait_time * 1.3)
        elif volatility > self.high_volatility_threshold:
            # High volatility = prices moving fast = need to be quicker
            wait_time = int(wait_time * 0.7)

        # Spread adjustments
        if spread_bps < self.tight_spread_bps:
            # Tight spread = competitive market = need to be faster
            wait_time = int(wait_time * 0.8)
        elif spread_bps > self.wide_spread_bps:
            # Wide spread = less competitive = can be more patient
            wait_time = int(wait_time * 1.4)

        # Apply urgency
        wait_time = int(wait_time * urgency_mult)

        # Enforce bounds
        wait_time = max(self.min_wait_seconds, min(self.max_wait_seconds, wait_time))

        # Calculate step count and aggressiveness
        step_count = self.base_step_count

        # More steps for wider spreads (more room to work)
        if spread_bps > self.wide_spread_bps:
            step_count = min(5, step_count + 1)
        elif spread_bps < self.tight_spread_bps:
            step_count = max(2, step_count - 1)

        # Calculate step percentages (how much of spread to traverse at each step)
        if step_count == 2:
            step_percentages = [0.0, 1.0]  # Midpoint, then full spread
        elif step_count == 3:
            step_percentages = [0.0, 0.5, 1.0]  # Midpoint, halfway, full spread
        elif step_count == 4:
            step_percentages = [0.0, 0.3, 0.7, 1.0]
        else:  # 5 steps
            step_percentages = [0.0, 0.2, 0.5, 0.8, 1.0]

        # Calculate tick aggressiveness
        tick_aggressiveness = 1.0

        if urgency_level in ["high", "urgent"]:
            # More aggressive pricing when urgent
            tick_aggressiveness = 1.5 if urgency_level == "high" else 2.0
        elif urgency_level == "low":
            # More passive when not urgent
            tick_aggressiveness = 0.7

        # Adjust for volatility
        if volatility > self.high_volatility_threshold:
            # In volatile markets, be more aggressive to ensure fills
            tick_aggressiveness *= 1.3

        params = OrderExecutionParams(
            max_wait_seconds=wait_time,
            step_count=step_count,
            step_percentages=step_percentages,
            tick_aggressiveness=tick_aggressiveness,
        )

        logging.info(f"🎯 Execution params for {symbol}: {params}")

        return params

    def calculate_step_price(
        self,
        bid: float,
        ask: float,
        side: Any,  # BrokerOrderSide or compatible
        step_percentage: float,
        tick_aggressiveness: float = 1.0,
    ) -> float:
        """Calculate the limit price for a specific step.

        Args:
            bid: Current bid price
            ask: Current ask price
            side: Order side
            step_percentage: Percentage through spread (0.0 = midpoint, 1.0 = bid/ask)
            tick_aggressiveness: Multiplier for how aggressive to be

        Returns:
            Calculated limit price

        """
        midpoint = (bid + ask) / 2.0
        spread = ask - bid

        # Handle side comparison - support both BrokerOrderSide and alpaca OrderSide
        is_buy_side = False
        if hasattr(side, "value"):  # BrokerOrderSide enum
            is_buy_side = side.value == "buy" or str(side).endswith("BUY")
        else:  # Alpaca OrderSide or string
            is_buy_side = str(side).endswith("BUY") or str(side).lower() == "buy"

        if is_buy_side:
            # For BUY: 0% = midpoint, 100% = ask (less favorable)
            base_price = midpoint + (spread / 2 * step_percentage)
            # Add aggressiveness (move further toward ask)
            if step_percentage > 0:  # Don't adjust midpoint
                additional_premium = spread * 0.1 * (tick_aggressiveness - 1.0)
                base_price += additional_premium
        else:
            # For SELL: 0% = midpoint, 100% = bid (less favorable)
            base_price = midpoint - (spread / 2 * step_percentage)
            # Add aggressiveness (move further toward bid)
            if step_percentage > 0:  # Don't adjust midpoint
                additional_discount = spread * 0.1 * (tick_aggressiveness - 1.0)
                base_price -= additional_discount

        # Round to nearest cent
        return round(base_price, 2)

    def get_execution_strategy_description(
        self, params: OrderExecutionParams, symbol: str, side: OrderSide
    ) -> str:
        """Generate a human-readable description of the execution strategy.

        Args:
            params: Execution parameters
            symbol: Stock symbol
            side: Order side

        Returns:
            Description string

        """
        strategy_desc = f"{side.value} {symbol} with {params.step_count} steps, "
        strategy_desc += f"{params.max_wait_seconds}s wait per step"

        if params.tick_aggressiveness > 1.2:
            strategy_desc += " (aggressive pricing)"
        elif params.tick_aggressiveness < 0.8:
            strategy_desc += " (passive pricing)"

        return strategy_desc


def get_market_urgency_level(hour: int | None = None) -> str:
    """Determine market urgency based on time of day.

    Args:
        hour: Hour of day (0-23), if None uses current time

    Returns:
        Urgency level: "low", "normal", "high", or "urgent"

    """
    if hour is None:
        from datetime import UTC, datetime

        hour = datetime.now(UTC).hour

    # Market hours are roughly 9:30 AM - 4:00 PM ET (14:30 - 21:00 UTC)
    # Adjust based on your timezone

    if hour < 10 or hour > 15:
        # Pre-market or after-hours = low urgency
        return "low"
    if hour in [9, 10, 15, 16]:
        # Market open/close = high urgency
        return "high"
    # Regular trading hours = normal urgency
    return "normal"
