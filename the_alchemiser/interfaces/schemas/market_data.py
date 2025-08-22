#!/usr/bin/env python3
"""
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

from the_alchemiser.interfaces.schemas.base import ResultDTO


class PriceDTO(ResultDTO):
    """
    DTO for latest price information.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    symbol: str | None = None
    price: Decimal | None = None
    error: str | None = None


class PriceHistoryDTO(ResultDTO):
    """
    DTO for price history data.
    """

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


class SpreadAnalysisDTO(ResultDTO):
    """
    DTO for bid-ask spread analysis.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    symbol: str | None = None
    spread_analysis: dict[str, Any] | None = None
    error: str | None = None


class MarketStatusDTO(ResultDTO):
    """
    DTO for market status information.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    market_open: bool | None = None
    error: str | None = None


class MultiSymbolQuotesDTO(ResultDTO):
    """
    DTO for multi-symbol quote data.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    quotes: dict[str, Decimal] | None = None
    symbols: list[str] | None = None
    error: str | None = None
