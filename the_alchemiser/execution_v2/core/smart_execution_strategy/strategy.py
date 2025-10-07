"""Business Unit: execution | Status: current.

Smart execution strategy orchestrator.

This module provides the main SmartExecutionStrategy class that coordinates
all the extracted components to provide intelligent order placement and execution.
"""

from __future__ import annotations

import asyncio
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

from the_alchemiser.execution_v2.utils.execution_validator import ExecutionValidator
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.services.real_time_pricing import RealTimePricingService
from the_alchemiser.shared.types.market_data import QuoteModel

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

logger = get_logger(__name__)


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

        # Initialize execution validator for preflight checks
        self.validator = ExecutionValidator(alpaca_manager)

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

        # Preflight validation for non-fractionable assets
        validation_result = self.validator.validate_order(
            symbol=request.symbol,
            quantity=Decimal(str(request.quantity)),
            side=request.side,
            correlation_id=getattr(request, "correlation_id", None),
            auto_adjust=True,
        )

        if not validation_result.is_valid:
            error_msg = (
                validation_result.error_message
                or f"Validation failed for {request.symbol}"
            )
            logger.error(
                f"❌ Preflight validation failed for {request.symbol}: {error_msg}"
            )
            return SmartOrderResult(
                success=False,
                error_message=error_msg,
                execution_strategy="validation_failed",
            )

        # Use adjusted quantity if validation made changes
        if validation_result.adjusted_quantity is not None:
            # Update request with adjusted quantity without float conversion
            original_quantity = request.quantity
            request = replace(request, quantity=validation_result.adjusted_quantity)
            logger.info(
                f"🔄 Adjusted quantity for {request.symbol}: {original_quantity} → {request.quantity}"
            )

        # Log any warnings from validation
        for warning in validation_result.warnings:
            logger.warning(f"⚠️ Smart order validation: {warning}")

        # Symbol should already be pre-subscribed by executor
        # Brief wait to allow any pending subscription to receive initial data
        await asyncio.sleep(0.1)  # 100ms wait for quote data to flow

        try:
            # Get validated quote with retry logic
            quote, used_fallback = await self._get_validated_quote_with_retry(request)
            if not quote:
                # Handle quote validation failure (may trigger market fallback)
                failure_result = self._handle_quote_validation_failure(request)
                if failure_result.execution_strategy == "market_fallback_required":
                    return await self._place_market_order_fallback(request)
                return failure_result

            # Calculate optimal price based on quote source
            optimal_price, analysis_metadata = self._calculate_optimal_price(
                quote, request, used_fallback=used_fallback
            )

            # Validate and place the order
            return await self._place_validated_order(
                request,
                optimal_price,
                analysis_metadata,
                quote,
                used_fallback=used_fallback,
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

    async def _get_validated_quote_with_retry(
        self, request: SmartOrderRequest
    ) -> tuple[QuoteModel | None, bool]:
        """Get validated quote with retry logic.

        Args:
            request: Smart order request

        Returns:
            Tuple of (quote, used_fallback) or (None, False) if failed

        """
        quote = None
        used_fallback = False

        # Retry up to 3 times with increasing waits
        for attempt in range(3):
            validated = self.quote_provider.get_quote_with_validation(request.symbol)
            if validated:
                quote, used_fallback = validated
                break

            if attempt < 2:  # Don't wait on last attempt
                await asyncio.sleep(0.3 * (attempt + 1))  # 300ms, 600ms waits

        return quote, used_fallback

    def _handle_quote_validation_failure(
        self, request: SmartOrderRequest
    ) -> SmartOrderResult:
        """Handle case where quote validation fails.

        Args:
            request: Original smart order request

        Returns:
            SmartOrderResult (either market fallback or failure)

        """
        # Fallback to market order for high urgency
        if request.urgency == "HIGH":
            logger.warning(
                f"Quote validation failed for {request.symbol}, using market order fallback"
            )
            # Return a task that can be awaited by the caller
            return self._create_market_fallback_result(request)

        return SmartOrderResult(
            success=False,
            error_message=f"Quote validation failed for {request.symbol}",
            execution_strategy="smart_limit_failed",
        )

    def _create_market_fallback_result(
        self, request: SmartOrderRequest
    ) -> SmartOrderResult:
        """Create a market fallback result that indicates need for async processing.

        Args:
            request: Original smart order request

        Returns:
            SmartOrderResult indicating market fallback needed

        """
        return SmartOrderResult(
            success=False,
            error_message=f"Quote validation failed for {request.symbol}, market fallback required",
            execution_strategy="market_fallback_required",
        )

    def _calculate_optimal_price(
        self, quote: QuoteModel, request: SmartOrderRequest, *, used_fallback: bool
    ) -> tuple[Decimal, LiquidityMetadata]:
        """Calculate optimal price based on quote source and order details.

        Args:
            quote: Validated quote
            request: Smart order request
            used_fallback: Whether REST fallback was used

        Returns:
            Tuple of (optimal_price, analysis_metadata)

        """
        order_size = float(request.quantity)

        # Calculate optimal price: full liquidity analysis when streaming, simple when fallback
        if not used_fallback:
            return self.pricing_calculator.calculate_liquidity_aware_price(
                quote, request.side, order_size
            )
        return self.pricing_calculator.calculate_simple_inside_spread_price(
            quote, request.side
        )

    async def _place_validated_order(
        self,
        request: SmartOrderRequest,
        optimal_price: Decimal,
        analysis_metadata: LiquidityMetadata,
        quote: QuoteModel,
        *,
        used_fallback: bool,
    ) -> SmartOrderResult:
        """Validate optimal price and place the order.

        Args:
            request: Smart order request
            optimal_price: Calculated optimal price
            analysis_metadata: Pricing analysis metadata
            quote: Market quote
            used_fallback: Whether REST fallback was used

        Returns:
            SmartOrderResult with placement details

        """
        # Validate optimal price before proceeding
        if optimal_price <= 0:
            logger.error(
                f"⚠️ Invalid optimal price ${optimal_price} calculated for {request.symbol} {request.side}. "
                f"This should not happen after validation - falling back to market order."
            )
            return await self._handle_invalid_price_fallback(request)

        # Ensure price is properly quantized and validated
        quantized_price = self._prepare_final_price(optimal_price, request)
        if quantized_price <= 0:
            return await self._handle_invalid_price_fallback(request)

        # Place the actual limit order
        return await self._execute_limit_order(
            request,
            quantized_price,
            optimal_price,
            analysis_metadata,
            quote,
            used_fallback=used_fallback,
        )

    async def _handle_invalid_price_fallback(
        self, request: SmartOrderRequest
    ) -> SmartOrderResult:
        """Handle invalid price by falling back to market order if urgency is high.

        Args:
            request: Original smart order request

        Returns:
            SmartOrderResult

        """
        if request.urgency == "HIGH":
            return await self._place_market_order_fallback(request)

        return SmartOrderResult(
            success=False,
            error_message=f"Invalid optimal price calculated for {request.symbol}",
            execution_strategy="smart_limit_failed",
        )

    def _prepare_final_price(
        self, optimal_price: Decimal, request: SmartOrderRequest
    ) -> Decimal:
        """Prepare final price with quantization and validation.

        Args:
            optimal_price: Optimal price from calculation
            request: Smart order request for logging

        Returns:
            Quantized and validated price

        """
        # Ensure price is properly quantized to avoid sub-penny precision errors
        quantized_price = Decimal(str(float(optimal_price))).quantize(Decimal("0.01"))

        # Final validation before placing order
        if quantized_price <= 0:
            logger.error(
                f"⚠️ Quantized optimal price ${quantized_price} is invalid for {request.symbol}. "
                f"This should not happen after validation - falling back to market order."
            )

        return quantized_price

    async def _execute_limit_order(
        self,
        request: SmartOrderRequest,
        quantized_price: Decimal,
        optimal_price: Decimal,
        analysis_metadata: LiquidityMetadata,
        quote: QuoteModel,
        *,
        used_fallback: bool,
    ) -> SmartOrderResult:
        """Execute the limit order and handle the result.

        Args:
            request: Smart order request
            quantized_price: Final quantized price
            optimal_price: Original optimal price
            analysis_metadata: Pricing analysis metadata
            quote: Market quote
            used_fallback: Whether REST fallback was used

        Returns:
            SmartOrderResult with placement details

        """
        # Use asyncio.to_thread to make blocking I/O async
        result = await asyncio.to_thread(
            self.alpaca_manager.place_limit_order,
            symbol=request.symbol,
            side=request.side.lower(),
            quantity=float(request.quantity),
            limit_price=float(quantized_price),
            time_in_force="day",
        )

        placement_time = datetime.now(UTC)

        if result.success and result.order_id:
            return self._handle_successful_placement(
                result,
                request,
                placement_time,
                optimal_price,
                analysis_metadata,
                quote,
                used_fallback=used_fallback,
            )
        return SmartOrderResult(
            success=False,
            error_message=result.error or "Limit order placement failed",
            execution_strategy="smart_limit_failed",
            placement_timestamp=placement_time,
        )

    def _handle_successful_placement(
        self,
        result: Any,  # noqa: ANN401 # Broker-specific result type
        request: SmartOrderRequest,
        placement_time: datetime,
        optimal_price: Decimal,
        analysis_metadata: LiquidityMetadata,
        quote: QuoteModel,
        *,
        used_fallback: bool,
    ) -> SmartOrderResult:
        """Handle successful order placement.

        Args:
            result: Broker result
            request: Smart order request
            placement_time: When order was placed
            optimal_price: Optimal price used
            analysis_metadata: Pricing analysis metadata
            quote: Market quote
            used_fallback: Whether REST fallback was used

        Returns:
            SmartOrderResult with success details

        """
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
            "bid_price": float(quote.bid_price),
            "ask_price": float(quote.ask_price),
            "spread_percent": float(
                (quote.ask_price - quote.bid_price) / quote.bid_price * 100
            ),
            "bid_size": float(quote.bid_size),
            "ask_size": float(quote.ask_size),
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

        # Use asyncio.to_thread to make blocking I/O async
        executed_order = await asyncio.to_thread(
            self.alpaca_manager.place_market_order,
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
