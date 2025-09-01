#!/usr/bin/env python3
"""Business Unit: execution | Status: current.

Spread Assessment for Better Order Execution.

Implements pre-market and real-time spread analysis to optimize
order timing and pricing decisions.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any


class SpreadQuality(Enum):
    """Qualitative classification of bid/ask spreads."""

    TIGHT = "tight"  # ≤ 3¢
    NORMAL = "normal"  # 3-5¢
    WIDE = "wide"  # > 5¢


@dataclass
class PreMarketConditions:
    """Assessment of pre-market spread information."""

    spread_cents: float
    spread_quality: SpreadQuality
    recommended_wait_minutes: int
    max_slippage_bps: float


@dataclass
class SpreadAnalysis:
    """Computed spread metrics for a single quote."""

    spread_cents: float
    spread_quality: SpreadQuality
    spread_bps: float
    midpoint: float


class SpreadAssessment:
    """Pre-market and real-time spread analysis."""

    def __init__(self, data_provider: Any) -> None:
        """Store the data provider used to fetch quotes."""
        self.data_provider = data_provider

    def assess_premarket_conditions(self, symbol: str) -> PreMarketConditions | None:
        """Step 0: Pre-market spread assessment.

        Returns recommendations for:
        - Whether to wait for market open
        - Maximum acceptable slippage
        - Timing strategy
        """
        try:
            # Get pre-market bid/ask
            bid, ask = self.data_provider.get_latest_quote(symbol)
            if bid <= 0 or ask <= 0:
                return None

            spread_cents = (ask - bid) * 100  # Convert to cents
            spread_quality = self._classify_spread(spread_cents)

            # Determine wait time and slippage tolerance
            if spread_quality == SpreadQuality.WIDE:
                wait_minutes = 2  # Wait 1-2 minutes post-open
                max_slippage_bps = 15  # Allow higher slippage for wide spreads
            elif spread_quality == SpreadQuality.NORMAL:
                wait_minutes = 1
                max_slippage_bps = 10
            else:  # TIGHT
                wait_minutes = 0  # Execute immediately
                max_slippage_bps = 5

            return PreMarketConditions(
                spread_cents=spread_cents,
                spread_quality=spread_quality,
                recommended_wait_minutes=wait_minutes,
                max_slippage_bps=max_slippage_bps,
            )

        except Exception as e:
            logging.warning(f"Error assessing pre-market conditions for {symbol}: {e}")
            return None

    def analyze_current_spread(self, symbol: str, bid: float, ask: float) -> SpreadAnalysis:
        """Analyze current spread quality for execution decisions."""
        spread_cents = (ask - bid) * 100
        spread_quality = self._classify_spread(spread_cents)
        midpoint = (bid + ask) / 2
        spread_bps = ((ask - bid) / midpoint) * 10000 if midpoint > 0 else 0

        return SpreadAnalysis(
            spread_cents=spread_cents,
            spread_quality=spread_quality,
            spread_bps=spread_bps,
            midpoint=midpoint,
        )

    def _classify_spread(self, spread_cents: float) -> SpreadQuality:
        """Classify spread quality based on cents."""
        if spread_cents <= 3.0:
            return SpreadQuality.TIGHT
        if spread_cents <= 5.0:
            return SpreadQuality.NORMAL
        return SpreadQuality.WIDE
