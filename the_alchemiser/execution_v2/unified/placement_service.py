"""Business Unit: execution | Status: current.

Unified order placement service - single entry point for all order placement.

This service orchestrates the entire order placement flow:
1. Quote acquisition (streaming-first with REST fallback)
2. Order type routing (market vs walk-the-book based on urgency)
3. Execution monitoring and progression
4. Portfolio validation after execution
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.execution_v2.utils.execution_validator import ExecutionValidator
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.utils.order_id_utils import generate_client_order_id

if TYPE_CHECKING:
    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
    from the_alchemiser.shared.schemas.execution_report import ExecutedOrder
    from the_alchemiser.shared.services.real_time_pricing import RealTimePricingService

    from .order_intent import OrderIntent
    from .portfolio_validator import ValidationResult
    from .quote_service import QuoteResult
    from .walk_the_book import WalkResult

from .order_intent import Urgency
from .portfolio_validator import PortfolioValidator
from .quote_service import UnifiedQuoteService
from .walk_the_book import WalkTheBookStrategy

logger = get_logger(__name__)


@dataclass(frozen=True)
class ExecutionResult:
    """Result of unified order placement.

    Attributes:
        success: Whether order was successfully placed and filled
        intent: Original order intent
        quote_result: Quote that was used for pricing
        walk_result: Result of walk-the-book execution (if used)
        validation_result: Portfolio validation result (if performed)
        execution_strategy: Which strategy was used
        total_filled: Total quantity filled
        avg_fill_price: Average fill price
        final_order_id: Final Alpaca order ID
        execution_time_seconds: Total execution time
        error_message: Error message if failed

    """

    success: bool
    intent: OrderIntent
    quote_result: QuoteResult | None
    walk_result: WalkResult | None
    validation_result: ValidationResult | None
    execution_strategy: str
    total_filled: Decimal
    avg_fill_price: Decimal | None
    final_order_id: str | None
    execution_time_seconds: float
    error_message: str | None = None

    def describe(self) -> str:
        """Human-readable description of execution result."""
        if not self.success:
            return f"❌ Execution failed: {self.error_message}"

        strategy_desc = {
            "market_immediate": "market order",
            "walk_the_book": f"walk-the-book ({self.walk_result.num_steps_used} steps)"
            if self.walk_result
            else "walk-the-book",
        }.get(self.execution_strategy, self.execution_strategy)

        price_str = f" @ ${self.avg_fill_price:.2f}" if self.avg_fill_price else ""

        return f"✅ {self.intent.describe()} filled {self.total_filled} shares{price_str} via {strategy_desc} in {self.execution_time_seconds:.1f}s"


class UnifiedOrderPlacementService:
    """Single, unified order placement service.

    This is the ONLY entry point for order placement in the system.
    It provides:
    - Single quote acquisition path (streaming-first with REST fallback)
    - Clear order intent abstractions (BUY/SELL_PARTIAL/SELL_FULL)
    - Explicit walk-the-book strategy or immediate market orders
    - Portfolio validation after execution
    - Full audit trail of execution

    Thread Safety:
        This class is not thread-safe. Use from a single async context.

    """

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        pricing_service: RealTimePricingService | None = None,
        *,
        enable_validation: bool = True,
    ) -> None:
        """Initialize unified order placement service.

        Args:
            alpaca_manager: Alpaca broker manager
            pricing_service: Real-time pricing service (optional)
            enable_validation: Whether to validate portfolio after execution

        """
        self.alpaca_manager = alpaca_manager
        self.enable_validation = enable_validation

        # Initialize components
        self.quote_service = UnifiedQuoteService(
            alpaca_manager=alpaca_manager,
            pricing_service=pricing_service,
        )

        self.walk_strategy = WalkTheBookStrategy(
            alpaca_manager=alpaca_manager,
        )

        self.validator = PortfolioValidator(
            alpaca_manager=alpaca_manager,
        )

        self.execution_validator = ExecutionValidator(alpaca_manager)

        logger.info(
            "UnifiedOrderPlacementService initialized",
            has_streaming=pricing_service is not None,
            validation_enabled=enable_validation,
        )

    async def place_order(self, intent: OrderIntent) -> ExecutionResult:
        """Place an order with unified flow.

        This is the single entry point for ALL order placement.

        Args:
            intent: Order intent specifying what to execute

        Returns:
            ExecutionResult with full execution details

        """
        start_time = datetime.now(UTC)

        # Generate client_order_id if not provided
        client_order_id = intent.client_order_id
        if not client_order_id:
            # Use strategy_id from intent if available, otherwise use "alch" as default
            strategy_id = intent.strategy_id if intent.strategy_id else "alch"
            client_order_id = generate_client_order_id(intent.symbol, strategy_id)
            # Update intent with generated client_order_id
            intent = replace(intent, client_order_id=client_order_id)

        log_extra = {
            "symbol": intent.symbol,
            "side": intent.side.value,
            "quantity": str(intent.quantity),
            "urgency": intent.urgency.value,
            "close_type": intent.close_type.value,
            "correlation_id": intent.correlation_id,
            "client_order_id": client_order_id,
        }

        logger.info(
            "🚀 Starting unified order placement",
            **log_extra,
            intent_description=intent.describe(),
        )

        # Step 1: Preflight validation
        preflight_result = self.execution_validator.validate_order(
            symbol=intent.symbol,
            quantity=intent.quantity,
            correlation_id=intent.correlation_id,
            auto_adjust=True,
        )

        if not preflight_result.is_valid:
            error_msg = preflight_result.error_message or "Preflight validation failed"
            logger.error(
                "Preflight validation failed",
                **log_extra,
                error=error_msg,
            )
            return self._create_failure_result(intent, start_time, "validation_failed", error_msg)

        # Use adjusted quantity if provided
        if preflight_result.adjusted_quantity:
            intent = replace(intent, quantity=preflight_result.adjusted_quantity)
            logger.info(
                "Adjusted quantity from preflight validation",
                **log_extra,
                adjusted_quantity=str(preflight_result.adjusted_quantity),
            )

        # Step 2: Pre-execution portfolio validation (get initial position)
        initial_position = Decimal("0")
        if self.enable_validation:
            can_execute, initial_position, validation_error = (
                self.validator.validate_before_execution(intent)
            )
            if not can_execute and validation_error:
                logger.error(
                    "Pre-execution validation failed",
                    **log_extra,
                    error=validation_error,
                )
                return self._create_failure_result(
                    intent, start_time, "pre_validation_failed", validation_error
                )

        # Step 3: Get quote
        quote_result = await self.quote_service.get_best_quote(
            intent.symbol, correlation_id=intent.correlation_id
        )

        if not quote_result.success:
            # High urgency: proceed with market order anyway
            if intent.urgency == Urgency.HIGH:
                logger.warning(
                    "No usable quote but urgency is HIGH, proceeding with market order",
                    **log_extra,
                )
                return await self._execute_immediate_market(
                    intent, quote_result, initial_position, start_time
                )

            # Medium/Low urgency: fail if no quote
            error_msg = quote_result.error_message or "No usable quote available"
            logger.error(
                "No usable quote and urgency not HIGH",
                **log_extra,
                error=error_msg,
            )
            return self._create_failure_result(
                intent, start_time, "no_quote_available", error_msg, quote_result=quote_result
            )

        logger.info(
            "Got quote for order placement",
            **log_extra,
            quote_source=quote_result.source.value,
            bid=str(quote_result.bid),
            ask=str(quote_result.ask),
            spread_pct=f"{quote_result.spread_percent:.2f}%",
        )

        # Step 4: Route to execution strategy based on urgency
        if intent.urgency == Urgency.HIGH:
            result = await self._execute_immediate_market(
                intent, quote_result, initial_position, start_time
            )
        else:
            result = await self._execute_walk_the_book(
                intent, quote_result, initial_position, start_time
            )

        # Step 5: Log metrics for observability
        execution_time = result.execution_time_seconds
        logger.info(
            "📊 Order placement complete",
            **log_extra,
            success=result.success,
            strategy=result.execution_strategy,
            filled=str(result.total_filled),
            avg_price=str(result.avg_fill_price) if result.avg_fill_price else None,
            execution_time_seconds=execution_time,
            validation_passed=result.validation_result.success
            if result.validation_result
            else None,
        )

        return result

    async def _execute_immediate_market(
        self,
        intent: OrderIntent,
        quote_result: QuoteResult,
        initial_position: Decimal,
        start_time: datetime,
    ) -> ExecutionResult:
        """Execute immediate market order (high urgency).

        Args:
            intent: Order intent
            quote_result: Quote result (may be unavailable for high urgency)
            initial_position: Initial position for validation
            start_time: Execution start time

        Returns:
            ExecutionResult

        """
        log_extra = {
            "symbol": intent.symbol,
            "correlation_id": intent.correlation_id,
        }

        logger.info(
            "Executing immediate market order (high urgency)",
            **log_extra,
        )

        try:
            executed_order: ExecutedOrder = await asyncio.to_thread(
                self.alpaca_manager.place_market_order,
                symbol=intent.symbol,
                side=intent.side.to_alpaca(),
                qty=intent.quantity,
                is_complete_exit=intent.is_full_close,
                client_order_id=intent.client_order_id,
            )

            if executed_order.status in ["REJECTED", "CANCELED"]:
                error_msg = (
                    getattr(executed_order, "error_message", None) or "Market order rejected"
                )
                logger.error(
                    "Market order rejected",
                    **log_extra,
                    status=executed_order.status,
                )
                return self._create_failure_result(
                    intent,
                    start_time,
                    "market_order_rejected",
                    error_msg,
                    quote_result=quote_result,
                )

            filled_qty = getattr(executed_order, "filled_qty", intent.quantity)
            avg_price = getattr(executed_order, "filled_avg_price", executed_order.price)

            # Create a simple walk result for consistency
            from .walk_the_book import OrderAttempt, OrderStatus, WalkResult

            walk_result = WalkResult(
                success=True,
                order_attempts=[
                    OrderAttempt(
                        step=0,
                        price=executed_order.price if executed_order.price else Decimal("0"),
                        quantity=intent.quantity,
                        order_id=executed_order.order_id,
                        timestamp=executed_order.execution_timestamp or datetime.now(UTC),
                        status=OrderStatus.FILLED,
                        filled_quantity=filled_qty if filled_qty else intent.quantity,
                        avg_fill_price=avg_price,
                    )
                ],
                final_order_id=executed_order.order_id,
                total_filled=filled_qty if filled_qty else intent.quantity,
                avg_fill_price=avg_price,
            )

            # Validate portfolio if enabled
            validation_result = None
            if self.enable_validation:
                validation_result = await self.validator.validate_execution(
                    intent, walk_result, initial_position
                )
                if not validation_result.success:
                    logger.warning(
                        "Portfolio validation failed after market order",
                        **log_extra,
                        initial_position=str(initial_position),
                        validation_message=validation_result.validation_message,
                    )

            execution_time = (datetime.now(UTC) - start_time).total_seconds()

            return ExecutionResult(
                success=True,
                intent=intent,
                quote_result=quote_result,
                walk_result=walk_result,
                validation_result=validation_result,
                execution_strategy="market_immediate",
                total_filled=walk_result.total_filled,
                avg_fill_price=avg_price,
                final_order_id=executed_order.order_id,
                execution_time_seconds=execution_time,
            )

        except Exception as e:
            logger.error(
                "Market order execution failed",
                **log_extra,
                error=str(e),
                error_type=type(e).__name__,
            )
            return self._create_failure_result(
                intent, start_time, "market_order_failed", str(e), quote_result=quote_result
            )

    async def _execute_walk_the_book(
        self,
        intent: OrderIntent,
        quote_result: QuoteResult,
        initial_position: Decimal,
        start_time: datetime,
    ) -> ExecutionResult:
        """Execute walk-the-book strategy (medium/low urgency).

        Args:
            intent: Order intent
            quote_result: Quote result
            initial_position: Initial position for validation
            start_time: Execution start time

        Returns:
            ExecutionResult

        """
        log_extra = {
            "symbol": intent.symbol,
            "correlation_id": intent.correlation_id,
        }

        logger.info(
            "Executing walk-the-book strategy",
            **log_extra,
            urgency=intent.urgency.value,
        )

        walk_result = await self.walk_strategy.execute(intent, quote_result)

        # Validate portfolio if enabled
        validation_result = None
        if self.enable_validation and walk_result.success:
            validation_result = await self.validator.validate_execution(
                intent, walk_result, initial_position
            )
            if not validation_result.success:
                logger.warning(
                    "Portfolio validation failed after walk-the-book",
                    **log_extra,
                    initial_position=str(initial_position),
                    validation_message=validation_result.validation_message,
                )

        execution_time = (datetime.now(UTC) - start_time).total_seconds()

        if not walk_result.success:
            error_msg = walk_result.error_message or "Walk-the-book execution failed"
            logger.error(
                "Walk-the-book execution failed",
                **log_extra,
                error=error_msg,
            )
            return ExecutionResult(
                success=False,
                intent=intent,
                quote_result=quote_result,
                walk_result=walk_result,
                validation_result=validation_result,
                execution_strategy="walk_the_book",
                total_filled=walk_result.total_filled,
                avg_fill_price=walk_result.avg_fill_price,
                final_order_id=walk_result.final_order_id,
                execution_time_seconds=execution_time,
                error_message=error_msg,
            )

        return ExecutionResult(
            success=True,
            intent=intent,
            quote_result=quote_result,
            walk_result=walk_result,
            validation_result=validation_result,
            execution_strategy="walk_the_book",
            total_filled=walk_result.total_filled,
            avg_fill_price=walk_result.avg_fill_price,
            final_order_id=walk_result.final_order_id,
            execution_time_seconds=execution_time,
        )

    def _create_failure_result(
        self,
        intent: OrderIntent,
        start_time: datetime,
        strategy: str,
        error_message: str,
        *,
        quote_result: QuoteResult | None = None,
    ) -> ExecutionResult:
        """Create a failure result.

        Args:
            intent: Order intent
            start_time: Execution start time
            strategy: Execution strategy that failed
            error_message: Error message
            quote_result: Quote result if available

        Returns:
            ExecutionResult with success=False

        """
        execution_time = (datetime.now(UTC) - start_time).total_seconds()

        return ExecutionResult(
            success=False,
            intent=intent,
            quote_result=quote_result,
            walk_result=None,
            validation_result=None,
            execution_strategy=strategy,
            total_filled=Decimal("0"),
            avg_fill_price=None,
            final_order_id=None,
            execution_time_seconds=execution_time,
            error_message=error_message,
        )

    def log_metrics_summary(self) -> None:
        """Log metrics summary for observability."""
        self.quote_service.log_metrics_summary()
