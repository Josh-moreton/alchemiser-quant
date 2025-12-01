#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Strategy allocation data transfer objects for inter-module communication.

Provides typed DTOs for strategy allocation plans with correlation tracking
and serialization helpers for communication between strategy and portfolio modules.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..constants import CONTRACT_VERSION
from ..logging import get_logger
from ..utils.timezone_utils import ensure_timezone_aware

logger = get_logger(__name__)

# Weight sum tolerance constants
WEIGHT_SUM_TOLERANCE_MIN = Decimal("0.99")
WEIGHT_SUM_TOLERANCE_MAX = Decimal("1.01")


class StrategyAllocation(BaseModel):
    """DTO for strategy allocation plan.

    Contains target weights for portfolio rebalancing with optional constraints
    and metadata for correlation tracking.

    Schema version: 1.0

    Examples:
        >>> from decimal import Decimal
        >>> from datetime import datetime, UTC
        >>>
        >>> # Create allocation with minimal fields
        >>> alloc = StrategyAllocation(
        ...     target_weights={"AAPL": Decimal("0.6"), "MSFT": Decimal("0.4")},
        ...     correlation_id="trade-123"
        ... )
        >>>
        >>> # Create allocation with all fields
        >>> alloc = StrategyAllocation(
        ...     target_weights={"SPY": Decimal("1.0")},
        ...     correlation_id="rebalance-456",
        ...     portfolio_value=Decimal("10000"),
        ...     as_of=datetime.now(UTC),
        ...     constraints={"max_position_size": 0.5}
        ... )
        >>>
        >>> # Use from_dict for type conversion
        >>> alloc = StrategyAllocation.from_dict({
        ...     "target_weights": {"AAPL": "0.6", "MSFT": 0.4},
        ...     "correlation_id": "trade-789",
        ...     "portfolio_value": 10000.0
        ... })

    """

    __schema_version__: str = CONTRACT_VERSION

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    schema_version: str = Field(
        default=CONTRACT_VERSION, description="Schema version for backward compatibility"
    )
    target_weights: dict[str, Decimal] = Field(
        ..., description="Target allocation weights by symbol (symbol -> weight 0-1)"
    )
    portfolio_value: Decimal | None = Field(
        default=None,
        ge=0,
        description="Optional portfolio value; if None, compute from snapshot",
    )
    correlation_id: str = Field(
        ..., min_length=1, max_length=100, description="Correlation ID for tracking"
    )
    as_of: datetime | None = Field(
        default=None, description="Optional timestamp when allocation was calculated"
    )
    constraints: dict[str, float | bool | str] | None = Field(
        default=None, description="Optional allocation constraints and metadata"
    )

    @field_validator("target_weights")
    @classmethod
    def validate_weights(cls, v: dict[str, Decimal]) -> dict[str, Decimal]:
        """Validate target weights.

        Args:
            v: Dictionary mapping symbols to target weights

        Returns:
            Normalized dictionary with uppercase symbols

        Raises:
            ValueError: If weights are invalid (empty, out of range, don't sum to ~1.0)

        Examples:
            >>> # Valid weights
            >>> StrategyAllocation.validate_weights(
            ...     {"aapl": Decimal("0.6"), "msft": Decimal("0.4")}
            ... )
            {'AAPL': Decimal('0.6'), 'MSFT': Decimal('0.4')}

            >>> # Invalid: doesn't sum to 1.0
            >>> StrategyAllocation.validate_weights({"aapl": Decimal("0.5")})
            Traceback (most recent call last):
                ...
            ValueError: Total weights must sum to ~1.0, got 0.5

        """
        if not v:
            raise ValueError("target_weights cannot be empty")

        # Normalize symbols to uppercase
        normalized = {}
        total_weight = Decimal("0")

        for symbol, weight in v.items():
            if not symbol or not isinstance(symbol, str):
                raise ValueError(f"Invalid symbol: {symbol}")

            symbol_upper = symbol.strip().upper()
            if symbol_upper in normalized:
                raise ValueError(f"Duplicate symbol: {symbol_upper}")

            if weight < 0 or weight > 1:
                raise ValueError(f"Weight for {symbol_upper} must be between 0 and 1, got {weight}")

            normalized[symbol_upper] = weight
            total_weight += weight

        # Allow small tolerance for weight sum (common with floating point conversions)
        if not (WEIGHT_SUM_TOLERANCE_MIN <= total_weight <= WEIGHT_SUM_TOLERANCE_MAX):
            raise ValueError(f"Total weights must sum to ~1.0, got {total_weight}")

        return normalized

    @field_validator("correlation_id")
    @classmethod
    def validate_correlation_id(cls, v: str) -> str:
        """Validate correlation ID format.

        Args:
            v: Correlation ID string

        Returns:
            Stripped correlation ID

        Raises:
            ValueError: If correlation_id is empty after stripping whitespace

        """
        v = v.strip()
        if not v:
            raise ValueError("correlation_id cannot be empty")
        return v

    @field_validator("as_of")
    @classmethod
    def ensure_timezone_aware_as_of(cls, v: datetime | None) -> datetime | None:
        """Ensure as_of timestamp is timezone-aware.

        Args:
            v: Optional datetime timestamp

        Returns:
            Timezone-aware datetime or None

        """
        if v is None:
            return None
        return ensure_timezone_aware(v)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StrategyAllocation:
        """Create DTO from dictionary with type conversion.

        Args:
            data: Dictionary containing DTO fields

        Returns:
            StrategyAllocation instance

        Raises:
            ValueError: If data is invalid or cannot be converted

        Examples:
            >>> data = {
            ...     "target_weights": {"AAPL": "0.6", "MSFT": 0.4},
            ...     "correlation_id": "trade-123",
            ...     "portfolio_value": 10000.0
            ... }
            >>> alloc = StrategyAllocation.from_dict(data)
            >>> alloc.portfolio_value
            Decimal('10000.0')

        """
        converted_data = data.copy()
        correlation_id = data.get("correlation_id", "unknown")

        try:
            # Convert target weights
            if "target_weights" in converted_data:
                converted_data["target_weights"] = cls._convert_target_weights(
                    converted_data["target_weights"], correlation_id
                )

            # Convert portfolio value
            if "portfolio_value" in converted_data:
                converted_data["portfolio_value"] = cls._convert_portfolio_value(
                    converted_data["portfolio_value"], correlation_id
                )

            return cls(**converted_data)
        except Exception as e:
            logger.error(
                "Failed to create StrategyAllocation from dict",
                correlation_id=correlation_id,
                error=str(e),
                data_keys=list(data.keys()),
            )
            raise

    @classmethod
    def _convert_target_weights(
        cls, weights_data: dict[str, float | Decimal | int | str], correlation_id: str = "unknown"
    ) -> dict[str, Decimal]:
        """Convert target weights to Decimal format.

        Args:
            weights_data: Dictionary mapping symbols to weights (various numeric types)
            correlation_id: Correlation ID for error context (optional)

        Returns:
            Dictionary mapping symbols to Decimal weights

        Raises:
            ValueError: If weight value cannot be converted to Decimal

        """
        if not isinstance(weights_data, dict):
            return weights_data

        converted_weights = {}
        for symbol, weight in weights_data.items():
            try:
                if isinstance(weight, str):
                    converted_weights[symbol] = Decimal(weight)
                else:
                    converted_weights[symbol] = Decimal(str(weight))
            except (ValueError, TypeError) as e:
                raise ValueError(
                    f"Invalid weight value for {symbol}: {weight} "
                    f"(correlation_id: {correlation_id})"
                ) from e

        return converted_weights

    @classmethod
    def _convert_portfolio_value(
        cls, portfolio_value: float | Decimal | int | str | None, correlation_id: str = "unknown"
    ) -> Decimal | None:
        """Convert portfolio value to Decimal if needed.

        Args:
            portfolio_value: Portfolio value in various numeric types
            correlation_id: Correlation ID for error context (optional)

        Returns:
            Decimal portfolio value or None

        Raises:
            ValueError: If portfolio_value cannot be converted to Decimal

        """
        if portfolio_value is None:
            return None

        try:
            # Always convert via str() to avoid float precision issues
            return Decimal(str(portfolio_value))
        except (ValueError, TypeError) as e:
            raise ValueError(
                f"Invalid portfolio_value: {portfolio_value} (correlation_id: {correlation_id})"
            ) from e

    def idempotency_key(self) -> str:
        """Generate deterministic idempotency key for deduplication.

        Creates a hash from correlation_id, schema_version, and target_weights
        to enable idempotent event processing and replay tolerance.

        Returns:
            16-character hex string hash for deduplication

        Examples:
            >>> from decimal import Decimal
            >>> alloc = StrategyAllocation(
            ...     target_weights={"AAPL": Decimal("0.6"), "MSFT": Decimal("0.4")},
            ...     correlation_id="trade-123"
            ... )
            >>> key = alloc.idempotency_key()
            >>> len(key)
            16
            >>> isinstance(key, str)
            True

        """
        weights_str = json.dumps(
            {k: str(v) for k, v in sorted(self.target_weights.items())}, sort_keys=True
        )
        key_material = f"{self.correlation_id}:{self.schema_version}:{weights_str}"
        return hashlib.sha256(key_material.encode()).hexdigest()[:16]
