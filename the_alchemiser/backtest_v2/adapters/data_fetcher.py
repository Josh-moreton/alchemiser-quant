"""Business Unit: backtest | Status: current.

Data fetcher for backtest module.

Fetch historical market data from S3 and store locally as Parquet files
for use in backtesting. Supports incremental updates and initial seeding.

Data Cascade:
    1. Local Parquet files (fastest, offline-first)
    2. S3 bucket fallback (alchemiser-{stage}-market-data)

Note: Alpaca API is NOT used for backtests. All historical data comes from
S3 which is seeded separately via scripts/seed_market_data.py.
"""

from __future__ import annotations

import os
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pandas as pd

from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    from the_alchemiser.data_v2.market_data_store import MarketDataStore

logger = get_logger(__name__)

# Module constants
MODULE_NAME: Final[str] = "backtest_v2.adapters.data_fetcher"

# Default lookback for initial data seeding (1+ year for 252 trading days)
DEFAULT_LOOKBACK_DAYS: Final[int] = 400

# Rate limiting: Conservative for S3 calls (generous limit)
API_RATE_LIMIT_DELAY: Final[float] = 0.1  # seconds between S3 calls


class BacktestDataFetcher:
    """Fetch historical market data from S3 to local Parquet files.

    Designed specifically for the backtest module with offline-first approach.
    Downloads OHLCV data from S3 and stores it locally in the standard
    backtest data directory structure:
    data/historical/{SYMBOL}/{YEAR}/daily.parquet

    Data Cascade:
        1. Check local Parquet files (fastest)
        2. Fetch from S3 bucket (alchemiser-{stage}-market-data)
        3. Fail gracefully with clear error message

    Attributes:
        data_dir: Root directory for historical data storage
        market_data_store: S3 store for fetching data when not local

    Example:
        >>> fetcher = BacktestDataFetcher(data_dir=Path("data/historical"))
        >>> results = fetcher.fetch_symbols(["SPY", "AAPL", "QQQ"])
        >>> print(f"Synced {sum(results.values())} of {len(results)} symbols from S3")

    """

    def __init__(
        self,
        data_dir: Path | str,
        market_data_store: MarketDataStore | None = None,
    ) -> None:
        """Initialize the data fetcher.

        Args:
            data_dir: Root directory for storing historical data
            market_data_store: Optional S3 store. If None, creates from env vars.

        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        self._market_data_store = market_data_store
        self._s3_available: bool | None = None  # Cached availability check

        logger.info(
            "BacktestDataFetcher initialized",
            module=MODULE_NAME,
            data_dir=str(self.data_dir),
        )

    @property
    def market_data_store(self) -> MarketDataStore | None:
        """Lazy-initialized S3 market data store.

        Returns None if S3 is not available (no bucket configured or no credentials).
        """
        if self._market_data_store is not None:
            return self._market_data_store

        if self._s3_available is False:
            return None

        try:
            from the_alchemiser.data_v2.market_data_store import MarketDataStore

            # Try to get bucket name from env
            bucket_name = os.environ.get("MARKET_DATA_BUCKET")
            stage = os.environ.get("APP__STAGE", "dev")

            if not bucket_name:
                bucket_name = f"alchemiser-{stage}-market-data"

            self._market_data_store = MarketDataStore(bucket_name=bucket_name)
            self._s3_available = True

            logger.info(
                "S3 market data store initialized",
                module=MODULE_NAME,
                bucket=bucket_name,
            )
            return self._market_data_store

        except Exception as e:
            logger.warning(
                "S3 market data store not available - will use local data only",
                module=MODULE_NAME,
                error=str(e),
            )
            self._s3_available = False
            return None

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

    def _fetch_from_s3(
        self,
        symbol: str,
    ) -> pd.DataFrame:
        """Fetch historical data from S3 bucket.

        Args:
            symbol: Ticker symbol

        Returns:
            DataFrame with OHLCV data indexed by timestamp, or empty DataFrame

        """
        store = self.market_data_store
        if store is None:
            logger.warning(
                "S3 not available for fetching",
                module=MODULE_NAME,
                symbol=symbol,
            )
            return pd.DataFrame()

        try:
            df = store.read_symbol_data(symbol.upper(), use_cache=False)

            if df is None or df.empty:
                logger.debug(
                    "No data in S3 for symbol",
                    module=MODULE_NAME,
                    symbol=symbol,
                )
                return pd.DataFrame()

            # Normalize column names (S3 stores use lowercase)
            column_mapping = {
                "timestamp": "timestamp",
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

            # Keep only required columns
            required_cols = ["Open", "High", "Low", "Close", "Volume"]
            df = df[[c for c in required_cols if c in df.columns]]

            # Sort by index
            df = df.sort_index()

            logger.info(
                "Fetched data from S3",
                module=MODULE_NAME,
                symbol=symbol,
                rows=len(df),
            )

            return df

        except Exception as e:
            logger.error(
                "Failed to fetch from S3",
                module=MODULE_NAME,
                symbol=symbol,
                error=str(e),
            )
            return pd.DataFrame()

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
        """Fetch data for a single symbol from S3.

        Downloads data from S3 bucket and stores locally. Does NOT use Alpaca API.
        For seeding S3 with fresh data, use scripts/seed_market_data.py.

        Args:
            symbol: Ticker symbol
            lookback_days: Unused (kept for API compatibility)
            force_full: If True, re-fetch from S3 even if local data exists

        Returns:
            True if successful, False otherwise

        """
        symbol_upper = symbol.upper()

        try:
            # Check if we already have local data
            local_metadata = self._get_symbol_metadata(symbol_upper)

            if local_metadata and not force_full:
                # Check if S3 has newer data
                store = self.market_data_store
                if store is not None:
                    s3_metadata = store.get_metadata(symbol_upper)
                    if s3_metadata and s3_metadata.last_bar_date > str(local_metadata["last_date"]):
                        logger.info(
                            "S3 has newer data, will refresh",
                            module=MODULE_NAME,
                            symbol=symbol_upper,
                            local_last_date=str(local_metadata["last_date"]),
                            s3_last_date=s3_metadata.last_bar_date,
                        )
                    else:
                        logger.info(
                            "Symbol data already up to date locally",
                            module=MODULE_NAME,
                            symbol=symbol_upper,
                            last_date=str(local_metadata["last_date"]),
                            rows=local_metadata["row_count"],
                        )
                        return True
                else:
                    # No S3 available, use local data
                    logger.info(
                        "Symbol data available locally (S3 unavailable)",
                        module=MODULE_NAME,
                        symbol=symbol_upper,
                        last_date=str(local_metadata["last_date"]),
                        rows=local_metadata["row_count"],
                    )
                    return True

            # Fetch from S3
            logger.info(
                "Fetching symbol from S3",
                module=MODULE_NAME,
                symbol=symbol_upper,
            )
            df = self._fetch_from_s3(symbol_upper)

            if df.empty:
                logger.warning(
                    "No data available in S3",
                    module=MODULE_NAME,
                    symbol=symbol_upper,
                )
                return False

            # Save to local Parquet
            success = self._save_to_parquet(symbol_upper, df)

            if success:
                logger.info(
                    "Successfully synced symbol from S3",
                    module=MODULE_NAME,
                    symbol=symbol_upper,
                    rows=len(df),
                )

            return success

        except Exception as e:
            logger.error(
                "Error fetching symbol from S3",
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
        """Fetch data for multiple symbols from S3 with rate limiting.

        Args:
            symbols: List of ticker symbols
            lookback_days: Unused (kept for API compatibility)
            force_full: If True, re-fetch all from S3 even if local data exists

        Returns:
            Dict mapping symbol to success status

        """
        logger.info(
            "Starting batch sync from S3",
            module=MODULE_NAME,
            symbol_count=len(symbols),
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
            "Batch sync complete",
            module=MODULE_NAME,
            total=len(results),
            success=success_count,
            failed=len(results) - success_count,
            failed_symbols=failed_symbols[:10] if failed_symbols else [],
        )

        return results

    def sync_all_from_s3(self, *, force_full: bool = False) -> dict[str, bool]:
        """Sync all symbols from S3 to local storage.

        Discovers all symbols available in S3 and downloads them locally.
        This is useful for offline development.

        Args:
            force_full: If True, re-download even if local data exists

        Returns:
            Dict mapping symbol to success status

        """
        store = self.market_data_store
        if store is None:
            logger.error(
                "S3 not available - cannot sync",
                module=MODULE_NAME,
            )
            return {}

        try:
            # List all symbols in S3
            s3_symbols = store.list_symbols()

            if not s3_symbols:
                logger.warning(
                    "No symbols found in S3 bucket",
                    module=MODULE_NAME,
                )
                return {}

            logger.info(
                "Found symbols in S3",
                module=MODULE_NAME,
                count=len(s3_symbols),
            )

            return self.fetch_symbols(s3_symbols, force_full=force_full)

        except Exception as e:
            logger.error(
                "Failed to list S3 symbols",
                module=MODULE_NAME,
                error=str(e),
            )
            return {}

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
