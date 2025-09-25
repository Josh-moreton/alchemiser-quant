#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Indicator request schemas for DSL engine.

Provides typed schemas for requesting technical indicators from indicator services
with proper validation and type safety.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class IndicatorRequest(BaseModel):
    """Schema for requesting technical indicators.

    Contains the parameters needed to request specific indicators
    from indicator calculation services.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Request identification
    request_id: str = Field(..., min_length=1, description="Unique request identifier")
    correlation_id: str = Field(..., min_length=1, description="Correlation ID for tracking")

    # Indicator specification
    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")
    indicator_type: str = Field(..., min_length=1, description="Type of indicator (rsi, ma, etc.)")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Indicator parameters")

    # Optional metadata
    timeframe: str | None = Field(default=None, description="Timeframe for indicator calculation")
    lookback_periods: int | None = Field(default=None, ge=1, description="Number of periods to look back")

    @classmethod
    def rsi(cls, symbol: str, periods: int = 14, request_id: str | None = None, 
            correlation_id: str | None = None) -> IndicatorRequest:
        """Create RSI indicator request."""
        import uuid
        return cls(
            request_id=request_id or str(uuid.uuid4()),
            correlation_id=correlation_id or str(uuid.uuid4()),
            symbol=symbol,
            indicator_type="rsi",
            parameters={"periods": periods}
        )

    @classmethod  
    def moving_average(cls, symbol: str, periods: int = 20, ma_type: str = "sma",
                      request_id: str | None = None, correlation_id: str | None = None) -> IndicatorRequest:
        """Create moving average indicator request."""
        import uuid
        return cls(
            request_id=request_id or str(uuid.uuid4()),
            correlation_id=correlation_id or str(uuid.uuid4()),
            symbol=symbol,
            indicator_type="moving_average",
            parameters={"periods": periods, "type": ma_type}
        )


class PortfolioFragment(BaseModel):
    """Schema for portfolio fragment data used in DSL evaluations.

    Contains a subset of portfolio data needed for strategy evaluation
    without exposing the full portfolio state.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Portfolio identification
    portfolio_id: str = Field(..., min_length=1, description="Portfolio identifier")
    fragment_id: str = Field(..., min_length=1, description="Fragment identifier")
    correlation_id: str = Field(..., min_length=1, description="Correlation ID for tracking")

    # Relevant symbols for this fragment
    symbols: list[str] = Field(..., min_size=1, description="Symbols included in this fragment")
    
    # Portfolio metrics relevant to the fragment
    total_value: float = Field(..., ge=0, description="Total portfolio value")
    available_cash: float = Field(..., ge=0, description="Available cash")
    
    # Position data for included symbols
    positions: dict[str, float] = Field(default_factory=dict, description="Position quantities by symbol")
    position_values: dict[str, float] = Field(default_factory=dict, description="Position values by symbol")
    
    # Optional metadata
    timestamp: str | None = Field(default=None, description="Fragment timestamp")
    strategy_context: dict[str, Any] = Field(default_factory=dict, description="Strategy-specific context")