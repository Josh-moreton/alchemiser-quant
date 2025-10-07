"""Business Unit: scripts | Status: current.

Data persistence layer for backtesting.

Stores and retrieves historical market data in Parquet format.
"""

from __future__ import annotations

import sys
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pandas as pd

# Add project root to path for imports
_project_root = Path(__file__).resolve().parents[3]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from scripts.backtest.models.market_data import (
    DailyBar,
    MarketDataMetadata,
)  # noqa: E402
from the_alchemiser.shared.logging import get_logger  # noqa: E402

# Constants
# Heuristic: In most markets, about 70% of calendar days are trading days.
# Used for gap detection - if we have fewer bars than this ratio suggests,
# there are likely gaps in the data (e.g., missing trading days).
TRADING_DAYS_RATIO = 0.7

logger = get_logger(__name__)


class DataStore:
    """Parquet-based data store for historical market data.

    Storage format: data/historical/{symbol}/{year}/daily.parquet
    Schema: Date (index), Open, High, Low, Close, Volume, Adjusted_Close
    """

    def __init__(
        self, base_path: str = "data/historical", data_provider=None
    ) -> None:
        """Initialize data store.

        Args:
            base_path: Base directory for data storage
            data_provider: Optional data provider for auto-downloading missing data

        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        self.data_provider = data_provider
        logger.info(f"DataStore initialized at {self.base_path}")

    def _get_file_path(self, symbol: str, year: int) -> Path:
        """Get file path for a symbol and year.

        Args:
            symbol: Stock symbol
            year: Year of data

        Returns:
            Path to parquet file

        """
        return self.base_path / symbol / str(year) / "daily.parquet"

    def save_bars(self, symbol: str, bars: list[DailyBar]) -> None:
        """Save daily bars to Parquet files organized by year.

        Args:
            symbol: Stock symbol
            bars: List of daily bars to save

        """
        if not bars:
            logger.warning(f"No bars to save for {symbol}")
            return

        logger.info(
            f"Saving {len(bars)} bars for {symbol}", symbol=symbol, bar_count=len(bars)
        )

        # Group bars by year
        bars_by_year: dict[int, list[DailyBar]] = {}
        for bar in bars:
            year = bar.date.year
            if year not in bars_by_year:
                bars_by_year[year] = []
            bars_by_year[year].append(bar)

        # Save each year to separate file
        for year, year_bars in bars_by_year.items():
            file_path = self._get_file_path(symbol, year)
            file_path.parent.mkdir(parents=True, exist_ok=True)

            # Convert to DataFrame
            data = {
                "Date": [bar.date for bar in year_bars],
                "Open": [float(bar.open) for bar in year_bars],
                "High": [float(bar.high) for bar in year_bars],
                "Low": [float(bar.low) for bar in year_bars],
                "Close": [float(bar.close) for bar in year_bars],
                "Volume": [bar.volume for bar in year_bars],
                "Adjusted_Close": [float(bar.adjusted_close) for bar in year_bars],
            }

            df = pd.DataFrame(data)
            df.set_index("Date", inplace=True)
            df.sort_index(inplace=True)

            # Save to Parquet
            df.to_parquet(file_path, engine="pyarrow", compression="snappy")
            logger.info(
                f"Saved {len(year_bars)} bars for {symbol} year {year}",
                symbol=symbol,
                year=year,
                bar_count=len(year_bars),
                file_path=str(file_path),
            )

    def load_bars(
        self, symbol: str, start_date: datetime, end_date: datetime
    ) -> list[DailyBar]:
        """Load daily bars from Parquet files.

        If data files are missing and a data provider is configured,
        attempts to auto-download the missing data.

        Args:
            symbol: Stock symbol
            start_date: Start date (inclusive)
            end_date: End date (inclusive)

        Returns:
            List of DailyBar objects sorted by date

        Raises:
            DataUnavailableError: When data is unavailable and cannot be downloaded

        """
        logger.info(
            f"Loading bars for {symbol}",
            symbol=symbol,
            start_date=start_date.isoformat(),
            end_date=end_date.isoformat(),
        )

        # Ensure dates are timezone-aware (UTC)
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=UTC)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=UTC)

        # Determine which years to load
        start_year = start_date.year
        end_year = end_date.year
        years = range(start_year, end_year + 1)

        # Check for missing years
        missing_years = []
        for year in years:
            file_path = self._get_file_path(symbol, year)
            if not file_path.exists():
                missing_years.append(year)

        # If we have missing years and a data provider, try to download
        if missing_years and self.data_provider:
            logger.info(
                f"Missing data files for {symbol} years {missing_years}, attempting auto-download",
                symbol=symbol,
                missing_years=missing_years,
            )
            
            try:
                # Download data for the missing years
                bars = self.data_provider.fetch_daily_bars(symbol, start_date, end_date)
                
                if not bars:
                    # Import here to avoid circular dependency
                    from the_alchemiser.shared.types.exceptions import DataUnavailableError
                    
                    error_msg = (
                        f"Symbol '{symbol}' has no data available from provider for the requested date range. "
                        f"Required: {start_date.date()} to {end_date.date()}."
                    )
                    raise DataUnavailableError(
                        error_msg,
                        symbol=symbol,
                        required_start_date=start_date.isoformat(),
                        required_end_date=end_date.isoformat(),
                    )
                
                # Save the downloaded data
                self.save_bars(symbol, bars)
                logger.info(
                    f"Successfully auto-downloaded and cached {len(bars)} bars for {symbol}",
                    symbol=symbol,
                    bar_count=len(bars),
                )
            except Exception as e:
                # If it's already a DataUnavailableError, re-raise it
                if e.__class__.__name__ == "DataUnavailableError":
                    raise
                
                # Import here to avoid circular dependency
                from the_alchemiser.shared.types.exceptions import DataUnavailableError
                
                # Wrap other exceptions
                error_msg = (
                    f"Failed to download data for '{symbol}' from provider. "
                    f"Required: {start_date.date()} to {end_date.date()}. Error: {str(e)}"
                )
                raise DataUnavailableError(
                    error_msg,
                    symbol=symbol,
                    required_start_date=start_date.isoformat(),
                    required_end_date=end_date.isoformat(),
                ) from e
        
        elif missing_years:
            # No data provider configured, raise error
            from the_alchemiser.shared.types.exceptions import DataUnavailableError
            
            error_msg = (
                f"Missing data files for {symbol} years {missing_years}. "
                f"Required: {start_date.date()} to {end_date.date()}. "
                f"No data provider configured for auto-download."
            )
            raise DataUnavailableError(
                error_msg,
                symbol=symbol,
                required_start_date=start_date.isoformat(),
                required_end_date=end_date.isoformat(),
            )

        # Load data from each year
        all_dfs: list[pd.DataFrame] = []
        for year in years:
            file_path = self._get_file_path(symbol, year)
            if not file_path.exists():
                # This should not happen after auto-download above
                logger.warning(
                    f"No data file for {symbol} year {year}", symbol=symbol, year=year
                )
                continue

            df = pd.read_parquet(file_path, engine="pyarrow")
            all_dfs.append(df)

        if not all_dfs:
            from the_alchemiser.shared.types.exceptions import DataUnavailableError
            
            error_msg = f"No data found for {symbol} in date range {start_date.date()} to {end_date.date()}"
            raise DataUnavailableError(
                error_msg,
                symbol=symbol,
                required_start_date=start_date.isoformat(),
                required_end_date=end_date.isoformat(),
            )

        # Combine and filter by date range
        df = pd.concat(all_dfs)
        df = df.sort_index()

        # Filter to date range
        df = df[(df.index >= start_date) & (df.index <= end_date)]

        # Convert to DailyBar objects
        bars: list[DailyBar] = []
        for date, row in df.iterrows():
            # Ensure date is timezone-aware
            if isinstance(date, pd.Timestamp):
                date_dt = date.to_pydatetime()
                if date_dt.tzinfo is None:
                    date_dt = date_dt.replace(tzinfo=UTC)
            else:
                date_dt = date.replace(tzinfo=UTC) if date.tzinfo is None else date

            bar = DailyBar(
                date=date_dt,
                open=Decimal(str(row["Open"])),
                high=Decimal(str(row["High"])),
                low=Decimal(str(row["Low"])),
                close=Decimal(str(row["Close"])),
                volume=int(row["Volume"]),
                adjusted_close=Decimal(str(row["Adjusted_Close"])),
            )
            bars.append(bar)

        logger.info(
            f"Loaded {len(bars)} bars for {symbol}", symbol=symbol, bar_count=len(bars)
        )

        return bars

    def get_metadata(self, symbol: str) -> MarketDataMetadata | None:
        """Get metadata about stored data for a symbol.

        Args:
            symbol: Stock symbol

        Returns:
            MarketDataMetadata or None if no data exists

        """
        symbol_path = self.base_path / symbol
        if not symbol_path.exists():
            return None

        # Find all parquet files for this symbol
        parquet_files = list(symbol_path.glob("*/daily.parquet"))
        if not parquet_files:
            return None

        # Load all data to get metadata
        all_dfs: list[pd.DataFrame] = []
        for file_path in parquet_files:
            df = pd.read_parquet(file_path, engine="pyarrow")
            all_dfs.append(df)

        df = pd.concat(all_dfs)
        df = df.sort_index()

        # Calculate metadata
        start_date = df.index.min().to_pydatetime()
        end_date = df.index.max().to_pydatetime()

        # Ensure timezone-aware
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=UTC)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=UTC)

        bar_count = len(df)

        # Check for gaps (simple check: compare row count to date range)
        expected_trading_days = (end_date - start_date).days
        has_gaps = bar_count < (expected_trading_days * TRADING_DAYS_RATIO)

        return MarketDataMetadata(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            bar_count=bar_count,
            last_updated=datetime.now(UTC),
            has_gaps=has_gaps,
        )
