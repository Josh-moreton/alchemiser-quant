"""Business Unit: backtest | Status: current.

Historical market data adapter for backtesting.

Implements MarketDataPort protocol using local Parquet files from data/historical/.
Provides point-in-time correct data access with look-ahead bias protection.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from pathlib import Path
from typing import Final

import pandas as pd

from the_alchemiser.shared.logging import get_logger
from the_alchemiser.shared.types.market_data import BarModel, QuoteModel
from the_alchemiser.shared.value_objects.symbol import Symbol

logger = get_logger(__name__)

# Module constant for logging context
MODULE_NAME = "backtest_v2.adapters.historical_market_data"

# Default data directory relative to project root
DEFAULT_DATA_DIR: Final[str] = "data/historical"


class LookAheadBiasError(Exception):
    """Raised when an operation would introduce look-ahead bias.

    This is a critical error that indicates the backtest would use
    future information not available at the simulated point in time.
    """

    def __init__(self, message: str, as_of: datetime, requested_date: datetime) -> None:
        """Initialize look-ahead bias error.

        Args:
            message: Error description
            as_of: Current simulation date
            requested_date: Date of data that was requested

        """
        self.as_of = as_of
        self.requested_date = requested_date
        super().__init__(message)


class BacktestMarketDataAdapter:
    """MarketDataPort implementation for backtesting using historical Parquet files.

    Loads OHLCV data from Parquet files and provides point-in-time correct
    data access. Enforces look-ahead bias protection by filtering data to
    only include bars up to and including the current simulation date.

    Attributes:
        data_dir: Path to historical data directory
        as_of: Current simulation date (point-in-time)
        _data_cache: In-memory cache of loaded DataFrames by symbol

    Example:
        >>> adapter = BacktestMarketDataAdapter(
        ...     data_dir=Path("data/historical"),
        ...     as_of=datetime(2024, 6, 15, tzinfo=UTC),
        ... )
        >>> bars = adapter.get_bars(Symbol("SPY"), period="1Y", timeframe="1Day")
        >>> # Returns only bars up to and including 2024-06-15

    """

    def __init__(
        self,
        data_dir: Path | str,
        as_of: datetime,
        preload_symbols: list[str] | None = None,
    ) -> None:
        """Initialize historical market data adapter.

        Args:
            data_dir: Path to historical data directory (e.g., "data/historical")
            as_of: Current simulation date. All data returned will be <= this date.
                   Must be timezone-aware (UTC).
            preload_symbols: Optional list of symbols to preload into cache

        Raises:
            ValueError: If as_of is not timezone-aware

        """
        if as_of.tzinfo is None:
            raise ValueError("as_of must be timezone-aware (use UTC)")

        self.data_dir = Path(data_dir)
        self.as_of = as_of
        self._data_cache: dict[str, pd.DataFrame] = {}

        logger.info(
            "BacktestMarketDataAdapter initialized",
            module=MODULE_NAME,
            data_dir=str(self.data_dir),
            as_of=self.as_of.isoformat(),
            preload_symbols=preload_symbols,
        )

        # Preload symbols if specified
        if preload_symbols:
            for symbol in preload_symbols:
                self._load_symbol_data(symbol)

    def set_as_of(self, as_of: datetime) -> None:
        """Update the simulation date (point-in-time).

        This allows the adapter to be reused across multiple simulation
        dates without reloading data.

        Args:
            as_of: New simulation date. Must be timezone-aware (UTC).

        Raises:
            ValueError: If as_of is not timezone-aware

        """
        if as_of.tzinfo is None:
            raise ValueError("as_of must be timezone-aware (use UTC)")

        self.as_of = as_of
        logger.debug(
            "as_of updated",
            module=MODULE_NAME,
            new_as_of=as_of.isoformat(),
        )

    def _load_symbol_data(self, symbol: str) -> pd.DataFrame:
        """Load all historical data for a symbol from Parquet files.

        Loads and concatenates data from all year directories for the symbol.
        Caches the result for subsequent requests.

        Args:
            symbol: Trading symbol (e.g., "SPY", "AAPL")

        Returns:
            DataFrame with OHLCV data indexed by Date

        Raises:
            ValueError: If no data found for symbol

        """
        symbol_upper = symbol.upper()

        if symbol_upper in self._data_cache:
            return self._data_cache[symbol_upper]

        symbol_dir = self.data_dir / symbol_upper
        if not symbol_dir.exists():
            logger.warning(
                "No data directory for symbol",
                module=MODULE_NAME,
                symbol=symbol_upper,
                path=str(symbol_dir),
            )
            raise ValueError(f"No historical data found for symbol: {symbol_upper}")

        # Find all parquet files across years
        parquet_files = list(symbol_dir.glob("**/daily.parquet"))
        if not parquet_files:
            raise ValueError(f"No parquet files found for symbol: {symbol_upper}")

        # Load and concatenate all files
        dfs = []
        for pf in sorted(parquet_files):
            try:
                df = pd.read_parquet(pf)
                dfs.append(df)
                logger.debug(
                    "Loaded parquet file",
                    module=MODULE_NAME,
                    symbol=symbol_upper,
                    file=str(pf),
                    rows=len(df),
                )
            except Exception as e:
                logger.error(
                    "Failed to load parquet file",
                    module=MODULE_NAME,
                    symbol=symbol_upper,
                    file=str(pf),
                    error=str(e),
                )
                raise

        if not dfs:
            raise ValueError(f"No data loaded for symbol: {symbol_upper}")

        # Concatenate and sort by date
        combined = pd.concat(dfs)
        combined = combined.sort_index()

        # Remove duplicates (keep last)
        combined = combined[~combined.index.duplicated(keep="last")]

        self._data_cache[symbol_upper] = combined

        logger.info(
            "Symbol data loaded and cached",
            module=MODULE_NAME,
            symbol=symbol_upper,
            total_rows=len(combined),
            date_range_start=str(combined.index.min()),
            date_range_end=str(combined.index.max()),
        )

        return combined

    def _filter_by_as_of(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Filter DataFrame to only include data up to as_of date.

        This is the core look-ahead bias protection mechanism.

        Args:
            df: DataFrame with DatetimeIndex
            symbol: Symbol name for logging

        Returns:
            Filtered DataFrame with only historical data

        """
        # Filter to data <= as_of
        filtered = df[df.index <= self.as_of]

        if filtered.empty:
            logger.warning(
                "No data available at as_of date",
                module=MODULE_NAME,
                symbol=symbol,
                as_of=self.as_of.isoformat(),
                earliest_available=str(df.index.min()) if len(df) > 0 else "N/A",
            )

        return filtered

    def _parse_period(self, period: str) -> int:
        """Parse period string to number of trading days.

        Args:
            period: Period string (e.g., "1Y", "6M", "90D")

        Returns:
            Approximate number of trading days

        Raises:
            ValueError: If period format is invalid

        """
        period_upper = period.upper()

        try:
            if period_upper.endswith("Y"):
                years = int(period_upper[:-1])
                return years * 252  # Trading days per year
            if period_upper.endswith("M"):
                months = int(period_upper[:-1])
                return months * 21  # Trading days per month
            if period_upper.endswith("D"):
                return int(period_upper[:-1])
            raise ValueError(f"Invalid period format: {period}")
        except ValueError as e:
            raise ValueError(f"Invalid period format: {period}") from e

    def get_bars(self, symbol: Symbol, period: str, timeframe: str) -> list[BarModel]:
        """Fetch historical bars for a symbol up to as_of date.

        Implements MarketDataPort.get_bars with point-in-time correctness.
        Only returns data that would have been available at the simulation date.

        Args:
            symbol: Trading symbol
            period: Lookback period (e.g., "1Y", "6M", "90D")
            timeframe: Bar interval (only "1Day" supported currently)

        Returns:
            List of BarModel ordered chronologically (oldest first)

        Raises:
            ValueError: If symbol not found or timeframe not supported

        """
        symbol_str = str(symbol).upper()

        # Validate timeframe
        if timeframe.upper() not in ("1DAY", "1D", "DAY"):
            logger.warning(
                "Unsupported timeframe, defaulting to 1Day",
                module=MODULE_NAME,
                timeframe=timeframe,
            )

        # Load data
        df = self._load_symbol_data(symbol_str)

        # Filter by as_of (look-ahead bias protection)
        df = self._filter_by_as_of(df, symbol_str)

        if df.empty:
            return []

        # Parse period and filter
        trading_days = self._parse_period(period)
        df = df.tail(trading_days)

        # Convert to BarModel list
        bars = []
        for timestamp, row in df.iterrows():
            bar = BarModel(
                symbol=symbol_str,
                timestamp=timestamp,
                open=Decimal(str(row["Open"])),
                high=Decimal(str(row["High"])),
                low=Decimal(str(row["Low"])),
                close=Decimal(str(row["Close"])),
                volume=int(row["Volume"]),
            )
            bars.append(bar)

        logger.debug(
            "get_bars completed",
            module=MODULE_NAME,
            symbol=symbol_str,
            period=period,
            bars_returned=len(bars),
            as_of=self.as_of.isoformat(),
        )

        return bars

    def get_latest_quote(self, symbol: Symbol) -> QuoteModel | None:
        """Get simulated quote based on latest bar data.

        For backtesting, we simulate a quote using the close price as mid.
        Applies a small synthetic spread around the close.

        Args:
            symbol: Trading symbol

        Returns:
            Simulated QuoteModel or None if no data available

        """
        symbol_str = str(symbol).upper()

        try:
            df = self._load_symbol_data(symbol_str)
            df = self._filter_by_as_of(df, symbol_str)

            if df.empty:
                return None

            # Get latest bar
            latest = df.iloc[-1]
            close_price = Decimal(str(latest["Close"]))

            # Simulate a 0.01% spread
            half_spread = close_price * Decimal("0.00005")
            bid = close_price - half_spread
            ask = close_price + half_spread

            return QuoteModel(
                symbol=symbol_str,
                bid_price=bid,
                ask_price=ask,
                bid_size=Decimal("100"),  # Simulated
                ask_size=Decimal("100"),  # Simulated
                timestamp=df.index[-1],
            )
        except ValueError:
            return None

    def get_mid_price(self, symbol: Symbol) -> float | None:
        """Get mid price from latest bar close.

        For backtesting, the mid price is simply the close of the latest bar.

        Args:
            symbol: Trading symbol

        Returns:
            Close price as float or None if no data available

        """
        symbol_str = str(symbol).upper()

        try:
            df = self._load_symbol_data(symbol_str)
            df = self._filter_by_as_of(df, symbol_str)

            if df.empty:
                return None

            return float(df.iloc[-1]["Close"])
        except ValueError:
            return None

    def get_close_price_on_date(self, symbol: str, date: datetime) -> float | None:
        """Get close price for a specific date.

        Utility method for portfolio valuation during backtest.

        Args:
            symbol: Trading symbol
            date: Target date (must be <= as_of for safety)

        Returns:
            Close price as float or None if not available

        Raises:
            LookAheadBiasError: If date > as_of (would introduce look-ahead bias)

        """
        symbol_upper = symbol.upper()

        # Look-ahead bias protection
        if date > self.as_of:
            raise LookAheadBiasError(
                f"Cannot access data from {date.isoformat()} when as_of is {self.as_of.isoformat()}",
                as_of=self.as_of,
                requested_date=date,
            )

        try:
            df = self._load_symbol_data(symbol_upper)

            # Find the closest date <= target date
            valid_dates = df[df.index <= date]
            if valid_dates.empty:
                return None

            return float(valid_dates.iloc[-1]["Close"])
        except ValueError:
            return None

    def get_available_symbols(self) -> list[str]:
        """Get list of all symbols with available historical data.

        Returns:
            List of symbol names

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

    def get_date_range(self, symbol: str) -> tuple[datetime, datetime] | None:
        """Get available date range for a symbol.

        Args:
            symbol: Trading symbol

        Returns:
            Tuple of (start_date, end_date) or None if symbol not found

        """
        try:
            df = self._load_symbol_data(symbol.upper())
            if df.empty:
                return None
            return df.index.min(), df.index.max()
        except ValueError:
            return None
