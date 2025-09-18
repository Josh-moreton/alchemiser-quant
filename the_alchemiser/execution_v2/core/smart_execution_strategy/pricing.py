"""Business Unit: execution | Status: current.

Pricing calculations for smart execution strategy.

This module handles all pricing logic including liquidity-aware pricing,
fallback pricing, and re-pegging price calculations.
"""

from __future__ import annotations

import logging
from decimal import Decimal

from the_alchemiser.execution_v2.utils.liquidity_analysis import LiquidityAnalyzer
from the_alchemiser.shared.types.market_data import QuoteModel

from .models import ExecutionConfig, LiquidityMetadata

logger = logging.getLogger(__name__)


class PricingCalculator:
    """Handles all pricing calculations for smart execution."""

    def __init__(self, config: ExecutionConfig) -> None:
        """Initialize pricing calculator.

        Args:
            config: Execution configuration for pricing parameters

        """
        self.config = config
        # Initialize liquidity analyzer with adjusted thresholds
        self.liquidity_analyzer = LiquidityAnalyzer(
            min_volume_threshold=float(self.config.min_bid_ask_size),
            tick_size=float(self.config.bid_anchor_offset_cents),
        )

    def calculate_liquidity_aware_price(
        self, quote: QuoteModel, side: str, order_size: float
    ) -> tuple[Decimal, LiquidityMetadata]:
        """Calculate optimal price using advanced liquidity analysis.

        Args:
            quote: Valid quote data
            side: "BUY" or "SELL"
            order_size: Size of order in shares

        Returns:
            Tuple of (optimal_price, analysis_metadata)

        """
        # Perform comprehensive liquidity analysis
        analysis = self.liquidity_analyzer.analyze_liquidity(quote, order_size)

        # Get volume-aware pricing recommendation
        if side.upper() == "BUY":
            optimal_price = Decimal(str(analysis.recommended_bid_price))
            volume_available = analysis.volume_at_recommended_bid
            strategy_rec = (
                self.liquidity_analyzer.get_execution_strategy_recommendation(
                    analysis, side.lower(), order_size
                )
            )
        else:
            optimal_price = Decimal(str(analysis.recommended_ask_price))
            volume_available = analysis.volume_at_recommended_ask
            strategy_rec = (
                self.liquidity_analyzer.get_execution_strategy_recommendation(
                    analysis, side.lower(), order_size
                )
            )

        # Create metadata for logging and monitoring
        metadata: LiquidityMetadata = {
            "liquidity_score": analysis.liquidity_score,
            "volume_imbalance": analysis.volume_imbalance,
            "confidence": analysis.confidence,
            "volume_available": volume_available,
            "volume_ratio": order_size / max(volume_available, 1.0),
            "strategy_recommendation": strategy_rec,
            "bid_volume": analysis.total_bid_volume,
            "ask_volume": analysis.total_ask_volume,
        }

        logger.info(
            f"🧠 Liquidity-aware pricing for {quote.symbol} {side}: "
            f"price=${optimal_price} (score={analysis.liquidity_score:.1f}, "
            f"confidence={analysis.confidence:.2f}, strategy={strategy_rec})"
        )

        # Add detailed volume analysis to debug logs
        logger.debug(
            f"Volume analysis {quote.symbol}: bid_vol={analysis.total_bid_volume}, "
            f"ask_vol={analysis.total_ask_volume}, imbalance={analysis.volume_imbalance:.3f}, "
            f"order_vol_ratio={order_size / max(volume_available, 1.0):.2f}"
        )

        return optimal_price, metadata

    def calculate_simple_inside_spread_price(
        self, quote: QuoteModel, side: str
    ) -> tuple[Decimal, LiquidityMetadata]:
        """Compute a simple inside-spread anchor using configured offsets.

        This is used when we only have REST quotes or inadequate depth data.
        Uses 'normal' liquidity settings as per Josh's guidance for fallback scenarios.

        Args:
            quote: Quote data
            side: "BUY" or "SELL"

        Returns:
            Tuple of (anchor_price, metadata)

        """
        bid = Decimal(str(max(quote.bid_price, 0.0)))
        ask = Decimal(str(max(quote.ask_price, 0.0)))
        mid = (bid + ask) / Decimal("2") if bid > 0 and ask > 0 else (bid or ask)

        # Minimum step as 1 cent for safety
        tick = Decimal("0.01")

        if side.upper() == "BUY":
            # For buys, place slightly above bid (normal liquidity setting)
            anchor = bid + max(self.config.bid_anchor_offset_cents, tick)
            # Ensure we stay inside the spread when possible
            if ask > 0 and anchor >= ask:
                anchor = max(ask - max(self.config.bid_anchor_offset_cents, tick), bid)
            # Use mid as soft cap for reasonable execution
            if ask > 0 and bid > 0:
                anchor = min(anchor, mid)
        else:
            # For sells, place slightly below ask (normal liquidity setting)
            anchor = ask - max(self.config.ask_anchor_offset_cents, tick)
            if bid > 0 and anchor <= bid:
                anchor = min(ask, bid + max(self.config.ask_anchor_offset_cents, tick))
            if ask > 0 and bid > 0:
                anchor = max(anchor, mid)

        metadata: LiquidityMetadata = {
            "method": "simple_inside_spread_fallback",
            "mid": float(mid),
            "bid": float(bid),
            "ask": float(ask),
            "bid_price": float(bid),  # Ensure consistency with normal analysis
            "ask_price": float(ask),  # Ensure consistency with normal analysis
            "strategy_recommendation": "normal_liquidity_fallback",
            "liquidity_score": 0.5,  # Normal/moderate score for fallback
            "volume_imbalance": 0.0,
            "confidence": 0.7,  # Good confidence for REST API data
            "volume_available": 0.0,  # Not available from REST API
            "volume_ratio": 0.0,
            "bid_volume": 0.0,
            "ask_volume": 0.0,
            "bid_size": 0.0,  # REST API doesn't provide size data
            "ask_size": 0.0,  # REST API doesn't provide size data
            "spread_percent": float((ask - bid) / bid * 100) if bid > 0 else 0.0,
            "used_fallback": True,  # Mark as fallback pricing
        }
        # Quantize to cent precision to avoid sub-penny errors
        anchor_quantized = anchor.quantize(Decimal("0.01"))
        return anchor_quantized, metadata

    def calculate_repeg_price(
        self, quote: QuoteModel, side: str, original_price: Decimal | None
    ) -> Decimal | None:
        """Calculate a more aggressive price for re-pegging.

        Args:
            quote: Current market quote
            side: Order side ("BUY" or "SELL")
            original_price: Original order price

        Returns:
            New more aggressive price, or None if cannot calculate

        """
        try:
            if side.upper() == "BUY":
                # For buys, move price up towards ask (more aggressive)
                if original_price:
                    # Move 50% closer to the ask price
                    ask_price = Decimal(str(quote.ask_price))
                    adjustment = (ask_price - original_price) * Decimal("0.5")
                    new_price = original_price + adjustment
                else:
                    # If no original price, use ask price minus small offset
                    new_price = (
                        Decimal(str(quote.ask_price))
                        - self.config.ask_anchor_offset_cents
                    )

                # Ensure we don't exceed ask price
                new_price = min(new_price, Decimal(str(quote.ask_price)))

            else:  # SELL
                # For sells, move price down towards bid (more aggressive)
                if original_price:
                    # Move 50% closer to the bid price
                    bid_price = Decimal(str(quote.bid_price))
                    adjustment = (original_price - bid_price) * Decimal("0.5")
                    new_price = original_price - adjustment
                else:
                    # If no original price, use bid price plus small offset
                    new_price = (
                        Decimal(str(quote.bid_price))
                        + self.config.bid_anchor_offset_cents
                    )

                # Ensure we don't go below bid price
                new_price = max(new_price, Decimal(str(quote.bid_price)))

            # Quantize to cent precision to avoid sub-penny errors
            return new_price.quantize(Decimal("0.01"))

        except Exception as e:
            logger.error(f"Error calculating re-peg price: {e}")
            return None