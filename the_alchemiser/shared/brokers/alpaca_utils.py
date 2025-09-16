"""Business Unit: shared | Status: current.

Alpaca-specific constants and utilities for shared use.

This module provides Alpaca-specific constants, mappers, and utilities
that are used across multiple modules. By centralizing these here, we
reduce the number of direct Alpaca imports scattered throughout the codebase.
"""

from __future__ import annotations

# Import Alpaca types for proper typing
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.live import StockDataStream
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.client import TradingClient
from alpaca.trading.stream import TradingStream


# Alpaca data request helpers
def create_stock_bars_request(**kwargs: str | int | bool | None) -> StockBarsRequest:
    """Create an Alpaca StockBarsRequest with the given parameters."""
    return StockBarsRequest(**kwargs)


def create_stock_latest_quote_request(
    **kwargs: str | int | bool | None,
) -> StockLatestQuoteRequest:
    """Create an Alpaca StockLatestQuoteRequest with the given parameters."""
    return StockLatestQuoteRequest(**kwargs)


def create_timeframe(amount: int, unit: str) -> TimeFrame:
    """Create an Alpaca TimeFrame object."""
    from alpaca.data.timeframe import TimeFrameUnit

    # Map string units to Alpaca TimeFrameUnit
    unit_mapping = {
        "minute": TimeFrameUnit.Minute,
        "hour": TimeFrameUnit.Hour,
        "day": TimeFrameUnit.Day,
        "week": TimeFrameUnit.Week,
        "month": TimeFrameUnit.Month,
    }

    if unit.lower() in unit_mapping:
        return TimeFrame(amount, unit_mapping[unit.lower()])
    raise ValueError(f"Unknown time frame unit: {unit}")


# Alpaca client factory functions
def create_trading_client(
    api_key: str, secret_key: str, *, paper: bool = True
) -> TradingClient:
    """Create an Alpaca TradingClient."""
    return TradingClient(api_key=api_key, secret_key=secret_key, paper=paper)


def create_data_client(api_key: str, secret_key: str) -> StockHistoricalDataClient:
    """Create an Alpaca StockHistoricalDataClient."""
    return StockHistoricalDataClient(api_key=api_key, secret_key=secret_key)


def create_trading_stream(
    api_key: str, secret_key: str, *, paper: bool = True
) -> TradingStream:
    """Create an Alpaca TradingStream."""
    return TradingStream(api_key=api_key, secret_key=secret_key, paper=paper)


def create_stock_data_stream(
    api_key: str, secret_key: str, feed: str = "iex"
) -> StockDataStream:
    """Create an Alpaca StockDataStream."""
    from alpaca.data.enums import DataFeed

    # Map string feed to DataFeed enum
    feed_mapping = {
        "iex": DataFeed.IEX,
        "sip": DataFeed.SIP,
    }

    data_feed = feed_mapping.get(feed.lower(), DataFeed.IEX)
    return StockDataStream(api_key=api_key, secret_key=secret_key, feed=data_feed)


# Alpaca model imports (for type hints and instance checks)
def get_alpaca_quote_type() -> type:
    """Get the Alpaca Quote type for isinstance checks."""
    from alpaca.data.models import Quote

    return Quote


def get_alpaca_trade_type() -> type:
    """Get the Alpaca Trade type for isinstance checks."""
    from alpaca.data.models import Trade

    return Trade


__all__ = [
    "create_data_client",
    "create_stock_bars_request",
    "create_stock_data_stream",
    "create_stock_latest_quote_request",
    "create_timeframe",
    "create_trading_client",
    "create_trading_stream",
    "get_alpaca_quote_type",
    "get_alpaca_trade_type",
]
