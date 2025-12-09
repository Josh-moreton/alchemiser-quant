"""Business Unit: data | Status: current.

Data refresh service for incremental market data updates.

Orchestrates the process of identifying symbols that need data updates,
fetching new bars from Alpaca, and storing them in S3.
"""

from __future__ import annotations

import os
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd

from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.services.market_data_service import MarketDataService

from .market_data_store import MarketDataStore
from .symbol_extractor import get_all_configured_symbols

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)

# Default lookback for initial data seeding (1 year of trading days + buffer)
DEFAULT_INITIAL_LOOKBACK_DAYS = 400

# Minimum bars required for indicator computation
MIN_BARS_REQUIRED = 252

# Rate limiting: Alpaca allows 200 requests/minute for free tier
# We'll be conservative with 100 requests/minute = 0.6s between requests
API_RATE_LIMIT_DELAY = 0.6  # seconds between API calls


class DataRefreshService:
    """Service for refreshing market data from Alpaca to S3.

    Handles incremental updates by checking existing data and only fetching
    new bars since the last update. For new symbols, fetches full history.

    Attributes:
        market_data_store: S3 store for reading/writing data
        alpaca_manager: Alpaca client for fetching data
        market_data_service: Service wrapper for Alpaca data calls

    """

    def __init__(
        self,
        market_data_store: MarketDataStore | None = None,
        alpaca_manager: AlpacaManager | None = None,
    ) -> None:
        """Initialize data refresh service.

        Args:
            market_data_store: S3 store instance. If None, creates from env vars.
            alpaca_manager: Alpaca client. If None, creates from env vars.

        """
        self.market_data_store = market_data_store or MarketDataStore()

        if alpaca_manager is None:
            alpaca_manager = AlpacaManager(
                api_key=os.environ.get("ALPACA__KEY", ""),
                secret_key=os.environ.get("ALPACA__SECRET", ""),
                paper=True,  # Data API works same for paper/live
            )
        self.alpaca_manager = alpaca_manager
        self.market_data_service = MarketDataService(alpaca_manager)

        logger.info("DataRefreshService initialized")

    def _get_symbols_to_refresh(self, base_path: Path | None = None) -> set[str]:
        """Get all symbols that need data refresh.

        Args:
            base_path: Base path to the_alchemiser directory for symbol extraction

        Returns:
            Set of ticker symbols from strategy configurations

        """
        return get_all_configured_symbols(base_path)

    def _calculate_fetch_range(
        self,
        symbol: str,
    ) -> tuple[str, str] | None:
        """Calculate date range for fetching new data.

        Args:
            symbol: Ticker symbol

        Returns:
            Tuple of (start_date, end_date) as YYYY-MM-DD strings,
            or None if no fetch needed

        """
        # Get existing metadata
        metadata = self.market_data_store.get_metadata(symbol)

        # Calculate end date (yesterday, since today's bar isn't complete)
        end_date = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")

        if metadata is None:
            # No existing data - fetch full history
            start_date = (
                datetime.now(UTC) - timedelta(days=DEFAULT_INITIAL_LOOKBACK_DAYS)
            ).strftime("%Y-%m-%d")
            logger.info(
                "New symbol - fetching full history",
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
            )
            return start_date, end_date

        # Existing data - fetch only new bars
        last_bar_date = datetime.strptime(metadata.last_bar_date, "%Y-%m-%d").replace(tzinfo=UTC)
        start_date = (last_bar_date + timedelta(days=1)).strftime("%Y-%m-%d")

        # Check if we need to fetch anything
        if start_date > end_date:
            logger.debug(
                "Data is up to date",
                symbol=symbol,
                last_bar_date=metadata.last_bar_date,
            )
            return None

        logger.info(
            "Incremental update",
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            last_bar_date=metadata.last_bar_date,
        )
        return start_date, end_date

    def _fetch_bars_from_alpaca(
        self,
        symbol: str,
        start_date: str,
        end_date: str,
    ) -> pd.DataFrame:
        """Fetch historical bars from Alpaca API.

        Args:
            symbol: Ticker symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with OHLCV data

        Raises:
            RuntimeError: If fetch fails after retries

        """
        bars_list = self.market_data_service.get_historical_bars(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            timeframe="1Day",
        )

        if not bars_list:
            logger.warning(
                "No bars returned from Alpaca",
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
            )
            return pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame(bars_list)

        # Ensure consistent column names
        column_mapping = {
            "t": "timestamp",
            "o": "open",
            "h": "high",
            "l": "low",
            "c": "close",
            "v": "volume",
        }
        df = df.rename(columns=column_mapping)

        # Keep only standard OHLCV columns
        required_cols = ["timestamp", "open", "high", "low", "close", "volume"]
        available_cols = [c for c in required_cols if c in df.columns]
        df = df[available_cols]

        logger.debug(
            "Fetched bars from Alpaca",
            symbol=symbol,
            rows=len(df),
        )

        return df

    def refresh_symbol(self, symbol: str) -> bool:
        """Refresh data for a single symbol.

        Args:
            symbol: Ticker symbol to refresh

        Returns:
            True if successful (including no-op), False on error

        """
        try:
            # Calculate what needs to be fetched
            fetch_range = self._calculate_fetch_range(symbol)

            if fetch_range is None:
                # No update needed
                return True

            start_date, end_date = fetch_range

            # Fetch from Alpaca
            new_bars = self._fetch_bars_from_alpaca(symbol, start_date, end_date)

            if new_bars.empty:
                logger.warning(
                    "No new bars available",
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                )
                return True  # Not an error, just no data

            # Append to existing data
            success = self.market_data_store.append_bars(symbol, new_bars)

            if success:
                logger.info(
                    "Successfully refreshed symbol",
                    symbol=symbol,
                    new_bars=len(new_bars),
                )
            else:
                logger.error(
                    "Failed to store bars",
                    symbol=symbol,
                )

            return success

        except Exception as e:
            logger.error(
                "Error refreshing symbol",
                symbol=symbol,
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

    def refresh_all_symbols(self, base_path: Path | None = None) -> dict[str, bool]:
        """Refresh data for all configured symbols.

        Args:
            base_path: Base path for symbol extraction

        Returns:
            Dict mapping symbol to success status

        """
        symbols = self._get_symbols_to_refresh(base_path)

        logger.info(
            "Starting full data refresh",
            symbol_count=len(symbols),
        )

        results: dict[str, bool] = {}

        for i, symbol in enumerate(sorted(symbols)):
            results[symbol] = self.refresh_symbol(symbol)

            # Rate limiting: pause between API calls (skip after last symbol)
            if i < len(symbols) - 1:
                time.sleep(API_RATE_LIMIT_DELAY)

        # Summary logging
        success_count = sum(results.values())
        failure_count = len(results) - success_count

        logger.info(
            "Data refresh complete",
            total=len(results),
            success=success_count,
            failed=failure_count,
            failed_symbols=[s for s, ok in results.items() if not ok],
        )

        return results

    def seed_initial_data(
        self,
        symbols: list[str],
        lookback_days: int = DEFAULT_INITIAL_LOOKBACK_DAYS,
    ) -> dict[str, bool]:
        """Seed initial data for a list of symbols.

        Used for initial data population. Fetches full history for each symbol.

        Args:
            symbols: List of ticker symbols to seed
            lookback_days: Days of history to fetch

        Returns:
            Dict mapping symbol to success status

        """
        logger.info(
            "Starting initial data seeding",
            symbol_count=len(symbols),
            lookback_days=lookback_days,
        )

        end_date = (datetime.now(UTC) - timedelta(days=1)).strftime("%Y-%m-%d")
        start_date = (datetime.now(UTC) - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

        results: dict[str, bool] = {}
        sorted_symbols = sorted(symbols)

        for i, symbol in enumerate(sorted_symbols):
            try:
                # Fetch from Alpaca
                bars = self._fetch_bars_from_alpaca(symbol, start_date, end_date)

                if bars.empty:
                    logger.warning(
                        "No data available for symbol",
                        symbol=symbol,
                    )
                    results[symbol] = False
                    continue

                # Write to S3
                success = self.market_data_store.write_symbol_data(symbol, bars)
                results[symbol] = success

                if success:
                    logger.info(
                        "Seeded symbol",
                        symbol=symbol,
                        bars=len(bars),
                        progress=f"{i + 1}/{len(sorted_symbols)}",
                    )

            except Exception as e:
                logger.error(
                    "Error seeding symbol",
                    symbol=symbol,
                    error=str(e),
                )
                results[symbol] = False

            # Rate limiting: pause between API calls (skip after last symbol)
            if i < len(sorted_symbols) - 1:
                time.sleep(API_RATE_LIMIT_DELAY)

        # Summary
        success_count = sum(results.values())
        logger.info(
            "Initial seeding complete",
            total=len(results),
            success=success_count,
            failed=len(results) - success_count,
        )

        return results
