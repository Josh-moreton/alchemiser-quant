#!/usr/bin/env python3
"""Business Unit: utilities; Status: current.

Market Data DTOs for The Alchemiser Trading System.

This module contains DTOs for market data operations, price queries,
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

from the_alchemiser.shared.types.core import Symbol
from the_alchemiser.shared.value_objects.money import Money

from the_alchemiser.shared.schemas.core.base import Result


class PriceResult(Result):
    """DTO for latest price information."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    symbol: str | None = None
    price: Decimal | None = None
    error: str | None = None


class PriceHistoryResult(Result):
    """DTO for price history data."""

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
    """DTO for bid-ask spread analysis."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    symbol: str | None = None
    spread_analysis: dict[str, Any] | None = None
    error: str | None = None


class MarketStatusResult(Result):
    """DTO for market status information."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    market_open: bool | None = None
    error: str | None = None


class MultiSymbolQuotesResult(Result):
    """DTO for multi-symbol quote data."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    quotes: dict[str, Decimal] | None = None
    symbols: list[str] | None = None
    error: str | None = None
