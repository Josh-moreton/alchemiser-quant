"""Business Unit: scripts | Status: current.

Historical data manager for backtesting.

Coordinates data download, validation, and storage.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from pathlib import Path

# Add project root to path for imports
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.backtest.storage.data_store import DataStore  # noqa: E402
from scripts.backtest.storage.providers.alpaca_historical import (  # noqa: E402
    AlpacaHistoricalProvider,
)
from the_alchemiser.shared.logging import get_logger  # noqa: E402

logger = get_logger(__name__)


class DataManager:
    """Manages historical data download and storage.

    Coordinates between Alpaca provider and local data store.
    """

    def __init__(self, data_store: DataStore | None = None) -> None:
        """Initialize data manager.

        Args:
            data_store: Optional DataStore instance (creates default if None)

        """
        # Try to initialize provider, but don't fail if credentials are missing (e.g., in tests)
        try:
            self.provider = AlpacaHistoricalProvider()
        except (ValueError, Exception) as e:
            logger.warning(
                f"Failed to initialize AlpacaHistoricalProvider: {e}. "
                "Auto-download will not be available."
            )
            self.provider = None
        
        # Create or use provided data store
        if data_store:
            self.data_store = data_store
            # If data_store was provided, set the provider if available
            if self.provider and not data_store.data_provider:
                data_store.data_provider = self.provider
        else:
            # Create new data store with provider if available
            self.data_store = DataStore(data_provider=self.provider)
        
        logger.info("DataManager initialized")

    def _data_exists_for_range(
        self, symbol: str, start_date: datetime, end_date: datetime
    ) -> bool:
        """Check if data exists for the given symbol and date range.

        Args:
            symbol: Stock symbol
            start_date: Required start date
            end_date: Required end date

        Returns:
            True if data exists and covers the entire date range

        """
        metadata = self.data_store.get_metadata(symbol)
        return (
            metadata is not None
            and metadata.start_date <= start_date
            and metadata.end_date >= end_date
        )

    def download_data(
        self,
        symbols: list[str],
        start_date: datetime,
        end_date: datetime,
        *,
        force: bool = False,
    ) -> dict[str, bool]:
        """Download historical data for symbols.

        Args:
            symbols: List of symbols to download
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            force: If True, re-download even if data exists

        Returns:
            Dictionary mapping symbol to success status

        """
        if not self.provider:
            logger.error("Cannot download data: provider not initialized")
            return {symbol: False for symbol in symbols}
        
        logger.info(
            f"Downloading data for {len(symbols)} symbols",
            symbol_count=len(symbols),
            symbols=symbols,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
            force=force,
        )

        # Ensure dates are timezone-aware
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=UTC)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=UTC)

        results: dict[str, bool] = {}

        for symbol in symbols:
            try:
                # Check if data already exists
                if not force and self._data_exists_for_range(
                    symbol, start_date, end_date
                ):
                    logger.info(
                        f"Data already exists for {symbol}, skipping",
                        symbol=symbol,
                    )
                    results[symbol] = True
                    continue

                # Download data from Alpaca
                bars = self.provider.fetch_daily_bars(symbol, start_date, end_date)

                if not bars:
                    logger.warning(f"No data downloaded for {symbol}", symbol=symbol)
                    results[symbol] = False
                    continue

                # Save to data store
                self.data_store.save_bars(symbol, bars)

                # Validate saved data
                metadata = self.data_store.get_metadata(symbol)
                if metadata and metadata.bar_count > 0:
                    logger.info(
                        f"Successfully downloaded and saved data for {symbol}",
                        symbol=symbol,
                        bar_count=metadata.bar_count,
                    )
                    results[symbol] = True
                else:
                    logger.error(
                        f"Data validation failed for {symbol}",
                        symbol=symbol,
                    )
                    results[symbol] = False

            except Exception as e:
                logger.error(
                    f"Failed to download data for {symbol}",
                    symbol=symbol,
                    error=str(e),
                )
                results[symbol] = False

        successful = len([s for s, success in results.items() if success])
        logger.info(
            f"Download complete: {successful}/{len(symbols)} successful",
            successful=successful,
            total=len(symbols),
        )

        return results

    def get_available_data(self, symbol: str) -> dict[str, str | int | bool] | None:
        """Get information about available data for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            Dictionary with data info or None if no data exists

        """
        metadata = self.data_store.get_metadata(symbol)
        if not metadata:
            return None

        return {
            "symbol": metadata.symbol,
            "start_date": metadata.start_date.isoformat(),
            "end_date": metadata.end_date.isoformat(),
            "bar_count": metadata.bar_count,
            "last_updated": metadata.last_updated.isoformat(),
            "has_gaps": metadata.has_gaps,
        }

    def validate_data_availability(
        self, symbols: list[str], start_date: datetime, end_date: datetime
    ) -> dict[str, bool]:
        """Validate that data is available for symbols in date range.

        Args:
            symbols: List of symbols to validate
            start_date: Required start date
            end_date: Required end date

        Returns:
            Dictionary mapping symbol to availability status

        """
        logger.info(
            f"Validating data availability for {len(symbols)} symbols",
            symbol_count=len(symbols),
        )

        results: dict[str, bool] = {}

        for symbol in symbols:
            metadata = self.data_store.get_metadata(symbol)
            if not metadata:
                results[symbol] = False
                continue

            # Check if date range is covered
            is_available = (
                metadata.start_date <= start_date
                and metadata.end_date >= end_date
                and metadata.bar_count > 0
            )
            results[symbol] = is_available

        available = len([s for s, avail in results.items() if avail])
        logger.info(
            f"Data availability: {available}/{len(symbols)} symbols available",
            available=available,
            total=len(symbols),
        )

        return results
