"""Business Unit: execution | Status: current.

Smart execution strategy orchestrator.

This module provides the main SmartExecutionStrategy class that coordinates
all the extracted components to provide intelligent order placement and execution.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from decimal import Decimal

from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.services.real_time_pricing import RealTimePricingService

from .market_timing import should_place_order_now
from .models import (
    ExecutionConfig,
    LiquidityMetadata,
    SmartOrderRequest,
    SmartOrderResult,
)
from .pricing import PricingCalculator
from .quotes import QuoteProvider
from .repeg import RepegManager
from .tracking import OrderTracker

logger = logging.getLogger(__name__)


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

        # Initialize components
        self.quote_provider = QuoteProvider(
            alpaca_manager=alpaca_manager,
            pricing_service=pricing_service,
            config=self.config,
        )
        self.pricing_calculator = PricingCalculator(config=self.config)
        self.order_tracker = OrderTracker()
        self.repeg_manager = RepegManager(
            alpaca_manager=alpaca_manager,
            quote_provider=self.quote_provider,
            pricing_calculator=self.pricing_calculator,
            order_tracker=self.order_tracker,
            config=self.config,
        )

    def should_place_order_now(self) -> bool:
        """Check if it's appropriate to place orders based on market timing.

        Returns:
            True if orders can be placed, False if market timing is poor

        """
        return should_place_order_now(self.config)

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
        await asyncio.sleep(0.1)  # 100ms wait for quote data to flow

        try:
            # Get validated quote with order size, with retry logic
            order_size = float(request.quantity)
            quote = None
            used_fallback = False

            # Retry up to 3 times with increasing waits
            for attempt in range(3):
                validated = self.quote_provider.get_quote_with_validation(
                    request.symbol, order_size
                )
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
                optimal_price, analysis_metadata = (
                    self.pricing_calculator.calculate_liquidity_aware_price(
                        quote, request.side, order_size
                    )
                )
            else:
                optimal_price, analysis_metadata = (
                    self.pricing_calculator.calculate_simple_inside_spread_price(
                        quote, request.side
                    )
                )

            # Validate optimal price before proceeding
            if optimal_price <= 0:
                logger.error(
                    f"⚠️ Invalid optimal price ${optimal_price} calculated for {request.symbol} {request.side}. "
                    f"This should not happen after validation - falling back to market order."
                )
                if request.urgency == "HIGH":
                    return await self._place_market_order_fallback(request)
                return SmartOrderResult(
                    success=False,
                    error_message=f"Invalid optimal price calculated for {request.symbol}",
                    execution_strategy="smart_limit_failed",
                )

            # Place limit order with optimal pricing
            # Ensure price is properly quantized to avoid sub-penny precision errors
            quantized_price = Decimal(str(float(optimal_price))).quantize(
                Decimal("0.01")
            )

            # Final validation before placing order
            if quantized_price <= 0:
                logger.error(
                    f"⚠️ Quantized optimal price ${quantized_price} is invalid for {request.symbol}. "
                    f"This should not happen after validation - falling back to market order."
                )
                if request.urgency == "HIGH":
                    return await self._place_market_order_fallback(request)
                return SmartOrderResult(
                    success=False,
                    error_message=f"Invalid quantized price calculated for {request.symbol}",
                    execution_strategy="smart_limit_failed",
                )

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
                self.order_tracker.add_order(
                    result.order_id, request, placement_time, optimal_price
                )

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

                metadata_dict: LiquidityMetadata = {
                    **analysis_metadata,
                    "bid_price": quote.bid_price,
                    "ask_price": quote.ask_price,
                    "spread_percent": (quote.ask_price - quote.bid_price)
                    / quote.bid_price
                    * 100,
                    "bid_size": quote.bid_size,
                    "ask_size": quote.ask_size,
                    "used_fallback": used_fallback,
                }
                return SmartOrderResult(
                    success=True,
                    order_id=result.order_id,
                    final_price=optimal_price,
                    anchor_price=optimal_price,
                    repegs_used=0,
                    execution_strategy=f"smart_liquidity_{analysis_metadata['strategy_recommendation']}",
                    placement_timestamp=placement_time,
                    metadata=metadata_dict,
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
            self.quote_provider.cleanup_subscription(request.symbol)

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
        return await self.repeg_manager.check_and_repeg_orders()

    def get_active_order_count(self) -> int:
        """Get count of active orders being monitored.

        Returns:
            Number of active orders

        """
        return self.order_tracker.get_active_order_count()

    def clear_completed_orders(self) -> None:
        """Clear tracking for completed orders."""
        self.order_tracker.clear_completed_orders()

    # Legacy methods for backwards compatibility
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
        return self.quote_provider.wait_for_quote_data(symbol, timeout)

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
        return self.quote_provider.validate_quote_liquidity(symbol, quote)

    def get_latest_quote(self, symbol: str) -> dict[str, float | int] | None:
        """Get the latest quote from the pricing service.

        Args:
            symbol: Symbol to get quote for

        Returns:
            Quote data or None if not available

        """
        return self.quote_provider.get_latest_quote(symbol)
