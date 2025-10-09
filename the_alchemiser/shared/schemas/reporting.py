#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Reporting and dashboard DTOs for The Alchemiser Trading System.

This module contains Pydantic models for reporting, dashboard metrics, and email
notifications. Migrated from TypedDict to Pydantic for runtime validation and
consistent serialization.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from the_alchemiser.shared.value_objects.core_types import (
    OrderDetails,
    StrategyPnLSummary,
)


# Dashboard and Metrics Types
class DashboardMetrics(BaseModel):
    """Dashboard metrics for system monitoring."""

    model_config = ConfigDict(strict=True, frozen=True)

    total_positions: int = Field(description="Total number of open positions", ge=0)
    total_value: Decimal = Field(description="Total portfolio value")
    daily_pnl: Decimal = Field(description="Daily profit and loss")
    strategies_active: int = Field(description="Number of active strategies", ge=0)


class ReportingData(BaseModel):
    """Reporting data aggregation."""

    model_config = ConfigDict(strict=True, frozen=True)

    timestamp: str = Field(description="Report timestamp")
    metrics: DashboardMetrics = Field(description="Dashboard metrics")


# Email and Notification Types
class EmailReportData(BaseModel):
    """Email report data structure."""

    model_config = ConfigDict(strict=True, frozen=True)

    subject: str = Field(description="Email subject line")
    content: str = Field(description="Email content body")
    recipient: str = Field(description="Email recipient address")


class EmailCredentials(BaseModel):
    """Email service credentials."""

    model_config = ConfigDict(strict=True, frozen=True)

    username: str = Field(description="SMTP username")
    password: str = Field(description="SMTP password")
    host: str = Field(description="SMTP host address")
    port: int = Field(description="SMTP port", gt=0, le=65535)


class EmailSummary(BaseModel):
    """Email summary for trading reports.

    Aggregates order history, performance metrics, and strategy summaries
    for email reporting.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    total_orders: int = Field(description="Total number of orders", ge=0)
    recent_orders: list[OrderDetails] = Field(
        default_factory=list, description="List of recent orders"
    )
    performance_metrics: dict[str, float] = Field(
        default_factory=dict, description="Performance metrics summary"
    )
    strategy_summaries: dict[str, StrategyPnLSummary] = Field(
        default_factory=dict, description="Per-strategy P&L summaries"
    )


# Performance Analysis Types
class BacktestResult(BaseModel):
    """Backtest result data."""

    model_config = ConfigDict(strict=True, frozen=True)

    start_date: str = Field(description="Backtest start date")
    end_date: str = Field(description="Backtest end date")
    total_return: Decimal = Field(description="Total return percentage")
    sharpe_ratio: Decimal = Field(description="Sharpe ratio")
    max_drawdown: Decimal = Field(description="Maximum drawdown percentage")


class PerformanceMetrics(BaseModel):
    """Performance metrics summary."""

    model_config = ConfigDict(strict=True, frozen=True)

    total_return: Decimal = Field(description="Total return")
    sharpe_ratio: Decimal = Field(description="Sharpe ratio")
    volatility: Decimal = Field(description="Portfolio volatility")
    max_drawdown: Decimal = Field(description="Maximum drawdown")


# Monthly Summary Report Types
class MonthlySummaryDTO(BaseModel):
    """DTO for monthly portfolio and strategy performance summary."""

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    # Month identification
    month_label: str = Field(..., description="Human-readable month label (e.g., 'Aug 2025')")

    # Portfolio P&L for the month
    portfolio_first_value: Decimal | None = Field(
        default=None, description="Portfolio value at start of month"
    )
    portfolio_last_value: Decimal | None = Field(
        default=None, description="Portfolio value at end of month"
    )
    portfolio_pnl_abs: Decimal | None = Field(
        default=None, description="Absolute P&L change for the month"
    )
    portfolio_pnl_pct: Decimal | None = Field(
        default=None, description="Percentage P&L change for the month"
    )

    # Per-strategy realized P&L for the month
    strategy_rows: list[dict[str, Any]] = Field(
        default_factory=list, description="Strategy performance rows"
    )

    # Additional context and warnings
    notes: list[str] = Field(default_factory=list, description="Additional notes or warnings")
