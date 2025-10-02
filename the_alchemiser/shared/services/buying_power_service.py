"""Business Unit: shared | Status: current.

Buying power verification service for handling account state synchronization.

This service addresses the timing issue where broker account state (buying power)
hasn't been updated yet even though orders have settled. It provides retry logic
with exponential backoff to wait for account state synchronization.
"""

from __future__ import annotations

import time
from decimal import Decimal
from typing import TYPE_CHECKING

from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager

logger = get_logger(__name__)


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
    ) -> tuple[bool, Decimal]:
        """Verify that buying power is actually available in account with retry logic.

        This method addresses the timing issue where the broker's account buying_power
        field hasn't been updated yet even though sell orders have settled.

        Args:
            expected_amount: Minimum buying power expected to be available
            max_retries: Maximum number of retry attempts
            initial_wait: Initial wait time in seconds (doubles each retry). Accepts int or float

        Returns:
            Tuple of (is_available, actual_buying_power)

        """
        logger.info(
            "💰 Verifying $ buying power availability (with retries)",
            expected_amount=expected_amount,
        )

        for attempt in range(max_retries):
            try:
                result = self._check_buying_power_attempt(expected_amount, attempt)
                if result is not None:
                    return result

                self._wait_before_retry(attempt, max_retries, initial_wait)

            except Exception as e:
                logger.error(
                    "Error verifying buying power on attempt",
                    attempt_number=attempt + 1,
                    error=str(e),
                )
                self._wait_before_retry(attempt, max_retries, initial_wait)

        final_buying_power = self._get_final_buying_power()
        logger.error(
            "❌ Buying power verification failed after retries",
            max_retries=max_retries,
            final_buying_power=final_buying_power,
            expected_amount=expected_amount,
        )
        return False, final_buying_power

    def _check_buying_power_attempt(
        self, expected_amount: Decimal, attempt: int
    ) -> tuple[bool, Decimal] | None:
        """Check buying power for a single attempt.

        Args:
            expected_amount: Required buying power amount
            attempt: Current attempt number (0-based)

        Returns:
            Tuple of (success, buying_power) if definitive result, None to continue retrying

        """
        buying_power = self.broker_manager.get_buying_power()
        if buying_power is None:
            logger.warning("Could not retrieve buying power on attempt", attempt_number=attempt + 1)
            return None

        actual_buying_power = Decimal(str(buying_power))
        logger.info(
            "💰 Buying power check attempt",
            attempt_number=attempt + 1,
            actual_buying_power=actual_buying_power,
            expected_amount=expected_amount,
        )

        if actual_buying_power >= expected_amount:
            logger.info(
                "✅ Buying power verified: $ >= $",
                actual_buying_power=actual_buying_power,
                expected_amount=expected_amount,
            )
            return True, actual_buying_power

        # Log the shortfall and continue retrying
        shortfall = expected_amount - actual_buying_power
        logger.warning(
            "⚠️ Buying power shortfall detected",
            shortfall=shortfall,
            actual_buying_power=actual_buying_power,
            expected_amount=expected_amount,
        )
        return None

    def _wait_before_retry(self, attempt: int, max_retries: int, initial_wait: int | float) -> None:
        """Wait before retrying with exponential backoff.

        Args:
            attempt: Current attempt number (0-based)
            max_retries: Maximum number of retries
            initial_wait: Initial wait time in seconds

        """
        if attempt < max_retries - 1:
            wait_time = initial_wait * (2**attempt)
            logger.info(
                "⏳ Waiting for account state to update", wait_time_seconds=f"{wait_time:.1f}"
            )
            time.sleep(wait_time)

    def _get_final_buying_power(self) -> Decimal:
        """Get the final buying power after all retry attempts failed.

        Returns:
            Final buying power amount, or 0 if retrieval fails

        """
        try:
            final_buying_power_raw = self.broker_manager.get_buying_power()
            return Decimal(str(final_buying_power_raw)) if final_buying_power_raw else Decimal("0")
        except Exception:
            return Decimal("0")

    def force_account_refresh(self) -> bool:
        """Force a fresh account data retrieval from the broker.

        This can help when account state appears stale after order settlements.

        Returns:
            True if refresh successful, False otherwise

        """
        try:
            logger.info("🔄 Forcing account state refresh...")
            buying_power = self.broker_manager.get_buying_power()
            portfolio_value = self.broker_manager.get_portfolio_value()

            if buying_power is not None and portfolio_value is not None:
                logger.info(
                    "✅ Account refreshed",
                    buying_power=f"${buying_power:,.2f}",
                    portfolio_value=f"${portfolio_value:,.2f}",
                )
                return True
            logger.warning("⚠️ Account refresh returned incomplete data")
            return False
        except Exception as e:
            logger.error("❌ Failed to refresh account state", error=str(e))
            return False

    def estimate_order_cost(
        self, symbol: str, quantity: Decimal, buffer_pct: float = 5.0
    ) -> Decimal | None:
        """Estimate the cost of a buy order with a price buffer.

        Args:
            symbol: Stock symbol
            quantity: Number of shares
            buffer_pct: Price buffer percentage (default 5%)

        Returns:
            Estimated cost with buffer, or None if price unavailable

        """
        try:
            current_price = self.broker_manager.get_current_price(symbol)
            if current_price:
                estimated_cost = quantity * Decimal(str(current_price))
                buffer_multiplier = Decimal(str(1 + buffer_pct / 100))
                return estimated_cost * buffer_multiplier
            return None
        except Exception as e:
            logger.error("Failed to estimate order cost for", symbol=symbol, error=str(e))
            return None

    def check_sufficient_buying_power(
        self, symbol: str, quantity: Decimal, buffer_pct: float = 5.0
    ) -> tuple[bool, Decimal, Decimal | None]:
        """Check if there's sufficient buying power for a buy order.

        Args:
            symbol: Stock symbol
            quantity: Number of shares
            buffer_pct: Price buffer percentage

        Returns:
            Tuple of (is_sufficient, current_buying_power, estimated_cost)

        """
        try:
            estimated_cost = self.estimate_order_cost(symbol, quantity, buffer_pct)
            buying_power = self.broker_manager.get_buying_power()

            if buying_power is None or estimated_cost is None:
                return False, Decimal("0"), estimated_cost

            current_bp = Decimal(str(buying_power))
            is_sufficient = current_bp >= estimated_cost

            logger.info(
                "💰 Buying power check for symbol",
                symbol=symbol,
                estimated_cost=estimated_cost,
                buffer_pct=buffer_pct,
                available=current_bp,
                is_sufficient=is_sufficient,
            )

            return is_sufficient, current_bp, estimated_cost

        except Exception as e:
            logger.error("Error checking buying power for", symbol=symbol, error=str(e))
            return False, Decimal("0"), None
