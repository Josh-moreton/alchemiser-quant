"""Business Unit: shared | Status: current.

Data persistence layer using Parquet storage.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pandas as pd

from scripts.backtest.models.market_data import HistoricalBar
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


class DataStore:
    """Parquet-based storage for historical market data.
    
    Data is organized as: data/historical/{symbol}/{year}/daily.parquet
    This structure allows efficient loading of data by symbol and year.
    """

    def __init__(self, base_path: str = "data/historical") -> None:
        """Initialize data store.
        
        Args:
            base_path: Base directory for historical data storage

        """
        self.base_path = Path(base_path)
        self.logger = logger

    def save_bars(self, symbol: str, bars: list[HistoricalBar]) -> None:
        """Save historical bars to Parquet storage.
        
        Groups bars by year and saves to separate files for efficient loading.
        
        Args:
            symbol: Trading symbol
            bars: List of historical bars to save

        """
        if not bars:
            self.logger.warning(f"No bars to save for {symbol}")
            return

        # Group bars by year
        bars_by_year: dict[int, list[HistoricalBar]] = {}
        for bar in bars:
            year = bar.date.year
            if year not in bars_by_year:
                bars_by_year[year] = []
            bars_by_year[year].append(bar)

        # Save each year's data
        for year, year_bars in bars_by_year.items():
            self._save_year_data(symbol, year, year_bars)

        self.logger.info(
            f"Saved {len(bars)} bars for {symbol} across {len(bars_by_year)} years",
            extra={
                "symbol": symbol,
                "bar_count": len(bars),
                "years": list(bars_by_year.keys()),
            },
        )

    def _save_year_data(self, symbol: str, year: int, bars: list[HistoricalBar]) -> None:
        """Save a single year's data to Parquet.
        
        Args:
            symbol: Trading symbol
            year: Year of data
            bars: Bars for that year

        """
        # Create directory structure
        year_dir = self.base_path / symbol / str(year)
        year_dir.mkdir(parents=True, exist_ok=True)

        # Convert to DataFrame
        df = pd.DataFrame([bar.to_dict() for bar in bars])
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date").sort_index()

        # Save to Parquet
        parquet_path = year_dir / "daily.parquet"
        df.to_parquet(parquet_path, engine="auto", compression="snappy")

        self.logger.debug(
            f"Saved {len(bars)} bars for {symbol} year {year}",
            extra={"symbol": symbol, "year": year, "bar_count": len(bars)},
        )

    def load_bars(
        self, symbol: str, start_date: datetime, end_date: datetime
    ) -> list[HistoricalBar]:
        """Load historical bars from Parquet storage.
        
        Args:
            symbol: Trading symbol
            start_date: Start date (inclusive)
            end_date: End date (inclusive)
            
        Returns:
            List of historical bars for the date range

        """
        # Determine years to load
        start_year = start_date.year
        end_year = end_date.year
        years = range(start_year, end_year + 1)

        all_bars: list[HistoricalBar] = []

        for year in years:
            year_bars = self._load_year_data(symbol, year)
            all_bars.extend(year_bars)

        # Filter by date range
        filtered_bars = [
            bar for bar in all_bars if start_date <= bar.date <= end_date
        ]

        self.logger.info(
            f"Loaded {len(filtered_bars)} bars for {symbol}",
            extra={
                "symbol": symbol,
                "bar_count": len(filtered_bars),
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )

        return filtered_bars

    def _load_year_data(self, symbol: str, year: int) -> list[HistoricalBar]:
        """Load a single year's data from Parquet.
        
        Args:
            symbol: Trading symbol
            year: Year to load
            
        Returns:
            List of bars for that year (empty if file doesn't exist)

        """
        parquet_path = self.base_path / symbol / str(year) / "daily.parquet"

        if not parquet_path.exists():
            self.logger.debug(
                f"No data file for {symbol} year {year}",
                extra={"symbol": symbol, "year": year},
            )
            return []

        try:
            df = pd.read_parquet(parquet_path)
            df = df.reset_index()

            bars: list[HistoricalBar] = []
            for _, row in df.iterrows():
                bar = HistoricalBar.from_dict(row.to_dict())
                bars.append(bar)

            return bars

        except Exception as e:
            self.logger.error(
                f"Failed to load data for {symbol} year {year}: {e}",
                extra={"symbol": symbol, "year": year, "error": str(e)},
            )
            return []

    def has_data(self, symbol: str, start_date: datetime, end_date: datetime) -> bool:
        """Check if data exists for a symbol in the given date range.
        
        Args:
            symbol: Trading symbol
            start_date: Start date
            end_date: End date
            
        Returns:
            True if any data exists for the symbol in the range

        """
        start_year = start_date.year
        end_year = end_date.year

        for year in range(start_year, end_year + 1):
            parquet_path = self.base_path / symbol / str(year) / "daily.parquet"
            if parquet_path.exists():
                return True

        return False

    def list_symbols(self) -> list[str]:
        """List all symbols with stored data.
        
        Returns:
            List of symbol names

        """
        if not self.base_path.exists():
            return []

        symbols = [
            d.name for d in self.base_path.iterdir() if d.is_dir()
        ]
        return sorted(symbols)

    def clear_symbol(self, symbol: str) -> None:
        """Delete all stored data for a symbol.
        
        Args:
            symbol: Trading symbol to clear

        """
        symbol_dir = self.base_path / symbol
        if symbol_dir.exists():
            import shutil

            shutil.rmtree(symbol_dir)
            self.logger.info(f"Cleared all data for {symbol}", extra={"symbol": symbol})
