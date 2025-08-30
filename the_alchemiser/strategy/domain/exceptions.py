"""Business Unit: strategy & signal generation | Status: current.

Strategy context exception classes.

Defines strategy-specific exception types for market data operations,
signal generation, and indicator calculations.
"""

from __future__ import annotations

from typing import Any

from the_alchemiser.shared_kernel.exceptions.base_exceptions import AlchemiserError, DataAccessError


class DataProviderError(AlchemiserError):
    """Raised when data provider operations fail."""


class MarketDataError(DataProviderError):
    """Raised when market data operations fail."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        data_type: str | None = None,
        provider: str | None = None,
        retry_count: int = 0,
    ) -> None:
        """Create a market data error with provider details."""
        context: dict[str, Any] = {}
        if symbol:
            context["symbol"] = symbol
        if data_type:
            context["data_type"] = data_type
        if provider:
            context["provider"] = provider
        if retry_count > 0:
            context["retry_count"] = retry_count

        super().__init__(message, context)
        self.symbol = symbol
        self.data_type = data_type
        self.provider = provider
        self.retry_count = retry_count


class SpreadAnalysisError(DataProviderError):
    """Raised when spread analysis operations fail."""

    def __init__(
        self,
        message: str,
        symbol: str | None = None,
        bid_price: float | None = None,
        ask_price: float | None = None,
        analysis_type: str | None = None,
    ) -> None:
        """Create a spread analysis error with quote details."""
        context: dict[str, Any] = {}
        if symbol:
            context["symbol"] = symbol
        if bid_price is not None:
            context["bid_price"] = bid_price
        if ask_price is not None:
            context["ask_price"] = ask_price
        if analysis_type:
            context["analysis_type"] = analysis_type

        super().__init__(message, context)
        self.symbol = symbol
        self.bid_price = bid_price
        self.ask_price = ask_price
        self.analysis_type = analysis_type


class IndicatorCalculationError(AlchemiserError):
    """Raised when indicator calculations fail."""

    def __init__(
        self,
        message: str,
        indicator_name: str | None = None,
        symbol: str | None = None,
        timeframe: str | None = None,
    ) -> None:
        """Create an indicator calculation error with calculation details."""
        context: dict[str, Any] = {}
        if indicator_name:
            context["indicator_name"] = indicator_name
        if symbol:
            context["symbol"] = symbol
        if timeframe:
            context["timeframe"] = timeframe

        super().__init__(message, context)
        self.indicator_name = indicator_name
        self.symbol = symbol
        self.timeframe = timeframe


class WebSocketError(DataProviderError):
    """Raised when WebSocket operations fail."""

    def __init__(
        self,
        message: str,
        connection_status: str | None = None,
        endpoint: str | None = None,
    ) -> None:
        """Create a WebSocket error with connection details."""
        context: dict[str, Any] = {}
        if connection_status:
            context["connection_status"] = connection_status
        if endpoint:
            context["endpoint"] = endpoint

        super().__init__(message, context)
        self.connection_status = connection_status
        self.endpoint = endpoint


class StreamingError(DataProviderError):
    """Raised when streaming data operations fail."""

    def __init__(
        self,
        message: str,
        stream_type: str | None = None,
        symbols: list[str] | None = None,
    ) -> None:
        """Create a streaming error with stream details."""
        context: dict[str, Any] = {}
        if stream_type:
            context["stream_type"] = stream_type
        if symbols:
            context["symbols"] = symbols

        super().__init__(message, context)
        self.stream_type = stream_type
        self.symbols = symbols or []


class SymbolNotFoundError(DataAccessError):
    """Exception raised when market data symbol is not found."""


class PublishError(AlchemiserError):
    """Exception raised when signal publishing fails."""
