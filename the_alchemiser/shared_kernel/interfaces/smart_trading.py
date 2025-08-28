#!/usr/bin/env python3
"""Business Unit: order execution/placement; Status: current.

Smart Trading DTOs for The Alchemiser Trading System.

This module contains DTOs for advanced trading operations like smart order execution
and comprehensive trading dashboard results.

Key Features:
- Pydantic v2 BaseModel with strict validation
- Complex trading operation results
- Enhanced validation metadata
- Comprehensive trading dashboard data
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict

from the_alchemiser.shared_kernel.interfaces.accounts import AccountSummaryDTO, TradeEligibilityDTO
from the_alchemiser.shared_kernel.interfaces.base import ResultDTO
from the_alchemiser.shared_kernel.interfaces.orders import OrderExecutionResultDTO


class OrderValidationMetadataDTO(BaseModel):
    """DTO for order validation metadata from DTO validation process."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    validated_order_id: str | None
    estimated_value: Decimal | None
    risk_score: Decimal | None
    is_fractional: bool
    validation_timestamp: datetime


class SmartOrderExecutionDTO(ResultDTO):
    """DTO for smart order execution results with comprehensive metadata.

    Contains order execution results plus validation and account impact data.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    order_execution: OrderExecutionResultDTO | None = None
    pre_trade_validation: TradeEligibilityDTO | None = None
    order_validation: OrderValidationMetadataDTO | None = None
    account_impact: AccountSummaryDTO | None = None
    reason: str | None = None
    error: str | None = None

    validation_details: dict[str, Any] | None = None


class TradingDashboardDTO(ResultDTO):
    """DTO for comprehensive trading dashboard data."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    account: AccountSummaryDTO
    risk_metrics: dict[str, Any]
    portfolio_allocation: dict[str, Any]
    position_summary: dict[str, Any]
    open_orders: list[dict[str, Any]]
    market_status: dict[str, Any]
    timestamp: datetime
    error: str | None = None
