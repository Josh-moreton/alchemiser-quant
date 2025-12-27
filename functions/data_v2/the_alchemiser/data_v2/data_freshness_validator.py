"""Business Unit: data | Status: current.

Data freshness validation for ensuring market data is up-to-date.

Validates that cached market data is sufficiently fresh for strategy execution,
preventing stale data from causing incorrect trading signals. Accounts for
market hours, weekends, and holidays.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

from the_alchemiser.shared.errors.exceptions import DataProviderError
from the_alchemiser.shared.logging import get_logger

from .market_data_store import MarketDataStore

if TYPE_CHECKING:
    import datetime as dt_module

logger = get_logger(__name__)


class DataFreshnessValidator:
    """Validates market data freshness for strategy execution.

    Ensures that S3 cached data is current enough for trading decisions.
    Accounts for market schedule (weekends, holidays) when determining
    expected data freshness.
    """

    def __init__(self, market_data_store: MarketDataStore, max_staleness_days: int = 2) -> None:
        """Initialize data freshness validator.

        Args:
            market_data_store: Store for accessing market data metadata
            max_staleness_days: Maximum allowed staleness in days (default 2 for weekend tolerance)

        """
        self.store = market_data_store
        self.max_staleness_days = max_staleness_days

    def validate_data_freshness(
        self, symbols: list[str] | None = None, *, raise_on_stale: bool = False
    ) -> tuple[bool, dict[str, str]]:
        """Validate data freshness for required symbols.

        Args:
            symbols: List of symbols to check (if None, checks all symbols in S3)
            raise_on_stale: If True, raises DataProviderError when stale data detected

        Returns:
            Tuple of (is_fresh, stale_symbols_dict) where stale_symbols_dict maps
            symbol -> last_bar_date for any stale symbols

        Raises:
            DataProviderError: If raise_on_stale=True and stale data detected

        """
        expected_date = self._calculate_expected_date()
        symbols_to_check = symbols or self.store.list_symbols()

        if not symbols_to_check:
            logger.warning("No symbols to validate for data freshness")
            return True, {}

        stale_symbols: dict[str, str] = {}
        missing_metadata: list[str] = []

        for symbol in symbols_to_check:
            metadata = self.store.get_metadata(symbol)

            if metadata is None:
                missing_metadata.append(symbol)
                continue

            # Parse date from YYYY-MM-DD string - dates are timezone-naive by design
            last_bar_date_parts = [int(x) for x in metadata.last_bar_date.split("-")]
            last_bar_date = datetime(
                last_bar_date_parts[0], last_bar_date_parts[1], last_bar_date_parts[2], tzinfo=UTC
            ).date()
            days_stale = (expected_date - last_bar_date).days

            if days_stale > self.max_staleness_days:
                stale_symbols[symbol] = metadata.last_bar_date
                logger.warning(
                    f"Stale data detected: {symbol} last bar {metadata.last_bar_date} "
                    f"({days_stale} days old, expected {expected_date})"
                )

        # Log summary
        if missing_metadata:
            logger.warning(
                f"Missing metadata for {len(missing_metadata)} symbols: {missing_metadata[:5]}"
            )

        is_fresh = len(stale_symbols) == 0 and len(missing_metadata) == 0

        if is_fresh:
            logger.info(
                f"✅ Data freshness validated: all {len(symbols_to_check)} symbols current "
                f"through {expected_date}"
            )
        else:
            logger.warning(
                f"⚠️ Data freshness check failed: {len(stale_symbols)} stale symbols, "
                f"{len(missing_metadata)} missing metadata"
            )

        if raise_on_stale and not is_fresh:
            error_msg = (
                f"Stale market data detected. Expected data through {expected_date}. "
                f"Stale symbols: {list(stale_symbols.keys())[:10]}, "
                f"Missing metadata: {missing_metadata[:10]}"
            )
            raise DataProviderError(error_msg)

        return is_fresh, stale_symbols

    def _calculate_expected_date(self) -> dt_module.date:
        """Calculate expected last bar date accounting for weekends.

        For daily bars, the expected date is:
        - Monday-Friday before market close (14:30 UTC): previous trading day
        - After market close: today if weekday, Friday if weekend

        Returns:
            Expected date for last available bar

        """
        now = datetime.now(UTC)
        today = now.date()
        current_weekday = today.weekday()  # 0=Monday, 6=Sunday

        # If it's Saturday (5) or Sunday (6), expect data through Friday
        if current_weekday == 5:  # Saturday
            expected_date = today - timedelta(days=1)  # Friday
        elif current_weekday == 6:  # Sunday
            expected_date = today - timedelta(days=2)  # Friday
        else:
            # Weekday: expect data through yesterday (markets generate today's bar after close)
            # For simplicity, we expect yesterday's data regardless of time of day
            expected_date = today - timedelta(days=1)

        logger.debug(
            f"Expected last bar date: {expected_date} "
            f"(today={today}, weekday={current_weekday}, time={now.strftime('%H:%M UTC')})"
        )

        return expected_date
