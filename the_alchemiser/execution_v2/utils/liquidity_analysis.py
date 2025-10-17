"""Business Unit: execution | Status: current.

Advanced liquidity analysis for volume-aware order placement.

This module provides sophisticated analysis of market depth and volume distribution
to enable truly liquidity-aware order placement that goes beyond simple bid/ask + offset.
"""

from __future__ import annotations

from collections.abc import Callable
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

    def __init__(self, min_volume_threshold: float = 100.0, tick_size: float = 0.01) -> None:
        """Initialize liquidity analyzer.

        Args:
            min_volume_threshold: Minimum volume required for valid liquidity level
            tick_size: Price increment for calculations

        """
        self.min_volume_threshold = min_volume_threshold
        # Convert tick_size to Decimal to avoid floating point precision issues
        self.tick_size = Decimal(str(tick_size))

    def analyze_liquidity(
        self, quote: QuoteModel, order_size: float, side: str | None = None
    ) -> LiquidityAnalysis:
        """Perform comprehensive liquidity analysis.

        Args:
            quote: Current market quote with volume data
            order_size: Size of order to place (in shares)
            side: Order side ("BUY" or "SELL"). If provided, only computes that side's limit price.
                  If None (legacy), computes both sides for backward compatibility.

        Returns:
            LiquidityAnalysis with recommendations

        """
        logger.debug(
            f"Analyzing liquidity for {quote.symbol}: order_size={order_size}, side={side}"
        )

        # Early validation of quote prices to prevent downstream negative price calculations
        if quote.bid_price < 0 or quote.ask_price < 0:
            logger.error(
                f"CRITICAL: Negative prices detected in quote for {quote.symbol}: "
                f"bid={quote.bid_price}, ask={quote.ask_price}. "
                f"This indicates a data quality issue upstream that must be investigated."
            )
            # Continue processing but flag the issue prominently

        # Additional validation: ensure prices are reasonable
        if quote.bid_price == 0 or quote.ask_price == 0:
            logger.warning(
                f"Zero prices detected in quote for {quote.symbol}: "
                f"bid={quote.bid_price}, ask={quote.ask_price}. "
                f"Quote data may be stale or incomplete."
            )

        # Log full quote details for debugging when prices look suspicious
        if quote.bid_price <= 0 or quote.ask_price <= 0 or quote.bid_price > quote.ask_price:
            logger.error(
                f"Suspicious quote detected for {quote.symbol}: "
                f"bid_price={quote.bid_price}, ask_price={quote.ask_price}, "
                f"bid_size={quote.bid_size}, ask_size={quote.ask_size}, "
                f"timestamp={quote.timestamp}"
            )

        # Calculate volume metrics
        total_bid_volume = quote.bid_size
        total_ask_volume = quote.ask_size

        # Calculate volume imbalance (-1 = heavy bid, +1 = heavy ask)
        total_volume = total_bid_volume + total_ask_volume
        volume_imbalance = 0.0
        if total_volume > 0:
            # Convert Decimal to float for imbalance calculation
            volume_imbalance = float((total_ask_volume - total_bid_volume) / total_volume)

        # Calculate liquidity score (0-100)
        liquidity_score = self._calculate_liquidity_score(quote, float(total_volume))

        # Determine optimal pricing based on volume analysis
        recommended_prices = self._calculate_volume_aware_prices(quote, order_size, side)

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

    def _calculate_liquidity_score(self, quote: QuoteModel, total_volume: float) -> float:
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
        # Guard against zero mid_price to prevent division by zero
        if quote.mid_price <= 0:
            logger.warning(
                f"Invalid mid_price for liquidity score calculation: {quote.mid_price}",
                extra={"symbol": quote.symbol},
            )
            spread_score = 0.0  # Worst score for invalid data
        else:
            spread_pct = (quote.spread / quote.mid_price) * 100
            spread_score = max(0, 30 - float(spread_pct) * 10)  # Up to 30 points for spread

        # Balance score (balanced book = higher score)
        if total_volume > 0:
            volume_ratio = min(quote.bid_size, quote.ask_size) / max(quote.bid_size, quote.ask_size)
            balance_score = float(volume_ratio) * 20  # Up to 20 points for balance
        else:
            balance_score = 0.0

        return min(volume_score + spread_score + balance_score, 100.0)

    def _validate_and_convert_quote_prices(
        self, quote: QuoteModel
    ) -> tuple[Decimal, Decimal] | None:
        """Validate quote prices and convert to Decimal.

        Args:
            quote: Market quote to validate

        Returns:
            Tuple of (bid_price, ask_price) as Decimals, or None if invalid

        """
        # Early validation: Ensure quote prices are positive before any calculations
        if quote.bid_price <= 0 or quote.ask_price <= 0:
            logger.error(
                f"Invalid quote prices for {quote.symbol}: "
                f"bid_price={quote.bid_price}, ask_price={quote.ask_price}. "
                f"Cannot calculate volume-aware prices with non-positive values."
            )
            return None

        # Convert to Decimal for precise arithmetic
        bid_price = Decimal(str(quote.bid_price))
        ask_price = Decimal(str(quote.ask_price))

        # Ensure quote is not already crossed (would indicate upstream data issue)
        if bid_price >= ask_price:
            logger.error(
                f"Crossed quote detected for {quote.symbol}: "
                f"bid={bid_price} >= ask={ask_price}. "
                f"Using ask as fallback for both sides."
            )
            return None

        return (bid_price, ask_price)

    def _compute_side_specific_limits(
        self,
        quote: QuoteModel,
        order_size: float,
        side: str | None,
        bid_price: Decimal,
        ask_price: Decimal,
        quantize: Callable[[Decimal], Decimal],
    ) -> tuple[Decimal, Decimal]:
        """Compute buy and sell limit prices based on order side.

        Args:
            quote: Market quote
            order_size: Order size in shares
            side: "BUY", "SELL", or None (legacy mode)
            bid_price: Validated bid price as Decimal
            ask_price: Validated ask price as Decimal
            quantize: Function to round to tick_size

        Returns:
            Tuple of (buy_limit, sell_limit) as Decimals

        """
        if side and side.upper() == "BUY":
            # BUY: consume from ask side, anchor to ask_price
            ask_volume_ratio = order_size / max(float(quote.ask_size), 1.0)
            buy_limit = self._calculate_buy_limit(ask_price, ask_volume_ratio, quantize)
            # Fallback for sell side (not used in this execution)
            sell_limit = quantize(ask_price + self.tick_size)

        elif side and side.upper() == "SELL":
            # SELL: consume from bid side, anchor to bid_price
            bid_volume_ratio = order_size / max(float(quote.bid_size), 1.0)
            sell_limit = self._calculate_sell_limit(bid_price, bid_volume_ratio, quantize)
            # Fallback for buy side (not used in this execution)
            buy_limit = quantize(bid_price)

        else:
            # Legacy mode: compute both sides (for preview/display)
            buy_limit, sell_limit = self._compute_legacy_both_sides(
                quote, order_size, bid_price, ask_price, quantize
            )

        return (buy_limit, sell_limit)

    def _compute_legacy_both_sides(
        self,
        quote: QuoteModel,
        order_size: float,
        bid_price: Decimal,
        ask_price: Decimal,
        quantize: Callable[[Decimal], Decimal],
    ) -> tuple[Decimal, Decimal]:
        """Compute both buy and sell limits for legacy mode.

        Args:
            quote: Market quote
            order_size: Order size in shares
            bid_price: Validated bid price as Decimal
            ask_price: Validated ask price as Decimal
            quantize: Function to round to tick_size

        Returns:
            Tuple of (buy_limit, sell_limit) as Decimals

        """
        # This path is DEPRECATED and should be avoided in execution
        ask_volume_ratio = order_size / max(float(quote.ask_size), 1.0)
        bid_volume_ratio = order_size / max(float(quote.bid_size), 1.0)

        buy_limit = self._calculate_buy_limit(ask_price, ask_volume_ratio, quantize)
        sell_limit = self._calculate_sell_limit(bid_price, bid_volume_ratio, quantize)

        # Enforce non-cross invariant when computing both sides
        if buy_limit >= sell_limit:
            logger.warning(
                f"Computed buy_limit ({buy_limit}) >= sell_limit ({sell_limit}) for {quote.symbol}. "
                f"Widening to prevent self-cross."
            )
            # Widen, don't collapse: ensure at least 1 tick spread
            sell_limit = quantize(buy_limit + self.tick_size)

        return (buy_limit, sell_limit)

    def _apply_final_price_checks(
        self,
        buy_limit: Decimal,
        sell_limit: Decimal,
        side: str | None,
        symbol: str,
        quantize: Callable[[Decimal], Decimal],
    ) -> dict[str, float]:
        """Apply final sanity checks and enforce price invariants.

        Args:
            buy_limit: Calculated buy limit price
            sell_limit: Calculated sell limit price
            side: Order side (or None for legacy mode)
            symbol: Symbol for logging
            quantize: Function to round to tick_size

        Returns:
            Dictionary with "bid" and "ask" prices as floats

        """
        # Final sanity checks
        min_price = Decimal("0.01")
        buy_limit = max(buy_limit, min_price)
        sell_limit = max(sell_limit, min_price + self.tick_size)

        # Enforce invariant ONLY in legacy mode (side=None) where both sides are meaningful
        # When side is specified, the opposite side is just a fallback and comparisons are invalid
        if side is None and buy_limit >= sell_limit:
            logger.error(
                f"INVARIANT VIOLATION: buy_limit ({buy_limit}) >= sell_limit ({sell_limit}) "
                f"for {symbol}. Emergency widening."
            )
            sell_limit = quantize(buy_limit + self.tick_size)

        return {"bid": float(buy_limit), "ask": float(sell_limit)}

    def _calculate_volume_aware_prices(
        self, quote: QuoteModel, order_size: float, side: str | None = None
    ) -> dict[str, float]:
        """Calculate optimal limit price(s) based on volume analysis.

        CRITICAL INVARIANT: BUY limit must be < SELL limit (no self-cross).

        Args:
            quote: Market quote with volume data
            order_size: Size of order in shares
            side: "BUY" or "SELL". If specified, only computes that side.
                  If None, computes both (for legacy/preview use cases).

        Returns:
            Dictionary with "bid" (BUY limit) and "ask" (SELL limit) prices.
            When side is specified, the other side uses fallback (quote price).

        """
        # Validate quote and get validated prices, or early return on error
        validated_prices = self._validate_and_convert_quote_prices(quote)
        if validated_prices is None:
            min_price = Decimal("0.01")
            return {"bid": float(min_price), "ask": float(min_price * 2)}

        bid_price, ask_price = validated_prices

        # Helper to quantize to tick_size
        def quantize(price: Decimal) -> Decimal:
            return price.quantize(self.tick_size)

        # Compute limit prices based on order side
        buy_limit, sell_limit = self._compute_side_specific_limits(
            quote, order_size, side, bid_price, ask_price, quantize
        )

        # Apply final sanity checks and enforce invariants
        return self._apply_final_price_checks(buy_limit, sell_limit, side, quote.symbol, quantize)

    def _calculate_buy_limit(
        self,
        ask_price: Decimal,
        ask_volume_ratio: float,
        quantize: Callable[[Decimal], Decimal],
    ) -> Decimal:
        """Calculate BUY limit price anchored to ask_price.

        BUY orders consume liquidity from the ask side (sellers).
        Larger orders relative to ask_size need more aggressive pricing.

        Args:
            ask_price: Current ask price (Decimal)
            ask_volume_ratio: order_size / ask_size
            quantize: Function to round to tick_size

        Returns:
            Recommended BUY limit price (will NOT cross above ask by default)

        """
        # Base: BUY at the ask (join the queue)
        base_limit = ask_price

        # Aggressiveness based on volume consumption
        if ask_volume_ratio > 0.8:  # Order > 80% of ask liquidity
            # Large order: stay AT ask (don't cross above)
            # Rational: We want fill certainty but not overpay
            # If we need to cross, that's a policy decision above this layer
            limit = base_limit
            logger.debug(
                f"Large buy vs ask liquidity ({ask_volume_ratio:.1%}), pricing at ask: {limit}"
            )
        elif ask_volume_ratio > 0.3:  # Order > 30% of ask liquidity
            # Medium order: price at ask (no improvement attempt)
            limit = base_limit
        else:
            # Small order: try to improve by 1 tick (passive)
            # (but never go below current bid - that's handled by caller using bid_price floor)
            limit = quantize(ask_price - self.tick_size)

        return quantize(max(limit, Decimal("0.01")))  # Never negative

    def _calculate_sell_limit(
        self,
        bid_price: Decimal,
        bid_volume_ratio: float,
        quantize: Callable[[Decimal], Decimal],
    ) -> Decimal:
        """Calculate SELL limit price anchored to bid_price.

        SELL orders consume liquidity from the bid side (buyers).
        Larger orders relative to bid_size need more aggressive pricing.

        Args:
            bid_price: Current bid price (Decimal)
            bid_volume_ratio: order_size / bid_size
            quantize: Function to round to tick_size

        Returns:
            Recommended SELL limit price (will NOT cross below bid by default)

        """
        # Base: SELL at the bid (join the queue)
        base_limit = bid_price

        # Aggressiveness based on volume consumption
        if bid_volume_ratio > 0.8:  # Order > 80% of bid liquidity
            # Large order: stay AT bid (don't cross below)
            limit = base_limit
            logger.debug(
                f"Large sell vs bid liquidity ({bid_volume_ratio:.1%}), pricing at bid: {limit}"
            )
        elif bid_volume_ratio > 0.3:  # Order > 30% of bid liquidity
            # Medium order: price at bid (no improvement attempt)
            limit = base_limit
        else:
            # Small order: try to improve by 1 tick (passive)
            # (but never go above current ask - that's handled by caller using ask_price ceiling)
            limit = quantize(bid_price + self.tick_size)

        return quantize(max(limit, Decimal("0.01")))  # Never negative

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
        # Guard against zero mid_price to prevent division by zero
        if quote.mid_price <= 0:
            logger.warning(
                f"Invalid mid_price for confidence calculation: {quote.mid_price}",
                extra={"symbol": quote.symbol},
            )
            # Apply maximum spread penalty for invalid data
            confidence *= 0.6  # 40% penalty for invalid price
        else:
            spread_pct = float((quote.spread / quote.mid_price) * 100)
            if spread_pct > 1.0:  # > 1% spread
                spread_penalty = min(spread_pct / 5.0, 0.4)  # Up to 40% penalty
                confidence *= 1.0 - spread_penalty

        # Reduce confidence if order is very large relative to liquidity
        available_volume = float(max(total_volume, 1.0))
        order_volume_ratio = order_size / available_volume
        if order_volume_ratio > 1.0:  # Order larger than available liquidity
            size_penalty = min((order_volume_ratio - 1.0) * 0.5, 0.6)  # Up to 60% penalty
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
        volume_ratio = float(order_size) / float(available_volume)
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
