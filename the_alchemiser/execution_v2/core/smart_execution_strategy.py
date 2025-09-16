"""Business Unit: execution | Status: current.

Smart execution strategy for canonical order placement and execution.

This module implements intelligent limit order placement for swing trading with
true liquidity-aware anchoring, spread validation, volume analysis, and re-pegging logic.
Designed for accuracy and queue priority using sophisticated volume analysis.

Key Features:
- True liquidity-aware anchoring using volume analysis (not just bid/ask + offset)
- Volume-weighted pricing based on order size vs available liquidity
- Market timing awareness (avoids 9:30-9:35am placement)
- Advanced spread and volume validation before order placement
- Re-pegging logic with configurable thresholds and limits
- Async-friendly design leveraging existing real-time pricing
"""

from __future__ import annotations

import logging
import time  # Add this import
from dataclasses import dataclass, field  # Add field import
from datetime import UTC, datetime  # Rename to avoid conflict
from datetime import time as dt_time
from decimal import Decimal
from typing import Any

from the_alchemiser.execution_v2.utils.liquidity_analysis import LiquidityAnalyzer
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.services.real_time_pricing import RealTimePricingService
from the_alchemiser.shared.types.market_data import QuoteModel

logger = logging.getLogger(__name__)


@dataclass
class ExecutionConfig:
    """Configuration for smart execution strategy."""

    # Market timing
    market_open_delay_minutes: int = 5  # Wait 5 minutes after 9:30am ET

    # Spread limits
    max_spread_percent: Decimal = Decimal(
        "0.50"
    )  # 0.50% maximum spread (increased from 0.25%)

    # Re-pegging configuration
    repeg_threshold_percent: Decimal = Decimal("0.10")  # Re-peg if market moves >0.1%
    max_repegs_per_order: int = 5  # Maximum re-pegs before escalation

    # Volume requirements - ADJUSTED FOR LOW LIQUIDITY ETFS
    min_bid_ask_size: Decimal = Decimal("10")  # Reduced from 100 to 10 shares minimum
    min_bid_ask_size_high_liquidity: Decimal = Decimal(
        "100"
    )  # For liquid stocks like SPY

    # Order timing
    quote_freshness_seconds: int = 5  # Require quote within 5 seconds
    order_placement_timeout_seconds: int = 30  # Timeout for order placement
    fill_wait_seconds: int = 15  # Wait time before attempting re-peg

    # Anchoring offsets (in cents)
    bid_anchor_offset_cents: Decimal = Decimal("0.01")  # Place at bid + $0.01 for buys
    ask_anchor_offset_cents: Decimal = Decimal("0.01")  # Place at ask - $0.01 for sells

    # Symbol-specific overrides for low-liquidity ETFs
    low_liquidity_symbols: set[str] = field(
        default_factory=lambda: {"BTAL", "UVXY", "TECL", "KMLM"}
    )


@dataclass
class SmartOrderRequest:
    """Request for smart order placement."""

    symbol: str
    side: str  # "BUY" or "SELL"
    quantity: Decimal
    correlation_id: str
    urgency: str = "NORMAL"  # "LOW", "NORMAL", "HIGH"
    is_complete_exit: bool = False


@dataclass
class SmartOrderResult:
    """Result of smart order placement attempt."""

    success: bool
    order_id: str | None = None
    final_price: Decimal | None = None
    anchor_price: Decimal | None = None
    repegs_used: int = 0
    execution_strategy: str = "smart_limit"
    error_message: str | None = None
    placement_timestamp: datetime | None = None
    metadata: dict[str, Any] | None = None


class SmartExecutionStrategy:
    """Smart execution strategy using truly liquidity-aware limit orders."""

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        pricing_service: RealTimePricingService | None = None,
        config: ExecutionConfig | None = None,
    ) -> None:
        """Initialize smart execution strategy.

        Args:
            alpaca_manager: Alpaca broker manager
            pricing_service: Real-time pricing service (optional)
            config: Execution configuration (uses defaults if not provided)

        """
        self.alpaca_manager = alpaca_manager
        self.pricing_service = pricing_service
        self.config = config or ExecutionConfig()

        # Initialize liquidity analyzer with adjusted thresholds
        self.liquidity_analyzer = LiquidityAnalyzer(
            min_volume_threshold=float(self.config.min_bid_ask_size),
            tick_size=float(self.config.bid_anchor_offset_cents),
        )

        # Track active orders for re-pegging
        self._active_orders: dict[str, SmartOrderRequest] = {}
        self._repeg_counts: dict[str, int] = {}
        self._order_placement_times: dict[str, datetime] = {}
        self._order_anchor_prices: dict[str, Decimal] = {}

    def should_place_order_now(self) -> bool:
        """Check if it's appropriate to place orders based on market timing.

        Returns:
            True if orders can be placed, False if market timing is poor

        """
        now = datetime.now(UTC)

        # Convert to ET for market timing
        et_time = now.replace(tzinfo=UTC).astimezone()
        current_time = et_time.time()

        # Check if we're in the restricted window (9:30-9:35am ET)
        market_open_time = dt_time(9, 30)  # 9:30am ET
        restricted_end_time = dt_time(
            9, 30 + self.config.market_open_delay_minutes
        )  # 9:35am ET

        if market_open_time <= current_time <= restricted_end_time:
            logger.info(
                f"⏰ Delaying order placement - within restricted window "
                f"({market_open_time} - {restricted_end_time} ET)"
            )
            return False

        return True

    def get_quote_with_validation(
        self, symbol: str, order_size: float
    ) -> tuple[QuoteModel, bool] | None:
        """Get validated quote data from streaming source, waiting for data.

        Waits for streaming quote data to arrive after subscription.

        Args:
            symbol: Stock symbol
            order_size: Size of order to place (in shares)

        Returns:
            (QuoteModel, False) if valid streaming quote available, otherwise None

        """
        import time

        # Only try streaming quote if pricing service available
        if not self.pricing_service:
            logger.warning(f"No pricing service available for {symbol}")
            return None

        # Wait for quote data to arrive from stream
        logger.info(f"⏳ Waiting for streaming quote data for {symbol}...")
        max_wait_time = 10.0  # Maximum 10 seconds to wait
        check_interval = 0.1  # Check every 100ms
        elapsed = 0.0

        quote = None
        while elapsed < max_wait_time:
            quote = self.pricing_service.get_quote_data(symbol)
            if quote:
                logger.info(
                    f"✅ Received streaming quote for {symbol} after {elapsed:.1f}s"
                )
                break

            time.sleep(check_interval)
            elapsed += check_interval

        if not quote:
            logger.error(
                f"❌ No streaming quote data received for {symbol} after {max_wait_time}s"
            )
            return None

        # Check quote freshness
        quote_age = (datetime.now(UTC) - quote.timestamp).total_seconds()
        if quote_age > self.config.quote_freshness_seconds:
            logger.warning(
                f"Streaming quote stale for {symbol} ({quote_age:.1f}s > {self.config.quote_freshness_seconds}s)"
            )
            return None

        # Simple price validation - just ensure we have at least one valid price
        if quote.bid_price <= 0 and quote.ask_price <= 0:
            logger.warning(
                f"Invalid prices for {symbol}: bid={quote.bid_price}, ask={quote.ask_price}"
            )
            return None

        return quote, False

    def _calculate_simple_inside_spread_price(
        self, quote: QuoteModel, side: str
    ) -> tuple[Decimal, dict[str, Any]]:
        """Compute a simple inside-spread anchor using configured offsets.

        This is used when we only have REST quotes or inadequate depth data.
        """
        bid = Decimal(str(max(quote.bid_price, 0.0)))
        ask = Decimal(str(max(quote.ask_price, 0.0)))
        mid = (bid + ask) / Decimal("2") if bid > 0 and ask > 0 else (bid or ask)

        # Minimum step as 1 cent for safety
        tick = Decimal("0.01")

        if side.upper() == "BUY":
            anchor = bid + max(self.config.bid_anchor_offset_cents, tick)
            # Ensure we stay inside the spread when possible
            if ask > 0 and anchor >= ask:
                anchor = max(ask - max(self.config.bid_anchor_offset_cents, tick), bid)
            # Use mid as soft cap
            if ask > 0 and bid > 0:
                anchor = min(anchor, mid)
        else:
            anchor = ask - max(self.config.ask_anchor_offset_cents, tick)
            if bid > 0 and anchor <= bid:
                anchor = min(ask, bid + max(self.config.ask_anchor_offset_cents, tick))
            if ask > 0 and bid > 0:
                anchor = max(anchor, mid)

        metadata = {
            "method": "simple_inside_spread",
            "mid": float(mid),
            "bid": float(bid),
            "ask": float(ask),
            "strategy_recommendation": "simple_inside_spread_fallback",
            "liquidity_score": 0.0,
            "volume_imbalance": 0.0,
            "confidence": 0.5,  # Conservative confidence for fallback
            "volume_available": 0.0,
            "volume_ratio": 0.0,
            "bid_volume": 0.0,
            "ask_volume": 0.0,
        }
        # Quantize to cent precision to avoid sub-penny errors
        anchor_quantized = anchor.quantize(Decimal("0.01"))
        return anchor_quantized, metadata

    def calculate_liquidity_aware_price(
        self, quote: QuoteModel, side: str, order_size: float
    ) -> tuple[Decimal, dict[str, Any]]:
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
        metadata = {
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

    async def place_smart_order(self, request: SmartOrderRequest) -> SmartOrderResult:
        """Place a smart limit order with liquidity anchoring.

        Args:
            request: Smart order request

        Returns:
            SmartOrderResult with placement details

        """
        logger.info(
            f"🎯 Placing smart {request.side} order: {request.quantity} {request.symbol} "
            f"(urgency: {request.urgency})"
        )

        # Check market timing
        if not self.should_place_order_now():
            return SmartOrderResult(
                success=False,
                error_message="Order delayed due to market timing restrictions",
                execution_strategy="smart_limit_delayed",
            )

        # Symbol should already be pre-subscribed by executor
        # Brief wait to allow any pending subscription to receive initial data
        import asyncio

        await asyncio.sleep(0.1)  # 100ms wait for quote data to flow

        try:
            # Get validated quote with order size, with retry logic
            order_size = float(request.quantity)
            quote = None
            used_fallback = False

            # Retry up to 3 times with increasing waits
            for attempt in range(3):
                validated = self.get_quote_with_validation(request.symbol, order_size)
                if validated:
                    quote, used_fallback = validated
                    break

                if attempt < 2:  # Don't wait on last attempt
                    await asyncio.sleep(0.3 * (attempt + 1))  # 300ms, 600ms waits

            if not quote:
                # Fallback to market order for high urgency
                if request.urgency == "HIGH":
                    logger.warning(
                        f"Quote validation failed for {request.symbol}, using market order fallback"
                    )
                    return await self._place_market_order_fallback(request)
                return SmartOrderResult(
                    success=False,
                    error_message=f"Quote validation failed for {request.symbol}",
                    execution_strategy="smart_limit_failed",
                )

            # Calculate optimal price: full liquidity analysis when streaming, simple when fallback
            if not used_fallback:
                optimal_price, analysis_metadata = self.calculate_liquidity_aware_price(
                    quote, request.side, order_size
                )
            else:
                optimal_price, analysis_metadata = (
                    self._calculate_simple_inside_spread_price(quote, request.side)
                )

            # Place limit order with optimal pricing
            # Ensure price is properly quantized to avoid sub-penny precision errors
            from decimal import Decimal
            quantized_price = Decimal(str(float(optimal_price))).quantize(Decimal("0.01"))
            
            result = self.alpaca_manager.place_limit_order(
                symbol=request.symbol,
                side=request.side.lower(),
                quantity=float(request.quantity),
                limit_price=float(quantized_price),
                time_in_force="day",
            )

            placement_time = datetime.now(UTC)

            if result.success and result.order_id:
                # Track for potential re-pegging
                self._active_orders[result.order_id] = request
                self._repeg_counts[result.order_id] = 0
                self._order_placement_times[result.order_id] = placement_time
                self._order_anchor_prices[result.order_id] = optimal_price

                logger.info(
                    f"✅ Smart liquidity-aware order placed: {result.order_id} at ${optimal_price} "
                    f"(strategy: {analysis_metadata['strategy_recommendation']}, "
                    f"confidence: {analysis_metadata['confidence']:.2f})"
                )

                # Schedule re-pegging monitoring for this order
                if self.config.fill_wait_seconds > 0:
                    logger.info(
                        f"⏰ Will monitor order {result.order_id} for re-pegging "
                        f"after {self.config.fill_wait_seconds}s"
                    )

                return SmartOrderResult(
                    success=True,
                    order_id=result.order_id,
                    final_price=optimal_price,
                    anchor_price=optimal_price,
                    repegs_used=0,
                    execution_strategy=f"smart_liquidity_{analysis_metadata['strategy_recommendation']}",
                    placement_timestamp=placement_time,
                    metadata={
                        **analysis_metadata,
                        "bid_price": quote.bid_price,
                        "ask_price": quote.ask_price,
                        "spread_percent": (quote.ask_price - quote.bid_price)
                        / quote.bid_price
                        * 100,
                        "bid_size": quote.bid_size,
                        "ask_size": quote.ask_size,
                        "used_fallback": used_fallback,
                    },
                )
            return SmartOrderResult(
                success=False,
                error_message=result.error or "Limit order placement failed",
                execution_strategy="smart_limit_failed",
                placement_timestamp=placement_time,
            )

        except Exception as e:
            logger.error(f"Error in smart order placement for {request.symbol}: {e}")
            return SmartOrderResult(
                success=False,
                error_message=str(e),
                execution_strategy="smart_limit_error",
            )
        finally:
            # Clean up subscription after order placement
            if self.pricing_service:
                self.pricing_service.unsubscribe_after_order(request.symbol)

    async def _place_market_order_fallback(
        self, request: SmartOrderRequest
    ) -> SmartOrderResult:
        """Fallback to market order for high urgency situations.

        Args:
            request: Original smart order request

        Returns:
            SmartOrderResult using market order execution

        """
        logger.info(f"📈 Using market order fallback for {request.symbol}")

        executed_order = self.alpaca_manager.place_market_order(
            symbol=request.symbol,
            side=request.side.lower(),
            qty=float(request.quantity),
            is_complete_exit=request.is_complete_exit,
        )

        if executed_order.status not in ["REJECTED", "CANCELED"]:
            return SmartOrderResult(
                success=True,
                order_id=executed_order.order_id,
                final_price=executed_order.price,
                execution_strategy="market_fallback",
                placement_timestamp=executed_order.execution_timestamp,
            )
        return SmartOrderResult(
            success=False,
            error_message=executed_order.error_message,
            execution_strategy="market_fallback_failed",
            placement_timestamp=executed_order.execution_timestamp,
        )

    async def check_and_repeg_orders(self) -> list[SmartOrderResult]:
        """Check active orders and repeg if they haven't filled after the wait period.

        Returns:
            List of re-pegging results

        """
        if not self._active_orders:
            return []

        repeg_results: list[SmartOrderResult] = []
        orders_to_remove = []
        current_time = datetime.now(UTC)

        for order_id, request in list(self._active_orders.items()):
            try:
                # Check if order is still active
                order_status = self.alpaca_manager._check_order_completion_status(order_id)
                if order_status in ["FILLED", "CANCELED", "REJECTED", "EXPIRED"]:
                    orders_to_remove.append(order_id)
                    logger.info(f"📊 Order {order_id} completed with status: {order_status}")
                    continue

                # Check if enough time has passed to consider re-pegging
                placement_time = self._order_placement_times.get(order_id)
                if not placement_time:
                    continue
                    
                time_elapsed = (current_time - placement_time).total_seconds()
                if time_elapsed < self.config.fill_wait_seconds:
                    logger.debug(
                        f"⏳ Order {order_id} waiting for fill "
                        f"({time_elapsed:.1f}s/{self.config.fill_wait_seconds}s)"
                    )
                    continue

                # Check if we've reached max re-pegs
                if self._repeg_counts[order_id] >= self.config.max_repegs_per_order:
                    logger.info(
                        f"⚠️ Order {order_id} reached max re-pegs "
                        f"({self.config.max_repegs_per_order}), leaving as-is"
                    )
                    continue

                # Attempt re-pegging
                logger.info(
                    f"🔄 Order {order_id} hasn't filled after {time_elapsed:.1f}s, "
                    "attempting re-peg..."
                )
                repeg_result = await self._attempt_repeg(order_id, request)
                
                if repeg_result:
                    repeg_results.append(repeg_result)

            except Exception as e:
                logger.error(f"Error checking order {order_id} for re-pegging: {e}")

        # Clean up completed orders
        for order_id in orders_to_remove:
            self._cleanup_order_tracking(order_id)

        return repeg_results

    async def _attempt_repeg(
        self, order_id: str, request: SmartOrderRequest
    ) -> SmartOrderResult | None:
        """Attempt to re-peg an order with a more aggressive price.
        
        Args:
            order_id: The order ID to re-peg
            request: Original order request
            
        Returns:
            SmartOrderResult if re-peg was attempted, None if skipped

        """
        try:
            # Cancel the existing order
            logger.info(f"❌ Canceling order {order_id} for re-pegging")
            cancel_success = self.alpaca_manager.cancel_order(order_id)
            
            if not cancel_success:
                logger.warning(f"⚠️ Failed to cancel order {order_id}, skipping re-peg")
                return None

            # Get current market data
            validated = self.get_quote_with_validation(
                request.symbol, float(request.quantity)
            )
            if not validated:
                logger.warning(f"⚠️ No valid quote for {request.symbol}, skipping re-peg")
                return None
                
            quote, _ = validated
            
            # Calculate more aggressive price for re-peg
            original_anchor = self._order_anchor_prices.get(order_id)
            new_price = self._calculate_repeg_price(quote, request.side, original_anchor)
            
            if not new_price:
                logger.warning(f"⚠️ Cannot calculate re-peg price for {request.symbol}")
                return None

            # Place new order with more aggressive pricing
            logger.info(
                f"📈 Re-pegging {request.symbol} {request.side} from "
                f"${original_anchor} to ${new_price}"
            )
            
            # Ensure price is properly quantized to avoid sub-penny precision errors
            quantized_price = new_price.quantize(Decimal("0.01"))
            
            executed_order = self.alpaca_manager.place_limit_order(
                symbol=request.symbol,
                side=request.side.lower(),
                quantity=float(request.quantity),
                limit_price=float(quantized_price),
                time_in_force="day",
            )

            # Update tracking
            self._repeg_counts[order_id] = self._repeg_counts.get(order_id, 0) + 1
            repeg_count = self._repeg_counts[order_id]
            
            if executed_order.order_id:
                # Update tracking with new order ID
                self._cleanup_order_tracking(order_id)
                self._active_orders[executed_order.order_id] = request
                self._repeg_counts[executed_order.order_id] = repeg_count
                self._order_placement_times[executed_order.order_id] = datetime.now(UTC)
                self._order_anchor_prices[executed_order.order_id] = new_price

                logger.info(
                    f"✅ Re-peg successful: new order {executed_order.order_id} "
                    f"at ${new_price} (attempt {repeg_count})"
                )
                
                return SmartOrderResult(
                    success=True,
                    order_id=executed_order.order_id,
                    final_price=new_price,
                    anchor_price=original_anchor,
                    repegs_used=repeg_count,
                    execution_strategy=f"smart_repeg_{repeg_count}",
                    placement_timestamp=datetime.now(UTC),
                    metadata={
                        "original_order_id": order_id,
                        "original_price": float(original_anchor) if original_anchor else None,
                        "new_price": float(new_price),
                        "bid_price": quote.bid_price,
                        "ask_price": quote.ask_price,
                    },
                )
            logger.error(f"❌ Re-peg failed for {request.symbol}: no order ID returned")
            return SmartOrderResult(
                success=False,
                error_message="Re-peg order placement failed",
                execution_strategy="smart_repeg_failed",
                repegs_used=repeg_count,
            )
                
        except Exception as e:
            logger.error(f"❌ Error during re-peg attempt for {order_id}: {e}")
            return SmartOrderResult(
                success=False,
                error_message=str(e),
                execution_strategy="smart_repeg_error",
            )

    def _calculate_repeg_price(
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
                    new_price = Decimal(str(quote.ask_price)) - self.config.ask_anchor_offset_cents
                    
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
                    new_price = Decimal(str(quote.bid_price)) + self.config.bid_anchor_offset_cents
                    
                # Ensure we don't go below bid price
                new_price = max(new_price, Decimal(str(quote.bid_price)))

            # Quantize to cent precision to avoid sub-penny errors
            return new_price.quantize(Decimal("0.01"))
            
        except Exception as e:
            logger.error(f"Error calculating re-peg price: {e}")
            return None

    def _cleanup_order_tracking(self, order_id: str) -> None:
        """Clean up tracking data for a completed order."""
        self._active_orders.pop(order_id, None)
        self._repeg_counts.pop(order_id, None)
        self._order_placement_times.pop(order_id, None)
        self._order_anchor_prices.pop(order_id, None)

    def get_active_order_count(self) -> int:
        """Get count of active orders being monitored."""
        return len(self._active_orders)

    def clear_completed_orders(self) -> None:
        """Clear tracking for completed orders."""
        self._active_orders.clear()
        self._repeg_counts.clear()
        self._order_placement_times.clear()
        self._order_anchor_prices.clear()

    def wait_for_quote_data(
        self, symbol: str, timeout: float | None = None
    ) -> dict[str, float | int] | None:
        """Wait for real-time quote data to be available.

        Args:
            symbol: Symbol to get quote for
            timeout: Maximum time to wait in seconds

        Returns:
            Quote data or None if timeout

        """
        timeout = timeout or self.max_wait_time
        start_time = time.time()

        # Initial quick check
        quote = self.pricing_service.get_latest_quote(symbol)
        if quote:
            logger.info(f"✅ Got immediate quote for {symbol}")
            return quote

        # Subscribe if not already subscribed
        if symbol not in self.pricing_service.get_subscribed_symbols():
            logger.info(f"📊 Subscribing to {symbol} for quote data")
            self.pricing_service.subscribe_for_order_placement(symbol)

            # Wait a bit for subscription to take effect
            time.sleep(1.0)  # Give stream time to restart if needed

        # Poll for quote data with exponential backoff
        check_interval = 0.1  # Start with 100ms
        max_interval = 1.0  # Cap at 1 second

        while time.time() - start_time < timeout:
            quote = self.pricing_service.get_latest_quote(symbol)
            if quote:
                logger.info(
                    f"✅ Got quote for {symbol} after {time.time() - start_time:.1f}s"
                )
                return quote

            time.sleep(check_interval)
            # Exponential backoff to reduce CPU usage
            check_interval = min(check_interval * 1.5, max_interval)

        logger.warning(
            f"⏱️ Timeout waiting for quote data for {symbol} after {timeout}s"
        )
        return None

    def validate_quote_liquidity(
        self, symbol: str, quote: dict[str, float | int]
    ) -> bool:
        """Validate that the quote has sufficient liquidity.

        Args:
            symbol: Symbol being validated
            quote: Quote data to validate

        Returns:
            True if quote passes validation

        """
        try:
            # Handle both dict and Quote object formats
            if isinstance(quote, dict):
                bid_price = quote.get("bid_price", 0)
                ask_price = quote.get("ask_price", 0)
                bid_size = quote.get("bid_size", 0)
                ask_size = quote.get("ask_size", 0)
            else:
                bid_price = getattr(quote, "bid_price", 0)
                ask_price = getattr(quote, "ask_price", 0)
                bid_size = getattr(quote, "bid_size", 0)
                ask_size = getattr(quote, "ask_size", 0)

            # Basic price validation
            if bid_price <= 0 or ask_price <= 0:
                logger.warning(
                    f"Invalid prices for {symbol}: bid={bid_price}, ask={ask_price}"
                )
                return False

            # Spread validation (max 0.5% spread for liquidity)
            spread = (ask_price - bid_price) / ask_price
            max_spread = 0.005  # 0.5%
            if spread > max_spread:
                logger.warning(
                    f"Spread too wide for {symbol}: {spread:.2%} > {max_spread:.2%}"
                )
                return False

            # Size validation (ensure minimum liquidity)
            min_size = 100  # Minimum 100 shares at bid/ask
            if bid_size < min_size or ask_size < min_size:
                logger.warning(
                    f"Insufficient liquidity for {symbol}: "
                    f"bid_size={bid_size}, ask_size={ask_size} < {min_size}"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating quote for {symbol}: {e}")
            return False

    def get_latest_quote(self, symbol: str) -> dict[str, float | int] | None:
        """Get the latest quote from the pricing service.

        Args:
            symbol: Symbol to get quote for

        Returns:
            Quote data or None if not available

        """
        # Try to get structured quote data first
        quote_data = self.pricing_service.get_quote_data(symbol)
        if quote_data:
            # Convert to dict format for compatibility
            return {
                "bid_price": quote_data.bid_price,
                "ask_price": quote_data.ask_price,
                "bid_size": quote_data.bid_size,
                "ask_size": quote_data.ask_size,
                "timestamp": quote_data.timestamp,
            }

        # Fallback to bid/ask spread
        spread = self.pricing_service.get_bid_ask_spread(symbol)
        if spread:
            bid, ask = spread
            return {
                "bid_price": bid,
                "ask_price": ask,
                "bid_size": 0,  # Unknown
                "ask_size": 0,  # Unknown
                "timestamp": datetime.now(UTC),
            }

        return None
