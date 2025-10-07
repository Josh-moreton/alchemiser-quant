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

from the_alchemiser.shared.value_objects.core_types import OrderDetails, StrategyPnLSummary


# Dashboard and Metrics Types
class DashboardMetrics(BaseModel):
    """Dashboard metrics for real-time display.
    
    Contains current portfolio state and performance for dashboard display.
    """
    
    model_config = ConfigDict(strict=True, frozen=True)
    
    total_portfolio_value: float = Field(description="Current total portfolio value")
    daily_pnl: float = Field(description="Absolute daily P&L")
    daily_pnl_percentage: float = Field(description="Daily P&L as percentage")
    active_positions: int = Field(description="Number of active positions", ge=0)
    cash_balance: float = Field(description="Current cash balance")


class ReportingData(BaseModel):
    """General reporting data structure.
    
    Aggregates portfolio summary, performance metrics, and recent trades
    for reporting purposes.
    """
    
    model_config = ConfigDict(strict=True, frozen=True)
    
    timestamp: str = Field(description="ISO 8601 timestamp")
    portfolio_summary: dict[str, Any] = Field(
        description="Portfolio state summary"
    )
    performance_metrics: dict[str, float] = Field(
        description="Performance metrics dictionary"
    )
    recent_trades: list[OrderDetails] = Field(
        default_factory=list,
        description="List of recent order details"
    )


# Email and Notification Types
class EmailReportData(BaseModel):
    """Email report data structure.
    
    Contains formatted email content for sending trading reports.
    """
    
    model_config = ConfigDict(strict=True, frozen=True)
    
    subject: str = Field(description="Email subject line")
    html_content: str = Field(description="HTML-formatted email body")
    recipient: str = Field(description="Recipient email address")
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional email metadata"
    )


class EmailCredentials(BaseModel):
    """Email service credentials.
    
    Contains SMTP configuration for sending emails. Sensitive data should
    be redacted from logs.
    """
    
    model_config = ConfigDict(strict=True, frozen=True)
    
    smtp_server: str = Field(description="SMTP server hostname")
    smtp_port: int = Field(description="SMTP server port", gt=0, le=65535)
    email_address: str = Field(description="Sender email address")
    email_password: str = Field(description="Email password (sensitive)", repr=False)
    recipient_email: str = Field(description="Default recipient email address")


class EmailSummary(BaseModel):
    """Email summary for trading reports.
    
    Aggregates order history, performance metrics, and strategy summaries
    for email reporting.
    """
    
    model_config = ConfigDict(strict=True, frozen=True)
    
    total_orders: int = Field(description="Total number of orders", ge=0)
    recent_orders: list[OrderDetails] = Field(
        default_factory=list,
        description="List of recent orders"
    )
    performance_metrics: dict[str, float] = Field(
        default_factory=dict,
        description="Performance metrics summary"
    )
    strategy_summaries: dict[str, StrategyPnLSummary] = Field(
        default_factory=dict,
        description="Per-strategy P&L summaries"
    )


# Performance Analysis Types
class BacktestResult(BaseModel):
    """Backtest execution results.
    
    Contains comprehensive backtest performance metrics and metadata.
    """
    
    model_config = ConfigDict(strict=True, frozen=True)
    
    strategy_name: str = Field(description="Strategy identifier")
    start_date: str = Field(description="Backtest start date (ISO 8601)")
    end_date: str = Field(description="Backtest end date (ISO 8601)")
    total_return: float = Field(description="Total return percentage")
    sharpe_ratio: float = Field(description="Risk-adjusted return (Sharpe)")
    max_drawdown: float = Field(description="Maximum drawdown percentage")
    total_trades: int = Field(description="Total number of trades executed", ge=0)
    win_rate: float = Field(description="Win rate percentage", ge=0.0, le=100.0)
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional backtest metadata"
    )


class PerformanceMetrics(BaseModel):
    """Performance analysis metrics.
    
    Contains comprehensive risk and return metrics for strategy evaluation.
    """
    
    model_config = ConfigDict(strict=True, frozen=True)
    
    returns: list[float] = Field(
        default_factory=list,
        description="Time series of returns"
    )
    cumulative_return: float = Field(description="Cumulative return percentage")
    volatility: float = Field(description="Return volatility (annualized)", ge=0.0)
    sharpe_ratio: float = Field(description="Risk-adjusted return (Sharpe)")
    max_drawdown: float = Field(description="Maximum drawdown percentage")
    calmar_ratio: float = Field(description="Return to max drawdown ratio")
    sortino_ratio: float = Field(description="Downside risk-adjusted return")


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
