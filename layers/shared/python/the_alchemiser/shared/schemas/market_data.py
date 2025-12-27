#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Market Data schemas for The Alchemiser Trading System.

This module contains schemas for market data operations, price queries,
spread analysis, and market status information.

Key Features:
- Pydantic v2 BaseModel with strict validation
- Decimal precision for financial values
- Comprehensive field validation and normalization
- Type safety for market data operations

All schemas inherit from Result base class and follow frozen/immutable patterns.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import ConfigDict

from the_alchemiser.shared.schemas.base import Result


class PriceResult(Result):
    """Schema for latest price information.

    Represents the result of a price query operation for a single symbol.

    Attributes:
        success: Whether the operation succeeded
        symbol: The ticker symbol (e.g., "AAPL")
        price: The latest price as Decimal for precision
        error: Error message if operation failed

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    symbol: str | None = None
    price: Decimal | None = None
    error: str | None = None


class PriceHistoryResult(Result):
    """Schema for price history data.

    Represents the result of a historical price data query.

    Attributes:
        success: Whether the operation succeeded
        symbol: The ticker symbol
        timeframe: The timeframe for data (e.g., "1Day", "1Hour")
        limit: Maximum number of data points requested
        data: List of historical data dictionaries with timestamp and price fields
        error: Error message if operation failed

    Note:
        The data field contains raw dictionaries to maintain flexibility
        with different historical data structures from various providers.

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    symbol: str | None = None
    timeframe: str | None = None
    limit: int | None = None
    data: list[dict[str, str]] | None = None
    error: str | None = None


class SpreadAnalysisResult(Result):
    """Schema for bid-ask spread analysis.

    Represents the result of a spread analysis operation.

    Attributes:
        success: Whether the operation succeeded
        symbol: The ticker symbol
        spread_analysis: Dictionary containing spread metrics (bid, ask, spread, spread_bps)
        error: Error message if operation failed

    Note:
        The spread_analysis field uses string values to maintain precision
        and support various numeric formats from different providers.

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    symbol: str | None = None
    spread_analysis: dict[str, str | int] | None = None
    error: str | None = None


class MarketStatusResult(Result):
    """Schema for market status information.

    Represents the result of a market status query.

    Attributes:
        success: Whether the operation succeeded
        market_open: True if market is open, False if closed
        error: Error message if operation failed

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    market_open: bool | None = None
    error: str | None = None


class MultiSymbolQuotesResult(Result):
    """Schema for multi-symbol quote data.

    Represents the result of fetching quotes for multiple symbols.

    Attributes:
        success: Whether the operation succeeded
        quotes: Dictionary mapping symbols to their prices (Decimal for precision)
        symbols: List of symbols that were queried
        error: Error message if operation failed

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    quotes: dict[str, Decimal] | None = None
    symbols: list[str] | None = None
    error: str | None = None


# Backward compatibility aliases - will be removed in future version
PriceDTO = PriceResult
PriceHistoryDTO = PriceHistoryResult
SpreadAnalysisDTO = SpreadAnalysisResult
MarketStatusDTO = MarketStatusResult
MultiSymbolQuotesDTO = MultiSymbolQuotesResult
