"""Business Unit: backtest | Status: current.

Data fetcher for backtest module.

Fetch historical market data from Alpaca and store locally as Parquet files
for use in backtesting. Supports incremental updates and initial seeding.
"""

from __future__ import annotations

import os
import time
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Final

import pandas as pd

from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.services.market_data_service import MarketDataService

logger = get_logger(__name__)

# Module constants
MODULE_NAME: Final[str] = "backtest_v2.adapters.data_fetcher"

# Default lookback for initial data seeding (1+ year for 252 trading days)
DEFAULT_LOOKBACK_DAYS: Final[int] = 400

# Rate limiting: Conservative to stay under Alpaca limits
API_RATE_LIMIT_DELAY: Final[float] = 0.6  # seconds between API calls


class BacktestDataFetcher:
    """Fetch historical market data from Alpaca to local Parquet files.

    Designed specifically for the backtest module. Downloads OHLCV data
    and stores it in the standard backtest data directory structure:
    data/historical/{SYMBOL}/{YEAR}/daily.parquet

    Attributes:
        data_dir: Root directory for historical data storage
        alpaca_manager: Alpaca client for API access
        market_data_service: Service wrapper for Alpaca data calls

    Example:
        >>> fetcher = BacktestDataFetcher(data_dir=Path("data/historical"))
        >>> results = fetcher.fetch_symbols(["SPY", "AAPL", "QQQ"], lookback_days=400)
        >>> print(f"Fetched {sum(results.values())} of {len(results)} symbols")

    """

    def __init__(
        self,
        data_dir: Path | str,
        alpaca_manager: AlpacaManager | None = None,
    ) -> None:
        """Initialize the data fetcher.

        Args:
            data_dir: Root directory for storing historical data
            alpaca_manager: Optional Alpaca client. If None, creates from env vars.

        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Initialize Alpaca client
        if alpaca_manager is None:
            alpaca_manager = AlpacaManager(
                api_key=os.environ.get("ALPACA__KEY", ""),
                secret_key=os.environ.get("ALPACA__SECRET", ""),
                paper=True,
            )
        self.alpaca_manager = alpaca_manager
        self.market_data_service = MarketDataService(alpaca_manager)

        logger.info(
            "BacktestDataFetcher initialized",
            module=MODULE_NAME,
            data_dir=str(self.data_dir),
        )

    def _get_symbol_metadata(self, symbol: str) -> dict[str, str | int] | None:
        """Get metadata about existing local data for a symbol.

        Args:
            symbol: Ticker symbol

        Returns:
            Dict with 'last_date', 'row_count' or None if no data exists

        """
        symbol_dir = self.data_dir / symbol.upper()
        if not symbol_dir.exists():
            return None

        parquet_files = list(symbol_dir.glob("**/daily.parquet"))
        if not parquet_files:
            return None

        # Load and find the latest date
        all_dfs = []
        for pf in parquet_files:
            try:
                df = pd.read_parquet(pf)
                all_dfs.append(df)
            except Exception as e:
                logger.warning(
                    "Failed to read parquet file for metadata",
                    module=MODULE_NAME,
                    file=str(pf),
                    error=str(e),
                )

        if not all_dfs:
            return None

        combined = pd.concat(all_dfs)
        last_date = combined.index.max()

        return {
            "last_date": last_date.strftime("%Y-%m-%d")
            if hasattr(last_date, "strftime")
            else str(last_date),
            "row_count": len(combined),
        }

    def _fetch_from_alpaca(
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
            DataFrame with OHLCV data indexed by timestamp

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
                module=MODULE_NAME,
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
            )
            return pd.DataFrame()

        # Convert to DataFrame
        df = pd.DataFrame(bars_list)

        # Normalize column names
        column_mapping = {
            "t": "timestamp",
            "o": "Open",
            "h": "High",
            "l": "Low",
            "c": "Close",
            "v": "Volume",
            "open": "Open",
            "high": "High",
            "low": "Low",
            "close": "Close",
            "volume": "Volume",
        }
        df = df.rename(columns=column_mapping)

        # Set timestamp as index
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
            df = df.set_index("timestamp")
        elif "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"], utc=True)
            df = df.set_index("Date")

        # Keep only required columns
        required_cols = ["Open", "High", "Low", "Close", "Volume"]
        df = df[[c for c in required_cols if c in df.columns]]

        # Sort by index
        df = df.sort_index()

        logger.debug(
            "Fetched bars from Alpaca",
            module=MODULE_NAME,
            symbol=symbol,
            rows=len(df),
        )

        return df

    def _save_to_parquet(self, symbol: str, df: pd.DataFrame) -> bool:
        """Save DataFrame to Parquet files organized by year.

        Args:
            symbol: Ticker symbol
            df: DataFrame with OHLCV data indexed by timestamp

        Returns:
            True if successful, False otherwise

        """
        if df.empty:
            return False

        symbol_upper = symbol.upper()
        symbol_dir = self.data_dir / symbol_upper
        symbol_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Group by year and save
            df["year"] = df.index.year
            years = df["year"].unique()

            for year in years:
                year_df = df[df["year"] == year].drop(columns=["year"])
                year_dir = symbol_dir / str(year)
                year_dir.mkdir(parents=True, exist_ok=True)

                parquet_path = year_dir / "daily.parquet"

                # If file exists, merge with existing data
                if parquet_path.exists():
                    try:
                        existing_df = pd.read_parquet(parquet_path)
                        combined = pd.concat([existing_df, year_df])
                        combined = combined[~combined.index.duplicated(keep="last")]
                        combined = combined.sort_index()
                        combined.to_parquet(parquet_path)
                    except Exception as merge_error:
                        logger.warning(
                            "Failed to merge with existing data, overwriting",
                            module=MODULE_NAME,
                            file=str(parquet_path),
                            error=str(merge_error),
                        )
                        year_df.to_parquet(parquet_path)
                else:
                    year_df.to_parquet(parquet_path)

                logger.debug(
                    "Saved parquet file",
                    module=MODULE_NAME,
                    symbol=symbol_upper,
                    year=year,
                    rows=len(year_df),
                )

            return True

        except Exception as e:
            logger.error(
                "Failed to save parquet files",
                module=MODULE_NAME,
                symbol=symbol_upper,
                error=str(e),
            )
            return False

    def fetch_symbol(
        self,
        symbol: str,
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
        *,
        force_full: bool = False,
    ) -> bool:
        """Fetch data for a single symbol.

        Performs incremental update if data already exists, unless force_full=True.

        Args:
            symbol: Ticker symbol
            lookback_days: Number of days to fetch for new symbols
            force_full: If True, fetch full history even if data exists

        Returns:
            True if successful, False otherwise

        """
        symbol_upper = symbol.upper()

        try:
            # Calculate date range
            end_date = datetime.now(UTC).strftime("%Y-%m-%d")

            metadata = self._get_symbol_metadata(symbol_upper)
            if metadata and not force_full:
                # Incremental update
                last_date = datetime.strptime(str(metadata["last_date"]), "%Y-%m-%d").replace(
                    tzinfo=UTC
                )
                start_date = (last_date + timedelta(days=1)).strftime("%Y-%m-%d")

                if start_date > end_date:
                    logger.info(
                        "Symbol data is up to date",
                        module=MODULE_NAME,
                        symbol=symbol_upper,
                        last_date=str(metadata["last_date"]),
                    )
                    return True

                logger.info(
                    "Performing incremental update",
                    module=MODULE_NAME,
                    symbol=symbol_upper,
                    start_date=start_date,
                    end_date=end_date,
                )
            else:
                # Full fetch
                start_date = (datetime.now(UTC) - timedelta(days=lookback_days)).strftime(
                    "%Y-%m-%d"
                )
                logger.info(
                    "Fetching full history",
                    module=MODULE_NAME,
                    symbol=symbol_upper,
                    start_date=start_date,
                    end_date=end_date,
                    lookback_days=lookback_days,
                )

            # Fetch from Alpaca
            df = self._fetch_from_alpaca(symbol_upper, start_date, end_date)

            if df.empty:
                logger.warning(
                    "No data available",
                    module=MODULE_NAME,
                    symbol=symbol_upper,
                )
                return False

            # Save to local Parquet
            success = self._save_to_parquet(symbol_upper, df)

            if success:
                logger.info(
                    "Successfully fetched symbol data",
                    module=MODULE_NAME,
                    symbol=symbol_upper,
                    rows=len(df),
                )

            return success

        except Exception as e:
            logger.error(
                "Error fetching symbol",
                module=MODULE_NAME,
                symbol=symbol_upper,
                error=str(e),
                error_type=type(e).__name__,
            )
            return False

    def fetch_symbols(
        self,
        symbols: list[str],
        lookback_days: int = DEFAULT_LOOKBACK_DAYS,
        *,
        force_full: bool = False,
    ) -> dict[str, bool]:
        """Fetch data for multiple symbols with rate limiting.

        Args:
            symbols: List of ticker symbols
            lookback_days: Number of days to fetch for new symbols
            force_full: If True, fetch full history for all symbols

        Returns:
            Dict mapping symbol to success status

        """
        logger.info(
            "Starting batch fetch",
            module=MODULE_NAME,
            symbol_count=len(symbols),
            lookback_days=lookback_days,
            force_full=force_full,
        )

        results: dict[str, bool] = {}
        sorted_symbols = sorted({s.upper() for s in symbols})

        for i, symbol in enumerate(sorted_symbols):
            results[symbol] = self.fetch_symbol(
                symbol,
                lookback_days=lookback_days,
                force_full=force_full,
            )

            # Rate limiting (skip after last symbol)
            if i < len(sorted_symbols) - 1:
                time.sleep(API_RATE_LIMIT_DELAY)

        # Summary
        success_count = sum(results.values())
        failed_symbols = [s for s, ok in results.items() if not ok]

        logger.info(
            "Batch fetch complete",
            module=MODULE_NAME,
            total=len(results),
            success=success_count,
            failed=len(results) - success_count,
            failed_symbols=failed_symbols[:10] if failed_symbols else [],
        )

        return results

    def get_available_symbols(self) -> list[str]:
        """Get list of symbols with local data.

        Returns:
            Sorted list of symbol names

        """
        symbols = []
        if self.data_dir.exists():
            for item in self.data_dir.iterdir():
                if (
                    item.is_dir()
                    and not item.name.startswith(".")
                    and list(item.glob("**/daily.parquet"))
                ):
                    symbols.append(item.name.upper())

        return sorted(symbols)

    def get_missing_symbols(self, required: list[str]) -> list[str]:
        """Find symbols that are required but not available locally.

        Args:
            required: List of required ticker symbols

        Returns:
            List of symbols that need to be fetched

        """
        available = set(self.get_available_symbols())
        required_set = {s.upper() for s in required}
        return sorted(required_set - available)

    def check_data_freshness(
        self,
        symbol: str,
        max_age_days: int = 7,
    ) -> bool:
        """Check if local data is fresh enough.

        Args:
            symbol: Ticker symbol
            max_age_days: Maximum acceptable age in days

        Returns:
            True if data is fresh, False if stale or missing

        """
        metadata = self._get_symbol_metadata(symbol.upper())
        if metadata is None:
            return False

        last_date = datetime.strptime(str(metadata["last_date"]), "%Y-%m-%d").replace(tzinfo=UTC)
        age = (datetime.now(UTC) - last_date).days

        return age <= max_age_days
