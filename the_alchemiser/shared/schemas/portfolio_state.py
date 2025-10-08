#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Portfolio state data transfer objects for inter-module communication.

Provides typed schemas for portfolio state with correlation tracking and
serialization helpers for communication between portfolio and other modules.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..utils.timezone_utils import ensure_timezone_aware

# Constants for field lists to avoid duplication (DRY principle)
POSITION_DECIMAL_FIELDS = [
    "quantity",
    "average_cost",
    "current_price",
    "market_value",
    "unrealized_pnl",
    "unrealized_pnl_percent",
    "cost_basis",
]

METRICS_DECIMAL_FIELDS = [
    "total_value",
    "cash_value",
    "equity_value",
    "buying_power",
    "day_pnl",
    "day_pnl_percent",
    "total_pnl",
    "total_pnl_percent",
    "portfolio_margin",
    "maintenance_margin",
]

PORTFOLIO_STATE_DECIMAL_FIELDS = ["cash_target", "max_position_size", "rebalance_threshold"]

# Schema versions for event evolution
POSITION_SCHEMA_VERSION = "1.0"
PORTFOLIO_METRICS_SCHEMA_VERSION = "1.0"
PORTFOLIO_STATE_SCHEMA_VERSION = "1.0"


class Position(BaseModel):
    """DTO for individual position data."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Schema version for event evolution
    schema_version: str = Field(
        default=POSITION_SCHEMA_VERSION,
        description="Schema version for backwards compatibility",
    )

    symbol: str = Field(..., min_length=1, max_length=10, description="Trading symbol")
    quantity: Decimal = Field(..., description="Position quantity (can be negative for short)")
    average_cost: Decimal = Field(..., ge=0, description="Average cost basis")
    current_price: Decimal = Field(..., ge=0, description="Current market price")
    market_value: Decimal = Field(..., description="Current market value")
    unrealized_pnl: Decimal = Field(..., description="Unrealized profit/loss")
    unrealized_pnl_percent: Decimal = Field(..., description="Unrealized P&L percentage")

    # Optional position metadata
    last_updated: datetime | None = Field(default=None, description="Last update timestamp")
    side: str | None = Field(default=None, description="Position side (long/short)")
    cost_basis: Decimal | None = Field(default=None, ge=0, description="Total cost basis")

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase."""
        return v.strip().upper()

    @field_validator("last_updated")
    @classmethod
    def ensure_timezone_aware_last_updated(cls, v: datetime | None) -> datetime | None:
        """Ensure timestamp is timezone-aware."""
        return ensure_timezone_aware(v)


class PortfolioMetrics(BaseModel):
    """DTO for portfolio performance metrics."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    # Schema version for event evolution
    schema_version: str = Field(
        default=PORTFOLIO_METRICS_SCHEMA_VERSION,
        description="Schema version for backwards compatibility",
    )

    total_value: Decimal = Field(..., ge=0, description="Total portfolio value")
    cash_value: Decimal = Field(..., ge=0, description="Cash value")
    equity_value: Decimal = Field(..., ge=0, description="Equity value")
    buying_power: Decimal = Field(..., ge=0, description="Available buying power")

    # P&L metrics with reasonable bounds (-100% to +10000%)
    day_pnl: Decimal = Field(..., description="Day profit/loss")
    day_pnl_percent: Decimal = Field(
        ..., ge=-100, le=10000, description="Day P&L percentage (-100% to +10000%)"
    )
    total_pnl: Decimal = Field(..., description="Total profit/loss")
    total_pnl_percent: Decimal = Field(
        ..., ge=-100, le=10000, description="Total P&L percentage (-100% to +10000%)"
    )

    # Risk metrics
    portfolio_margin: Decimal | None = Field(default=None, ge=0, description="Portfolio margin")
    maintenance_margin: Decimal | None = Field(default=None, ge=0, description="Maintenance margin")


class PortfolioState(BaseModel):
    """DTO for complete portfolio state data transfer.

    Used for communication between portfolio module and other modules.
    Includes correlation tracking and serialization helpers.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Schema version for event evolution
    schema_version: str = Field(
        default=PORTFOLIO_STATE_SCHEMA_VERSION,
        description="Schema version for backwards compatibility",
    )

    # Required correlation fields
    correlation_id: str = Field(..., min_length=1, description="Unique correlation identifier")
    causation_id: str = Field(
        ..., min_length=1, description="Causation identifier for traceability"
    )
    timestamp: datetime = Field(..., description="State snapshot timestamp")

    # Portfolio identification
    portfolio_id: str = Field(..., min_length=1, description="Portfolio identifier")
    account_id: str | None = Field(default=None, description="Associated account ID")

    # Portfolio state
    positions: list[Position] = Field(
        default_factory=list, description="List of portfolio positions"
    )
    metrics: PortfolioMetrics = Field(..., description="Portfolio metrics")

    # Strategy allocation
    strategy_allocations: dict[str, Decimal] = Field(
        default_factory=dict, description="Strategy allocation weights"
    )

    # Portfolio constraints and settings
    cash_target: Decimal | None = Field(default=None, ge=0, description="Target cash percentage")
    max_position_size: Decimal | None = Field(
        default=None, ge=0, le=1, description="Maximum position size as percentage"
    )
    rebalance_threshold: Decimal | None = Field(
        default=None, ge=0, description="Rebalancing threshold"
    )

    # Optional metadata
    last_rebalance_time: datetime | None = Field(
        default=None, description="Last rebalancing timestamp"
    )
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional portfolio metadata"
    )

    @field_validator("timestamp", "last_rebalance_time")
    @classmethod
    def ensure_timezone_aware_timestamps(cls, v: datetime | None) -> datetime | None:
        """Ensure timestamp is timezone-aware."""
        return ensure_timezone_aware(v)

    @field_validator("strategy_allocations")
    @classmethod
    def validate_allocation_weights(cls, v: dict[str, Decimal]) -> dict[str, Decimal]:
        """Validate allocation weights are non-negative."""
        for strategy, weight in v.items():
            if weight < 0:
                raise ValueError(
                    f"Allocation weight for {strategy} must be non-negative, got {weight}"
                )
        return v

    def to_dict(self) -> dict[str, Any]:
        """Convert DTO to dictionary for serialization.

        Returns:
            Dictionary representation of the DTO with properly serialized values.

        """
        data = self.model_dump()

        # Convert various field types for serialization
        self._serialize_datetime_fields(data)
        self._serialize_decimal_fields(data)
        self._serialize_strategy_allocations(data)
        self._serialize_positions(data)
        self._serialize_metrics(data)

        return data

    def _serialize_datetime_fields(self, data: dict[str, Any]) -> None:
        """Convert datetime fields to ISO strings."""
        datetime_fields = ["timestamp", "last_rebalance_time"]
        for field_name in datetime_fields:
            if data.get(field_name) is not None:
                data[field_name] = data[field_name].isoformat()

    def _serialize_decimal_fields(self, data: dict[str, Any]) -> None:
        """Convert Decimal fields to strings for JSON serialization."""
        for field_name in PORTFOLIO_STATE_DECIMAL_FIELDS:
            if data.get(field_name) is not None:
                data[field_name] = str(data[field_name])

    def _serialize_strategy_allocations(self, data: dict[str, Any]) -> None:
        """Convert strategy allocations to string representations."""
        if "strategy_allocations" in data:
            data["strategy_allocations"] = {
                k: str(v) for k, v in data["strategy_allocations"].items()
            }

    def _serialize_positions(self, data: dict[str, Any]) -> None:
        """Convert nested positions data for serialization."""
        if "positions" in data:
            positions_data = []
            for position in data["positions"]:
                position_dict = dict(position)
                self._serialize_position_data(position_dict)
                positions_data.append(position_dict)
            data["positions"] = positions_data

    def _serialize_position_data(self, position_dict: dict[str, Any]) -> None:
        """Serialize individual position data fields."""
        # Convert datetime in position
        if position_dict.get("last_updated") is not None:
            position_dict["last_updated"] = position_dict["last_updated"].isoformat()

        # Convert Decimal fields in position using constant
        for field_name in POSITION_DECIMAL_FIELDS:
            if position_dict.get(field_name) is not None:
                position_dict[field_name] = str(position_dict[field_name])

    def _serialize_metrics(self, data: dict[str, Any]) -> None:
        """Convert metrics data for serialization."""
        if "metrics" in data:
            metrics_dict = dict(data["metrics"])
            # Convert Decimal fields in metrics using constant
            for field_name in METRICS_DECIMAL_FIELDS:
                if metrics_dict.get(field_name) is not None:
                    metrics_dict[field_name] = str(metrics_dict[field_name])
            data["metrics"] = metrics_dict

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PortfolioState:
        """Create DTO from dictionary.

        Args:
            data: Dictionary containing DTO data

        Returns:
            PortfolioState instance

        Raises:
            ValueError: If data is invalid or missing required fields

        """
        # Create a copy to avoid modifying the original
        data = data.copy()

        # Convert various field types
        cls._convert_datetime_fields(data)
        cls._convert_decimal_fields(data)
        cls._convert_strategy_allocations(data)
        cls._convert_positions(data)
        cls._convert_metrics(data)

        return cls(**data)

    @classmethod
    def _convert_datetime_fields(cls, data: dict[str, Any]) -> None:
        """Convert string timestamps back to datetime objects."""
        datetime_fields = ["timestamp", "last_rebalance_time"]
        for field_name in datetime_fields:
            if field_name in data and isinstance(data[field_name], str):
                try:
                    timestamp_str = data[field_name]
                    if timestamp_str.endswith("Z"):
                        timestamp_str = timestamp_str[:-1] + "+00:00"
                    data[field_name] = datetime.fromisoformat(timestamp_str)
                except ValueError as e:
                    raise ValueError(f"Invalid {field_name} format: {data[field_name]}") from e

    @classmethod
    def _convert_decimal_fields(cls, data: dict[str, Any]) -> None:
        """Convert string decimal fields back to Decimal objects."""
        for field_name in PORTFOLIO_STATE_DECIMAL_FIELDS:
            if (
                field_name in data
                and data[field_name] is not None
                and isinstance(data[field_name], str)
            ):
                try:
                    data[field_name] = Decimal(data[field_name])
                except (ValueError, TypeError) as e:
                    raise ValueError(f"Invalid {field_name} value: {data[field_name]}") from e

    @classmethod
    def _convert_strategy_allocations(cls, data: dict[str, Any]) -> None:
        """Convert strategy allocations from strings to Decimal objects."""
        if "strategy_allocations" in data and isinstance(data["strategy_allocations"], dict):
            allocations = {}
            for strategy, weight in data["strategy_allocations"].items():
                if isinstance(weight, str):
                    try:
                        allocations[strategy] = Decimal(weight)
                    except (ValueError, TypeError) as e:
                        raise ValueError(
                            f"Invalid allocation weight for {strategy}: {weight}"
                        ) from e
                else:
                    allocations[strategy] = weight
            data["strategy_allocations"] = allocations

    @classmethod
    def _convert_positions(cls, data: dict[str, Any]) -> None:
        """Convert positions data to Position objects."""
        if "positions" in data and isinstance(data["positions"], list):
            positions_data = []
            for position_data in data["positions"]:
                if isinstance(position_data, dict):
                    cls._convert_position_data(position_data)
                    positions_data.append(Position(**position_data))
                else:
                    positions_data.append(position_data)  # Assume already a DTO
            data["positions"] = positions_data

    @classmethod
    def _convert_position_data(cls, position_data: dict[str, Any]) -> None:
        """Convert individual position data fields."""
        # Convert last_updated timestamp in position
        if "last_updated" in position_data and isinstance(position_data["last_updated"], str):
            try:
                timestamp_str = position_data["last_updated"]
                if timestamp_str.endswith("Z"):
                    timestamp_str = timestamp_str[:-1] + "+00:00"
                position_data["last_updated"] = datetime.fromisoformat(timestamp_str)
            except ValueError as e:
                raise ValueError(
                    f"Invalid last_updated format in position: {position_data['last_updated']}"
                ) from e

        # Convert Decimal fields in position using constant
        for field_name in POSITION_DECIMAL_FIELDS:
            if (
                field_name in position_data
                and position_data[field_name] is not None
                and isinstance(position_data[field_name], str)
            ):
                try:
                    position_data[field_name] = Decimal(position_data[field_name])
                except (ValueError, TypeError) as e:
                    raise ValueError(
                        f"Invalid {field_name} value in position: {position_data[field_name]}"
                    ) from e

    @classmethod
    def _convert_metrics(cls, data: dict[str, Any]) -> None:
        """Convert metrics data to PortfolioMetrics."""
        if "metrics" in data and isinstance(data["metrics"], dict):
            metrics_data = data["metrics"]
            # Convert Decimal fields in metrics using constant
            for field_name in METRICS_DECIMAL_FIELDS:
                if (
                    field_name in metrics_data
                    and metrics_data[field_name] is not None
                    and isinstance(metrics_data[field_name], str)
                ):
                    try:
                        metrics_data[field_name] = Decimal(metrics_data[field_name])
                    except (ValueError, TypeError) as e:
                        raise ValueError(
                            f"Invalid {field_name} value in metrics: {metrics_data[field_name]}"
                        ) from e
            data["metrics"] = PortfolioMetrics(**metrics_data)
