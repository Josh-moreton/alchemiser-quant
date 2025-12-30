"""Business Unit: execution | Status: current.

Portfolio validation after order execution.

Ensures that orders actually changed the portfolio state as expected by:
- Checking position quantities match expected changes
- Validating full closes actually closed the position
- Detecting discrepancies between expected and actual state
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager

    from .order_intent import OrderIntent
    from .walk_the_book import WalkResult

logger = get_logger(__name__)

# Configuration constants
DEFAULT_SETTLEMENT_WAIT_SECONDS = 5.0
DEFAULT_SETTLEMENT_TIMEOUT_SECONDS = 30.0
SETTLEMENT_CHECK_INTERVAL_SECONDS = 1.0
FRACTIONAL_TOLERANCE = Decimal("0.001")  # Allow tiny fractional discrepancies
# Pre-execution sell tolerance: allow up to 1% difference between requested and available quantity
# This handles floating-point precision issues when portfolio calculations and broker positions differ
PRE_EXECUTION_SELL_TOLERANCE_PCT = Decimal("0.01")


@dataclass(frozen=True)
class ValidationResult:
    """Result of portfolio validation after order execution.

    Attributes:
        success: Whether validation passed
        symbol: Symbol that was traded
        expected_position: Expected position quantity after trade
        actual_position: Actual position quantity from broker
        discrepancy: Difference between expected and actual
        is_within_tolerance: Whether discrepancy is within acceptable range
        validation_message: Detailed message about validation
        error_message: Error message if validation failed

    """

    success: bool
    symbol: str
    expected_position: Decimal
    actual_position: Decimal
    discrepancy: Decimal
    is_within_tolerance: bool
    validation_message: str
    error_message: str | None = None

    def describe(self) -> str:
        """Human-readable description of validation result."""
        if self.success:
            if abs(self.discrepancy) < FRACTIONAL_TOLERANCE:
                return f"✅ Position validated: {self.symbol} = {self.actual_position} shares (exact match)"
            return f"✅ Position validated: {self.symbol} = {self.actual_position} shares (discrepancy {self.discrepancy} within tolerance)"
        return f"❌ Validation failed: {self.symbol} expected {self.expected_position}, got {self.actual_position} (discrepancy {self.discrepancy})"


class PortfolioValidator:
    """Validates portfolio state after order execution.

    This ensures that orders actually changed the portfolio as expected,
    catching issues like:
    - Partial fills that didn't fully close a position
    - Position updates that didn't settle correctly
    - Broker-side errors that left positions in unexpected states

    """

    def __init__(
        self,
        alpaca_manager: AlpacaManager,
        *,
        settlement_wait_seconds: float = DEFAULT_SETTLEMENT_WAIT_SECONDS,
        settlement_timeout_seconds: float = DEFAULT_SETTLEMENT_TIMEOUT_SECONDS,
        fractional_tolerance: Decimal = FRACTIONAL_TOLERANCE,
    ) -> None:
        """Initialize portfolio validator.

        Args:
            alpaca_manager: Alpaca broker manager for position queries
            settlement_wait_seconds: Initial wait for settlement
            settlement_timeout_seconds: Max time to wait for settlement
            fractional_tolerance: Acceptable discrepancy for fractional shares

        """
        self.alpaca_manager = alpaca_manager
        self.settlement_wait_seconds = settlement_wait_seconds
        self.settlement_timeout_seconds = settlement_timeout_seconds
        self.fractional_tolerance = fractional_tolerance

        logger.debug(
            "PortfolioValidator initialized",
            settlement_wait_seconds=settlement_wait_seconds,
            settlement_timeout_seconds=settlement_timeout_seconds,
            fractional_tolerance=str(fractional_tolerance),
        )

    async def validate_execution(
        self,
        intent: OrderIntent,
        walk_result: WalkResult,
        initial_position: Decimal | None = None,
    ) -> ValidationResult:
        """Validate that order execution changed portfolio as expected.

        Args:
            intent: Original order intent
            walk_result: Result of walk-the-book execution
            initial_position: Position before trade (fetched if not provided)

        Returns:
            ValidationResult with validation details

        """
        log_extra = {
            "symbol": intent.symbol,
            "side": intent.side.value,
            "close_type": intent.close_type.value,
            "correlation_id": intent.correlation_id,
        }

        if not walk_result.success:
            logger.warning(
                "Skipping validation for failed order execution",
                **log_extra,
            )
            return ValidationResult(
                success=False,
                symbol=intent.symbol,
                expected_position=Decimal("0"),
                actual_position=Decimal("0"),
                discrepancy=Decimal("0"),
                is_within_tolerance=False,
                validation_message="Order execution failed, validation skipped",
                error_message=walk_result.error_message,
            )

        # Step 1: Get initial position if not provided
        if initial_position is None:
            # Since order already executed, we can't get initial position
            # We'll validate based on the expected change only
            logger.warning(
                "No initial position provided, validation will be limited",
                **log_extra,
            )
            initial_position = Decimal("0")

        # Step 2: Calculate expected final position
        expected_position = self._calculate_expected_position(
            initial_position, intent, walk_result.total_filled
        )

        # Step 3: Wait for settlement
        logger.debug(
            f"Waiting {self.settlement_wait_seconds}s for order settlement",
            **log_extra,
        )
        await asyncio.sleep(self.settlement_wait_seconds)

        # Step 4: Fetch actual position with retries
        actual_position = await self._fetch_settled_position(
            intent.symbol, correlation_id=intent.correlation_id
        )

        # Step 5: Calculate discrepancy
        discrepancy = actual_position - expected_position
        is_within_tolerance = abs(discrepancy) <= self.fractional_tolerance

        # Step 6: Build validation result
        if is_within_tolerance:
            logger.info(
                "Portfolio validation passed",
                **log_extra,
                expected_position=str(expected_position),
                actual_position=str(actual_position),
                discrepancy=str(discrepancy),
            )
            return ValidationResult(
                success=True,
                symbol=intent.symbol,
                expected_position=expected_position,
                actual_position=actual_position,
                discrepancy=discrepancy,
                is_within_tolerance=True,
                validation_message=f"Position validated: {actual_position} shares (expected {expected_position})",
            )

        # Discrepancy outside tolerance
        logger.warning(
            "Portfolio validation discrepancy detected",
            **log_extra,
            initial_position=str(initial_position),
            filled_qty=str(walk_result.total_filled),
            expected_position=str(expected_position),
            actual_position=str(actual_position),
            discrepancy=str(discrepancy),
            tolerance=str(self.fractional_tolerance),
        )

        return ValidationResult(
            success=False,
            symbol=intent.symbol,
            expected_position=expected_position,
            actual_position=actual_position,
            discrepancy=discrepancy,
            is_within_tolerance=False,
            validation_message=f"Position mismatch: expected {expected_position}, got {actual_position}",
            error_message=f"Discrepancy {discrepancy} exceeds tolerance {self.fractional_tolerance}",
        )

    def _calculate_expected_position(
        self,
        initial_position: Decimal,
        intent: OrderIntent,
        filled_quantity: Decimal,
    ) -> Decimal:
        """Calculate expected position after order execution.

        Args:
            initial_position: Position before trade
            intent: Order intent
            filled_quantity: How much was actually filled

        Returns:
            Expected final position

        """
        if intent.is_buy:
            # Buy increases position
            return initial_position + filled_quantity

        if intent.is_full_close:
            # Full close should result in 0 position
            return Decimal("0")

        # Partial sell decreases position
        return initial_position - filled_quantity

    async def _fetch_settled_position(
        self, symbol: str, *, correlation_id: str | None = None
    ) -> Decimal:
        """Fetch settled position with retries.

        Args:
            symbol: Symbol to fetch position for
            correlation_id: Optional correlation ID for tracing

        Returns:
            Current position quantity (0 if no position)

        """
        timeout = self.settlement_timeout_seconds
        check_interval = SETTLEMENT_CHECK_INTERVAL_SECONDS  # Start with 1s
        max_interval = 5.0  # Cap at 5 seconds
        elapsed = 0.0

        while elapsed < timeout:
            try:
                position = await asyncio.to_thread(self.alpaca_manager.get_position, symbol)

                if position:
                    qty = getattr(position, "qty", Decimal("0"))
                    logger.debug(
                        "Fetched current position",
                        symbol=symbol,
                        position_qty=str(qty),
                        correlation_id=correlation_id,
                    )
                    return Decimal(str(qty)) if qty else Decimal("0")

                # No position found (likely closed position)
                logger.debug(
                    "No position found for symbol",
                    symbol=symbol,
                    correlation_id=correlation_id,
                )
                return Decimal("0")

            except Exception as e:
                logger.warning(
                    "Error fetching position, will retry",
                    symbol=symbol,
                    error=str(e),
                    elapsed=elapsed,
                    correlation_id=correlation_id,
                )

            await asyncio.sleep(check_interval)
            elapsed += check_interval
            # Exponential backoff: double interval up to max
            check_interval = min(check_interval * 2, max_interval)

        # Timeout - return 0 as fallback
        logger.error(
            "Timeout waiting for position settlement",
            symbol=symbol,
            timeout=timeout,
            correlation_id=correlation_id,
        )
        return Decimal("0")

    def validate_before_execution(
        self, intent: OrderIntent
    ) -> tuple[bool, Decimal, str | None, Decimal | None]:
        """Validate portfolio state before execution and return initial position.

        This fetches the current position so we can validate changes after execution.
        If the requested sell quantity slightly exceeds the available position (within
        tolerance), returns an adjusted quantity to prevent failures due to floating-point
        precision issues in portfolio calculations.

        Args:
            intent: Order intent to validate

        Returns:
            Tuple of (can_execute, initial_position, error_message, adjusted_quantity)
            - adjusted_quantity is set when sell qty needs to be capped to available position

        """
        try:
            # Fetch current position
            position = self.alpaca_manager.get_position(intent.symbol)

            if position:
                initial_qty = getattr(position, "qty", Decimal("0"))
                initial_position = Decimal(str(initial_qty)) if initial_qty else Decimal("0")
            else:
                initial_position = Decimal("0")

            adjusted_quantity: Decimal | None = None

            # Validate sell orders have sufficient position
            if intent.is_sell and initial_position < intent.quantity:
                # Calculate the discrepancy
                shortfall = intent.quantity - initial_position
                tolerance_threshold = intent.quantity * PRE_EXECUTION_SELL_TOLERANCE_PCT

                # If within tolerance (small floating-point discrepancy), adjust quantity
                if shortfall <= tolerance_threshold and initial_position > Decimal("0"):
                    adjusted_quantity = initial_position
                    logger.info(
                        "Adjusting sell quantity to match available position",
                        symbol=intent.symbol,
                        requested_qty=str(intent.quantity),
                        available_qty=str(initial_position),
                        shortfall=str(shortfall),
                        tolerance_threshold=str(tolerance_threshold),
                        correlation_id=intent.correlation_id,
                    )
                else:
                    # Genuine shortfall - fail validation
                    error_msg = (
                        f"Insufficient position for {intent.symbol}: "
                        f"need {intent.quantity}, have {initial_position}"
                    )
                    logger.error(
                        "Pre-execution validation failed",
                        symbol=intent.symbol,
                        error=error_msg,
                        shortfall=str(shortfall),
                        tolerance_threshold=str(tolerance_threshold),
                        correlation_id=intent.correlation_id,
                    )
                    return False, initial_position, error_msg, None

            # Validate full close matches position
            if intent.is_full_close and initial_position != intent.quantity:
                logger.warning(
                    "Full close quantity doesn't match current position",
                    symbol=intent.symbol,
                    requested_qty=str(intent.quantity),
                    actual_position=str(initial_position),
                    correlation_id=intent.correlation_id,
                )
                # This is just a warning, not a failure
                # The actual close will use the current position

            logger.info(
                "Pre-execution validation passed",
                symbol=intent.symbol,
                side=intent.side.value,
                order_qty=str(intent.quantity),
                initial_position=str(initial_position),
                adjusted_qty=str(adjusted_quantity) if adjusted_quantity else None,
                correlation_id=intent.correlation_id,
            )
            return True, initial_position, None, adjusted_quantity

        except Exception as e:
            error_msg = f"Failed to fetch position for validation: {e}"
            logger.error(
                "Pre-execution validation error",
                symbol=intent.symbol,
                error=str(e),
                correlation_id=intent.correlation_id,
            )
            # Don't block execution on validation errors
            return True, Decimal("0"), None, None
