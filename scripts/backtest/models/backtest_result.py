"""Business Unit: shared | Status: current.

Backtesting result models.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class TradeRecord(BaseModel):
    """Record of a single trade execution."""

    model_config = ConfigDict(strict=True, frozen=True)

    date: datetime = Field(description="Trade execution date")
    symbol: str = Field(description="Trading symbol")
    action: str = Field(description="BUY or SELL")
    quantity: Decimal = Field(description="Shares traded")
    price: Decimal = Field(description="Execution price (Open)")
    value: Decimal = Field(description="Total trade value")
    commission: Decimal = Field(description="Commission paid", default=Decimal("0"))


class PerformanceMetrics(BaseModel):
    """Performance metrics for a backtest run."""

    model_config = ConfigDict(strict=True, frozen=True)

    total_return: Decimal = Field(description="Total return percentage")
    sharpe_ratio: Decimal = Field(description="Risk-adjusted return")
    max_drawdown: Decimal = Field(description="Maximum drawdown percentage")
    win_rate: Decimal = Field(description="Percentage of winning trades")
    total_trades: int = Field(description="Total number of trades")
    avg_trade_return: Decimal = Field(description="Average return per trade")
    volatility: Decimal = Field(description="Return volatility (annualized)")


class BacktestResult(BaseModel):
    """Complete backtesting results."""

    model_config = ConfigDict(strict=True, frozen=True)

    start_date: datetime = Field(description="Backtest start date")
    end_date: datetime = Field(description="Backtest end date")
    initial_capital: Decimal = Field(description="Starting portfolio value")
    final_capital: Decimal = Field(description="Ending portfolio value")
    trades: list[TradeRecord] = Field(description="All executed trades")
    daily_values: list[tuple[datetime, Decimal]] = Field(
        description="Daily portfolio values"
    )
    metrics: PerformanceMetrics = Field(description="Performance metrics")
    strategy_name: str = Field(description="Strategy identifier")
