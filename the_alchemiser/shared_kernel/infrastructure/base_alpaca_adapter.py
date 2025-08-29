"""Business Unit: utilities | Status: current.

Base Alpaca adapter for shared connection management.

Provides common Alpaca client initialization and configuration for context-specific adapters.
"""

from __future__ import annotations

import logging
from typing import Any

from alpaca.data.historical import StockHistoricalDataClient
from alpaca.trading.client import TradingClient


class BaseAlpacaAdapter:
    """Base adapter for Alpaca API providing shared client management."""

    def __init__(self, api_key: str, secret_key: str, paper: bool = True) -> None:
        """Initialize base Alpaca adapter.

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca API secret key
            paper: Whether to use paper trading (default: True)

        """
        self._api_key = api_key
        self._secret_key = secret_key
        self._paper = paper
        self._trading_client: TradingClient | None = None
        self._data_client: StockHistoricalDataClient | None = None
        self.logger = logging.getLogger(__name__)

    @property
    def api_key(self) -> str:
        """Get API key."""
        return self._api_key

    @property
    def secret_key(self) -> str:
        """Get secret key."""
        return self._secret_key

    @property
    def paper(self) -> bool:
        """Get paper trading flag."""
        return self._paper

    @property
    def is_paper_trading(self) -> bool:
        """Check if using paper trading."""
        return self._paper

    def get_trading_client(self) -> TradingClient:
        """Get trading client instance (lazy initialization)."""
        if self._trading_client is None:
            self._trading_client = TradingClient(
                api_key=self._api_key,
                secret_key=self._secret_key,
                paper=self._paper,
            )
        return self._trading_client

    def get_data_client(self) -> StockHistoricalDataClient:
        """Get data client instance (lazy initialization)."""
        if self._data_client is None:
            self._data_client = StockHistoricalDataClient(
                api_key=self._api_key,
                secret_key=self._secret_key,
            )
        return self._data_client

    def validate_connection(self) -> bool:
        """Validate connection to Alpaca API.

        Returns:
            True if connection is valid, False otherwise

        """
        try:
            client = self.get_trading_client()
            account = client.get_account()
            return account is not None
        except Exception as e:
            self.logger.error(f"Connection validation failed: {e}")
            return False

    def is_market_open(self) -> bool:
        """Check if market is currently open.

        Returns:
            True if market is open, False otherwise

        """
        try:
            client = self.get_trading_client()
            clock = client.get_clock()
            return clock.is_open
        except Exception as e:
            self.logger.error(f"Failed to check market status: {e}")
            return False

    def get_market_calendar(self, start_date: str, end_date: str) -> list[dict[str, Any]]:
        """Get market calendar for date range.

        Args:
            start_date: Start date (YYYY-MM-DD format)
            end_date: End date (YYYY-MM-DD format)

        Returns:
            List of market calendar entries

        """
        try:
            client = self.get_trading_client()
            calendar = client.get_calendar(start_date, end_date)

            return [
                {
                    "date": entry.date.isoformat(),
                    "open": entry.open.isoformat(),
                    "close": entry.close.isoformat(),
                }
                for entry in calendar
            ]
        except Exception as e:
            self.logger.error(f"Failed to get market calendar: {e}")
            return []

    def __repr__(self) -> str:
        """String representation of the adapter."""
        return f"{self.__class__.__name__}(paper={self._paper})"
