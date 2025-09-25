#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Indicator request data transfer objects for DSL engine.

Provides typed DTOs for requesting technical indicators from indicator services
with proper validation and type safety.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class IndicatorRequest(BaseModel):
    """DTO for requesting technical indicators.

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
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional request metadata"
    )

    @classmethod
    def rsi_request(
        cls, request_id: str, correlation_id: str, symbol: str, window: int = 14
    ) -> IndicatorRequest:
        """Create RSI indicator request.

        Args:
            request_id: Unique request identifier
            correlation_id: Correlation ID for tracking
            symbol: Trading symbol
            window: RSI window period

        Returns:
            IndicatorRequest for RSI

        """
        return cls(
            request_id=request_id,
            correlation_id=correlation_id,
            symbol=symbol,
            indicator_type="rsi",
            parameters={"window": window},
        )

    @classmethod
    def moving_average_request(
        cls, request_id: str, correlation_id: str, symbol: str, window: int = 200
    ) -> IndicatorRequest:
        """Create moving average indicator request.

        Args:
            request_id: Unique request identifier
            correlation_id: Correlation ID for tracking
            symbol: Trading symbol
            window: Moving average window period

        Returns:
            IndicatorRequest for moving average

        """
        return cls(
            request_id=request_id,
            correlation_id=correlation_id,
            symbol=symbol,
            indicator_type="moving_average",
            parameters={"window": window},
        )


class PortfolioFragment(BaseModel):
    """DTO for intermediate portfolio allocation fragments.

    Represents partial allocation results during DSL evaluation
    that need to be combined into final portfolio allocations.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Fragment identification
    fragment_id: str = Field(..., min_length=1, description="Unique fragment identifier")
    source_step: str = Field(..., min_length=1, description="Evaluation step that created fragment")

    # Allocation data
    weights: dict[str, float] = Field(
        default_factory=dict, description="Symbol weights in fragment"
    )
    total_weight: float = Field(default=1.0, ge=0, le=1, description="Total weight of fragment")

    # Metadata
    metadata: dict[str, Any] = Field(default_factory=dict, description="Fragment metadata")

    def normalize_weights(self) -> PortfolioFragment:
        """Normalize weights to sum to total_weight.

        Returns:
            New PortfolioFragment with normalized weights

        """
        if not self.weights:
            return self

        current_sum = sum(self.weights.values())
        if current_sum == 0:
            return self

        scale_factor = self.total_weight / current_sum
        normalized_weights = {
            symbol: weight * scale_factor for symbol, weight in self.weights.items()
        }

        return self.model_copy(update={"weights": normalized_weights})


# TODO: Remove in Phase 3 - Temporary backward compatibility aliases
IndicatorRequestDTO = IndicatorRequest
PortfolioFragmentDTO = PortfolioFragment
