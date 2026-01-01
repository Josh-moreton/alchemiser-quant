"""Business Unit: scripts | Status: current.

Benchmark data service for fetching SPY historical prices from Alpaca.

Provides SPY benchmark returns aligned with strategy return dates
for QuantStats tearsheet comparison.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta

import pandas as pd
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest
from alpaca.data.timeframe import TimeFrame

logger = logging.getLogger(__name__)


class BenchmarkService:
    """Fetches benchmark (SPY) data from Alpaca for comparison.

    Uses Alpaca's Market Data API to fetch historical daily bars
    and converts them to returns series for QuantStats.
    """

    def __init__(
        self,
        api_key: str | None = None,
        api_secret: str | None = None,
    ) -> None:
        """Initialize the benchmark service.

        Args:
            api_key: Alpaca API key (defaults to ALPACA_KEY env var)
            api_secret: Alpaca API secret (defaults to ALPACA_SECRET env var)

        """
        self._api_key = api_key or os.environ.get("ALPACA_KEY", "")
        self._api_secret = api_secret or os.environ.get("ALPACA_SECRET", "")

        if not self._api_key or not self._api_secret:
            raise ValueError("Alpaca API credentials not provided")

        self._client = StockHistoricalDataClient(self._api_key, self._api_secret)
        logger.info("BenchmarkService initialized with Alpaca client")

    def fetch_benchmark_bars(
        self,
        symbol: str = "SPY",
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        days_lookback: int = 365,
    ) -> pd.DataFrame:
        """Fetch daily bars for benchmark symbol.

        Args:
            symbol: Benchmark ticker symbol (default: SPY)
            start_date: Start date for data (optional)
            end_date: End date for data (optional, defaults to today)
            days_lookback: Days of history if start_date not provided

        Returns:
            DataFrame with OHLCV data indexed by timestamp

        """
        if end_date is None:
            end_date = datetime.now()

        if start_date is None:
            start_date = end_date - timedelta(days=days_lookback)

        logger.info(
            f"Fetching {symbol} bars from {start_date.date()} to {end_date.date()}"
        )

        try:
            request = StockBarsRequest(
                symbol_or_symbols=symbol,
                timeframe=TimeFrame.Day,
                start=start_date,
                end=end_date,
            )

            bars = self._client.get_stock_bars(request)

            # Convert to DataFrame
            if symbol in bars.data:
                df = pd.DataFrame([
                    {
                        "timestamp": bar.timestamp,
                        "open": float(bar.open),
                        "high": float(bar.high),
                        "low": float(bar.low),
                        "close": float(bar.close),
                        "volume": int(bar.volume),
                    }
                    for bar in bars.data[symbol]
                ])

                if not df.empty:
                    df.set_index("timestamp", inplace=True)
                    df.index = pd.to_datetime(df.index)
                    logger.info(f"Fetched {len(df)} bars for {symbol}")
                    return df

            logger.warning(f"No data returned for {symbol}")
            return pd.DataFrame()

        except Exception as e:
            logger.error(f"Failed to fetch benchmark bars: {e}")
            return pd.DataFrame()

    def get_benchmark_returns(
        self,
        symbol: str = "SPY",
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        days_lookback: int = 365,
    ) -> pd.Series:
        """Get daily returns series for benchmark.

        Args:
            symbol: Benchmark ticker symbol (default: SPY)
            start_date: Start date for data (optional)
            end_date: End date for data (optional)
            days_lookback: Days of history if start_date not provided

        Returns:
            Series of daily percentage returns (decimals)

        """
        df = self.fetch_benchmark_bars(
            symbol=symbol,
            start_date=start_date,
            end_date=end_date,
            days_lookback=days_lookback,
        )

        if df.empty:
            return pd.Series(dtype=float, name=symbol)

        # Calculate returns from close prices
        returns = df["close"].pct_change().dropna()

        # QuantStats expects timezone-naive index
        if returns.index.tz is not None:
            returns.index = returns.index.tz_localize(None)

        # Normalize to date only (no time component)
        returns.index = returns.index.normalize()

        returns.name = symbol
        return returns

    def align_benchmark_to_strategy(
        self,
        strategy_returns: pd.Series,
        benchmark_symbol: str = "SPY",
    ) -> pd.Series:
        """Fetch and align benchmark returns to strategy date range.

        Fetches benchmark data covering the strategy's date range and
        aligns the dates to match (handles market holidays, etc.).

        Args:
            strategy_returns: Strategy returns series to align with
            benchmark_symbol: Benchmark ticker symbol

        Returns:
            Benchmark returns aligned to strategy dates

        """
        if strategy_returns.empty:
            return pd.Series(dtype=float, name=benchmark_symbol)

        # Get date range from strategy returns (with buffer for alignment)
        start_date = strategy_returns.index.min() - timedelta(days=10)
        end_date = strategy_returns.index.max() + timedelta(days=1)

        # Fetch benchmark data
        benchmark_returns = self.get_benchmark_returns(
            symbol=benchmark_symbol,
            start_date=start_date,
            end_date=end_date,
        )

        if benchmark_returns.empty:
            logger.warning(f"Could not fetch benchmark data for {benchmark_symbol}")
            return pd.Series(dtype=float, name=benchmark_symbol)

        # Align benchmark to strategy dates using forward fill
        # This handles cases where strategy trades on non-market days
        aligned = benchmark_returns.reindex(strategy_returns.index, method="ffill")

        # Fill any remaining NaN with 0 (no return for those days)
        aligned = aligned.fillna(0)

        logger.info(
            f"Aligned {benchmark_symbol} benchmark: "
            f"{len(aligned)} points matching strategy dates"
        )
        return aligned


def get_spy_returns(
    strategy_returns: pd.Series,
    api_key: str | None = None,
    api_secret: str | None = None,
) -> pd.Series:
    """Convenience function to get SPY returns aligned to strategy.

    Args:
        strategy_returns: Strategy returns to align with
        api_key: Alpaca API key (optional, uses env var)
        api_secret: Alpaca API secret (optional, uses env var)

    Returns:
        SPY returns aligned to strategy date range

    """
    service = BenchmarkService(api_key=api_key, api_secret=api_secret)
    return service.align_benchmark_to_strategy(strategy_returns, "SPY")
