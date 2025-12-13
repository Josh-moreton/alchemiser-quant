#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Consolidated portfolio data transfer objects for inter-module communication.

Provides typed DTOs for consolidated portfolio allocation data from strategy
signal aggregation, ensuring type safety in orchestrator communication.
"""

from __future__ import annotations

from collections.abc import Mapping
from datetime import UTC, datetime
from decimal import Decimal
from typing import TypedDict

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from ..constants import CONTRACT_VERSION
from ..logging import get_logger
from ..utils.timezone_utils import ensure_timezone_aware

logger = get_logger(__name__)

# Constants for allocation validation
ALLOCATION_SUM_TOLERANCE = Decimal("0.01")
ALLOCATION_SUM_MIN = Decimal("1.0") - ALLOCATION_SUM_TOLERANCE
ALLOCATION_SUM_MAX = Decimal("1.0") + ALLOCATION_SUM_TOLERANCE


class AllocationConstraints(TypedDict, total=False):
    """Type-safe constraints for allocation consolidation.

    Attributes:
        strategy_id: Identifier of the strategy
        symbols: List of symbols in allocation
        timeframe: Timeframe for the allocation
        max_position_size: Maximum position size constraint

    """

    strategy_id: str
    symbols: list[str]
    timeframe: str
    max_position_size: Decimal


class ConsolidatedPortfolio(BaseModel):
    """DTO for consolidated portfolio allocation from multiple strategies.

    Contains aggregated target allocations from strategy signals with
    correlation tracking and metadata for orchestrator communication.

    Examples:
        >>> from decimal import Decimal
        >>> from datetime import datetime, UTC
        >>> portfolio = ConsolidatedPortfolio(
        ...     target_allocations={"AAPL": Decimal("0.6"), "GOOGL": Decimal("0.4")},
        ...     correlation_id="test-123",
        ...     timestamp=datetime.now(UTC),
        ...     strategy_count=1,
        ...     source_strategies=["nuclear"],
        ...     schema_version="1.0.0"
        ... )

    """

    __schema_version__: str = CONTRACT_VERSION

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Core allocation data
    target_allocations: dict[str, Decimal] = Field(
        ..., description="Target allocation weights by symbol (symbol -> weight 0-1)"
    )

    # Strategy contribution tracking (for P&L attribution)
    strategy_contributions: dict[str, dict[str, Decimal]] = Field(
        default_factory=dict,
        description="Per-strategy allocation breakdown: {strategy_id: {symbol: weight}}",
    )

    # Correlation tracking
    correlation_id: str = Field(
        ..., min_length=1, max_length=100, description="Correlation ID for tracking"
    )

    # Metadata
    timestamp: datetime = Field(..., description="When the consolidation was performed")
    strategy_count: int = Field(..., ge=1, description="Number of strategies that contributed")
    source_strategies: list[str] = Field(
        default_factory=list, description="Names of contributing strategies"
    )

    # Schema versioning
    schema_version: str = Field(
        default=CONTRACT_VERSION, description="Schema version for evolution tracking"
    )

    # Optional context
    constraints: AllocationConstraints | None = Field(
        default=None, description="Optional consolidation constraints and metadata"
    )

    # Partial allocation flag (for multi-node mode)
    is_partial: bool = Field(
        default=False,
        description=(
            "If True, this portfolio is a partial allocation from a single strategy file "
            "in multi-node mode. Partial portfolios skip the sum-to-1.0 validation as they "
            "will be aggregated later. Only the final merged portfolio should have is_partial=False."
        ),
    )

    @field_validator("target_allocations")
    @classmethod
    def validate_allocations(cls, v: dict[str, Decimal]) -> dict[str, Decimal]:
        """Validate target allocations structure and individual weights.

        Validates symbols and individual weights (0-1). Sum validation is
        performed in validate_allocation_sum model validator which has
        access to is_partial flag.

        Args:
            v: Dictionary of symbol -> allocation weight

        Returns:
            Normalized dictionary with uppercase symbols

        Raises:
            ValueError: If allocations are empty or individual weights invalid

        Examples:
            Valid: {"AAPL": Decimal("0.6"), "GOOGL": Decimal("0.4")}
            Valid: {"AAPL": Decimal("0.1")} - partial allocation allowed
            Invalid: {"AAPL": Decimal("1.5")} - weight > 1.0

        """
        if not v:
            logger.warning(
                "Empty target_allocations provided",
                extra={"module": "consolidated_portfolio", "validator": "validate_allocations"},
            )
            raise ValueError("Target allocations cannot be empty")

        # Normalize symbols to uppercase and validate weights
        normalized = {}

        for symbol, weight in v.items():
            if not symbol or not isinstance(symbol, str):
                logger.warning(
                    "Invalid symbol provided",
                    extra={
                        "module": "consolidated_portfolio",
                        "validator": "validate_allocations",
                        "symbol": symbol,
                    },
                )
                raise ValueError(f"Invalid symbol: {symbol}")

            symbol_upper = symbol.strip().upper()
            if symbol_upper in normalized:
                logger.warning(
                    "Duplicate symbol detected",
                    extra={
                        "module": "consolidated_portfolio",
                        "validator": "validate_allocations",
                        "symbol": symbol_upper,
                    },
                )
                raise ValueError(f"Duplicate symbol: {symbol_upper}")

            if weight < 0 or weight > 1:
                logger.warning(
                    "Weight out of valid range",
                    extra={
                        "module": "consolidated_portfolio",
                        "validator": "validate_allocations",
                        "symbol": symbol_upper,
                        "weight": str(weight),
                    },
                )
                raise ValueError(f"Weight for {symbol_upper} must be between 0 and 1, got {weight}")

            normalized[symbol_upper] = weight

        # Note: Sum validation moved to model_validator to access is_partial flag
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
            ValueError: If correlation_id is empty after stripping

        Examples:
            Valid: "signal_handler_20230101_120000"
            Valid: "test-correlation-123"
            Invalid: "" - empty string
            Invalid: "   " - whitespace only

        """
        v = v.strip()
        if not v:
            logger.warning(
                "Empty correlation_id provided",
                extra={"module": "consolidated_portfolio", "validator": "validate_correlation_id"},
            )
            raise ValueError("Correlation ID cannot be empty")
        return v

    @field_validator("timestamp")
    @classmethod
    def ensure_timezone_aware_timestamp(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware.

        Args:
            v: Datetime that may be naive or aware

        Returns:
            Timezone-aware datetime in UTC

        Raises:
            ValueError: If timestamp cannot be made timezone-aware

        Examples:
            Valid: datetime(2023, 1, 1, 12, 0, 0, tzinfo=UTC)
            Valid: datetime(2023, 1, 1, 12, 0, 0) - converted to UTC

        """
        result = ensure_timezone_aware(v)
        if result is None:
            logger.error(
                "Timestamp validation failed",
                extra={
                    "module": "consolidated_portfolio",
                    "validator": "ensure_timezone_aware_timestamp",
                },
            )
            raise ValueError("Timestamp cannot be None")
        return result

    @field_validator("source_strategies")
    @classmethod
    def validate_strategies(cls, v: list[str]) -> list[str]:
        """Validate and normalize strategy names.

        Args:
            v: List of strategy name strings

        Returns:
            List of stripped, non-empty strategy names

        Examples:
            Valid: ["nuclear", "tecl"]
            Valid: [" nuclear ", "tecl "] - stripped to ["nuclear", "tecl"]
            Valid: [] - empty list allowed

        """
        return [strategy.strip() for strategy in v if strategy.strip()]

    @model_validator(mode="after")
    def validate_strategy_count_consistency(self) -> ConsolidatedPortfolio:
        """Validate strategy_count matches source_strategies length.

        Raises:
            ValueError: If strategy_count doesn't match actual source_strategies length

        Examples:
            Valid: strategy_count=2, source_strategies=["nuclear", "tecl"]
            Invalid: strategy_count=1, source_strategies=["nuclear", "tecl"]

        """
        expected_count = len(self.source_strategies) if self.source_strategies else 1
        if self.strategy_count != expected_count:
            logger.warning(
                "Strategy count mismatch",
                extra={
                    "module": "consolidated_portfolio",
                    "validator": "validate_strategy_count_consistency",
                    "strategy_count": self.strategy_count,
                    "expected_count": expected_count,
                    "source_strategies": self.source_strategies,
                },
            )
            raise ValueError(
                f"Strategy count ({self.strategy_count}) does not match "
                f"source_strategies length ({expected_count})"
            )
        return self

    @model_validator(mode="after")
    def validate_allocation_sum(self) -> ConsolidatedPortfolio:
        """Validate that allocations sum to ~1.0 for non-partial portfolios.

        In multi-node mode, partial portfolios (is_partial=True) contain only
        a portion of the total allocation and will be aggregated later.
        Final/aggregated portfolios (is_partial=False) must sum to ~1.0.

        Raises:
            ValueError: If is_partial=False and allocations don't sum to ~1.0

        Examples:
            Valid: is_partial=False, allocations sum to 1.0
            Valid: is_partial=True, allocations sum to 0.1 (partial)
            Invalid: is_partial=False, allocations sum to 0.1

        """
        if self.is_partial:
            # Partial portfolios skip sum validation - they will be aggregated
            total_weight = sum(self.target_allocations.values())
            logger.debug(
                "Partial portfolio created (sum validation skipped)",
                extra={
                    "module": "consolidated_portfolio",
                    "validator": "validate_allocation_sum",
                    "total_weight": str(total_weight),
                    "is_partial": True,
                },
            )
            return self

        # Full portfolio must sum to ~1.0
        total_weight = sum(self.target_allocations.values())
        if not (ALLOCATION_SUM_MIN <= total_weight <= ALLOCATION_SUM_MAX):
            logger.warning(
                "Allocation sum out of tolerance",
                extra={
                    "module": "consolidated_portfolio",
                    "validator": "validate_allocation_sum",
                    "total_weight": str(total_weight),
                    "expected": "~1.0",
                    "tolerance": str(ALLOCATION_SUM_TOLERANCE),
                    "is_partial": False,
                },
            )
            raise ValueError(f"Total allocations must sum to ~1.0, got {total_weight}")

        return self

    @model_validator(mode="after")
    def validate_strategy_contributions(self) -> ConsolidatedPortfolio:
        """Validate strategy contributions are consistent with target allocations.

        Ensures that for each symbol, the sum of strategy contributions matches
        the total allocation weight. Empty strategy_contributions is valid for
        backward compatibility.

        Raises:
            ValueError: If contributions don't sum correctly to target allocations

        Examples:
            Valid: target_allocations={"AAPL": 1.0}, strategy_contributions={}
            Valid: target_allocations={"AAPL": 1.0}, strategy_contributions={"momentum": {"AAPL": 0.6}, "mean_rev": {"AAPL": 0.4}}
            Invalid: target_allocations={"AAPL": 1.0}, strategy_contributions={"momentum": {"AAPL": 0.5}}

        """
        # Empty contributions is valid (backward compatibility)
        if not self.strategy_contributions:
            return self

        # Validate each symbol's contributions sum to target allocation
        for symbol, target_weight in self.target_allocations.items():
            contribution_sum = Decimal("0")
            for _strategy_id, allocations in self.strategy_contributions.items():
                if symbol in allocations:
                    contribution_sum += allocations[symbol]

            # Use same tolerance as allocation sum validation
            diff = abs(target_weight - contribution_sum)
            if diff > ALLOCATION_SUM_TOLERANCE:
                logger.warning(
                    "Strategy contributions don't match target allocation",
                    extra={
                        "module": "consolidated_portfolio",
                        "validator": "validate_strategy_contributions",
                        "symbol": symbol,
                        "target_weight": str(target_weight),
                        "contribution_sum": str(contribution_sum),
                        "difference": str(diff),
                    },
                )
                raise ValueError(
                    f"Strategy contributions for {symbol} sum to {contribution_sum}, "
                    f"expected {target_weight} (tolerance {ALLOCATION_SUM_TOLERANCE})"
                )

        return self

    @classmethod
    def from_dict_allocation(
        cls,
        allocation_dict: Mapping[str, float | Decimal],
        correlation_id: str,
        source_strategies: list[str] | None = None,
        timestamp: datetime | None = None,
    ) -> ConsolidatedPortfolio:
        """Create ConsolidatedPortfolio from dict allocation data.

        Args:
            allocation_dict: Mapping of symbol -> weight allocations (float or Decimal)
            correlation_id: Correlation ID for tracking
            source_strategies: Optional list of contributing strategy names
            timestamp: Optional timestamp; defaults to datetime.now(UTC) if not provided

        Returns:
            ConsolidatedPortfolio instance

        Raises:
            ValueError: If allocation data is invalid

        Examples:
            >>> portfolio = ConsolidatedPortfolio.from_dict_allocation(
            ...     {"AAPL": 0.6, "GOOGL": 0.4},
            ...     "test-123",
            ...     ["nuclear"]
            ... )

        """
        # Convert allocations to Decimal, preserving Decimal values for precision
        target_allocations = {
            symbol: weight if isinstance(weight, Decimal) else Decimal(str(weight))
            for symbol, weight in allocation_dict.items()
        }

        return cls(
            target_allocations=target_allocations,
            correlation_id=correlation_id,
            timestamp=timestamp or datetime.now(UTC),
            strategy_count=len(source_strategies) if source_strategies else 1,
            source_strategies=source_strategies or [],
        )

    def to_dict_allocation(self) -> dict[str, float]:
        """Convert to simple dict allocation format for backward compatibility.

        Returns:
            Dictionary of symbol -> weight as floats

        Examples:
            >>> portfolio = ConsolidatedPortfolio.from_dict_allocation(
            ...     {"AAPL": 0.6, "GOOGL": 0.4},
            ...     "test-123"
            ... )
            >>> portfolio.to_dict_allocation()
            {'AAPL': 0.6, 'GOOGL': 0.4}

        """
        return {symbol: float(weight) for symbol, weight in self.target_allocations.items()}

    @classmethod
    def from_json_dict(
        cls,
        data: dict[str, object],
    ) -> ConsolidatedPortfolio:
        """Create ConsolidatedPortfolio from JSON-serialized dict.

        This method handles deserialization from EventBridge/SQS where
        Decimal values are serialized as strings. It converts string
        values back to Decimal before validation.

        Args:
            data: Dictionary from JSON deserialization (e.g., from EventBridge)

        Returns:
            ConsolidatedPortfolio instance

        Raises:
            ValueError: If data is invalid

        Examples:
            >>> data = {
            ...     "target_allocations": {"AAPL": "0.60", "GOOGL": "0.40"},
            ...     "correlation_id": "test-123",
            ...     "timestamp": "2023-01-01T12:00:00+00:00",
            ...     "strategy_count": 1,
            ...     "source_strategies": ["nuclear"],
            ...     "schema_version": "1.0.0"
            ... }
            >>> portfolio = ConsolidatedPortfolio.from_json_dict(data)

        """
        # Deep copy to avoid mutating input
        normalized = dict(data)

        # Convert target_allocations from string to Decimal
        if "target_allocations" in normalized:
            allocations = normalized["target_allocations"]
            if isinstance(allocations, dict):
                normalized["target_allocations"] = {
                    symbol: Decimal(str(weight)) if not isinstance(weight, Decimal) else weight
                    for symbol, weight in allocations.items()
                }

        # Convert strategy_contributions from string to Decimal
        if "strategy_contributions" in normalized:
            contributions = normalized["strategy_contributions"]
            if isinstance(contributions, dict):
                normalized["strategy_contributions"] = {
                    strategy_id: {
                        symbol: Decimal(str(weight)) if not isinstance(weight, Decimal) else weight
                        for symbol, weight in strategy_allocs.items()
                    }
                    for strategy_id, strategy_allocs in contributions.items()
                    if isinstance(strategy_allocs, dict)
                }

        # Parse timestamp if it's a string
        if "timestamp" in normalized and isinstance(normalized["timestamp"], str):
            from datetime import datetime as dt

            ts_str = str(normalized["timestamp"])
            normalized["timestamp"] = dt.fromisoformat(ts_str.replace("Z", "+00:00"))

        return cls.model_validate(normalized)
