"""Business Unit: shared | Status: current.

Alpaca-specific constants and utilities for shared use.

This module provides Alpaca-specific constants, mappers, and utilities
that are used across multiple modules. By centralizing these here, we
reduce the number of direct Alpaca imports scattered throughout the codebase.

All factory functions include:
- Credential validation
- Error handling with proper logging
- Structured error messages
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from alpaca.data.enums import DataFeed
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.live import StockDataStream
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from alpaca.trading.client import TradingClient
from alpaca.trading.stream import TradingStream

from the_alchemiser.shared.errors.exceptions import ConfigurationError
from the_alchemiser.shared.logging import get_logger

if TYPE_CHECKING:
    pass

logger = get_logger(__name__)

# Module constants for default values
DEFAULT_PAPER_TRADING = True
DEFAULT_DATA_FEED = "iex"

# Valid values for string enums
VALID_TIMEFRAME_UNITS = ["minute", "hour", "day", "week", "month"]
VALID_DATA_FEEDS = ["iex", "sip"]


def _validate_credentials(api_key: str, secret_key: str) -> None:
    """Validate API credentials are non-empty.
    
    Args:
        api_key: Alpaca API key
        secret_key: Alpaca secret key
    
    Raises:
        ConfigurationError: If credentials are empty, None, or contain only whitespace
    
    """
    if not api_key or not api_key.strip():
        raise ConfigurationError(
            "Alpaca API key cannot be empty",
            config_key="api_key",
        )
    if not secret_key or not secret_key.strip():
        raise ConfigurationError(
            "Alpaca secret key cannot be empty",
            config_key="secret_key",
        )


# Alpaca data request helpers
def create_stock_bars_request(**kwargs: str | int | bool | None) -> StockBarsRequest:
    """Create an Alpaca StockBarsRequest with the given parameters.
    
    Args:
        **kwargs: Parameters to pass to StockBarsRequest (e.g., symbol_or_symbols, timeframe, start, end)
    
    Returns:
        Configured StockBarsRequest instance
    
    Raises:
        ConfigurationError: If request creation fails due to invalid parameters
    
    Example:
        >>> request = create_stock_bars_request(
        ...     symbol_or_symbols=["AAPL", "GOOGL"],
        ...     timeframe=TimeFrame.Day,
        ...     start="2023-01-01"
        ... )
    
    """
    try:
        return StockBarsRequest(**kwargs)
    except Exception as e:
        logger.error(
            "Failed to create StockBarsRequest",
            error=str(e),
            kwargs_keys=list(kwargs.keys()) if kwargs else [],
        )
        raise ConfigurationError(
            f"Failed to create StockBarsRequest: {e}",
            config_key="stock_bars_request",
        ) from e


def create_stock_latest_quote_request(
    **kwargs: str | int | bool | None,
) -> StockLatestQuoteRequest:
    """Create an Alpaca StockLatestQuoteRequest with the given parameters.
    
    Args:
        **kwargs: Parameters to pass to StockLatestQuoteRequest (e.g., symbol_or_symbols)
    
    Returns:
        Configured StockLatestQuoteRequest instance
    
    Raises:
        ConfigurationError: If request creation fails due to invalid parameters
    
    Example:
        >>> request = create_stock_latest_quote_request(
        ...     symbol_or_symbols=["AAPL", "GOOGL"]
        ... )
    
    """
    try:
        return StockLatestQuoteRequest(**kwargs)
    except Exception as e:
        logger.error(
            "Failed to create StockLatestQuoteRequest",
            error=str(e),
            kwargs_keys=list(kwargs.keys()) if kwargs else [],
        )
        raise ConfigurationError(
            f"Failed to create StockLatestQuoteRequest: {e}",
            config_key="stock_latest_quote_request",
        ) from e


def create_timeframe(amount: int, unit: str) -> TimeFrame:
    """Create an Alpaca TimeFrame object.
    
    Args:
        amount: Number of time units (must be positive)
        unit: Time unit ('minute', 'hour', 'day', 'week', 'month') - case insensitive
    
    Returns:
        Configured TimeFrame instance
    
    Raises:
        ConfigurationError: If amount is not positive or unit is invalid
    
    Example:
        >>> tf = create_timeframe(1, "day")
        >>> tf = create_timeframe(5, "minute")
    
    """
    # Validate amount
    if amount <= 0:
        raise ConfigurationError(
            f"TimeFrame amount must be positive, got: {amount}",
            config_key="timeframe_amount",
            config_value=amount,
        )
    
    # Map string units to Alpaca TimeFrameUnit
    unit_mapping = {
        "minute": TimeFrameUnit.Minute,
        "hour": TimeFrameUnit.Hour,
        "day": TimeFrameUnit.Day,
        "week": TimeFrameUnit.Week,
        "month": TimeFrameUnit.Month,
    }

    unit_lower = unit.lower()
    if unit_lower not in unit_mapping:
        valid_units = ", ".join(VALID_TIMEFRAME_UNITS)
        raise ConfigurationError(
            f"Unknown time frame unit: '{unit}'. Valid units: {valid_units}",
            config_key="timeframe_unit",
            config_value=unit,
        )
    
    try:
        return TimeFrame(amount, unit_mapping[unit_lower])
    except Exception as e:
        logger.error(
            "Failed to create TimeFrame",
            error=str(e),
            amount=amount,
            unit=unit,
        )
        raise ConfigurationError(
            f"Failed to create TimeFrame: {e}",
            config_key="timeframe",
        ) from e


# Alpaca client factory functions
def create_trading_client(
    api_key: str,
    secret_key: str,
    *,
    paper: bool = DEFAULT_PAPER_TRADING,
) -> TradingClient:
    """Create an Alpaca TradingClient with validated credentials.
    
    Args:
        api_key: Alpaca API key (will be redacted in logs)
        secret_key: Alpaca secret key (will be redacted in logs)
        paper: Whether to use paper trading (default True)
    
    Returns:
        Configured TradingClient instance
    
    Raises:
        ConfigurationError: If credentials are invalid or client creation fails
    
    Example:
        >>> client = create_trading_client(api_key, secret_key, paper=True)
    
    """
    _validate_credentials(api_key, secret_key)
    
    try:
        logger.debug(
            "Creating TradingClient",
            paper=paper,
            # Note: api_key/secret_key automatically redacted by logger
        )
        return TradingClient(api_key=api_key, secret_key=secret_key, paper=paper)
    except Exception as e:
        logger.error(
            "Failed to create TradingClient",
            error=str(e),
            paper=paper,
        )
        raise ConfigurationError(
            f"Failed to initialize Alpaca TradingClient: {e}",
            config_key="trading_client",
        ) from e


def create_data_client(api_key: str, secret_key: str) -> StockHistoricalDataClient:
    """Create an Alpaca StockHistoricalDataClient with validated credentials.
    
    Args:
        api_key: Alpaca API key (will be redacted in logs)
        secret_key: Alpaca secret key (will be redacted in logs)
    
    Returns:
        Configured StockHistoricalDataClient instance
    
    Raises:
        ConfigurationError: If credentials are invalid or client creation fails
    
    Example:
        >>> client = create_data_client(api_key, secret_key)
    
    """
    _validate_credentials(api_key, secret_key)
    
    try:
        logger.debug("Creating StockHistoricalDataClient")
        return StockHistoricalDataClient(api_key=api_key, secret_key=secret_key)
    except Exception as e:
        logger.error(
            "Failed to create StockHistoricalDataClient",
            error=str(e),
        )
        raise ConfigurationError(
            f"Failed to initialize Alpaca StockHistoricalDataClient: {e}",
            config_key="data_client",
        ) from e


def create_trading_stream(
    api_key: str,
    secret_key: str,
    *,
    paper: bool = DEFAULT_PAPER_TRADING,
) -> TradingStream:
    """Create an Alpaca TradingStream with validated credentials.
    
    Args:
        api_key: Alpaca API key (will be redacted in logs)
        secret_key: Alpaca secret key (will be redacted in logs)
        paper: Whether to use paper trading (default True)
    
    Returns:
        Configured TradingStream instance
    
    Raises:
        ConfigurationError: If credentials are invalid or stream creation fails
    
    Example:
        >>> stream = create_trading_stream(api_key, secret_key, paper=True)
    
    """
    _validate_credentials(api_key, secret_key)
    
    try:
        logger.debug(
            "Creating TradingStream",
            paper=paper,
        )
        return TradingStream(api_key=api_key, secret_key=secret_key, paper=paper)
    except Exception as e:
        logger.error(
            "Failed to create TradingStream",
            error=str(e),
            paper=paper,
        )
        raise ConfigurationError(
            f"Failed to initialize Alpaca TradingStream: {e}",
            config_key="trading_stream",
        ) from e


def create_stock_data_stream(
    api_key: str,
    secret_key: str,
    feed: str = DEFAULT_DATA_FEED,
) -> StockDataStream:
    """Create an Alpaca StockDataStream with validated credentials.
    
    Args:
        api_key: Alpaca API key (will be redacted in logs)
        secret_key: Alpaca secret key (will be redacted in logs)
        feed: Data feed to use ('iex' or 'sip', default 'iex') - case insensitive
    
    Returns:
        Configured StockDataStream instance
    
    Raises:
        ConfigurationError: If credentials are invalid or stream creation fails
    
    Example:
        >>> stream = create_stock_data_stream(api_key, secret_key, feed="iex")
    
    """
    _validate_credentials(api_key, secret_key)
    
    # Map string feed to DataFeed enum
    feed_mapping = {
        "iex": DataFeed.IEX,
        "sip": DataFeed.SIP,
    }

    feed_lower = feed.lower()
    if feed_lower not in feed_mapping:
        logger.warning(
            f"Unknown data feed '{feed}', defaulting to 'iex'",
            feed=feed,
            valid_feeds=VALID_DATA_FEEDS,
        )
        feed_lower = "iex"
    
    data_feed = feed_mapping[feed_lower]
    
    try:
        logger.debug(
            "Creating StockDataStream",
            feed=feed_lower,
        )
        return StockDataStream(api_key=api_key, secret_key=secret_key, feed=data_feed)
    except Exception as e:
        logger.error(
            "Failed to create StockDataStream",
            error=str(e),
            feed=feed_lower,
        )
        raise ConfigurationError(
            f"Failed to initialize Alpaca StockDataStream: {e}",
            config_key="stock_data_stream",
        ) from e


# Alpaca model imports (for type hints and instance checks)
def get_alpaca_quote_type() -> type:
    """Get the Alpaca Quote type for isinstance checks.
    
    Returns:
        The Alpaca Quote class for runtime type checking
    
    Example:
        >>> Quote = get_alpaca_quote_type()
        >>> if isinstance(obj, Quote):
        ...     # Handle quote object
        ...     pass
    
    """
    from alpaca.data.models import Quote

    return Quote


def get_alpaca_trade_type() -> type:
    """Get the Alpaca Trade type for isinstance checks.
    
    Returns:
        The Alpaca Trade class for runtime type checking
    
    Example:
        >>> Trade = get_alpaca_trade_type()
        >>> if isinstance(obj, Trade):
        ...     # Handle trade object
        ...     pass
    
    """
    from alpaca.data.models import Trade

    return Trade


__all__ = [
    "DEFAULT_DATA_FEED",
    "DEFAULT_PAPER_TRADING",
    "VALID_DATA_FEEDS",
    "VALID_TIMEFRAME_UNITS",
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
