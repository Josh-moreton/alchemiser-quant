#!/usr/bin/env python3
"""Business Unit: utilities; Status: current.

Account DTOs for The Alchemiser Trading System.

This module contains DTOs for account data, buying power checks, risk metrics,
and account-related operations.

Key Features:
- Pydantic v2 BaseModel with strict validation
- Decimal precision for financial values
- Comprehensive field validation and normalization
- Type safety for account management operations
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict

from the_alchemiser.interfaces.schemas.base import ResultDTO


class AccountSummaryDTO(BaseModel):
    """DTO for comprehensive account summary.

    Used when returning account data from TradingSystemCoordinator methods.
    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    account_id: str
    equity: Decimal
    cash: Decimal
    market_value: Decimal
    buying_power: Decimal
    last_equity: Decimal
    day_trade_count: int
    pattern_day_trader: bool
    trading_blocked: bool
    transfers_blocked: bool
    account_blocked: bool
    calculated_metrics: AccountMetricsDTO


class AccountMetricsDTO(BaseModel):
    """DTO for calculated account metrics."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    cash_ratio: Decimal
    market_exposure: Decimal
    leverage_ratio: Decimal | None
    available_buying_power_ratio: Decimal


class BuyingPowerDTO(ResultDTO):
    """DTO for buying power check results."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    available_buying_power: Decimal | None = None
    required_amount: Decimal | None = None
    sufficient_funds: bool | None = None


class RiskMetricsDTO(ResultDTO):
    """DTO for comprehensive risk metrics."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    risk_metrics: dict[str, Any] | None = None


class TradeEligibilityDTO(BaseModel):
    """DTO for trade eligibility validation results."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    eligible: bool
    reason: str | None = None
    details: dict[str, Any] | None = None
    symbol: str | None = None
    quantity: int | None = None
    side: str | None = None
    estimated_cost: Decimal | None = None


class PortfolioAllocationDTO(ResultDTO):
    """DTO for portfolio allocation and diversification metrics."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    allocation_data: dict[str, Any] | None = None


class EnrichedAccountSummaryDTO(BaseModel):
    """DTO for enriched account summary with typed domain objects."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    raw: dict[str, Any]
    summary: AccountSummaryDTO
