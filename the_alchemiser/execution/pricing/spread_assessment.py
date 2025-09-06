#!/usr/bin/env python3
"""Business Unit: order execution/placement; Status: current.

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

    TIGHT = "tight"  # ≤ 3¢ or ≤ 10 bps
    NORMAL = "normal"  # 3-5¢ or 10-50 bps
    WIDE = "wide"  # > 5¢ or > 50 bps


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
            spread_bps = ((ask - bid) / ((bid + ask) / 2)) * 10000 if (bid + ask) > 0 else 0
            spread_quality = self._classify_spread(spread_cents, spread_bps)

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
        midpoint = (bid + ask) / 2
        spread_bps = ((ask - bid) / midpoint) * 10000 if midpoint > 0 else 0
        spread_quality = self._classify_spread(spread_cents, spread_bps)

        return SpreadAnalysis(
            spread_cents=spread_cents,
            spread_quality=spread_quality,
            spread_bps=spread_bps,
            midpoint=midpoint,
        )

    def _classify_spread(self, spread_cents: float, spread_bps: float | None = None) -> SpreadQuality:
        """Classify spread quality based on cents and basis points.
        
        Uses both absolute (cents) and relative (bps) measures for better classification.
        """
        # Primary classification by cents
        if spread_cents <= 3.0:
            primary_quality = SpreadQuality.TIGHT
        elif spread_cents <= 5.0:
            primary_quality = SpreadQuality.NORMAL
        else:
            primary_quality = SpreadQuality.WIDE
            
        # Secondary validation by basis points if available
        if spread_bps is not None:
            if spread_bps <= 10:
                bps_quality = SpreadQuality.TIGHT
            elif spread_bps <= 50:
                bps_quality = SpreadQuality.NORMAL
            else:
                bps_quality = SpreadQuality.WIDE
                
            # Use the more conservative (wider) classification
            if primary_quality == SpreadQuality.TIGHT and bps_quality != SpreadQuality.TIGHT:
                return bps_quality
            elif primary_quality == SpreadQuality.NORMAL and bps_quality == SpreadQuality.WIDE:
                return SpreadQuality.WIDE
                
        return primary_quality

    def get_execution_recommendations(self, spread_analysis: SpreadAnalysis) -> dict[str, str | float]:
        """Get execution recommendations based on spread analysis.
        
        Returns recommended pricing strategy and urgency level for liquidity-anchored execution.
        """
        recommendations: dict[str, str | float] = {
            "pricing_strategy": "liquidity_anchored",
            "urgency": "normal",
            "inside_factor": 0.3,  # How far inside spread to place order
            "timeout_multiplier": 1.0,
        }
        
        if spread_analysis.spread_quality == SpreadQuality.TIGHT:
            # Tight spreads: need to be more aggressive to get fills
            recommendations.update({
                "urgency": "high",
                "inside_factor": 0.6,
                "timeout_multiplier": 0.8,  # Faster execution
            })
        elif spread_analysis.spread_quality == SpreadQuality.WIDE:
            # Wide spreads: can be more patient
            recommendations.update({
                "urgency": "low", 
                "inside_factor": 0.1,
                "timeout_multiplier": 1.4,  # More patient
            })
            
        # Special handling for very tight spreads (< 1¢)
        if spread_analysis.spread_cents < 1.0:
            recommendations.update({
                "urgency": "urgent",
                "inside_factor": 0.8,
                "timeout_multiplier": 0.5,
            })
            
        return recommendations
