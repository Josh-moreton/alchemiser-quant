#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Order request data transfer objects for inter-module communication.

Provides typed schemas for order requests with correlation tracking and
serialization helpers for communication between portfolio and execution modules.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..utils.timezone_utils import ensure_timezone_aware


class OrderRequest(BaseModel):
    """DTO for order request data transfer.

    Used for communication from portfolio module to execution module.
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
    timestamp: datetime = Field(..., description="Order request timestamp")

    # Order identification
    request_id: str = Field(..., min_length=1, description="Unique request identifier")
    portfolio_id: str = Field(..., min_length=1, description="Portfolio identifier")
    strategy_id: str | None = Field(default=None, description="Strategy identifier if applicable")

    # Order details
    symbol: str = Field(..., min_length=1, max_length=50, description="Trading symbol (supports extended notation like EQUITIES::SYMBOL//USD)")
    side: Literal["BUY", "SELL"] = Field(..., description="Order side")
    quantity: Decimal = Field(..., gt=0, description="Order quantity")
    order_type: Literal["MARKET", "LIMIT", "STOP", "STOP_LIMIT"] = Field(
        default="MARKET", description="Order type"
    )

    # Pricing (optional depending on order type)
    limit_price: Decimal | None = Field(
        default=None, gt=0, description="Limit price for limit orders"
    )
    stop_price: Decimal | None = Field(default=None, gt=0, description="Stop price for stop orders")

    # Order constraints
    time_in_force: Literal["DAY", "GTC", "IOC", "FOK"] = Field(
        default="DAY", description="Time in force"
    )
    extended_hours: bool = Field(default=False, description="Allow extended hours trading")

    # Execution preferences
    execution_priority: Literal["SPEED", "COST", "BALANCE"] = Field(
        default="BALANCE", description="Execution priority preference"
    )
    max_slippage_percent: Decimal | None = Field(
        default=None, ge=0, le=1, description="Maximum acceptable slippage percentage"
    )

    # Risk management
    position_intent: Literal["OPEN", "CLOSE", "INCREASE", "DECREASE"] = Field(
        default="OPEN", description="Position intent for risk management"
    )
    risk_budget: Decimal | None = Field(default=None, gt=0, description="Risk budget for the order")

    # Optional metadata
    reason: str | None = Field(default=None, description="Human-readable reason for the order")
    rebalance_plan_id: str | None = Field(
        default=None, description="Associated rebalance plan ID if applicable"
    )
    metadata: dict[str, Any] | None = Field(default=None, description="Additional order metadata")

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase."""
        return v.strip().upper()

    @field_validator("timestamp")
    @classmethod
    def ensure_timezone_aware_order_timestamp(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware."""
        return ensure_timezone_aware(v)

    def to_dict(self) -> dict[str, Any]:
        """Convert DTO to dictionary for serialization.

        Returns:
            Dictionary representation of the DTO with properly serialized values.

        """
        data = self.model_dump()

        # Convert datetime to ISO string
        if self.timestamp:
            data["timestamp"] = self.timestamp.isoformat()

        # Convert Decimal fields to string for JSON serialization
        decimal_fields = [
            "quantity",
            "limit_price",
            "stop_price",
            "max_slippage_percent",
            "risk_budget",
        ]
        for field_name in decimal_fields:
            if data.get(field_name) is not None:
                data[field_name] = str(data[field_name])

        return data

    @classmethod
    def _convert_timestamp_from_string(cls, data: dict[str, Any]) -> None:
        """Convert string timestamp to datetime in-place.

        Args:
            data: Dictionary to modify

        Raises:
            ValueError: If timestamp format is invalid

        """
        if "timestamp" not in data or not isinstance(data["timestamp"], str):
            return

        try:
            timestamp_str = data["timestamp"]
            if timestamp_str.endswith("Z"):
                timestamp_str = timestamp_str[:-1] + "+00:00"
            data["timestamp"] = datetime.fromisoformat(timestamp_str)
        except ValueError as e:
            raise ValueError(f"Invalid timestamp format: {data['timestamp']}") from e

    @classmethod
    def _convert_decimal_field(cls, data: dict[str, Any], field_name: str) -> None:
        """Convert string decimal field to Decimal in-place.

        Args:
            data: Dictionary to modify
            field_name: Name of the field to convert

        Raises:
            ValueError: If decimal value is invalid

        """
        if field_name not in data or data[field_name] is None:
            return
        if not isinstance(data[field_name], str):
            return

        try:
            data[field_name] = Decimal(data[field_name])
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid {field_name} value: {data[field_name]}") from e
        except Exception as e:
            raise ValueError(f"Invalid {field_name} value: {data[field_name]}") from e

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> OrderRequest:
        """Create DTO from dictionary.

        Args:
            data: Dictionary containing DTO data

        Returns:
            OrderRequest instance

        Raises:
            ValueError: If data is invalid or missing required fields

        """
        cls._convert_timestamp_from_string(data)

        decimal_fields = [
            "quantity",
            "limit_price",
            "stop_price",
            "max_slippage_percent",
            "risk_budget",
        ]
        for field_name in decimal_fields:
            cls._convert_decimal_field(data, field_name)

        return cls(**data)


class MarketData(BaseModel):
    """DTO for market data transfer between modules."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Required correlation fields
    correlation_id: str = Field(..., min_length=1, description="Unique correlation identifier")
    timestamp: datetime = Field(..., description="Market data timestamp")

    # Market data identification
    symbol: str = Field(..., min_length=1, max_length=50, description="Trading symbol (supports extended notation like EQUITIES::SYMBOL//USD)")
    data_type: Literal["QUOTE", "TRADE", "BAR", "SNAPSHOT"] = Field(
        ..., description="Type of market data"
    )

    # Price data
    price: Decimal | None = Field(default=None, gt=0, description="Current/last price")
    bid_price: Decimal | None = Field(default=None, gt=0, description="Bid price")
    ask_price: Decimal | None = Field(default=None, gt=0, description="Ask price")

    # Size data
    volume: Decimal | None = Field(default=None, ge=0, description="Volume")
    bid_size: Decimal | None = Field(default=None, ge=0, description="Bid size")
    ask_size: Decimal | None = Field(default=None, ge=0, description="Ask size")

    # OHLC data (for bars)
    open_price: Decimal | None = Field(default=None, gt=0, description="Open price")
    high_price: Decimal | None = Field(default=None, gt=0, description="High price")
    low_price: Decimal | None = Field(default=None, gt=0, description="Low price")
    close_price: Decimal | None = Field(default=None, gt=0, description="Close price")

    # Market status
    market_open: bool | None = Field(default=None, description="Whether market is open")
    halted: bool | None = Field(default=None, description="Whether trading is halted")

    # Data quality and source
    data_source: str | None = Field(default=None, description="Data source identifier")
    quality_score: Decimal | None = Field(
        default=None, ge=0, le=1, description="Data quality score (0-1)"
    )

    # Optional metadata
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional market data metadata"
    )

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase."""
        return v.strip().upper()

    @field_validator("timestamp")
    @classmethod
    def ensure_timezone_aware_market_timestamp(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware."""
        return ensure_timezone_aware(v)

    def to_dict(self) -> dict[str, Any]:
        """Convert DTO to dictionary for serialization."""
        data = self.model_dump()

        # Convert datetime to ISO string
        if self.timestamp:
            data["timestamp"] = self.timestamp.isoformat()

        # Convert Decimal fields to string for JSON serialization
        decimal_fields = [
            "price",
            "bid_price",
            "ask_price",
            "volume",
            "bid_size",
            "ask_size",
            "open_price",
            "high_price",
            "low_price",
            "close_price",
            "quality_score",
        ]
        for field_name in decimal_fields:
            if data.get(field_name) is not None:
                data[field_name] = str(data[field_name])

        return data

    @classmethod
    def _convert_timestamp_from_string(cls, data: dict[str, Any]) -> None:
        """Convert string timestamp to datetime in-place.

        Args:
            data: Dictionary to modify

        Raises:
            ValueError: If timestamp format is invalid

        """
        if "timestamp" not in data or not isinstance(data["timestamp"], str):
            return

        try:
            timestamp_str = data["timestamp"]
            if timestamp_str.endswith("Z"):
                timestamp_str = timestamp_str[:-1] + "+00:00"
            data["timestamp"] = datetime.fromisoformat(timestamp_str)
        except ValueError as e:
            raise ValueError(f"Invalid timestamp format: {data['timestamp']}") from e

    @classmethod
    def _convert_decimal_field(cls, data: dict[str, Any], field_name: str) -> None:
        """Convert string decimal field to Decimal in-place.

        Args:
            data: Dictionary to modify
            field_name: Name of the field to convert

        Raises:
            ValueError: If decimal value is invalid

        """
        if field_name not in data or data[field_name] is None:
            return
        if not isinstance(data[field_name], str):
            return

        try:
            data[field_name] = Decimal(data[field_name])
        except (ValueError, TypeError) as e:
            raise ValueError(f"Invalid {field_name} value: {data[field_name]}") from e
        except Exception as e:
            raise ValueError(f"Invalid {field_name} value: {data[field_name]}") from e

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> MarketData:
        """Create DTO from dictionary."""
        cls._convert_timestamp_from_string(data)

        decimal_fields = [
            "price",
            "bid_price",
            "ask_price",
            "volume",
            "bid_size",
            "ask_size",
            "open_price",
            "high_price",
            "low_price",
            "close_price",
            "quality_score",
        ]
        for field_name in decimal_fields:
            cls._convert_decimal_field(data, field_name)

        return cls(**data)
