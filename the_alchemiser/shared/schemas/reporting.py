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
    """Dashboard metrics for monitoring and observability."""

    model_config = ConfigDict(strict=True, frozen=True)

    total_positions: int = Field(description="Total number of open positions", ge=0)
    total_value: Decimal = Field(description="Total portfolio value")
    daily_pnl: Decimal = Field(description="Daily profit and loss")
    win_rate: Decimal = Field(description="Win rate percentage", ge=0, le=100)


class ReportingData(BaseModel):
    """Reporting data aggregation for performance analysis."""

    model_config = ConfigDict(strict=True, frozen=True)

    period_label: str = Field(description="Time period label (e.g., 'Daily', 'Monthly')")
    total_trades: int = Field(description="Total number of trades executed", ge=0)
    profitable_trades: int = Field(description="Number of profitable trades", ge=0)
    total_pnl: Decimal = Field(description="Total profit and loss")
    sharpe_ratio: Decimal | None = Field(
        default=None, description="Sharpe ratio if calculable"
    )


# Email and Notification Types
class EmailReportData(BaseModel):
    """Email report data for notification system."""

    model_config = ConfigDict(strict=True, frozen=True)

    subject: str = Field(description="Email subject line")
    recipient: str = Field(description="Email recipient address")
    report_type: str = Field(description="Type of report (e.g., 'daily', 'monthly')")
    generated_at: str = Field(description="ISO 8601 timestamp of report generation")


class EmailCredentials(BaseModel):
    """Email credentials for SMTP authentication."""

    model_config = ConfigDict(strict=True)

    smtp_host: str = Field(description="SMTP server hostname")
    smtp_port: int = Field(description="SMTP server port", ge=1, le=65535)
    username: str = Field(description="SMTP username")
    password: str = Field(description="SMTP password")
    from_address: str = Field(description="Sender email address")


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

    strategy_name: str = Field(description="Name of the strategy")
    start_date: str = Field(description="Backtest start date (ISO 8601)")
    end_date: str = Field(description="Backtest end date (ISO 8601)")
    total_return: Decimal = Field(description="Total return percentage")
    sharpe_ratio: Decimal | None = Field(
        default=None, description="Sharpe ratio if calculable"
    )
    max_drawdown: Decimal = Field(description="Maximum drawdown percentage")
    win_rate: Decimal = Field(description="Win rate percentage", ge=0, le=100)


class PerformanceMetrics(BaseModel):
    """Performance metrics for strategy evaluation."""

    model_config = ConfigDict(strict=True, frozen=True)

    total_trades: int = Field(description="Total number of trades", ge=0)
    winning_trades: int = Field(description="Number of winning trades", ge=0)
    losing_trades: int = Field(description="Number of losing trades", ge=0)
    total_pnl: Decimal = Field(description="Total profit and loss")
    average_win: Decimal = Field(description="Average winning trade amount")
    average_loss: Decimal = Field(description="Average losing trade amount")
    profit_factor: Decimal | None = Field(
        default=None, description="Profit factor (gross profit / gross loss)"
    )


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
