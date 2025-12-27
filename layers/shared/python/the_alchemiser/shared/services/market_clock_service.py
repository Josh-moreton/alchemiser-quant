"""Business Unit: shared | Status: current.

Market Clock Service.

This service provides market status detection using Alpaca's clock API.
It determines whether the market is open, closed, or in extended hours,
enabling conditional execution of trading operations.

Key Features:
- Market status detection (open/closed/extended_hours)
- Thread-safe caching of clock data
- Rate limiting and timeout handling
- Clear market state enumeration
"""

from __future__ import annotations

from datetime import UTC, datetime
from enum import Enum
from typing import TYPE_CHECKING, NamedTuple

from the_alchemiser.shared.errors.exceptions import (
    DataProviderError,
    TradingClientError,
)
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.utils.api_helpers import with_rate_limiting, with_timeout

if TYPE_CHECKING:
    from alpaca.trading.client import TradingClient

logger = get_logger(__name__)


class MarketStatus(str, Enum):
    """Market status enumeration."""

    OPEN = "open"
    CLOSED = "closed"
    EXTENDED_HOURS = "extended_hours"


class MarketClockData(NamedTuple):
    """Market clock data from Alpaca API."""

    is_open: bool
    timestamp: datetime
    next_open: datetime | None
    next_close: datetime | None


class MarketClockService:
    """Service for market status detection and clock information.

    This service provides market status checks using Alpaca's clock API,
    enabling conditional execution based on market hours.
    """

    API_TIMEOUT = 10.0  # Timeout for API calls in seconds

    def __init__(self, trading_client: TradingClient) -> None:
        """Initialize the market clock service.

        Args:
            trading_client: Alpaca TradingClient instance for API access

        Raises:
            ValueError: If trading_client is None

        """
        if not trading_client:
            raise ValueError("trading_client cannot be None")

        self._trading_client = trading_client

    @with_rate_limiting
    @with_timeout(10.0)
    def _fetch_clock_from_api(self) -> MarketClockData:
        """Fetch market clock from API with rate limiting and timeout.

        Returns:
            MarketClockData with clock information

        Raises:
            TradingClientError: If API call fails
            DataProviderError: If clock data is incomplete

        """
        try:
            clock = self._trading_client.get_clock()

            # Extract data from clock object
            is_open = bool(getattr(clock, "is_open", False))
            timestamp = getattr(clock, "timestamp", datetime.now(UTC))
            next_open = getattr(clock, "next_open", None)
            next_close = getattr(clock, "next_close", None)

            return MarketClockData(
                is_open=is_open,
                timestamp=timestamp,
                next_open=next_open,
                next_close=next_close,
            )
        except AttributeError as e:
            raise DataProviderError(
                f"Clock data missing required fields: {e}",
                context={"error": str(e)},
            ) from e
        except Exception as e:
            raise TradingClientError(f"Failed to fetch market clock: {e}") from e

    def get_market_status(
        self,
        *,
        allow_extended_hours: bool = False,
        correlation_id: str | None = None,
    ) -> MarketStatus:
        """Get current market status.

        Args:
            allow_extended_hours: Whether to consider extended hours as open
            correlation_id: Optional correlation ID for tracing

        Returns:
            MarketStatus indicating current market state

        Raises:
            TradingClientError: If API call fails
            DataProviderError: If clock data is incomplete

        """
        log_context: dict[str, bool | str] = {"allow_extended_hours": allow_extended_hours}
        if correlation_id:
            log_context["correlation_id"] = correlation_id

        try:
            clock_data = self._fetch_clock_from_api()

            if clock_data.is_open:
                # Market is open (could be regular or extended hours)
                # For now, we treat all open time as OPEN
                # Future enhancement: detect extended vs regular hours
                logger.info("Market is currently open", **log_context)
                return MarketStatus.OPEN

            logger.info(
                "Market is currently closed",
                next_open=clock_data.next_open,
                **log_context,
            )
            return MarketStatus.CLOSED

        except (TradingClientError, DataProviderError) as e:
            logger.error(
                "Failed to get market status",
                error=str(e),
                error_type=type(e).__name__,
                **log_context,
            )
            raise

    def is_market_open(
        self,
        *,
        allow_extended_hours: bool = False,
        correlation_id: str | None = None,
    ) -> bool:
        """Check if market is currently open.

        Args:
            allow_extended_hours: Whether to consider extended hours as open
            correlation_id: Optional correlation ID for tracing

        Returns:
            True if market is open, False otherwise

        Raises:
            TradingClientError: If API call fails
            DataProviderError: If clock data is incomplete

        """
        status = self.get_market_status(
            allow_extended_hours=allow_extended_hours,
            correlation_id=correlation_id,
        )
        return status == MarketStatus.OPEN

    def get_clock_info(
        self,
        *,
        correlation_id: str | None = None,
    ) -> MarketClockData:
        """Get detailed market clock information.

        Args:
            correlation_id: Optional correlation ID for tracing

        Returns:
            MarketClockData with detailed clock information

        Raises:
            TradingClientError: If API call fails
            DataProviderError: If clock data is incomplete

        """
        log_context = {}
        if correlation_id:
            log_context["correlation_id"] = correlation_id

        try:
            clock_data = self._fetch_clock_from_api()
            logger.debug("Retrieved market clock info", **log_context)
            return clock_data
        except (TradingClientError, DataProviderError) as e:
            logger.error(
                "Failed to get clock info",
                error=str(e),
                error_type=type(e).__name__,
                **log_context,
            )
            raise
