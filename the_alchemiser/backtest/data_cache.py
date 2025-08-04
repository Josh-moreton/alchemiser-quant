#!/usr/bin/env python3
"""
Enhanced Data Caching System for Backtest Performance

This module implements a sophisticated caching system that pre-loads all required
historical data once and shares it efficiently across multiple backtest workers,
preventing API rate limit issues.

Key Features:
- Pre-loads all symbol data for the entire date range once
- Efficient memory sharing across workers using pickle/shared memory
- Intelligent symbol detection from all strategies
- Fallback mechanisms for missing data
- Memory-efficient data storage and retrieval
"""

import argparse
import datetime as dt
import hashlib
import os
import pickle
import sys
from pathlib import Path
from typing import Any

import pandas as pd
from rich.console import Console
from rich.panel import Panel

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from the_alchemiser.core.data.data_provider import UnifiedDataProvider

console = Console()


class BacktestDataCache:
    """
    Centralized data cache for backtest operations.

    Handles pre-loading, caching, and efficient distribution of historical data
    across multiple backtest workers without hitting API rate limits.
    """

    def __init__(self, cache_dir: str = "backtest_cache"):
        """Initialize the data cache system."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)

        # In-memory cache
        self._daily_data_cache: dict[str, pd.DataFrame] = {}
        self._minute_data_cache: dict[str, pd.DataFrame] = {}
        self._cache_metadata: dict[str, dict[str, Any]] = {}

        # Data provider for fetching
        self._data_provider: UnifiedDataProvider | None = None

    def get_cache_key(
        self,
        start_date: dt.datetime,
        end_date: dt.datetime,
        symbols: list[str],
        include_minute_data: bool = False,
    ) -> str:
        """Generate a unique cache key for the given parameters."""
        symbols_str = "_".join(sorted(symbols))
        date_str = f"{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
        minute_str = "_minute" if include_minute_data else "_daily"

        # Create hash for very long symbol lists
        if len(symbols_str) > 200:
            symbols_hash = hashlib.md5(symbols_str.encode()).hexdigest()[:12]
            symbols_str = f"hash_{symbols_hash}"

        return f"backtest_{date_str}_{symbols_str}{minute_str}"

    def get_cache_file_path(self, cache_key: str) -> Path:
        """Get the file path for a cache key."""
        return self.cache_dir / f"{cache_key}.pkl"

    def is_cached(self, cache_key: str) -> bool:
        """Check if data is already cached."""
        cache_file = self.get_cache_file_path(cache_key)
        return cache_file.exists()

    def save_cache_to_disk(
        self,
        cache_key: str,
        daily_data: dict[str, pd.DataFrame],
        minute_data: dict[str, pd.DataFrame] | None = None,
    ) -> bool:
        """Save cached data to disk for reuse."""
        try:
            cache_file = self.get_cache_file_path(cache_key)

            cache_data = {
                "daily_data": daily_data,
                "minute_data": minute_data or {},
                "created_at": dt.datetime.now(),
                "cache_key": cache_key,
            }

            with open(cache_file, "wb") as f:
                pickle.dump(cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)

            console.print(f"[green]💾 Saved cache to disk: {cache_file.name}[/green]")
            return True

        except Exception as e:
            console.print(f"[red]❌ Failed to save cache: {e}[/red]")
            return False

    def load_cache_from_disk(
        self, cache_key: str
    ) -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame]]:
        """Load cached data from disk."""
        try:
            cache_file = self.get_cache_file_path(cache_key)

            if not cache_file.exists():
                return {}, {}

            with open(cache_file, "rb") as f:
                cache_data = pickle.load(f)

            daily_data = cache_data.get("daily_data", {})
            minute_data = cache_data.get("minute_data", {})

            console.print(f"[green]📂 Loaded cache from disk: {cache_file.name}[/green]")
            console.print(f"[blue]   Daily data: {len(daily_data)} symbols[/blue]")
            console.print(f"[blue]   Minute data: {len(minute_data)} symbols[/blue]")

            return daily_data, minute_data

        except Exception as e:
            console.print(f"[red]❌ Failed to load cache: {e}[/red]")
            return {}, {}

    def get_all_required_symbols(self, include_benchmarks: bool = True) -> set[str]:
        """
        Discover all symbols that might be needed for backtesting.

        This analyzes all strategies to determine what symbols they could potentially use.
        """
        symbols = set()

        # Strategy-specific symbols
        strategy_symbols = {
            # Nuclear strategy symbols
            "OKLO",
            "SMR",
            "LEU",
            "URA",
            "URNM",
            "DNN",
            "CCJ",
            "NXE",
            # TECL strategy symbols
            "TECL",
            "TECS",
            "XLK",
            "QQQ",
            "TQQQ",
            "SQQQ",
            # KLM strategy symbols (leveraged ETFs)
            "FNGU",
            "FNGD",
            "UVXY",
            "SVXY",
            "SPXU",
            "SPXL",
            "TNA",
            "TZA",
            "FAS",
            "FAZ",
            "NUGT",
            "DUST",
            "LABU",
            "LABD",
            "CURE",
            "SH",
            "UPRO",
            "SPDN",
            # Sector ETFs for KLM switching
            "KMLM",
            "XLE",
            "XLF",
            "XLV",
            "XLI",
            "XLP",
            "XLY",
            "XLU",
            "XLRE",
        }
        symbols.update(strategy_symbols)

        # Benchmark and market data symbols
        if include_benchmarks:
            benchmark_symbols = {
                "SPY",
                "QQQ",
                "IWM",
                "DIA",  # Major index ETFs
                "VTI",
                "VEA",
                "VWO",  # Broad market ETFs
                "TLT",
                "SHY",
                "GLD",
                "SLV",  # Alternative assets
                "VIX",
                "UVXY",
                "SVXY",  # Volatility
            }
            symbols.update(benchmark_symbols)

        # Individual stocks that might be used
        individual_stocks = {"AAPL", "MSFT", "GOOGL", "AMZN", "NVDA", "TSLA", "META", "NFLX"}
        symbols.update(individual_stocks)

        return symbols

    def _process_timestamp(self, timestamp: Any, symbol: str, bar_index: int) -> dt.datetime | None:
        """Process and normalize timestamp from bar data."""
        if timestamp is None:
            console.print(f"[red]⚠️ No timestamp found for {symbol} bar {bar_index}[/red]")
            return None

        try:
            processed_timestamp: dt.datetime
            if hasattr(timestamp, "to_pydatetime"):
                processed_timestamp = timestamp.to_pydatetime()
            elif isinstance(timestamp, str):
                processed_timestamp = pd.to_datetime(timestamp).to_pydatetime()
            else:
                processed_timestamp = pd.to_datetime(timestamp).to_pydatetime()

            # Remove timezone info for consistency
            if hasattr(processed_timestamp, "replace") and processed_timestamp.tzinfo is not None:
                processed_timestamp = processed_timestamp.replace(tzinfo=None)

            return processed_timestamp
        except Exception as ts_error:
            console.print(f"[red]⚠️ Error processing timestamp for {symbol} bar {bar_index}: {ts_error}[/red]")
            return None

    def _extract_timestamp_from_bar(self, bar: Any) -> Any:
        """Extract timestamp from bar using various attribute names."""
        for ts_attr in ["timestamp", "time", "date", "t"]:
            if hasattr(bar, ts_attr):
                return getattr(bar, ts_attr)
        return None

    def _create_bar_row(self, bar: Any) -> dict[str, float] | None:
        """Create a data row from a bar object."""
        if not (hasattr(bar, "open") and hasattr(bar, "high")):
            return None

        return {
            "Open": float(bar.open),
            "High": float(bar.high),
            "Low": float(bar.low),
            "Close": float(bar.close),
            "Volume": int(bar.volume) if hasattr(bar, "volume") else 0,
        }

    def _convert_bars_to_dataframe(self, bars: list[Any], symbol: str) -> pd.DataFrame | None:
        """Convert bar data to pandas DataFrame."""
        data_rows: list[dict[str, float]] = []
        timestamps: list[dt.datetime] = []

        for i, bar in enumerate(bars):
            try:
                row = self._create_bar_row(bar)
                if row is None:
                    console.print(f"[red]⚠️ Invalid bar structure for {symbol} bar {i}: missing open/high[/red]")
                    if hasattr(bar, "__dict__"):
                        console.print(f"[dim]Bar attributes: {list(bar.__dict__.keys())}[/dim]")
                    continue

                timestamp = self._extract_timestamp_from_bar(bar)
                processed_timestamp = self._process_timestamp(timestamp, symbol, i)

                if processed_timestamp is not None:
                    data_rows.append(row)
                    timestamps.append(processed_timestamp)

            except Exception as bar_error:
                console.print(f"[red]❌ Error processing bar {i} for {symbol}: {bar_error}[/red]")
                continue

        if data_rows and timestamps:
            df = pd.DataFrame(data_rows)
            df.index = pd.to_datetime(timestamps)
            df.index.name = "Date"
            return df

        return None

    def _load_daily_data_for_symbol(self, symbol: str, start_date: dt.datetime, end_date: dt.datetime) -> pd.DataFrame | None:
        """Load daily data for a single symbol."""
        if self._data_provider is None:
            console.print(f"[red]❌ Data provider not initialized for {symbol}[/red]")
            return None

        try:
            bars = self._data_provider.get_historical_data(symbol, start_date, end_date, timeframe="1d")

            if not bars:
                console.print(f"[red]⚠️ No daily data for {symbol} (empty response)[/red]")
                return None

            df = self._convert_bars_to_dataframe(bars, symbol)
            if df is not None:
                console.print(f"[green]✅ Cached {len(df)} rows for {symbol}[/green]")
                return df
            else:
                console.print(f"[red]⚠️ No valid bars for {symbol}[/red]")
                return None

        except Exception as e:
            console.print(f"[red]❌ Failed to fetch daily data for {symbol}: {e}[/red]")
            import traceback
            console.print(f"[dim]Traceback: {traceback.format_exc()}[/dim]")
            return None

    def _load_minute_data_for_symbol(self, symbol: str, start_date: dt.datetime, end_date: dt.datetime) -> pd.DataFrame | None:
        """Load minute data for a single symbol."""
        if self._data_provider is None:
            console.print(f"[red]❌ Data provider not initialized for {symbol}[/red]")
            return None

        try:
            bars = self._data_provider.get_historical_data(symbol, start_date, end_date, timeframe="1m")

            if not bars:
                console.print(f"[yellow]⚠️ No minute data for {symbol}[/yellow]")
                return None

            data_rows = []
            timestamps = []

            for bar in bars:
                if hasattr(bar, "open") and hasattr(bar, "high"):
                    data_rows.append({
                        "Open": float(bar.open),
                        "High": float(bar.high),
                        "Low": float(bar.low),
                        "Close": float(bar.close),
                        "Volume": int(bar.volume) if hasattr(bar, "volume") else 0,
                    })
                    timestamps.append(bar.timestamp)

            if data_rows:
                df = pd.DataFrame(data_rows)
                df.index = pd.to_datetime(timestamps)
                df.index.name = "Date"
                return df
            else:
                console.print(f"[yellow]⚠️ No valid minute bars for {symbol}[/yellow]")
                return None

        except Exception as e:
            console.print(f"[red]❌ Failed to fetch minute data for {symbol}: {e}[/red]")
            return None

    def _load_all_daily_data(self, symbols: list[str], start_date: dt.datetime, end_date: dt.datetime) -> tuple[dict[str, pd.DataFrame], list[str]]:
        """Load daily data for all symbols."""
        daily_data: dict[str, pd.DataFrame] = {}
        failed_symbols: list[str] = []

        for symbol in symbols:
            df = self._load_daily_data_for_symbol(symbol, start_date, end_date)
            if df is not None:
                daily_data[symbol] = df
            else:
                failed_symbols.append(symbol)

        return daily_data, failed_symbols

    def _load_all_minute_data(self, symbols: list[str], start_date: dt.datetime, end_date: dt.datetime, failed_symbols: list[str]) -> dict[str, pd.DataFrame]:
        """Load minute data for all valid symbols."""
        minute_data: dict[str, pd.DataFrame] = {}
        console.print(f"[yellow]⏱️ Loading minute data for {len(symbols)} symbols...[/yellow]")

        valid_symbols = [s for s in symbols if s not in failed_symbols]
        for i, symbol in enumerate(valid_symbols):
            # Show progress every 10 symbols
            if len(valid_symbols) > 10 and i % 10 == 0:
                console.print(f"[dim]Processing minute data {i+1}/{len(valid_symbols)} symbols...[/dim]")

            df = self._load_minute_data_for_symbol(symbol, start_date, end_date)
            if df is not None:
                minute_data[symbol] = df

        return minute_data

    def _print_loading_summary(self, daily_data: dict[str, pd.DataFrame], minute_data: dict[str, pd.DataFrame], failed_symbols: list[str], include_minute_data: bool) -> None:
        """Print summary of loading results."""
        console.print(f"[green]✅ Successfully cached {len(daily_data)} symbols with daily data[/green]")

        if include_minute_data:
            console.print(f"[green]✅ Successfully cached {len(minute_data)} symbols with minute data[/green]")

        if failed_symbols:
            console.print(f"[yellow]⚠️ Failed to cache {len(failed_symbols)} symbols: {failed_symbols[:10]}{'...' if len(failed_symbols) > 10 else ''}[/yellow]")

        # Ensure output is flushed and progress bars are cleared
        console.print("")  # Clear line

    def preload_all_data(
        self,
        start_date: dt.datetime,
        end_date: dt.datetime,
        symbols: list[str] | None = None,
        include_minute_data: bool = False,
        force_refresh: bool = False,
    ) -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame]]:
        """
        Pre-load all required historical data for backtesting.

        Args:
            start_date: Start date for data
            end_date: End date for data
            symbols: Specific symbols to load (None = auto-detect all)
            include_minute_data: Whether to fetch minute-level data
            force_refresh: Force refresh even if cached

        Returns:
            Tuple of (daily_data, minute_data) dictionaries
        """
        # Auto-detect symbols if not provided
        if symbols is None:
            console.print("[yellow]🔍 Auto-detecting required symbols for all strategies...[/yellow]")
            symbols = sorted(self.get_all_required_symbols())
            console.print(f"[green]📊 Detected {len(symbols)} symbols to cache[/green]")

        # Check cache first
        cache_key = self.get_cache_key(start_date, end_date, symbols, include_minute_data)

        if not force_refresh and self.is_cached(cache_key):
            console.print(f"[green]🎯 Loading existing cache: {cache_key}[/green]")
            return self.load_cache_from_disk(cache_key)

        # Initialize data provider if needed
        if self._data_provider is None:
            console.print("[yellow]🔌 Initializing data provider...[/yellow]")
            self._data_provider = UnifiedDataProvider(paper_trading=True, cache_duration=3600)

        console.print(
            Panel(
                f"[bold cyan]📊 Pre-loading Historical Data[/bold cyan]\n"
                f"Period: {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}\n"
                f"Symbols: {len(symbols)} total\n"
                f"Include minute data: {include_minute_data}\n"
                f"Cache key: {cache_key}",
                title="🚀 Data Cache Loading",
            )
        )

        # Load daily data using helper method
        daily_data, failed_symbols = self._load_all_daily_data(symbols, start_date, end_date)

        # Load minute data if requested
        minute_data: dict[str, pd.DataFrame] = {}
        if include_minute_data:
            minute_data = self._load_all_minute_data(symbols, start_date, end_date, failed_symbols)

        # Save to cache
        self.save_cache_to_disk(cache_key, daily_data, minute_data)

        # Store in memory cache
        self._daily_data_cache.update(daily_data)
        if minute_data:
            self._minute_data_cache.update(minute_data)

        # Print summary
        self._print_loading_summary(daily_data, minute_data, failed_symbols, include_minute_data)

        return daily_data, minute_data

    def get_symbol_data(self, symbol: str, data_type: str = "daily") -> pd.DataFrame | None:
        """
        Get cached data for a specific symbol.

        Args:
            symbol: Symbol to retrieve
            data_type: 'daily' or 'minute'

        Returns:
            DataFrame or None if not found
        """
        if data_type == "daily":
            return self._daily_data_cache.get(symbol)
        elif data_type == "minute":
            return self._minute_data_cache.get(symbol)
        else:
            raise ValueError(f"Invalid data_type: {data_type}")

    def get_cache_stats(self) -> dict[str, float]:
        """Get statistics about the current cache."""
        total_daily_rows = sum(len(df) for df in self._daily_data_cache.values())
        total_minute_rows = sum(len(df) for df in self._minute_data_cache.values())

        # Estimate memory usage (rough calculation)
        total_rows = total_daily_rows + total_minute_rows
        estimated_size_mb = (total_rows * 50) / (1024 * 1024)  # ~50 bytes per row estimate

        return {
            "daily_symbols": len(self._daily_data_cache),
            "minute_symbols": len(self._minute_data_cache),
            "total_symbols": len(self._daily_data_cache) + len(self._minute_data_cache),
            "total_daily_rows": total_daily_rows,
            "total_minute_rows": total_minute_rows,
            "total_size_mb": estimated_size_mb,
        }

    def clear_cache(self):
        """Clear the in-memory cache."""
        self._daily_data_cache.clear()
        self._minute_data_cache.clear()
        self._cache_metadata.clear()
        console.print("[yellow]🧹 Cleared in-memory cache[/yellow]")

    def clean_disk_cache(self, max_age_days: int = 7):
        """Clean old cache files from disk."""
        cutoff_date = dt.datetime.now() - dt.timedelta(days=max_age_days)

        removed_count = 0
        for cache_file in self.cache_dir.glob("*.pkl"):
            if cache_file.stat().st_mtime < cutoff_date.timestamp():
                cache_file.unlink()
                removed_count += 1

        console.print(f"[green]🧹 Cleaned {removed_count} old cache files[/green]")


# Global cache instance for sharing across modules
_global_cache: BacktestDataCache | None = None


def get_global_cache() -> BacktestDataCache:
    """Get the global cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = BacktestDataCache()
    return _global_cache


def preload_backtest_data(
    start_date: dt.datetime,
    end_date: dt.datetime,
    symbols: list[str] | None = None,
    include_minute_data: bool = False,
    force_refresh: bool = False,
) -> tuple[dict[str, pd.DataFrame], dict[str, pd.DataFrame]]:
    """
    Convenience function to pre-load data using the global cache.

    This should be called once before running multiple backtests to avoid
    repeated API calls and rate limiting.
    """
    cache = get_global_cache()
    return cache.preload_all_data(start_date, end_date, symbols, include_minute_data, force_refresh)


def get_cached_symbol_data(symbol: str, data_type: str = "daily") -> pd.DataFrame | None:
    """Get cached data for a symbol from the global cache."""
    cache = get_global_cache()
    return cache.get_symbol_data(symbol, data_type)


def clear_global_cache():
    """Clear the global cache."""
    cache = get_global_cache()
    cache.clear_cache()


if __name__ == "__main__":
    """Test the caching system."""
    import argparse

    parser = argparse.ArgumentParser(description="Test backtest data caching")
    parser.add_argument("--start", default="2024-01-01", help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", default="2024-06-30", help="End date (YYYY-MM-DD)")
    parser.add_argument("--minute-data", action="store_true", help="Include minute data")
    parser.add_argument("--force-refresh", action="store_true", help="Force refresh cache")
    parser.add_argument("--clean-cache", action="store_true", help="Clean old cache files")
    parser.add_argument("--symbols", nargs="*", help="Specific symbols to cache")

    args = parser.parse_args()

    start_dt = dt.datetime.strptime(args.start, "%Y-%m-%d")
    end_dt = dt.datetime.strptime(args.end, "%Y-%m-%d")

    if args.clean_cache:
        cache = get_global_cache()
        cache.clean_disk_cache()

    # Pre-load data
    daily_data, minute_data = preload_backtest_data(
        start_dt,
        end_dt,
        symbols=args.symbols,
        include_minute_data=args.minute_data,
        force_refresh=args.force_refresh,
    )

    # Show cache stats
    cache = get_global_cache()
    stats = cache.get_cache_stats()

    console.print(
        Panel(
            f"[bold green]📊 Cache Statistics[/bold green]\n"
            f"Daily symbols: {stats['daily_symbols']}\n"
            f"Minute symbols: {stats['minute_symbols']}\n"
            f"Total daily rows: {stats['total_daily_rows']:,}\n"
            f"Total minute rows: {stats['total_minute_rows']:,}",
            title="✅ Caching Complete",
        )
    )
