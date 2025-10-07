"""Business Unit: execution | Status: current.

Advanced liquidity analysis for volume-aware order placement.

This module provides sophisticated analysis of market depth and volume distribution
to enable truly liquidity-aware order placement that goes beyond simple bid/ask + offset.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING, NamedTuple

from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from the_alchemiser.shared.types.market_data import QuoteModel

logger = get_logger(__name__)


class LiquidityLevel(NamedTuple):
    """Represents a liquidity level with price and volume."""

    price: float
    volume: float
    depth_percent: float  # How far from mid-price as percentage


@dataclass
class LiquidityAnalysis:
    """Analysis results for market liquidity."""

    symbol: str
    total_bid_volume: float
    total_ask_volume: float
    volume_imbalance: float  # (ask_vol - bid_vol) / (ask_vol + bid_vol)
    liquidity_score: float  # 0-100, higher = more liquid
    recommended_bid_price: float
    recommended_ask_price: float
    volume_at_recommended_bid: float
    volume_at_recommended_ask: float
    confidence: float  # 0-1, confidence in recommendations


class LiquidityAnalyzer:
    """Advanced liquidity analysis for smart execution."""

    def __init__(
        self, min_volume_threshold: float = 100.0, tick_size: float = 0.01
    ) -> None:
        """Initialize liquidity analyzer.

        Args:
            min_volume_threshold: Minimum volume required for valid liquidity level
            tick_size: Price increment for calculations

        """
        self.min_volume_threshold = min_volume_threshold
        # Convert tick_size to Decimal to avoid floating point precision issues
        self.tick_size = Decimal(str(tick_size))

    def analyze_liquidity(
        self, quote: QuoteModel, order_size: float
    ) -> LiquidityAnalysis:
        """Perform comprehensive liquidity analysis.

        Args:
            quote: Current market quote with volume data
            order_size: Size of order to place (in shares)

        Returns:
            LiquidityAnalysis with recommendations

        """
        logger.debug(f"Analyzing liquidity for {quote.symbol}: order_size={order_size}")

        # Early validation of quote prices to prevent downstream negative price calculations
        if quote.bid_price < 0 or quote.ask_price < 0:
            logger.warning(
                f"Negative prices detected in quote for {quote.symbol}: "
                f"bid={quote.bid_price}, ask={quote.ask_price}. This should have been caught earlier."
            )
            # Don't fail here - let the existing validation handle it downstream
            # but log the issue for debugging

        # Calculate volume metrics
        total_bid_volume = quote.bid_size
        total_ask_volume = quote.ask_size

        # Calculate volume imbalance (-1 = heavy bid, +1 = heavy ask)
        total_volume = total_bid_volume + total_ask_volume
        volume_imbalance = 0.0
        if total_volume > 0:
            # Convert Decimal to float for imbalance calculation
            volume_imbalance = float(
                (total_ask_volume - total_bid_volume) / total_volume
            )

        # Calculate liquidity score (0-100)
        liquidity_score = self._calculate_liquidity_score(quote, float(total_volume))

        # Determine optimal pricing based on volume analysis
        recommended_prices = self._calculate_volume_aware_prices(quote, order_size)

        # Calculate confidence based on data quality and volume
        confidence = self._calculate_confidence(quote, order_size, float(total_volume))

        analysis = LiquidityAnalysis(
            symbol=quote.symbol,
            total_bid_volume=float(total_bid_volume),
            total_ask_volume=float(total_ask_volume),
            volume_imbalance=volume_imbalance,
            liquidity_score=liquidity_score,
            recommended_bid_price=recommended_prices["bid"],
            recommended_ask_price=recommended_prices["ask"],
            volume_at_recommended_bid=float(total_bid_volume),
            volume_at_recommended_ask=float(total_ask_volume),
            confidence=confidence,
        )

        logger.debug(
            f"Liquidity analysis for {quote.symbol}: "
            f"score={liquidity_score:.1f}, imbalance={volume_imbalance:.3f}, "
            f"confidence={confidence:.2f}"
        )

        return analysis

    def _calculate_liquidity_score(
        self, quote: QuoteModel, total_volume: float
    ) -> float:
        """Calculate overall liquidity score (0-100).

        Args:
            quote: Market quote
            total_volume: Total volume at best bid/ask

        Returns:
            Liquidity score from 0 (illiquid) to 100 (very liquid)

        """
        # Base score from volume
        volume_score = min(total_volume / 1000.0, 50.0)  # Up to 50 points for volume

        # Spread score (tighter spreads = higher score)
        spread_pct = (quote.spread / quote.mid_price) * 100
        spread_score = max(0, 30 - float(spread_pct) * 10)  # Up to 30 points for spread

        # Balance score (balanced book = higher score)
        if total_volume > 0:
            volume_ratio = min(quote.bid_size, quote.ask_size) / max(
                quote.bid_size, quote.ask_size
            )
            balance_score = float(volume_ratio) * 20  # Up to 20 points for balance
        else:
            balance_score = 0.0

        return min(volume_score + spread_score + balance_score, 100.0)

    def _calculate_volume_aware_prices(
        self, quote: QuoteModel, order_size: float
    ) -> dict[str, float]:
        """Calculate optimal prices based on volume analysis.

        Args:
            quote: Market quote with volume data
            order_size: Size of order in shares

        Returns:
            Dictionary with recommended bid and ask prices

        """
        # Analyze volume sufficiency at current levels
        bid_volume_ratio = order_size / max(float(quote.bid_size), 1.0)
        ask_volume_ratio = order_size / max(float(quote.ask_size), 1.0)

        # Convert prices to Decimal for precise arithmetic
        bid_price = Decimal(str(quote.bid_price))
        ask_price = Decimal(str(quote.ask_price))

        # Adjust based on order size vs available volume
        if bid_volume_ratio > 0.8:  # Order size > 80% of available volume
            # Large order relative to liquidity - be more aggressive
            recommended_bid = bid_price + (self.tick_size * 2)
            logger.debug(
                f"Large buy order vs liquidity ({bid_volume_ratio:.1%}), "
                f"pricing aggressively: {recommended_bid}"
            )
        elif bid_volume_ratio > 0.3:  # Order size > 30% of available volume
            # Medium order - price just inside
            recommended_bid = bid_price + self.tick_size
        else:
            # Small order - can be patient, price at best bid
            recommended_bid = bid_price

        # Similar logic for ask side
        if ask_volume_ratio > 0.8:
            recommended_ask = ask_price - (self.tick_size * 2)
            logger.debug(
                f"Large sell order vs liquidity ({ask_volume_ratio:.1%}), "
                f"pricing aggressively: {recommended_ask}"
            )
        elif ask_volume_ratio > 0.3:
            recommended_ask = ask_price - self.tick_size
        else:
            recommended_ask = ask_price

        # Additional adjustments based on volume imbalance
        total_volume = quote.bid_size + quote.ask_size
        if total_volume > 0:
            imbalance = float((quote.ask_size - quote.bid_size) / total_volume)

            # If heavy bid side (imbalance < -0.2), be more aggressive on buys
            if imbalance < -0.2:
                recommended_bid = min(
                    recommended_bid + self.tick_size, ask_price - self.tick_size
                )
                logger.debug(
                    f"Heavy bid side detected, adjusting buy price to {recommended_bid}"
                )

            # If heavy ask side (imbalance > 0.2), be more aggressive on sells
            elif imbalance > 0.2:
                recommended_ask = max(
                    recommended_ask - self.tick_size, bid_price + self.tick_size
                )
                logger.debug(
                    f"Heavy ask side detected, adjusting sell price to {recommended_ask}"
                )

        # Quantize prices to tick_size precision to avoid floating point errors
        recommended_bid = recommended_bid.quantize(self.tick_size)
        recommended_ask = recommended_ask.quantize(self.tick_size)

        # Validate that recommended prices are positive and reasonable
        # This prevents issues with bad quote data leading to zero or negative limit prices
        min_price = Decimal("0.01")  # Minimum 1 cent

        if recommended_bid <= 0:
            logger.warning(
                f"Invalid recommended bid price {recommended_bid} for {quote.symbol}, "
                f"using fallback of ${min_price}"
            )
            recommended_bid = min_price

        if recommended_ask <= 0:
            logger.warning(
                f"Invalid recommended ask price {recommended_ask} for {quote.symbol}, "
                f"using fallback of ${min_price}"
            )
            recommended_ask = min_price

        # Ensure ask >= bid (basic sanity check)
        if recommended_ask < recommended_bid:
            logger.warning(
                f"Ask price {recommended_ask} < bid price {recommended_bid} for {quote.symbol}, "
                f"adjusting ask to match bid"
            )
            recommended_ask = recommended_bid

        return {"bid": float(recommended_bid), "ask": float(recommended_ask)}

    def _calculate_confidence(
        self, quote: QuoteModel, order_size: float, total_volume: float
    ) -> float:
        """Calculate confidence in the liquidity analysis.

        Args:
            quote: Market quote
            order_size: Order size in shares
            total_volume: Total volume at best levels

        Returns:
            Confidence score from 0.0 to 1.0

        """
        confidence = 1.0

        # Reduce confidence if volumes are very low
        if total_volume < self.min_volume_threshold:
            volume_penalty = 1.0 - (total_volume / self.min_volume_threshold)
            confidence *= 1.0 - volume_penalty * 0.5  # Up to 50% penalty

        # Reduce confidence if spread is very wide
        spread_pct = float((quote.spread / quote.mid_price) * 100)
        if spread_pct > 1.0:  # > 1% spread
            spread_penalty = min(spread_pct / 5.0, 0.4)  # Up to 40% penalty
            confidence *= 1.0 - spread_penalty

        # Reduce confidence if order is very large relative to liquidity
        available_volume = float(max(total_volume, 1.0))
        order_volume_ratio = order_size / available_volume
        if order_volume_ratio > 1.0:  # Order larger than available liquidity
            size_penalty = min(
                (order_volume_ratio - 1.0) * 0.5, 0.6
            )  # Up to 60% penalty
            confidence *= 1.0 - size_penalty

        return max(confidence, 0.1)  # Minimum 10% confidence

    def validate_liquidity_for_order(
        self, quote: QuoteModel, side: str, order_size: float
    ) -> tuple[bool, str]:
        """Validate if there's sufficient liquidity for an order.

        Args:
            quote: Market quote
            side: 'buy' or 'sell'
            order_size: Size of order in shares

        Returns:
            Tuple of (is_valid, reason)

        """
        if side.lower() == "buy":
            available_volume = quote.ask_size  # Buy against ask
            price_level = "ask"
        else:
            available_volume = quote.bid_size  # Sell against bid
            price_level = "bid"

        # Check absolute minimum volume
        if available_volume < self.min_volume_threshold:
            return (
                False,
                f"Insufficient volume at {price_level}: {available_volume} < {self.min_volume_threshold}",
            )

        # Check volume ratio
        volume_ratio = order_size / available_volume
        if volume_ratio > 2.0:  # Order more than 2x available volume
            return (
                False,
                f"Order too large vs liquidity: {order_size} vs {available_volume} at {price_level}",
            )

        # Check spread reasonableness
        spread_pct = (quote.spread / quote.mid_price) * 100
        if spread_pct > 5.0:  # > 5% spread is probably problematic
            return False, f"Spread too wide: {spread_pct:.2f}%"

        return True, "Liquidity validation passed"

    def get_execution_strategy_recommendation(
        self, analysis: LiquidityAnalysis, side: str, order_size: float
    ) -> str:
        """Recommend execution strategy based on liquidity analysis.

        Args:
            analysis: Liquidity analysis results
            side: 'buy' or 'sell'
            order_size: Order size in shares

        Returns:
            Recommended strategy: 'aggressive', 'normal', 'patient', 'split'

        """
        # High confidence and good liquidity = normal strategy
        if analysis.confidence > 0.8 and analysis.liquidity_score > 70:
            return "normal"

        # Low liquidity = patient strategy
        if analysis.liquidity_score < 30:
            return "patient"

        # Large order vs available volume = consider splitting
        relevant_volume = (
            analysis.volume_at_recommended_ask
            if side.lower() == "buy"
            else analysis.volume_at_recommended_bid
        )
        volume_ratio = order_size / max(relevant_volume, 1.0)

        if volume_ratio > 1.5:
            return "split"

        # Volume imbalance suggests aggressive strategy
        if side.lower() == "buy" and analysis.volume_imbalance < -0.3:
            return "aggressive"  # Heavy bid side, be aggressive
        if side.lower() == "sell" and analysis.volume_imbalance > 0.3:
            return "aggressive"  # Heavy ask side, be aggressive

        return "normal"
