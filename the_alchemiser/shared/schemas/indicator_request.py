#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Indicator request data transfer objects for DSL engine.

Provides typed DTOs for requesting technical indicators from indicator services
with proper validation and type safety.
"""

from __future__ import annotations

import math
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..constants import CONTRACT_VERSION

# Type aliases for indicator types
IndicatorType = Literal[
    "rsi",
    "current_price",
    "moving_average",
    "moving_average_return",
    "cumulative_return",
    "exponential_moving_average_price",
    "stdev_return",
    "max_drawdown",
]

__all__ = ["IndicatorRequest", "IndicatorType", "PortfolioFragment"]


class IndicatorRequest(BaseModel):
    """DTO for requesting technical indicators.

    Contains the parameters needed to request specific indicators
    from indicator calculation services.
    """

    __schema_version__: str = CONTRACT_VERSION

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Schema version
    schema_version: str = Field(default=CONTRACT_VERSION, description="DTO schema version")

    # Request identification
    request_id: str = Field(..., min_length=1, description="Unique request identifier")
    correlation_id: str = Field(..., min_length=1, description="Correlation ID for tracking")
    causation_id: str | None = Field(
        default=None, description="Causation ID for event chain tracking"
    )

    # Indicator specification
    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")
    indicator_type: IndicatorType = Field(
        ..., description="Type of indicator (rsi, moving_average, etc.)"
    )
    parameters: dict[str, int | float | str] = Field(
        default_factory=dict, description="Indicator parameters"
    )

    # Optional metadata
    metadata: dict[str, int | float | str | bool] = Field(
        default_factory=dict, description="Additional request metadata"
    )

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase and validate format.

        Args:
            v: Raw symbol string

        Returns:
            Normalized uppercase symbol

        Raises:
            ValueError: If symbol format is invalid

        """
        normalized = v.strip().upper()
        if not normalized.replace(".", "").replace("-", "").isalnum():
            raise ValueError(f"Invalid symbol format: {v}")
        return normalized

    @classmethod
    def rsi_request(
        cls,
        request_id: str,
        correlation_id: str,
        symbol: str,
        window: int = 14,
        causation_id: str | None = None,
    ) -> IndicatorRequest:
        """Create RSI indicator request.

        Args:
            request_id: Unique request identifier
            correlation_id: Correlation ID for tracking
            symbol: Trading symbol
            window: RSI window period (default: 14)
            causation_id: Optional causation ID for event chain tracking

        Returns:
            IndicatorRequest for RSI

        Example:
            >>> request = IndicatorRequest.rsi_request(
            ...     request_id="req-123",
            ...     correlation_id="corr-456",
            ...     symbol="AAPL",
            ...     window=14
            ... )
            >>> request.indicator_type
            'rsi'

        """
        return cls(
            request_id=request_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
            symbol=symbol,
            indicator_type="rsi",
            parameters={"window": window},
        )

    @classmethod
    def moving_average_request(
        cls,
        request_id: str,
        correlation_id: str,
        symbol: str,
        window: int = 200,
        causation_id: str | None = None,
    ) -> IndicatorRequest:
        """Create moving average indicator request.

        Args:
            request_id: Unique request identifier
            correlation_id: Correlation ID for tracking
            symbol: Trading symbol
            window: Moving average window period (default: 200)
            causation_id: Optional causation ID for event chain tracking

        Returns:
            IndicatorRequest for moving average

        Example:
            >>> request = IndicatorRequest.moving_average_request(
            ...     request_id="req-123",
            ...     correlation_id="corr-456",
            ...     symbol="AAPL",
            ...     window=200
            ... )
            >>> request.indicator_type
            'moving_average'

        """
        return cls(
            request_id=request_id,
            correlation_id=correlation_id,
            causation_id=causation_id,
            symbol=symbol,
            indicator_type="moving_average",
            parameters={"window": window},
        )


class PortfolioFragment(BaseModel):
    """DTO for intermediate portfolio allocation fragments.

    Represents partial allocation results during DSL evaluation
    that need to be combined into final portfolio allocations.
    """

    __schema_version__: str = CONTRACT_VERSION

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Schema version
    schema_version: str = Field(default=CONTRACT_VERSION, description="DTO schema version")

    # Fragment identification
    fragment_id: str = Field(..., min_length=1, description="Unique fragment identifier")
    source_step: str = Field(..., min_length=1, description="Evaluation step that created fragment")

    # Event traceability
    correlation_id: str | None = Field(
        default=None, description="Correlation ID for request tracking"
    )
    causation_id: str | None = Field(
        default=None, description="Causation ID for event chain tracking"
    )

    # Allocation data
    weights: dict[str, Decimal] = Field(
        default_factory=dict, description="Symbol weights in fragment"
    )
    total_weight: Decimal = Field(
        default=Decimal("1.0"),
        ge=Decimal("0"),
        le=Decimal("1"),
        description="Total weight of fragment",
    )

    # Metadata
    metadata: dict[str, int | float | str | bool] = Field(
        default_factory=dict,
        description="Fragment metadata (e.g., computation parameters, timestamps)",
    )

    def normalize_weights(self) -> PortfolioFragment:
        """Normalize weights to sum to total_weight using Decimal arithmetic.

        Returns:
            New PortfolioFragment with normalized weights

        Note:
            Uses Decimal arithmetic to preserve precision.
            If sum is zero, returns self unchanged.

        """
        if not self.weights:
            return self

        current_sum = sum(self.weights.values())
        # Use Decimal comparison (no tolerance needed!)
        if current_sum == Decimal("0"):
            return self

        scale_factor = self.total_weight / current_sum
        normalized_weights = {
            symbol: weight * scale_factor for symbol, weight in self.weights.items()
        }

        return self.model_copy(update={"weights": normalized_weights})
