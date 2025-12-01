"""Business Unit: execution | Status: current.

Daily Trade Limit Service - Circuit Breaker for Cumulative Trade Value.

This service enforces the MAX_DAILY_TRADE_VALUE_USD limit by tracking
cumulative trade value throughout the day. It provides a critical safety
mechanism to prevent runaway trading bugs from deploying excessive capital.

Implementation Notes:
- Uses DynamoDB for persistence (same table as trade ledger)
- Resets daily at midnight UTC
- Thread-safe within single process (daily runs don't need cross-process safety)
- Logs all limit checks for audit trail
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from the_alchemiser.shared.config.config import load_settings
from the_alchemiser.shared.constants import MAX_DAILY_TRADE_VALUE_USD
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

__all__ = ["DailyTradeLimitCheck", "DailyTradeLimitExceededError", "DailyTradeLimitService"]


class DailyTradeLimitExceededError(Exception):
    """Raised when daily trade limit would be exceeded.

    This is a critical safety exception that halts trading execution
    to prevent catastrophic capital deployment.
    """

    def __init__(
        self,
        message: str,
        *,
        proposed_trade_value: Decimal,
        current_cumulative: Decimal,
        daily_limit: Decimal,
        headroom: Decimal,
    ) -> None:
        """Initialize with limit details.

        Args:
            message: Error message
            proposed_trade_value: Value of trade that would exceed limit
            current_cumulative: Current cumulative value for the day
            daily_limit: Configured daily limit
            headroom: How much more could be traded before limit

        """
        super().__init__(message)
        self.proposed_trade_value = proposed_trade_value
        self.current_cumulative = current_cumulative
        self.daily_limit = daily_limit
        self.headroom = headroom


class DailyTradeLimitCheck(BaseModel):
    """Result of a daily trade limit check.

    Immutable DTO representing whether a proposed trade is within limits.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        extra="forbid",
    )

    is_within_limit: bool = Field(..., description="Whether trade is allowed")
    proposed_trade_value: Decimal = Field(..., description="Value of proposed trade")
    current_cumulative: Decimal = Field(..., description="Current day's cumulative value")
    daily_limit: Decimal = Field(..., description="Configured daily limit")
    headroom: Decimal = Field(..., description="Remaining capacity before limit")
    would_exceed_by: Decimal = Field(
        default=Decimal("0"), description="Amount by which limit would be exceeded"
    )
    check_timestamp: datetime = Field(..., description="When check was performed")
    correlation_id: str | None = Field(default=None, description="Correlation ID for tracing")


class DailyTradeLimitService:
    """Service for enforcing daily cumulative trade value limits.

    This is a critical circuit breaker that prevents runaway trading from
    deploying more than MAX_DAILY_TRADE_VALUE_USD in a single day.

    Usage:
        service = DailyTradeLimitService()

        # Before placing any order:
        check = service.check_limit(order_value, correlation_id)
        if not check.is_within_limit:
            # Halt execution
            raise DailyTradeLimitExceededError(...)

        # After order fills:
        service.record_trade(filled_value, correlation_id)
    """

    def __init__(
        self,
        daily_limit: Decimal | None = None,
    ) -> None:
        """Initialize the service.

        Args:
            daily_limit: Optional override for daily limit (defaults to MAX_DAILY_TRADE_VALUE_USD)

        Note:
            This service uses in-memory tracking only, which is appropriate for
            daily 10-minute trading runs. For multi-instance deployments,
            DynamoDB-backed persistence could be added.

        """
        self._daily_limit = daily_limit or MAX_DAILY_TRADE_VALUE_USD
        self._settings = load_settings()

        # In-memory tracking for current session (resets on restart)
        self._session_cumulative: Decimal = Decimal("0")
        self._session_date: str = self._get_today_key()

        logger.info(
            "Daily trade limit service initialized",
            daily_limit=str(self._daily_limit),
        )

    def _get_today_key(self) -> str:
        """Get today's date as a string key (UTC)."""
        return datetime.now(UTC).strftime("%Y-%m-%d")

    def _reset_if_new_day(self) -> None:
        """Reset session cumulative if we've crossed midnight UTC."""
        today = self._get_today_key()
        if today != self._session_date:
            logger.info(
                "New trading day detected, resetting cumulative",
                previous_date=self._session_date,
                new_date=today,
                previous_cumulative=str(self._session_cumulative),
            )
            self._session_date = today
            self._session_cumulative = Decimal("0")

    def get_cumulative_today(self, correlation_id: str | None = None) -> Decimal:
        """Get current cumulative trade value for today.

        Args:
            correlation_id: Optional correlation ID for tracing (reserved for future use)

        Returns:
            Cumulative trade value for today

        """
        self._reset_if_new_day()
        return self._session_cumulative

    def check_limit(
        self,
        proposed_trade_value: Decimal,
        correlation_id: str | None = None,
    ) -> DailyTradeLimitCheck:
        """Check if a proposed trade is within daily limits.

        This should be called BEFORE placing any order.

        Args:
            proposed_trade_value: Absolute value of proposed trade
            correlation_id: Optional correlation ID for tracing

        Returns:
            DailyTradeLimitCheck with limit status

        """
        self._reset_if_new_day()

        current_cumulative = self.get_cumulative_today(correlation_id)
        headroom = self._daily_limit - current_cumulative
        would_exceed_by = max(
            Decimal("0"), (current_cumulative + proposed_trade_value) - self._daily_limit
        )
        is_within_limit = proposed_trade_value <= headroom

        check = DailyTradeLimitCheck(
            is_within_limit=is_within_limit,
            proposed_trade_value=proposed_trade_value,
            current_cumulative=current_cumulative,
            daily_limit=self._daily_limit,
            headroom=headroom,
            would_exceed_by=would_exceed_by,
            check_timestamp=datetime.now(UTC),
            correlation_id=correlation_id,
        )

        if is_within_limit:
            logger.debug(
                "Trade within daily limit",
                proposed=str(proposed_trade_value),
                cumulative=str(current_cumulative),
                headroom=str(headroom),
                correlation_id=correlation_id,
            )
        else:
            logger.error(
                "🚨 DAILY TRADE LIMIT WOULD BE EXCEEDED",
                proposed=str(proposed_trade_value),
                cumulative=str(current_cumulative),
                limit=str(self._daily_limit),
                would_exceed_by=str(would_exceed_by),
                correlation_id=correlation_id,
            )

        return check

    def record_trade(
        self,
        trade_value: Decimal,
        correlation_id: str | None = None,
    ) -> Decimal:
        """Record a completed trade against the daily limit.

        This should be called AFTER an order fills successfully.

        Args:
            trade_value: Absolute value of the filled trade
            correlation_id: Optional correlation ID for tracing

        Returns:
            New cumulative trade value for today

        """
        self._reset_if_new_day()

        self._session_cumulative += abs(trade_value)

        logger.info(
            "Trade recorded against daily limit",
            trade_value=str(trade_value),
            new_cumulative=str(self._session_cumulative),
            remaining_headroom=str(self._daily_limit - self._session_cumulative),
            correlation_id=correlation_id,
        )

        return self._session_cumulative

    def assert_within_limit(
        self,
        proposed_trade_value: Decimal,
        correlation_id: str | None = None,
    ) -> DailyTradeLimitCheck:
        """Assert that a trade is within limits, raising if not.

        Convenience method that combines check and raise in one call.

        Args:
            proposed_trade_value: Absolute value of proposed trade
            correlation_id: Optional correlation ID for tracing

        Returns:
            DailyTradeLimitCheck if within limit

        Raises:
            DailyTradeLimitExceededError: If trade would exceed limit

        """
        check = self.check_limit(proposed_trade_value, correlation_id)

        if not check.is_within_limit:
            raise DailyTradeLimitExceededError(
                f"Trade of ${proposed_trade_value} would exceed daily limit. "
                f"Current cumulative: ${check.current_cumulative}, "
                f"Limit: ${check.daily_limit}, "
                f"Would exceed by: ${check.would_exceed_by}",
                proposed_trade_value=proposed_trade_value,
                current_cumulative=check.current_cumulative,
                daily_limit=check.daily_limit,
                headroom=check.headroom,
            )

        return check

    @property
    def daily_limit(self) -> Decimal:
        """Get the configured daily limit."""
        return self._daily_limit

    @property
    def current_cumulative(self) -> Decimal:
        """Get current session cumulative value."""
        self._reset_if_new_day()
        return self._session_cumulative
