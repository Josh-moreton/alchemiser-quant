"""Business Unit: execution | Status: current.

Pricing calculations for smart execution strategy.

This module handles all pricing logic including liquidity-aware pricing,
fallback pricing, and re-pegging price calculations.
"""

from __future__ import annotations

from decimal import Decimal

from the_alchemiser.execution_v2.utils.liquidity_analysis import LiquidityAnalyzer
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.types.market_data import QuoteModel

from .models import ExecutionConfig, LiquidityMetadata

logger = get_logger(__name__)


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
        self, quote: QuoteModel, side: str, order_size: Decimal
    ) -> tuple[Decimal, LiquidityMetadata]:
        """Calculate optimal price using advanced liquidity analysis.

        Args:
            quote: Valid quote data
            side: "BUY" or "SELL"
            order_size: Size of order in shares (as Decimal for precision)

        Returns:
            Tuple of (optimal_price, analysis_metadata)

        """
        # Perform comprehensive liquidity analysis (convert to float only for analysis)
        analysis = self.liquidity_analyzer.analyze_liquidity(quote, float(order_size))

        # Get volume-aware pricing recommendation
        if side.upper() == "BUY":
            optimal_price = Decimal(str(analysis.recommended_bid_price))
            volume_available = analysis.volume_at_recommended_bid
            strategy_rec = self.liquidity_analyzer.get_execution_strategy_recommendation(
                analysis, side.lower(), float(order_size)
            )
        else:
            optimal_price = Decimal(str(analysis.recommended_ask_price))
            volume_available = analysis.volume_at_recommended_ask
            strategy_rec = self.liquidity_analyzer.get_execution_strategy_recommendation(
                analysis, side.lower(), float(order_size)
            )

        # Create metadata for logging and monitoring
        order_size_float = float(order_size)
        metadata: LiquidityMetadata = {
            "liquidity_score": analysis.liquidity_score,
            "volume_imbalance": analysis.volume_imbalance,
            "confidence": analysis.confidence,
            "volume_available": volume_available,
            "volume_ratio": order_size_float / max(volume_available, 1.0),
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
            f"order_vol_ratio={order_size_float / max(volume_available, 1.0):.2f}"
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
        bid, ask, mid, tick = self._calculate_price_fundamentals(quote)

        anchor = self._calculate_side_specific_anchor(side, bid, ask, mid, tick)

        metadata = self._build_fallback_metadata(bid, ask, mid)

        anchor_quantized = self._quantize_and_validate_anchor(anchor, quote.symbol, side)

        return anchor_quantized, metadata

    def _calculate_price_fundamentals(
        self, quote: QuoteModel
    ) -> tuple[Decimal, Decimal, Decimal, Decimal]:
        """Calculate basic price values needed for anchor calculation.

        Args:
            quote: Quote data

        Returns:
            Tuple of (bid, ask, mid, tick)

        """
        bid = Decimal(str(max(quote.bid_price, 0.0)))
        ask = Decimal(str(max(quote.ask_price, 0.0)))
        mid = (bid + ask) / Decimal("2") if bid > 0 and ask > 0 else (bid or ask)
        tick = Decimal("0.01")  # Minimum step as 1 cent for safety

        return bid, ask, mid, tick

    def _calculate_side_specific_anchor(
        self, side: str, bid: Decimal, ask: Decimal, mid: Decimal, tick: Decimal
    ) -> Decimal:
        """Calculate anchor price based on order side.

        Args:
            side: "BUY" or "SELL"
            bid: Bid price
            ask: Ask price
            mid: Mid price
            tick: Minimum tick size

        Returns:
            Calculated anchor price

        """
        if side.upper() == "BUY":
            return self._calculate_buy_anchor(bid, ask, mid, tick)
        return self._calculate_sell_anchor(bid, ask, mid, tick)

    def _calculate_buy_anchor(
        self, bid: Decimal, ask: Decimal, mid: Decimal, tick: Decimal
    ) -> Decimal:
        """Calculate buy-side anchor price with spread constraints.

        Args:
            bid: Bid price
            ask: Ask price
            mid: Mid price
            tick: Minimum tick size

        Returns:
            Buy anchor price

        """
        # For buys, place slightly above bid (normal liquidity setting)
        anchor = bid + max(self.config.bid_anchor_offset_cents, tick)

        # Ensure we stay inside the spread when possible
        if ask > 0 and anchor >= ask:
            anchor = max(ask - max(self.config.bid_anchor_offset_cents, tick), bid)

        # Use mid as soft cap for reasonable execution
        if ask > 0 and bid > 0:
            anchor = min(anchor, mid)

        return anchor

    def _calculate_sell_anchor(
        self, bid: Decimal, ask: Decimal, mid: Decimal, tick: Decimal
    ) -> Decimal:
        """Calculate sell-side anchor price with spread constraints.

        Args:
            bid: Bid price
            ask: Ask price
            mid: Mid price
            tick: Minimum tick size

        Returns:
            Sell anchor price

        """
        # For sells, place slightly below ask (normal liquidity setting)
        anchor = ask - max(self.config.ask_anchor_offset_cents, tick)

        if bid > 0 and anchor <= bid:
            anchor = min(ask, bid + max(self.config.ask_anchor_offset_cents, tick))

        if ask > 0 and bid > 0:
            anchor = max(anchor, mid)

        return anchor

    def _build_fallback_metadata(
        self, bid: Decimal, ask: Decimal, mid: Decimal
    ) -> LiquidityMetadata:
        """Build metadata for fallback pricing scenario.

        Args:
            bid: Bid price
            ask: Ask price
            mid: Mid price

        Returns:
            Fallback metadata dictionary

        """
        return {
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

    def _quantize_and_validate_anchor(self, anchor: Decimal, symbol: str, side: str) -> Decimal:
        """Quantize anchor to cent precision and validate it's positive.

        Args:
            anchor: Raw anchor price
            symbol: Symbol for logging
            side: Order side for logging

        Returns:
            Quantized and validated anchor price

        """
        # Quantize to cent precision to avoid sub-penny errors
        anchor_quantized = anchor.quantize(Decimal("0.01"))

        # Validate that the calculated anchor price is positive and reasonable
        min_price = Decimal("0.01")  # Minimum 1 cent
        if anchor_quantized <= 0:
            logger.warning(
                f"Invalid anchor price {anchor_quantized} calculated for {symbol} {side}, "
                f"using minimum price ${min_price}"
            )
            anchor_quantized = min_price

        return anchor_quantized

    def calculate_repeg_price(
        self,
        quote: QuoteModel,
        side: str,
        original_price: Decimal | None,
        price_history: list[Decimal] | None = None,
    ) -> Decimal | None:
        """Calculate a more aggressive price for re-pegging.

        Args:
            quote: Current market quote
            side: Order side ("BUY" or "SELL")
            original_price: Original order price
            price_history: List of previously used prices to avoid

        Returns:
            New more aggressive price, or None if cannot calculate

        """
        try:
            new_price = self._calculate_aggressive_price(quote, side, original_price)

            # Check against price history to avoid repegging at same prices
            if price_history:
                from .utils import validate_repeg_price_with_history

                # Use configured minimum improvement
                min_imp = getattr(self.config, "repeg_min_improvement_cents", Decimal("0.01"))
                new_price = validate_repeg_price_with_history(
                    new_price, price_history, side, quote, min_improvement=min_imp
                )

            # Final validation and quantization
            return self._finalize_repeg_price(new_price, original_price)

        except Exception as e:
            logger.error(f"Error calculating re-peg price: {e}")
            return None

    def _calculate_aggressive_price(
        self, quote: QuoteModel, side: str, original_price: Decimal | None
    ) -> Decimal:
        """Calculate more aggressive price based on side and original price.

        Args:
            quote: Current market quote
            side: Order side ("BUY" or "SELL")
            original_price: Original order price

        Returns:
            More aggressive price

        """
        from .utils import calculate_price_adjustment

        allow_cross = getattr(self.config, "allow_cross_spread_on_repeg", False)
        if side.upper() == "BUY":
            ask_price = Decimal(str(quote.ask_price))
            if original_price:
                # Move 50% closer to the ask price
                new_price = calculate_price_adjustment(original_price, ask_price)
            else:
                # If no original price, use ask price minus small offset
                new_price = ask_price - self.config.ask_anchor_offset_cents

            # Optionally allow crossing the ask to ensure marketability
            if allow_cross:
                # Cross by at least min improvement to avoid same-price repeats
                min_imp = getattr(self.config, "repeg_min_improvement_cents", Decimal("0.01"))
                new_price = max(new_price, ask_price + min_imp)
            else:
                # Ensure we don't exceed ask price
                new_price = min(new_price, ask_price)

        else:  # SELL
            bid_price = Decimal(str(quote.bid_price))
            if original_price:
                # Move 50% closer to the bid price
                new_price = calculate_price_adjustment(original_price, bid_price)
            else:
                # If no original price, use bid price plus small offset
                new_price = bid_price + self.config.bid_anchor_offset_cents

            # Optionally allow crossing the bid to ensure marketability
            if allow_cross:
                min_imp = getattr(self.config, "repeg_min_improvement_cents", Decimal("0.01"))
                new_price = min(new_price, bid_price - min_imp)
            else:
                # Ensure we don't go below bid price
                new_price = max(new_price, bid_price)

        return new_price

    def _finalize_repeg_price(self, new_price: Decimal, original_price: Decimal | None) -> Decimal:
        """Finalize repeg price with validation and quantization.

        Args:
            new_price: Calculated new price
            original_price: Original price for fallback

        Returns:
            Final validated price

        """
        from .utils import ensure_minimum_price, quantize_price_safely

        # Quantize to cent precision to avoid sub-penny errors
        new_price = quantize_price_safely(new_price)

        # Validate that the calculated price is positive and reasonable
        min_price = Decimal("0.01")  # Minimum 1 cent
        if new_price <= 0:
            logger.warning(
                f"Invalid re-peg price {new_price} calculated, "
                f"falling back to original price or minimum price"
            )
            # Use original price if available and valid, otherwise use minimum
            if original_price and original_price > min_price:
                new_price = original_price
            else:
                new_price = min_price

        return ensure_minimum_price(new_price, min_price)
