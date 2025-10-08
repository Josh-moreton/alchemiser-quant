"""Business Unit: shared | Status: current.

Buying power verification service for handling account state synchronization.

This service addresses the timing issue where broker account state (buying power)
hasn't been updated yet even though orders have settled. It provides retry logic
with exponential backoff to wait for account state synchronization.
"""

from __future__ import annotations

import random
import time
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING

from the_alchemiser.shared.errors.exceptions import (
    DataProviderError,
    TradingClientError,
)
from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager

logger = get_logger(__name__)

# Module-level constants
MONEY_PRECISION = Decimal("0.01")  # 2 decimal places for USD
DEFAULT_PRICE_BUFFER_PCT = 5.0
PERCENTAGE_DIVISOR = 100
MAX_BACKOFF_SECONDS = 10.0  # Cap individual wait at 10 seconds


class BuyingPowerService:
    """Service for verifying buying power availability with retry logic."""

    def __init__(self, broker_manager: AlpacaManager) -> None:
        """Initialize buying power service.

        Args:
            broker_manager: Broker manager for account operations

        """
        self.broker_manager = broker_manager

    def verify_buying_power_available(
        self,
        expected_amount: Decimal,
        max_retries: int = 5,
        initial_wait: int | float = 1.0,
        correlation_id: str | None = None,
    ) -> tuple[bool, Decimal]:
        """Verify that buying power is actually available in account with retry logic.

        This method addresses the timing issue where the broker's account buying_power
        field hasn't been updated yet even though sell orders have settled.

        Preconditions:
            - expected_amount must be positive (> 0)
            - max_retries must be >= 1
            - initial_wait must be positive (> 0)

        Args:
            expected_amount: Minimum buying power expected to be available
            max_retries: Maximum number of retry attempts
            initial_wait: Initial wait time in seconds (doubles each retry). Accepts int or float
            correlation_id: Optional correlation ID for event traceability

        Returns:
            Tuple of (is_available, actual_buying_power)

        Raises:
            ValueError: If expected_amount, max_retries, or initial_wait are invalid

        """
        # Input validation
        if expected_amount <= 0:
            raise ValueError(f"expected_amount must be positive, got {expected_amount}")
        if max_retries < 1:
            raise ValueError(f"max_retries must be >= 1, got {max_retries}")
        if initial_wait <= 0:
            raise ValueError(f"initial_wait must be positive, got {initial_wait}")

        logger.info(
            "💰 Verifying $ buying power availability (with retries)",
            expected_amount=expected_amount,
            correlation_id=correlation_id,
        )

        for attempt in range(max_retries):
            try:
                result = self._check_buying_power_attempt(expected_amount, attempt, correlation_id)
                if result is not None:
                    return result

                self._wait_before_retry(attempt, max_retries, initial_wait, correlation_id)

            except (DataProviderError, TradingClientError) as e:
                logger.error(
                    "Error verifying buying power on attempt",
                    attempt_number=attempt + 1,
                    error=str(e),
                    error_type=type(e).__name__,
                    correlation_id=correlation_id,
                )
                self._wait_before_retry(attempt, max_retries, initial_wait, correlation_id)

        final_buying_power = self._get_final_buying_power(correlation_id)
        logger.error(
            "❌ Buying power verification failed after retries",
            max_retries=max_retries,
            final_buying_power=final_buying_power,
            expected_amount=expected_amount,
            correlation_id=correlation_id,
        )
        return False, final_buying_power

    def _check_buying_power_attempt(
        self, expected_amount: Decimal, attempt: int, correlation_id: str | None = None
    ) -> tuple[bool, Decimal] | None:
        """Check buying power for a single attempt.

        Args:
            expected_amount: Required buying power amount
            attempt: Current attempt number (0-based)
            correlation_id: Optional correlation ID for event traceability

        Returns:
            Tuple of (success, buying_power) if definitive result, None to continue retrying

        """
        buying_power = self.broker_manager.get_buying_power()
        if buying_power is None:
            logger.warning(
                "Could not retrieve buying power on attempt",
                attempt_number=attempt + 1,
                correlation_id=correlation_id,
            )
            return None

        # Convert to Decimal with explicit rounding
        actual_buying_power = Decimal(str(buying_power)).quantize(
            MONEY_PRECISION, rounding=ROUND_HALF_UP
        )
        logger.info(
            "💰 Buying power check attempt",
            attempt_number=attempt + 1,
            actual_buying_power=actual_buying_power,
            expected_amount=expected_amount,
            correlation_id=correlation_id,
        )

        if actual_buying_power >= expected_amount:
            logger.info(
                "✅ Buying power verified: $ >= $",
                actual_buying_power=actual_buying_power,
                expected_amount=expected_amount,
                correlation_id=correlation_id,
            )
            return True, actual_buying_power

        # Log the shortfall and continue retrying
        shortfall = expected_amount - actual_buying_power
        logger.warning(
            "⚠️ Buying power shortfall detected",
            shortfall=shortfall,
            actual_buying_power=actual_buying_power,
            expected_amount=expected_amount,
            correlation_id=correlation_id,
        )
        return None

    def _wait_before_retry(
        self,
        attempt: int,
        max_retries: int,
        initial_wait: int | float,
        correlation_id: str | None = None,
    ) -> None:
        """Wait before retrying with exponential backoff and jitter.

        Args:
            attempt: Current attempt number (0-based)
            max_retries: Maximum number of retries
            initial_wait: Initial wait time in seconds
            correlation_id: Optional correlation ID for event traceability

        """
        if attempt < max_retries - 1:
            # Calculate base wait with exponential backoff
            base_wait = initial_wait * (2**attempt)
            # Cap the wait time
            base_wait = min(base_wait, MAX_BACKOFF_SECONDS)
            # Add jitter (±10% random variation) - not cryptographic use
            jitter = base_wait * random.uniform(-0.1, 0.1)  # noqa: S311
            wait_time = base_wait + jitter

            logger.info(
                "⏳ Waiting for account state to update",
                wait_time_seconds=wait_time,
                correlation_id=correlation_id,
            )
            time.sleep(wait_time)

    def _get_final_buying_power(self, correlation_id: str | None = None) -> Decimal:
        """Get the final buying power after all retry attempts failed.

        Args:
            correlation_id: Optional correlation ID for event traceability

        Returns:
            Final buying power amount, or 0 if retrieval fails

        """
        try:
            final_buying_power_raw = self.broker_manager.get_buying_power()
            if final_buying_power_raw:
                return Decimal(str(final_buying_power_raw)).quantize(
                    MONEY_PRECISION, rounding=ROUND_HALF_UP
                )
            return Decimal("0")
        except Exception as e:
            logger.error(
                "Failed to retrieve final buying power",
                error=str(e),
                error_type=type(e).__name__,
                correlation_id=correlation_id,
            )
            return Decimal("0")

    def force_account_refresh(self, correlation_id: str | None = None) -> bool:
        """Force a fresh account data retrieval from the broker.

        This can help when account state appears stale after order settlements.

        Args:
            correlation_id: Optional correlation ID for event traceability

        Returns:
            True if refresh successful, False otherwise

        """
        try:
            logger.info(
                "🔄 Forcing account state refresh...",
                correlation_id=correlation_id,
            )
            buying_power = self.broker_manager.get_buying_power()
            portfolio_value = self.broker_manager.get_portfolio_value()

            if buying_power is not None and portfolio_value is not None:
                logger.info(
                    "✅ Account refreshed",
                    buying_power=buying_power,
                    portfolio_value=portfolio_value,
                    correlation_id=correlation_id,
                )
                return True
            logger.warning(
                "⚠️ Account refresh returned incomplete data",
                correlation_id=correlation_id,
            )
            return False
        except (DataProviderError, TradingClientError) as e:
            logger.error(
                "❌ Failed to refresh account state",
                error=str(e),
                error_type=type(e).__name__,
                correlation_id=correlation_id,
            )
            return False

    def estimate_order_cost(
        self,
        symbol: str,
        quantity: Decimal,
        buffer_pct: float = DEFAULT_PRICE_BUFFER_PCT,
        correlation_id: str | None = None,
    ) -> Decimal | None:
        """Estimate the cost of a buy order with a price buffer.

        Preconditions:
            - quantity must be positive (> 0)
            - buffer_pct must be non-negative (>= 0)

        Args:
            symbol: Stock symbol
            quantity: Number of shares
            buffer_pct: Price buffer percentage (default 5%)
            correlation_id: Optional correlation ID for event traceability

        Returns:
            Estimated cost with buffer, or None if price unavailable

        Raises:
            ValueError: If quantity or buffer_pct are invalid

        """
        # Input validation
        if quantity <= 0:
            raise ValueError(f"quantity must be positive, got {quantity}")
        if buffer_pct < 0:
            raise ValueError(f"buffer_pct must be non-negative, got {buffer_pct}")

        try:
            current_price = self.broker_manager.get_current_price(symbol)
            if current_price:
                # Convert price to Decimal with explicit rounding
                price_decimal = Decimal(str(current_price)).quantize(
                    MONEY_PRECISION, rounding=ROUND_HALF_UP
                )
                estimated_cost = quantity * price_decimal

                # Calculate buffer multiplier
                buffer_multiplier = Decimal(str(1 + buffer_pct / PERCENTAGE_DIVISOR))
                return (estimated_cost * buffer_multiplier).quantize(
                    MONEY_PRECISION, rounding=ROUND_HALF_UP
                )
            return None
        except (DataProviderError, TradingClientError) as e:
            logger.error(
                "Failed to estimate order cost",
                symbol=symbol,
                error=str(e),
                error_type=type(e).__name__,
                correlation_id=correlation_id,
            )
            return None

    def check_sufficient_buying_power(
        self,
        symbol: str,
        quantity: Decimal,
        buffer_pct: float = DEFAULT_PRICE_BUFFER_PCT,
        correlation_id: str | None = None,
    ) -> tuple[bool, Decimal, Decimal | None]:
        """Check if there's sufficient buying power for a buy order.

        Preconditions:
            - quantity must be positive (> 0)
            - buffer_pct must be non-negative (>= 0)

        Args:
            symbol: Stock symbol
            quantity: Number of shares
            buffer_pct: Price buffer percentage
            correlation_id: Optional correlation ID for event traceability

        Returns:
            Tuple of (is_sufficient, current_buying_power, estimated_cost)

        Raises:
            ValueError: If quantity or buffer_pct are invalid

        """
        try:
            estimated_cost = self.estimate_order_cost(symbol, quantity, buffer_pct, correlation_id)
            buying_power = self.broker_manager.get_buying_power()

            if buying_power is None or estimated_cost is None:
                return False, Decimal("0"), estimated_cost

            # Convert to Decimal with explicit rounding
            current_bp = Decimal(str(buying_power)).quantize(
                MONEY_PRECISION, rounding=ROUND_HALF_UP
            )
            is_sufficient = current_bp >= estimated_cost

            logger.info(
                "💰 Buying power check for symbol",
                symbol=symbol,
                estimated_cost=estimated_cost,
                buffer_pct=buffer_pct,
                available=current_bp,
                is_sufficient=is_sufficient,
                correlation_id=correlation_id,
            )

            return is_sufficient, current_bp, estimated_cost

        except (DataProviderError, TradingClientError) as e:
            logger.error(
                "Error checking buying power",
                symbol=symbol,
                error=str(e),
                error_type=type(e).__name__,
                correlation_id=correlation_id,
            )
            return False, Decimal("0"), None
