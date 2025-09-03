#!/usr/bin/env python3
"""Business Unit: shared | Status: current.."""

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


# Backward compatibility aliases - will be removed in future version
PriceDTO = PriceResult
PriceHistoryDTO = PriceHistoryResult
SpreadAnalysisDTO = SpreadAnalysisResult
MarketStatusDTO = MarketStatusResult
MultiSymbolQuotesDTO = MultiSymbolQuotesResult
