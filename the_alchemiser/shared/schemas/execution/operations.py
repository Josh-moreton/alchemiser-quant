#!/usr/bin/env python3
"""Business Unit: utilities; Status: current.

General execution result DTOs for The Alchemiser Trading System.

This module contains DTOs for general operation results, including
success/error handling patterns used across the trading system.

Key Features:
- Pydantic v2 BaseModel with strict validation
- Consistent success/error patterns
- Type safety for operation results
- Comprehensive field validation
"""

from __future__ import annotations

from typing import Any

from pydantic import ConfigDict

from the_alchemiser.shared.schemas.core.base import Result


class OperationResult(Result):
    """Generic DTO for operation results with success/error handling."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    details: dict[str, Any] | None = None


class OrderCancellationResult(Result):
    """DTO for order cancellation results."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    order_id: str | None = None


class OrderStatusResult(Result):
    """DTO for order status query results."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    order_id: str | None = None
    status: str | None = None
