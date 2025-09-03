#!/usr/bin/env python3
"""Business Unit: portfolio | Status: current..

    Aggregated view of all positions and portfolio metrics.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    portfolio: PortfolioMetrics | None = None
    error: str | None = None


class PortfolioMetrics(BaseModel):
    """DTO for portfolio-level metrics."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    total_market_value: Decimal
    cash_balance: Decimal
    total_positions: int
    largest_position_percent: Decimal


class PositionAnalyticsResult(Result):
    """DTO for position risk analytics."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    symbol: str | None = None
    risk_metrics: dict[str, Any] | None = None
    error: str | None = None


class PositionMetricsResult(Result):
    """DTO for portfolio-wide position metrics."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    diversification_score: Decimal | None = None
    largest_positions: list[LargestPosition] | None = None
    error: str | None = None


class LargestPosition(BaseModel):
    """DTO for largest position information."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    symbol: str
    weight_percent: Decimal
    market_value: Decimal


class ClosePositionResult(Result):
    """DTO for position closure results."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    order_id: str | None = None
    error: str | None = None


class PortfolioValue(BaseModel):
    """DTO for portfolio value information.

    Provides both raw numeric value and typed Money object for portfolio valuation.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    value: Decimal = Field(..., ge=0, description="Raw portfolio value")
    money: Any = Field(..., description="Typed Money object for portfolio value")


# Backward compatibility aliases - will be removed in future version
PositionDTO = Position
PositionSummaryDTO = PositionSummaryResult
PortfolioSummaryDTO = PortfolioSummaryResult
PortfolioMetricsDTO = PortfolioMetrics
PositionAnalyticsDTO = PositionAnalyticsResult
PositionMetricsDTO = PositionMetricsResult
LargestPositionDTO = LargestPosition
ClosePositionResultDTO = ClosePositionResult
PortfolioValueDTO = PortfolioValue
