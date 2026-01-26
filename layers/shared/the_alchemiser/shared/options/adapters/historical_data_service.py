"""Business Unit: shared | Status: current.

Historical data service for fetching daily returns from Alpaca.

Provides methods for:
- Fetching daily historical bars for ETFs
- Calculating daily returns
- Caching historical data for beta/correlation calculations
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import requests

from ...errors import TradingClientError
from ...logging import get_logger

logger = get_logger(__name__)


class HistoricalDataService:
    """Service for fetching historical market data from Alpaca.

    Fetches daily bars and calculates returns for use in beta and
    correlation calculations.
    """

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        *,
        paper: bool = True,
    ) -> None:
        """Initialize Historical Data Service.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca API secret key
            paper: If True, use paper trading endpoint (doesn't affect data endpoint)

        """
        self._api_key = api_key
        self._secret_key = secret_key
        self._data_url = "https://data.alpaca.markets"

        # Create session with auth headers
        self._session = requests.Session()
        self._session.headers.update(
            {
                "APCA-API-KEY-ID": api_key,
                "APCA-API-SECRET-KEY": secret_key,
                "accept": "application/json",
            }
        )

        logger.info("Initialized Historical Data Service")

    def get_daily_bars(
        self,
        symbol: str,
        days: int = 90,
    ) -> list[dict[str, Any]]:
        """Fetch daily bars for a symbol.

        Args:
            symbol: ETF symbol (e.g., "SPY", "QQQ")
            days: Number of days of historical data to fetch

        Returns:
            List of daily bar dictionaries with keys: timestamp, open, high, low, close, volume

        Raises:
            TradingClientError: If API request fails

        """
        try:
            # Calculate date range
            end_date = datetime.now(UTC)
            start_date = end_date - timedelta(days=days)

            # Format dates for API
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")

            # Build request URL
            url = f"{self._data_url}/v2/stocks/{symbol}/bars"
            params = {
                "timeframe": "1Day",
                "start": start_str,
                "end": end_str,
                "limit": 10000,  # Max limit
                "adjustment": "split",  # Adjust for splits
            }

            logger.debug(
                "Fetching daily bars",
                symbol=symbol,
                days=days,
                start=start_str,
                end=end_str,
            )

            response = self._session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            # Extract bars from response
            bars = data.get("bars", [])

            logger.info(
                "Fetched daily bars",
                symbol=symbol,
                bar_count=len(bars),
            )

            return bars

        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to fetch daily bars for {symbol}: {e}"
            logger.error(error_msg, symbol=symbol, error=str(e))
            raise TradingClientError(error_msg) from e

    def calculate_daily_returns(
        self,
        bars: list[dict[str, Any]],
    ) -> list[Decimal]:
        """Calculate daily returns from bars.

        Args:
            bars: List of daily bar dictionaries

        Returns:
            List of daily returns (percentage change from close to close)

        """
        if len(bars) < 2:
            logger.warning("Insufficient bars for return calculation", bar_count=len(bars))
            return []

        returns: list[Decimal] = []

        for i in range(1, len(bars)):
            prev_close = Decimal(str(bars[i - 1]["c"]))  # 'c' is close price
            curr_close = Decimal(str(bars[i]["c"]))

            if prev_close > 0:
                daily_return = (curr_close - prev_close) / prev_close
                returns.append(daily_return)
            else:
                logger.warning(
                    "Skipping invalid bar with zero/negative close",
                    index=i,
                    prev_close=str(prev_close),
                )

        logger.debug("Calculated daily returns", return_count=len(returns))

        return returns

    def get_daily_returns(
        self,
        symbol: str,
        days: int = 90,
    ) -> list[Decimal]:
        """Fetch daily bars and calculate returns.

        Convenience method that combines get_daily_bars and calculate_daily_returns.

        Args:
            symbol: ETF symbol (e.g., "SPY", "QQQ")
            days: Number of days of historical data to fetch

        Returns:
            List of daily returns

        Raises:
            TradingClientError: If API request fails

        """
        bars = self.get_daily_bars(symbol, days)
        return self.calculate_daily_returns(bars)
