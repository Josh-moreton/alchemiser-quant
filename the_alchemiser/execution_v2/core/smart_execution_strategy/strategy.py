"""Business Unit: execution | Status: current.

Smart execution strategy orchestrator.

This module provides the main SmartExecutionStrategy class that coordinates
all the extracted components to provide intelligent order placement and execution.
"""

from __future__ import annotations

import asyncio
import warnings
from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from structlog.stdlib import BoundLogger

from the_alchemiser.execution_v2.errors import (
    ExecutionTimeoutError,
    ExecutionValidationError,
    OrderPlacementError,
    QuoteValidationError,
)
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

logger: BoundLogger = get_logger(__name__)


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
            "Placing smart order",
            extra={
                "symbol": request.symbol,
                "side": request.side,
                "quantity": str(request.quantity),
                "urgency": request.urgency,
                "correlation_id": request.correlation_id,
            },
        )

        # Preflight validation for non-fractionable assets
        side_normalized = request.side.lower()
        if side_normalized not in ("buy", "sell"):
            logger.error(
                "Invalid order side",
                extra={
                    "symbol": request.symbol,
                    "side": request.side,
                    "correlation_id": request.correlation_id,
                },
            )
            return SmartOrderResult(
                success=False,
                error_message=f"Invalid side: {request.side}. Must be 'buy' or 'sell'",
                execution_strategy="validation_failed",
            )

        validation_result = self.validator.validate_order(
            symbol=request.symbol,
            quantity=request.quantity,
            correlation_id=request.correlation_id,
            auto_adjust=True,
        )

        if not validation_result.is_valid:
            error_msg = validation_result.error_message or f"Validation failed for {request.symbol}"
            logger.error(
                "Preflight validation failed",
                extra={
                    "symbol": request.symbol,
                    "error_message": error_msg,
                    "correlation_id": request.correlation_id,
                },
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
                "Adjusted order quantity",
                extra={
                    "symbol": request.symbol,
                    "original_quantity": str(original_quantity),
                    "adjusted_quantity": str(request.quantity),
                    "correlation_id": request.correlation_id,
                },
            )

        # Log any warnings from validation
        for warning in validation_result.warnings:
            logger.warning(
                "Order validation warning",
                extra={
                    "warning": warning,
                    "symbol": request.symbol,
                    "correlation_id": request.correlation_id,
                },
            )

        # Symbol should already be pre-subscribed by executor
        # Brief wait to allow any pending subscription to receive initial data
        await asyncio.sleep(
            self.config.quote_wait_milliseconds / 1000.0
        )  # Configurable wait for quote data

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

        except ExecutionTimeoutError as e:
            logger.error(
                "Smart order placement timeout",
                extra={
                    "symbol": request.symbol,
                    "error": str(e),
                    "correlation_id": request.correlation_id,
                },
            )
            return SmartOrderResult(
                success=False,
                error_message=f"Order placement timed out: {e}",
                execution_strategy="smart_limit_timeout",
            )
        except (ExecutionValidationError, QuoteValidationError) as e:
            logger.error(
                "Smart order validation error",
                extra={
                    "symbol": request.symbol,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "correlation_id": request.correlation_id,
                },
            )
            return SmartOrderResult(
                success=False,
                error_message=str(e),
                execution_strategy="smart_limit_validation_error",
            )
        except OrderPlacementError as e:
            logger.error(
                "Smart order placement error",
                extra={
                    "symbol": request.symbol,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "correlation_id": request.correlation_id,
                },
            )
            return SmartOrderResult(
                success=False,
                error_message=str(e),
                execution_strategy="smart_limit_error",
            )
        except Exception as e:
            # Catch-all for unexpected errors - log with full context for debugging
            logger.error(
                "Unexpected error in smart order placement",
                extra={
                    "symbol": request.symbol,
                    "error": str(e),
                    "error_type": type(e).__name__,
                    "correlation_id": request.correlation_id,
                },
            )
            # Re-raise as OrderPlacementError for consistent error handling upstream
            raise OrderPlacementError(
                f"Unexpected error during order placement: {e}",
                correlation_id=request.correlation_id,
                context={"symbol": request.symbol, "original_error": str(e)},
            ) from e
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

        # Retry up to 3 times with configurable waits
        retry_intervals = self.config.quote_retry_intervals_ms
        for attempt in range(3):
            validated = self.quote_provider.get_quote_with_validation(request.symbol)
            if validated:
                quote, used_fallback = validated
                break

            if attempt < 2:  # Don't wait on last attempt
                wait_ms = (
                    retry_intervals[attempt]
                    if attempt < len(retry_intervals)
                    else retry_intervals[-1]
                )
                await asyncio.sleep(wait_ms / 1000.0)

        return quote, used_fallback

    def _handle_quote_validation_failure(self, request: SmartOrderRequest) -> SmartOrderResult:
        """Handle case where quote validation fails.

        Args:
            request: Original smart order request

        Returns:
            SmartOrderResult (either market fallback or failure)

        """
        # Fallback to market order for high urgency
        if request.urgency == "HIGH":
            logger.warning(
                "Quote validation failed, using market order fallback",
                extra={
                    "symbol": request.symbol,
                    "urgency": request.urgency,
                    "correlation_id": request.correlation_id,
                },
            )
            # Return a task that can be awaited by the caller
            return self._create_market_fallback_result(request)

        return SmartOrderResult(
            success=False,
            error_message=f"Quote validation failed for {request.symbol}",
            execution_strategy="smart_limit_failed",
        )

    def _create_market_fallback_result(self, request: SmartOrderRequest) -> SmartOrderResult:
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
        # Keep quantity as Decimal for precision
        order_size = request.quantity

        # Calculate optimal price: full liquidity analysis when streaming, simple when fallback
        if not used_fallback:
            return self.pricing_calculator.calculate_liquidity_aware_price(
                quote, request.side, order_size
            )
        return self.pricing_calculator.calculate_simple_inside_spread_price(quote, request.side)

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
                "Invalid optimal price calculated",
                extra={
                    "symbol": request.symbol,
                    "side": request.side,
                    "optimal_price": str(optimal_price),
                    "correlation_id": request.correlation_id,
                },
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

    async def _handle_invalid_price_fallback(self, request: SmartOrderRequest) -> SmartOrderResult:
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

    def _prepare_final_price(self, optimal_price: Decimal, request: SmartOrderRequest) -> Decimal:
        """Prepare final price with quantization and validation.

        Args:
            optimal_price: Optimal price from calculation
            request: Smart order request for logging

        Returns:
            Quantized and validated price

        """
        # Quantize directly without float conversion to maintain precision
        quantized_price = optimal_price.quantize(Decimal("0.01"))

        # Final validation before placing order
        if quantized_price <= 0:
            logger.error(
                "Invalid quantized price",
                extra={
                    "symbol": request.symbol,
                    "quantized_price": str(quantized_price),
                    "original_price": str(optimal_price),
                    "correlation_id": request.correlation_id,
                },
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
        # Use asyncio.to_thread to make blocking I/O async with timeout
        try:
            # NOTE: Float conversion required by broker API
            # AlpacaManager.place_limit_order signature requires float for quantity and limit_price
            # as per Alpaca SDK requirements (lines 520-521 in alpaca_manager.py).
            # This is a known limitation of the broker API that cannot be changed.
            # Precision loss is minimal for typical stock quantities (< 0.000001 shares).
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    self.alpaca_manager.place_limit_order,
                    symbol=request.symbol,
                    side=request.side.lower(),
                    quantity=float(request.quantity),  # Broker API requires float
                    limit_price=float(quantized_price),  # Broker API requires float
                    time_in_force="day",
                ),
                timeout=self.config.order_placement_timeout_seconds,
            )
        except TimeoutError:
            logger.error(
                "Order placement timeout",
                extra={
                    "symbol": request.symbol,
                    "timeout_seconds": self.config.order_placement_timeout_seconds,
                    "correlation_id": request.correlation_id,
                },
            )
            return SmartOrderResult(
                success=False,
                error_message=f"Order placement timed out after {self.config.order_placement_timeout_seconds}s",
                execution_strategy="smart_limit_timeout",
                placement_timestamp=datetime.now(UTC),
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
        self.order_tracker.add_order(result.order_id, request, placement_time, optimal_price)

        logger.info(
            "Smart order placed successfully",
            extra={
                "order_id": result.order_id,
                "price": str(optimal_price),
                "strategy": analysis_metadata["strategy_recommendation"],
                "confidence": analysis_metadata["confidence"],
                "correlation_id": request.correlation_id,
            },
        )

        # Schedule re-pegging monitoring for this order
        if self.config.fill_wait_seconds > 0:
            logger.info(
                "Monitoring order for re-pegging",
                extra={
                    "order_id": result.order_id,
                    "fill_wait_seconds": self.config.fill_wait_seconds,
                    "correlation_id": request.correlation_id,
                },
            )

        # Calculate spread percent with zero-check
        spread_percent = 0.0
        if quote.bid_price > 0:
            spread_percent = float((quote.ask_price - quote.bid_price) / quote.bid_price * 100)

        metadata_dict: LiquidityMetadata = {
            **analysis_metadata,
            "bid_price": float(quote.bid_price),
            "ask_price": float(quote.ask_price),
            "spread_percent": spread_percent,
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

    async def _place_market_order_fallback(self, request: SmartOrderRequest) -> SmartOrderResult:
        """Fallback to market order for high urgency situations.

        Args:
            request: Original smart order request

        Returns:
            SmartOrderResult using market order execution

        """
        logger.info(
            "Using market order fallback",
            extra={
                "symbol": request.symbol,
                "correlation_id": request.correlation_id,
            },
        )

        # Use asyncio.to_thread to make blocking I/O async
        # NOTE: place_market_order accepts Decimal for qty (line 489 in alpaca_manager.py)
        executed_order = await asyncio.to_thread(
            self.alpaca_manager.place_market_order,
            symbol=request.symbol,
            side=request.side.lower(),
            qty=request.quantity,  # Decimal is accepted by broker API
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

        .. deprecated::
            This method is deprecated and will be removed in a future version.
            Use the internal quote provider directly or place_smart_order instead.

        Args:
            symbol: Symbol to get quote for
            timeout: Maximum time to wait in seconds

        Returns:
            Quote data or None if timeout

        """
        warnings.warn(
            "wait_for_quote_data is deprecated and will be removed in a future version",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.quote_provider.wait_for_quote_data(symbol, timeout)

    def validate_quote_liquidity(self, symbol: str, quote: dict[str, float | int]) -> bool:
        """Validate that the quote has sufficient liquidity.

        .. deprecated::
            This method is deprecated and will be removed in a future version.
            Use the internal quote provider directly or place_smart_order instead.

        Args:
            symbol: Symbol being validated
            quote: Quote data to validate

        Returns:
            True if quote passes validation

        """
        warnings.warn(
            "validate_quote_liquidity is deprecated and will be removed in a future version",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.quote_provider.validate_quote_liquidity(symbol, quote)

    def get_latest_quote(self, symbol: str) -> dict[str, float | int] | None:
        """Get the latest quote from the pricing service.

        .. deprecated::
            This method is deprecated and will be removed in a future version.
            Use the internal quote provider directly or place_smart_order instead.

        Args:
            symbol: Symbol to get quote for

        Returns:
            Quote data or None if not available

        """
        warnings.warn(
            "get_latest_quote is deprecated and will be removed in a future version",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.quote_provider.get_latest_quote(symbol)
