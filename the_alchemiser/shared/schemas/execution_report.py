#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Execution report data transfer objects for inter-module communication.

Provides typed DTOs for execution reports with correlation tracking and
serialization helpers for communication between execution and other modules.
"""

from __future__ import annotations

import hashlib
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core.core_schema import ValidationInfo

from ..constants import CONTRACT_VERSION
from ..utils.data_conversion import (
    convert_datetime_fields_from_dict,
    convert_datetime_fields_to_dict,
    convert_decimal_fields_from_dict,
    convert_decimal_fields_to_dict,
    convert_nested_order_data,
)
from ..utils.timezone_utils import ensure_timezone_aware


class ExecutedOrder(BaseModel):
    """DTO for individual executed order.

    Represents a single executed order with all relevant execution details.
    This DTO is immutable (frozen) and strictly validated.

    Example:
        >>> from decimal import Decimal
        >>> from datetime import datetime, UTC
        >>> order = ExecutedOrder(
        ...     schema_version="1.0",
        ...     order_id="abc123",
        ...     symbol="AAPL",
        ...     action="BUY",
        ...     quantity=Decimal("10"),
        ...     filled_quantity=Decimal("10"),
        ...     price=Decimal("150.50"),
        ...     total_value=Decimal("1505.00"),
        ...     status="FILLED",
        ...     execution_timestamp=datetime.now(UTC)
        ... )

    """

    __schema_version__: str = CONTRACT_VERSION

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Schema version for evolution
    schema_version: str = Field(
        default=CONTRACT_VERSION,
        frozen=True,
        description="Schema version for DTO evolution",
    )

    order_id: str = Field(..., min_length=1, description="Unique order identifier")
    client_order_id: str | None = Field(
        default=None, description="Client-specified order identifier for tracking"
    )
    symbol: str = Field(..., min_length=1, max_length=20, description="Trading symbol")
    action: str = Field(..., description="Trading action (BUY, SELL)")
    quantity: Decimal = Field(..., gt=0, description="Order quantity")
    filled_quantity: Decimal = Field(..., ge=0, description="Filled quantity")
    price: Decimal = Field(..., gt=0, description="Execution price")
    total_value: Decimal = Field(..., gt=0, description="Total execution value")
    status: str = Field(..., description="Order status (FILLED, PARTIAL, REJECTED, etc.)")
    execution_timestamp: datetime = Field(..., description="Order execution timestamp")

    # Optional fields
    commission: Decimal | None = Field(default=None, ge=0, description="Commission paid")
    fees: Decimal | None = Field(default=None, ge=0, description="Additional fees")
    error_message: str | None = Field(default=None, description="Error message if failed")

    @field_validator("symbol")
    @classmethod
    def normalize_symbol(cls, v: str) -> str:
        """Normalize symbol to uppercase."""
        return v.strip().upper()

    @field_validator("action")
    @classmethod
    def validate_action(cls, v: str) -> str:
        """Validate and normalize action to uppercase.

        Accepts lowercase or uppercase input and normalizes to uppercase.
        Only 'BUY' or 'SELL' are valid actions.
        """
        action_upper = v.strip().upper()
        if action_upper not in {"BUY", "SELL"}:
            raise ValueError(f"Action must be 'BUY' or 'SELL', got '{action_upper}'")
        return action_upper

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: str) -> str:
        """Validate order status.

        Normalizes status to uppercase and validates against known statuses.
        Note: CANCELLED and CANCELED are both accepted (different spellings).
        """
        valid_statuses = {
            "FILLED",
            "PARTIAL",
            "REJECTED",
            "CANCELLED",
            "CANCELED",
            "PENDING",
            "PENDING_NEW",
            "FAILED",
            "ACCEPTED",
        }
        status_upper = v.strip().upper()
        if status_upper not in valid_statuses:
            raise ValueError(f"Status must be one of {valid_statuses}, got '{status_upper}'")
        return status_upper

    @field_validator("execution_timestamp")
    @classmethod
    def ensure_timezone_aware_execution_timestamp(cls, v: datetime) -> datetime:
        """Ensure execution_timestamp is timezone-aware.

        Raises:
            ValueError: If timestamp cannot be made timezone-aware.

        """
        result = ensure_timezone_aware(v)
        if result is None:
            raise ValueError("execution_timestamp cannot be None")
        return result


class ExecutionReport(BaseModel):
    """DTO for execution report data transfer.

    Used for communication between execution module and other modules.
    Includes correlation tracking, schema versioning, idempotency support,
    and serialization helpers for event-driven architecture.

    The idempotency_key is generated from a hash of key fields to enable
    deduplication in event replay scenarios.

    Example:
        >>> from decimal import Decimal
        >>> from datetime import datetime, UTC
        >>> report = ExecutionReport(
        ...     schema_version="1.0",
        ...     correlation_id="corr-123",
        ...     causation_id="cause-456",
        ...     timestamp=datetime.now(UTC),
        ...     execution_id="exec-789",
        ...     total_orders=5,
        ...     successful_orders=5,
        ...     failed_orders=0,
        ...     total_value_traded=Decimal("10000.00"),
        ...     total_commissions=Decimal("10.00"),
        ...     total_fees=Decimal("5.00"),
        ...     net_cash_flow=Decimal("-10015.00"),
        ...     execution_start_time=datetime.now(UTC),
        ...     execution_end_time=datetime.now(UTC),
        ...     total_duration_seconds=Decimal("45.5"),
        ...     success_rate=Decimal("1.0")
        ... )

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Schema version for evolution
    schema_version: str = Field(
        default=CONTRACT_VERSION,
        frozen=True,
        description="Schema version for DTO evolution",
    )

    # Required correlation fields
    correlation_id: str = Field(..., min_length=1, description="Unique correlation identifier")
    causation_id: str = Field(
        ..., min_length=1, description="Causation identifier for traceability"
    )
    timestamp: datetime = Field(..., description="Report generation timestamp")

    # Report identification
    execution_id: str = Field(..., min_length=1, description="Unique execution identifier")
    session_id: str | None = Field(default=None, description="Trading session identifier")

    # Execution summary
    total_orders: int = Field(..., ge=0, description="Total number of orders")
    successful_orders: int = Field(..., ge=0, description="Number of successful orders")
    failed_orders: int = Field(..., ge=0, description="Number of failed orders")

    # Financial summary
    total_value_traded: Decimal = Field(..., ge=0, description="Total value traded")
    total_commissions: Decimal = Field(..., ge=0, description="Total commissions paid")
    total_fees: Decimal = Field(..., ge=0, description="Total fees paid")
    net_cash_flow: Decimal = Field(
        ...,
        description="Net cash flow (negative for net purchases, positive for net sales)",
    )

    # Timing - use Decimal for consistency with average_execution_time_seconds
    execution_start_time: datetime = Field(..., description="Execution start timestamp")
    execution_end_time: datetime = Field(..., description="Execution end timestamp")
    total_duration_seconds: Decimal = Field(
        ..., ge=0, description="Total execution duration in seconds"
    )

    # Order details
    orders: list[ExecutedOrder] = Field(
        default_factory=list,
        description="List of executed orders",
        max_length=10000,  # Reasonable limit to prevent memory issues
    )

    # Performance metrics
    success_rate: Decimal = Field(..., ge=0, le=1, description="Success rate (0-1)")
    average_execution_time_seconds: Decimal | None = Field(
        default=None, ge=0, description="Average order execution time"
    )

    # Optional metadata
    broker_used: str | None = Field(default=None, description="Broker used for execution")
    execution_strategy: str | None = Field(default=None, description="Execution strategy used")
    market_conditions: str | None = Field(
        default=None, description="Market conditions during execution"
    )
    metadata: dict[str, Any] | None = Field(
        default=None, description="Additional execution metadata"
    )

    @field_validator("timestamp", "execution_start_time", "execution_end_time")
    @classmethod
    def ensure_timezone_aware_timestamps(cls, v: datetime, info: ValidationInfo) -> datetime:
        """Ensure timestamp is timezone-aware.

        Args:
            v: The datetime value to validate
            info: Pydantic validation info containing field name

        Raises:
            ValueError: If timestamp cannot be made timezone-aware, with field name in error.

        """
        result = ensure_timezone_aware(v)
        if result is None:
            field_name = info.field_name if hasattr(info, "field_name") else "timestamp"
            raise ValueError(f"{field_name} cannot be None")
        return result

    @property
    def idempotency_key(self) -> str:
        """Generate deterministic idempotency key from report content.

        The key is a SHA-256 hash of critical fields to enable deduplication
        in event replay scenarios. This ensures the same execution report
        produces the same idempotency key.

        Returns:
            Hex string representation of SHA-256 hash of key fields.

        Example:
            >>> report = ExecutionReport(...)
            >>> key1 = report.idempotency_key
            >>> key2 = report.idempotency_key
            >>> assert key1 == key2  # Deterministic

        """
        # Create deterministic string from key fields
        key_data = (
            f"{self.schema_version}|"
            f"{self.execution_id}|"
            f"{self.correlation_id}|"
            f"{self.timestamp.isoformat()}|"
            f"{self.total_orders}|"
            f"{self.successful_orders}|"
            f"{self.failed_orders}|"
            f"{self.total_value_traded}|"
            f"{self.success_rate}"
        )
        return hashlib.sha256(key_data.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        """Convert DTO to dictionary for serialization.

        Uses centralized data_conversion utilities for consistent serialization
        across all DTOs. Returns a new dictionary without modifying internal state.

        Returns:
            Dictionary representation of the DTO with properly serialized values.

        Example:
            >>> report = ExecutionReport(...)
            >>> data = report.to_dict()
            >>> isinstance(data["total_value_traded"], str)  # Decimals as strings
            True
            >>> isinstance(data["timestamp"], str)  # Datetimes as ISO strings
            True

        """
        data = self.model_dump()

        # Convert datetime fields to ISO strings using centralized utility
        datetime_fields = ["timestamp", "execution_start_time", "execution_end_time"]
        convert_datetime_fields_to_dict(data, datetime_fields)

        # Convert Decimal fields to string for JSON serialization using centralized utility
        decimal_fields = [
            "total_value_traded",
            "total_commissions",
            "total_fees",
            "net_cash_flow",
            "success_rate",
            "average_execution_time_seconds",
            "total_duration_seconds",
        ]
        convert_decimal_fields_to_dict(data, decimal_fields)

        # Convert nested orders using helper method
        if data.get("orders"):
            data["orders"] = self._convert_orders_to_dict(data["orders"])

        return data

    @staticmethod
    def _convert_orders_to_dict(orders: list[Any]) -> list[dict[str, Any]]:
        """Convert orders list to dictionary format for serialization.

        Extracts order conversion logic to reduce cognitive complexity
        in the main to_dict method.

        Args:
            orders: List of order data (dicts or DTOs)

        Returns:
            List of order dictionaries with properly serialized values

        """
        orders_data = []
        for order in orders:
            # Convert order model to dict if needed
            order_dict = dict(order) if not isinstance(order, dict) else order

            # Convert order datetime fields
            if order_dict.get("execution_timestamp") is not None and isinstance(
                order_dict["execution_timestamp"], datetime
            ):
                order_dict["execution_timestamp"] = order_dict["execution_timestamp"].isoformat()

            # Convert order Decimal fields
            order_decimal_fields = [
                "quantity",
                "filled_quantity",
                "price",
                "total_value",
                "commission",
                "fees",
            ]
            for field_name in order_decimal_fields:
                if order_dict.get(field_name) is not None and isinstance(
                    order_dict[field_name], Decimal
                ):
                    order_dict[field_name] = str(order_dict[field_name])

            orders_data.append(order_dict)
        return orders_data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ExecutionReport:
        """Create DTO from dictionary.

        Handles deserialization from JSON-compatible dictionaries,
        converting string representations back to proper types.

        Args:
            data: Dictionary containing DTO data

        Returns:
            ExecutionReport instance

        Raises:
            ValueError: If data is invalid or missing required fields

        Example:
            >>> data = {
            ...     "schema_version": "1.0",
            ...     "correlation_id": "corr-123",
            ...     "execution_id": "exec-456",
            ...     "timestamp": "2024-01-01T12:00:00+00:00",
            ...     "total_orders": 5,
            ...     "successful_orders": 5,
            ...     "failed_orders": 0,
            ...     "total_value_traded": "10000.00",
            ...     "success_rate": "1.0",
            ...     # ... other required fields
            ... }
            >>> report = ExecutionReport.from_dict(data)

        """
        # Convert string timestamps back to datetime
        datetime_fields = ["timestamp", "execution_start_time", "execution_end_time"]
        convert_datetime_fields_from_dict(data, datetime_fields)

        # Convert string decimal fields back to Decimal
        decimal_fields = [
            "total_value_traded",
            "total_commissions",
            "total_fees",
            "net_cash_flow",
            "success_rate",
            "average_execution_time_seconds",
            "total_duration_seconds",
        ]
        convert_decimal_fields_from_dict(data, decimal_fields)

        # Convert orders if present
        data["orders"] = cls._convert_orders_from_dict(data.get("orders", []))

        return cls(**data)

    @classmethod
    def _convert_orders_from_dict(cls, orders: list[Any]) -> list[ExecutedOrder]:
        """Convert orders list from dictionary format.

        Provides type-safe conversion with explicit validation that all
        items are either dicts (to be converted) or ExecutedOrder instances.

        Args:
            orders: List of order data (dicts or DTOs)

        Returns:
            List of ExecutedOrder instances

        Raises:
            TypeError: If orders contains invalid types

        """
        if not isinstance(orders, list):
            return []

        orders_data: list[ExecutedOrder] = []
        for order_data in orders:
            if isinstance(order_data, dict):
                # Convert dict to ExecutedOrder
                converted_order = convert_nested_order_data(dict(order_data))
                orders_data.append(ExecutedOrder(**converted_order))
            elif isinstance(order_data, ExecutedOrder):
                # Already a proper DTO
                orders_data.append(order_data)
            else:
                # Invalid type - fail explicitly rather than silently assuming
                raise TypeError(
                    f"Order data must be dict or ExecutedOrder, got {type(order_data).__name__}"
                )

        return orders_data
