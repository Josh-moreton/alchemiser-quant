"""Business Unit: shared | Status: current.

Historical data manager for downloading and storing market data.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta

from alpaca.data.timeframe import TimeFrame

from scripts.backtest.storage.data_store import DataStore
from scripts.backtest.storage.providers.alpaca_historical import AlpacaHistoricalProvider
from the_alchemiser.shared.config import env_loader  # noqa: F401  # auto-load .env
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)


class DataManager:
    """Manages historical data download and storage for backtesting.
    
    Coordinates between Alpaca historical provider and Parquet storage,
    ensuring data is downloaded, validated, and stored efficiently.
    """

    def __init__(
        self,
        alpaca_api_key: str | None = None,
        alpaca_secret_key: str | None = None,
        storage_path: str = "data/historical",
    ) -> None:
        """Initialize data manager.
        
        Args:
            alpaca_api_key: Alpaca API key (reads from env if not provided)
            alpaca_secret_key: Alpaca secret key (reads from env if not provided)
            storage_path: Path for data storage

        """
        # Support both ALPACA_API_KEY/ALPACA_SECRET_KEY (backtest convention)
        # and ALPACA_KEY/ALPACA_SECRET (shared secrets convention)
        api_key = alpaca_api_key or os.getenv("ALPACA_API_KEY") or os.getenv("ALPACA_KEY")
        secret_key = (
            alpaca_secret_key or os.getenv("ALPACA_SECRET_KEY") or os.getenv("ALPACA_SECRET")
        )

        if not api_key or not secret_key:
            raise ValueError(
                "Alpaca credentials required. Set ALPACA_API_KEY and ALPACA_SECRET_KEY"
            )

        self.provider = AlpacaHistoricalProvider(api_key, secret_key)
        self.store = DataStore(storage_path)
        self.logger = logger

    def download_symbol(
        self,
        symbol: str,
        start_date: datetime,
        end_date: datetime,
        force_refresh: bool = False,
    ) -> int:
        """Download historical data for a single symbol.
        
        Args:
            symbol: Trading symbol
            start_date: Start date for data
            end_date: End date for data
            force_refresh: If True, re-download even if data exists
            
        Returns:
            Number of bars downloaded and stored

        """
        # Check if data already exists
        if not force_refresh and self.store.has_data(symbol, start_date, end_date):
            self.logger.info(
                f"Data already exists for {symbol}",
                extra={"symbol": symbol, "action": "skip"},
            )
            return 0

        # Download data
        self.logger.info(
            f"Downloading data for {symbol}",
            extra={
                "symbol": symbol,
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
            },
        )

        bars = self.provider.fetch_bars(symbol, start_date, end_date, TimeFrame.Day)

        if not bars:
            self.logger.warning(f"No data downloaded for {symbol}")
            return 0

        # Validate data
        is_valid, errors = self.provider.validate_data(bars)
        if not is_valid:
            self.logger.warning(
                f"Data validation warnings for {symbol}: {errors}",
                extra={"symbol": symbol, "errors": errors},
            )
            # Continue anyway - warnings are logged but don't prevent storage

        # Store data
        self.store.save_bars(symbol, bars)

        self.logger.info(
            f"Successfully downloaded and stored {len(bars)} bars for {symbol}",
            extra={"symbol": symbol, "bar_count": len(bars)},
        )

        return len(bars)

    def download_symbols(
        self,
        symbols: list[str],
        start_date: datetime,
        end_date: datetime,
        force_refresh: bool = False,
    ) -> dict[str, int]:
        """Download historical data for multiple symbols.
        
        Args:
            symbols: List of trading symbols
            start_date: Start date for data
            end_date: End date for data
            force_refresh: If True, re-download even if data exists
            
        Returns:
            Dictionary mapping symbols to number of bars downloaded

        """
        results: dict[str, int] = {}

        for symbol in symbols:
            try:
                bar_count = self.download_symbol(symbol, start_date, end_date, force_refresh)
                results[symbol] = bar_count
            except Exception as e:
                self.logger.error(
                    f"Failed to download data for {symbol}: {e}",
                    extra={"symbol": symbol, "error": str(e)},
                )
                results[symbol] = 0

        total_bars = sum(results.values())
        self.logger.info(
            f"Downloaded {total_bars} total bars across {len(symbols)} symbols",
            extra={"total_bars": total_bars, "symbol_count": len(symbols)},
        )

        return results

    def download_lookback(
        self, symbols: list[str], lookback_days: int = 365, force_refresh: bool = False
    ) -> dict[str, int]:
        """Download historical data for a lookback period.
        
        Args:
            symbols: List of trading symbols
            lookback_days: Number of days to look back
            force_refresh: If True, re-download even if data exists
            
        Returns:
            Dictionary mapping symbols to number of bars downloaded

        """
        end_date = datetime.now(UTC)
        start_date = end_date - timedelta(days=lookback_days)

        return self.download_symbols(symbols, start_date, end_date, force_refresh)

    def get_available_symbols(self) -> list[str]:
        """Get list of symbols with stored data.
        
        Returns:
            List of symbol names

        """
        return self.store.list_symbols()

    def clear_symbol_data(self, symbol: str) -> None:
        """Delete all stored data for a symbol.
        
        Args:
            symbol: Trading symbol to clear

        """
        self.store.clear_symbol(symbol)
        self.logger.info(f"Cleared data for {symbol}", extra={"symbol": symbol})
