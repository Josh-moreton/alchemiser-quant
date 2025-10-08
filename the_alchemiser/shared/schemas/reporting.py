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
    """Dashboard metrics for real-time display.

    Contains current portfolio state and performance for dashboard display.
    All monetary values use Decimal for precision per Copilot Instructions.

    Examples:
        >>> metrics = DashboardMetrics(
        ...     total_portfolio_value=Decimal("100000.50"),
        ...     daily_pnl=Decimal("1234.56"),
        ...     daily_pnl_percentage=Decimal("1.23"),
        ...     active_positions=5,
        ...     cash_balance=Decimal("50000.25")
        ... )

    """

    model_config = ConfigDict(strict=True, frozen=True, validate_assignment=True)

    total_portfolio_value: Decimal = Field(description="Current total portfolio value in USD")
    daily_pnl: Decimal = Field(description="Absolute daily P&L in USD")
    daily_pnl_percentage: Decimal = Field(description="Daily P&L as percentage (Decimal)")
    active_positions: int = Field(description="Number of active positions", ge=0)
    cash_balance: Decimal = Field(description="Current cash balance in USD")


class ReportingData(BaseModel):
    """General reporting data structure.

    Aggregates portfolio summary, performance metrics, and recent trades
    for reporting purposes. Performance metrics should use Decimal for monetary values.

    Examples:
        >>> data = ReportingData(
        ...     timestamp="2025-01-08T10:00:00Z",
        ...     portfolio_summary={"equity": "100000.00"},
        ...     performance_metrics={"sharpe": Decimal("1.5"), "return": Decimal("0.15")},
        ...     recent_trades=[]
        ... )

    """

    model_config = ConfigDict(strict=True, frozen=True, validate_assignment=True)

    timestamp: str = Field(description="ISO 8601 timestamp (UTC)")
    portfolio_summary: dict[str, Any] = Field(description="Portfolio state summary")
    performance_metrics: dict[str, Decimal] = Field(
        description="Performance metrics dictionary (use Decimal for monetary values)"
    )
    recent_trades: list[OrderDetails] = Field(
        default_factory=list, description="List of recent order details"
    )


# Email and Notification Types
class EmailReportData(BaseModel):
    """Email report data structure.

    Contains formatted email content for sending trading reports.

    Examples:
        >>> report = EmailReportData(
        ...     subject="Daily Trading Report",
        ...     html_content="<html><body>Report content</body></html>",
        ...     recipient="user@example.com",
        ...     metadata={"sender": "system"}
        ... )

    """

    model_config = ConfigDict(strict=True, frozen=True, validate_assignment=True)

    subject: str = Field(description="Email subject line")
    html_content: str = Field(description="HTML-formatted email body")
    recipient: str = Field(description="Recipient email address")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional email metadata")


class EmailCredentials(BaseModel):
    """Email service credentials.

    Contains SMTP configuration for sending emails. Sensitive data should
    be redacted from logs. Password field has repr=False to prevent logging.

    Examples:
        >>> creds = EmailCredentials(
        ...     smtp_server="smtp.gmail.com",
        ...     smtp_port=587,
        ...     email_address="sender@example.com",
        ...     email_password="secret_password",
        ...     recipient_email="recipient@example.com"
        ... )

    """

    model_config = ConfigDict(strict=True, frozen=True, validate_assignment=True)

    smtp_server: str = Field(description="SMTP server hostname")
    smtp_port: int = Field(description="SMTP server port", gt=0, le=65535)
    email_address: str = Field(description="Sender email address")
    email_password: str = Field(description="Email password (sensitive)", repr=False, min_length=1)
    recipient_email: str = Field(description="Default recipient email address")


class EmailSummary(BaseModel):
    """Email summary for trading reports.

    Aggregates order history, performance metrics, and strategy summaries
    for email reporting. Performance metrics should use Decimal for monetary values.

    Examples:
        >>> summary = EmailSummary(
        ...     total_orders=10,
        ...     recent_orders=[],
        ...     performance_metrics={"sharpe": Decimal("1.5")},
        ...     strategy_summaries={}
        ... )

    """

    model_config = ConfigDict(strict=True, frozen=True, validate_assignment=True)

    total_orders: int = Field(description="Total number of orders", ge=0)
    recent_orders: list[OrderDetails] = Field(
        default_factory=list, description="List of recent orders"
    )
    performance_metrics: dict[str, Decimal] = Field(
        default_factory=dict,
        description="Performance metrics summary (use Decimal for monetary values)",
    )
    strategy_summaries: dict[str, StrategyPnLSummary] = Field(
        default_factory=dict, description="Per-strategy P&L summaries"
    )


# Performance Analysis Types
class BacktestResult(BaseModel):
    """Backtest execution results.

    Contains comprehensive backtest performance metrics and metadata.
    All financial metrics use Decimal for precision per Copilot Instructions.

    Examples:
        >>> result = BacktestResult(
        ...     strategy_name="MomentumStrategy",
        ...     start_date="2024-01-01",
        ...     end_date="2025-01-08",
        ...     total_return=Decimal("15.5"),
        ...     sharpe_ratio=Decimal("1.8"),
        ...     max_drawdown=Decimal("-10.2"),
        ...     total_trades=100,
        ...     win_rate=Decimal("65.5")
        ... )

    """

    model_config = ConfigDict(strict=True, frozen=True, validate_assignment=True)

    strategy_name: str = Field(description="Strategy identifier")
    start_date: str = Field(description="Backtest start date (ISO 8601 format: YYYY-MM-DD)")
    end_date: str = Field(description="Backtest end date (ISO 8601 format: YYYY-MM-DD)")
    total_return: Decimal = Field(description="Total return percentage (Decimal)")
    sharpe_ratio: Decimal = Field(description="Risk-adjusted return (Sharpe ratio)")
    max_drawdown: Decimal = Field(description="Maximum drawdown percentage (typically negative)")
    total_trades: int = Field(description="Total number of trades executed", ge=0)
    win_rate: Decimal = Field(
        description="Win rate percentage [0-100]", ge=Decimal("0.0"), le=Decimal("100.0")
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional backtest metadata"
    )


class PerformanceMetrics(BaseModel):
    """Performance analysis metrics.

    Contains comprehensive risk and return metrics for strategy evaluation.
    All financial metrics use Decimal for precision per Copilot Instructions.

    Examples:
        >>> metrics = PerformanceMetrics(
        ...     returns=[Decimal("0.01"), Decimal("0.02"), Decimal("-0.01")],
        ...     cumulative_return=Decimal("15.5"),
        ...     volatility=Decimal("10.2"),
        ...     sharpe_ratio=Decimal("1.8"),
        ...     max_drawdown=Decimal("-10.2"),
        ...     calmar_ratio=Decimal("1.52"),
        ...     sortino_ratio=Decimal("2.1")
        ... )

    """

    model_config = ConfigDict(strict=True, frozen=True, validate_assignment=True)

    returns: list[Decimal] = Field(
        default_factory=list, description="Time series of returns (Decimal)"
    )
    cumulative_return: Decimal = Field(description="Cumulative return percentage (Decimal)")
    volatility: Decimal = Field(
        description="Return volatility (annualized, Decimal)", ge=Decimal("0.0")
    )
    sharpe_ratio: Decimal = Field(description="Risk-adjusted return (Sharpe ratio)")
    max_drawdown: Decimal = Field(description="Maximum drawdown percentage (typically negative)")
    calmar_ratio: Decimal = Field(description="Return to max drawdown ratio")
    sortino_ratio: Decimal = Field(description="Downside risk-adjusted return")


# Monthly Summary Report Types
class MonthlySummaryDTO(BaseModel):
    """DTO for monthly portfolio and strategy performance summary.

    All monetary values use Decimal for precision per Copilot Instructions.

    Examples:
        >>> summary = MonthlySummaryDTO(
        ...     month_label="Jan 2025",
        ...     portfolio_first_value=Decimal("100000.00"),
        ...     portfolio_last_value=Decimal("105000.00"),
        ...     portfolio_pnl_abs=Decimal("5000.00"),
        ...     portfolio_pnl_pct=Decimal("5.0"),
        ...     strategy_rows=[{"name": "Strategy1", "pnl": "1000.00"}],
        ...     notes=["Note 1"]
        ... )

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )

    # Month identification
    month_label: str = Field(..., description="Human-readable month label (e.g., 'Aug 2025')")

    # Portfolio P&L for the month
    portfolio_first_value: Decimal | None = Field(
        default=None, description="Portfolio value at start of month (USD)"
    )
    portfolio_last_value: Decimal | None = Field(
        default=None, description="Portfolio value at end of month (USD)"
    )
    portfolio_pnl_abs: Decimal | None = Field(
        default=None, description="Absolute P&L change for the month (USD)"
    )
    portfolio_pnl_pct: Decimal | None = Field(
        default=None, description="Percentage P&L change for the month (Decimal)"
    )

    # Per-strategy realized P&L for the month
    strategy_rows: list[dict[str, Any]] = Field(
        default_factory=list,
        description="Strategy performance rows (consider typed model in future)",
    )

    # Additional context and warnings
    notes: list[str] = Field(default_factory=list, description="Additional notes or warnings")


# Public API
__all__ = [
    "BacktestResult",
    "DashboardMetrics",
    "EmailCredentials",
    "EmailReportData",
    "EmailSummary",
    "MonthlySummaryDTO",
    "PerformanceMetrics",
    "ReportingData",
]
