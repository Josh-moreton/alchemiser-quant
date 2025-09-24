#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Portfolio state schemas for inter-module communication.

Provides typed schemas for portfolio state with correlation tracking and
serialization helpers for communication between portfolio and other modules.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..utils.timezone_utils import ensure_timezone_aware


class Position(BaseModel):
    """Schema for individual position data."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
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
    """Schema for portfolio performance metrics."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    total_value: Decimal = Field(..., ge=0, description="Total portfolio value")
    cash_value: Decimal = Field(..., ge=0, description="Cash value")
    equity_value: Decimal = Field(..., ge=0, description="Equity value")
    buying_power: Decimal = Field(..., ge=0, description="Available buying power")

    # P&L metrics
    day_pnl: Decimal = Field(..., description="Day profit/loss")
    day_pnl_percent: Decimal = Field(..., description="Day P&L percentage")
    total_pnl: Decimal = Field(..., description="Total profit/loss")
    total_pnl_percent: Decimal = Field(..., description="Total P&L percentage")

    # Risk metrics
    portfolio_margin: Decimal | None = Field(default=None, ge=0, description="Portfolio margin")
    maintenance_margin: Decimal | None = Field(default=None, ge=0, description="Maintenance margin")


class PortfolioSnapshot(BaseModel):
    """Schema for complete portfolio state data transfer.

    Used for communication between portfolio module and other modules.
    Includes correlation tracking and serialization helpers.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
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
    metrics: PortfolioMetrics | None = Field(default=None, description="Portfolio metrics")

    # Strategy allocations
    strategy_allocations: list[Any] = Field(
        default_factory=list, description="Current strategy allocations"
    )

    # Optional rebalancing metadata
    last_rebalance_time: datetime | None = Field(
        default=None, description="Last rebalancing timestamp"
    )
    last_rebalance_id: str | None = Field(default=None, description="Last rebalance correlation ID")

    @field_validator("timestamp", "last_rebalance_time")
    @classmethod
    def ensure_timezone_aware_timestamps(cls, v: datetime | None) -> datetime | None:
        """Ensure timestamps are timezone-aware."""
        return ensure_timezone_aware(v)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> PortfolioSnapshot:
        """Create PortfolioSnapshot from dictionary data with type conversion.

        Args:
            data: Dictionary containing portfolio state data

        Returns:
            PortfolioSnapshot instance with properly typed fields

        """
        # Create a copy to avoid mutating the original
        processed_data = data.copy()

        # Convert positions data to Position objects
        cls._convert_positions(processed_data)

        # Convert metrics data if present
        cls._convert_metrics(processed_data)

        # Convert datetime fields from strings if needed
        cls._convert_datetime_fields(processed_data)

        return cls(**processed_data)

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
                    positions_data.append(position_data)  # Assume already a schema
            data["positions"] = positions_data

    @classmethod
    def _convert_position_data(cls, position_data: dict[str, Any]) -> None:
        """Convert individual position data types."""
        # Convert decimal fields from strings
        decimal_fields = [
            "quantity",
            "average_cost",
            "current_price",
            "market_value",
            "unrealized_pnl",
            "unrealized_pnl_percent",
            "cost_basis",
        ]
        for field_name in decimal_fields:
            if (
                field_name in position_data
                and position_data[field_name] is not None
                and isinstance(position_data[field_name], str)
            ):
                position_data[field_name] = Decimal(position_data[field_name])

        # Convert datetime fields
        if (
            "last_updated" in position_data
            and position_data["last_updated"] is not None
            and isinstance(position_data["last_updated"], str)
        ):
            position_data["last_updated"] = datetime.fromisoformat(position_data["last_updated"])

    @classmethod
    def _convert_metrics(cls, data: dict[str, Any]) -> None:
        """Convert metrics data to PortfolioMetrics."""
        if "metrics" in data and data["metrics"] is not None:
            metrics_data = data["metrics"]
            if isinstance(metrics_data, dict):
                # Convert decimal fields from strings
                decimal_fields = [
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
                for field_name in decimal_fields:
                    if (
                        field_name in metrics_data
                        and metrics_data[field_name] is not None
                        and isinstance(metrics_data[field_name], str)
                    ):
                        metrics_data[field_name] = Decimal(metrics_data[field_name])

                data["metrics"] = PortfolioMetrics(**metrics_data)

    @classmethod
    def _convert_datetime_fields(cls, data: dict[str, Any]) -> None:
        """Convert datetime fields from strings."""
        datetime_fields = ["timestamp", "last_rebalance_time"]
        for field_name in datetime_fields:
            if (
                field_name in data
                and data[field_name] is not None
                and isinstance(data[field_name], str)
            ):
                data[field_name] = datetime.fromisoformat(data[field_name])

    def to_dict(self) -> dict[str, Any]:
        """Convert schema to dictionary for serialization.

        Returns:
            Dictionary representation with properly serialized values.

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
            if data.get(field_name):
                data[field_name] = data[field_name].isoformat()

    def _serialize_decimal_fields(self, data: dict[str, Any]) -> None:
        """Convert Decimal fields to strings."""
        # Top-level decimal fields
        for field_name in data:
            if isinstance(data[field_name], Decimal):
                data[field_name] = str(data[field_name])

    def _serialize_strategy_allocations(self, data: dict[str, Any]) -> None:
        """Serialize strategy allocations."""
        if data.get("strategy_allocations"):
            # Keep as-is for now, may need specific serialization later
            pass

    def _serialize_positions(self, data: dict[str, Any]) -> None:
        """Serialize positions data."""
        if data.get("positions"):
            for position_data in data["positions"]:
                if isinstance(position_data, dict):
                    # Convert decimals to strings
                    for key, value in position_data.items():
                        if isinstance(value, Decimal):
                            position_data[key] = str(value)
                        elif isinstance(value, datetime):
                            position_data[key] = value.isoformat()

    def _serialize_metrics(self, data: dict[str, Any]) -> None:
        """Serialize metrics data."""
        if "metrics" in data and data["metrics"] is not None:
            metrics_data = data["metrics"]
            if isinstance(metrics_data, dict):
                for key, value in metrics_data.items():
                    if isinstance(value, Decimal):
                        metrics_data[key] = str(value)