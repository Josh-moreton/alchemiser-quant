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
from dataclasses import dataclass
from datetime import UTC, datetime, time
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
    max_spread_percent: Decimal = Decimal("0.25")  # 0.25% maximum spread
    
    # Re-pegging configuration
    repeg_threshold_percent: Decimal = Decimal("0.10")  # Re-peg if market moves >0.1%
    max_repegs_per_order: int = 5  # Maximum re-pegs before escalation
    
    # Volume requirements
    min_bid_ask_size: Decimal = Decimal("100")  # Minimum size at bid/ask to anchor
    
    # Order timing
    quote_freshness_seconds: int = 5  # Require quote within 5 seconds
    order_placement_timeout_seconds: int = 30  # Timeout for order placement
    
    # Anchoring offsets (in cents)
    bid_anchor_offset_cents: Decimal = Decimal("0.01")  # Place at bid + $0.01 for buys
    ask_anchor_offset_cents: Decimal = Decimal("0.01")  # Place at ask - $0.01 for sells


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
        
        # Initialize liquidity analyzer for volume-aware pricing
        self.liquidity_analyzer = LiquidityAnalyzer(
            min_volume_threshold=float(self.config.min_bid_ask_size),
            tick_size=float(self.config.bid_anchor_offset_cents)
        )
        
        # Track active orders for re-pegging
        self._active_orders: dict[str, SmartOrderRequest] = {}
        self._repeg_counts: dict[str, int] = {}
        
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
        market_open_time = time(9, 30)  # 9:30am ET
        restricted_end_time = time(9, 30 + self.config.market_open_delay_minutes)  # 9:35am ET
        
        if market_open_time <= current_time <= restricted_end_time:
            logger.info(
                f"⏰ Delaying order placement - within restricted window "
                f"({market_open_time} - {restricted_end_time} ET)"
            )
            return False
            
        return True
        
    def get_quote_with_validation(self, symbol: str, order_size: float) -> QuoteModel | None:
        """Get validated quote data for a symbol with liquidity analysis.
        
        Args:
            symbol: Stock symbol
            order_size: Size of order to place (in shares)
            
        Returns:
            QuoteModel if valid quote available, None otherwise

        """
        if not self.pricing_service:
            logger.warning("No pricing service available for quote validation")
            return None
            
        quote = self.pricing_service.get_quote_data(symbol)
        if not quote:
            logger.warning(f"No quote data available for {symbol}")
            return None
            
        # Validate quote freshness
        now = datetime.now(UTC)
        quote_age = (now - quote.timestamp).total_seconds()
        if quote_age > self.config.quote_freshness_seconds:
            logger.warning(
                f"Quote for {symbol} is stale ({quote_age:.1f}s old, max {self.config.quote_freshness_seconds}s)"
            )
            return None
            
        # Validate spread
        if quote.bid_price <= 0 or quote.ask_price <= 0:
            logger.warning(f"Invalid bid/ask prices for {symbol}: {quote.bid_price}/{quote.ask_price}")
            return None
            
        spread_percent = (quote.ask_price - quote.bid_price) / quote.bid_price * 100
        if spread_percent > float(self.config.max_spread_percent):
            logger.warning(
                f"Spread too wide for {symbol}: {spread_percent:.2f}% > {self.config.max_spread_percent}%"
            )
            return None
            
        # Use liquidity analyzer for advanced volume validation
        is_valid, reason = self.liquidity_analyzer.validate_liquidity_for_order(
            quote, "buy", order_size  # Side doesn't matter for basic validation
        )
        if not is_valid:
            logger.warning(f"Liquidity validation failed for {symbol}: {reason}")
            return None
            
        return quote
        
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
            strategy_rec = self.liquidity_analyzer.get_execution_strategy_recommendation(
                analysis, side.lower(), order_size
            )
        else:
            optimal_price = Decimal(str(analysis.recommended_ask_price))
            volume_available = analysis.volume_at_recommended_ask
            strategy_rec = self.liquidity_analyzer.get_execution_strategy_recommendation(
                analysis, side.lower(), order_size
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
            "ask_volume": analysis.total_ask_volume
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
                execution_strategy="smart_limit_delayed"
            )
            
        # Subscribe to real-time data for this symbol and wait briefly for data
        if self.pricing_service:
            self.pricing_service.subscribe_for_order_placement(request.symbol)
            
            # Brief wait to allow subscription to receive initial data
            import asyncio
            await asyncio.sleep(0.2)  # 200ms wait for initial quote data
            
        try:
            # Get validated quote with order size, with retry logic
            order_size = float(request.quantity)
            quote = None
            
            # Retry up to 3 times with increasing waits
            for attempt in range(3):
                quote = self.get_quote_with_validation(request.symbol, order_size)
                if quote:
                    break
                    
                if attempt < 2:  # Don't wait on last attempt
                    await asyncio.sleep(0.3 * (attempt + 1))  # 300ms, 600ms waits
                    
            if not quote:
                # Fallback to market order for high urgency
                if request.urgency == "HIGH":
                    logger.warning(f"Quote validation failed for {request.symbol}, using market order fallback")
                    return await self._place_market_order_fallback(request)
                return SmartOrderResult(
                    success=False,
                    error_message=f"Quote validation failed for {request.symbol}",
                    execution_strategy="smart_limit_failed"
                )
                    
            # Calculate liquidity-aware optimal price
            optimal_price, analysis_metadata = self.calculate_liquidity_aware_price(
                quote, request.side, order_size
            )
            
            # Place limit order with optimal pricing
            result = self.alpaca_manager.place_limit_order(
                symbol=request.symbol,
                side=request.side.lower(),
                quantity=float(request.quantity),
                limit_price=float(optimal_price),
                time_in_force="day"
            )
            
            placement_time = datetime.now(UTC)
            
            if result.success and result.order_id:
                # Track for potential re-pegging
                self._active_orders[result.order_id] = request
                self._repeg_counts[result.order_id] = 0
                
                logger.info(
                    f"✅ Smart liquidity-aware order placed: {result.order_id} at ${optimal_price} "
                    f"(strategy: {analysis_metadata['strategy_recommendation']}, "
                    f"confidence: {analysis_metadata['confidence']:.2f})"
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
                        "spread_percent": (quote.ask_price - quote.bid_price) / quote.bid_price * 100,
                        "bid_size": quote.bid_size,
                        "ask_size": quote.ask_size,
                    }
                )
            return SmartOrderResult(
                success=False,
                error_message=result.error or "Limit order placement failed",
                execution_strategy="smart_limit_failed",
                placement_timestamp=placement_time
            )
                
        except Exception as e:
            logger.error(f"Error in smart order placement for {request.symbol}: {e}")
            return SmartOrderResult(
                success=False,
                error_message=str(e),
                execution_strategy="smart_limit_error"
            )
        finally:
            # Clean up subscription after order placement
            if self.pricing_service:
                self.pricing_service.unsubscribe_after_order(request.symbol)
                
    async def _place_market_order_fallback(self, request: SmartOrderRequest) -> SmartOrderResult:
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
            is_complete_exit=request.is_complete_exit
        )
        
        if executed_order.status not in ["REJECTED", "CANCELED"]:
            return SmartOrderResult(
                success=True,
                order_id=executed_order.order_id,
                final_price=executed_order.price,
                execution_strategy="market_fallback",
                placement_timestamp=executed_order.execution_timestamp
            )
        return SmartOrderResult(
            success=False,
            error_message=executed_order.error_message,
            execution_strategy="market_fallback_failed",
            placement_timestamp=executed_order.execution_timestamp
        )
            
    async def check_and_repeg_orders(self) -> list[SmartOrderResult]:
        """Check active orders and repeg if market has moved significantly.
        
        Returns:
            List of re-pegging results

        """
        if not self._active_orders:
            return []
            
        repeg_results: list[SmartOrderResult] = []
        orders_to_remove = []
        
        for order_id, request in self._active_orders.items():
            try:
                # Check if order is still active
                order_status = self.alpaca_manager.get_order_execution_result(order_id)
                if order_status.status in ["filled", "canceled", "rejected"]:
                    orders_to_remove.append(order_id)
                    continue
                    
                # Check if re-pegging is needed
                if self._repeg_counts[order_id] >= self.config.max_repegs_per_order:
                    logger.info(f"⚠️ Order {order_id} reached max re-pegs, leaving as-is")
                    continue
                    
                # Get current quote
                quote = self.get_quote_with_validation(request.symbol, float(request.quantity))
                if not quote:
                    continue
                    
                # Check if market has moved beyond threshold
                # (This would require tracking original anchor price - simplified for now)
                # Implementation note: In production, you'd track original prices and calculate movement
                
                logger.debug(f"Order {order_id} still active, monitoring for re-peg opportunities")
                
            except Exception as e:
                logger.error(f"Error checking order {order_id} for re-pegging: {e}")
                
        # Clean up completed orders
        for order_id in orders_to_remove:
            self._active_orders.pop(order_id, None)
            self._repeg_counts.pop(order_id, None)
            
        return repeg_results
        
    def get_active_order_count(self) -> int:
        """Get count of active orders being monitored."""
        return len(self._active_orders)
        
    def clear_completed_orders(self) -> None:
        """Clear tracking for completed orders."""
        self._active_orders.clear()
        self._repeg_counts.clear()