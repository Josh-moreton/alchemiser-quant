#!/usr/bin/env python3
"""Business Unit: utilities; Status: current.

Market Data schemas for The Alchemiser Trading System.

This module contains schemas for market data operations, price queries,
spread analysis, and market status information.

Key Features:
- Pydantic v2 BaseModel with strict validation
- Decimal precision for financial values
- Comprehensive field validation and normalization
- Type safety for market data operations
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import ConfigDict

from the_alchemiser.shared.schemas.base import Result


class PriceResult(Result):
    """schema for latest price information."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    symbol: str | None = None
    price: Decimal | None = None
    error: str | None = None


class PriceHistoryResult(Result):
    """schema for price history data."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    symbol: str | None = None
    timeframe: str | None = None
    limit: int | None = None
    data: list[dict[str, Any]] | None = None
    error: str | None = None


class SpreadAnalysisResult(Result):
    """schema for bid-ask spread analysis."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    symbol: str | None = None
    spread_analysis: dict[str, Any] | None = None
    error: str | None = None


class MarketStatusResult(Result):
    """schema for market status information."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    market_open: bool | None = None
    error: str | None = None


class MultiSymbolQuotesResult(Result):
    """schema for multi-symbol quote data."""

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
