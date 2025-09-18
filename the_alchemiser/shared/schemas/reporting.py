#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Reporting and dashboard DTOs for The Alchemiser Trading System.

This module contains DTOs for reporting, dashboard metrics, and email
notifications, moved from domain/types.py as part of the Pydantic migration.
"""

from __future__ import annotations

from typing import TypedDict

from the_alchemiser.shared.value_objects.core_types import OrderDetails, StrategyPnLSummary


# Dashboard and Metrics Types
class DashboardMetrics(TypedDict):
    """Dashboard metrics for real-time display."""

    total_portfolio_value: float
    daily_pnl: float
    daily_pnl_percentage: float
    active_positions: int
    cash_balance: float


class ReportingData(TypedDict):
    """General reporting data structure."""

    timestamp: str
    portfolio_summary: dict[str, str | int | bool | None]
    performance_metrics: dict[str, float]
    recent_trades: list[OrderDetails]


# Email and Notification Types
class EmailReportData(TypedDict):
    """Email report data structure."""

    subject: str
    html_content: str
    recipient: str
    metadata: dict[str, str | int | bool | None]


class EmailCredentials(TypedDict):
    """Email service credentials."""

    smtp_server: str
    smtp_port: int
    email_address: str
    email_password: str
    recipient_email: str


class EmailSummary(TypedDict):
    """Email summary for trading reports."""

    total_orders: int
    recent_orders: list[OrderDetails]
    performance_metrics: dict[str, float]
    strategy_summaries: dict[str, StrategyPnLSummary]


# Performance Analysis Types
class BacktestResult(TypedDict):
    """Backtest execution results."""

    strategy_name: str
    start_date: str
    end_date: str
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    total_trades: int
    win_rate: float
    metadata: dict[str, str | int | bool | None]


class PerformanceMetrics(TypedDict):
    """Performance analysis metrics."""

    returns: list[float]
    cumulative_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    calmar_ratio: float
    sortino_ratio: float
