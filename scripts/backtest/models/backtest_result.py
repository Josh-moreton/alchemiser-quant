"""Business Unit: scripts | Status: current.

Backtest result models.

Defines the output structure for backtesting runs.
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from scripts.backtest.models.portfolio_snapshot import PortfolioSnapshot, TradeRecord


class BacktestResult(BaseModel):
    """Complete result of a backtesting run.

    Contains portfolio evolution, trades, and performance metrics.
    """

    model_config = ConfigDict(frozen=False)

    # Backtest configuration
    strategy_name: str = Field(description="Name of strategy tested")
    start_date: datetime = Field(description="Backtest start date")
    end_date: datetime = Field(description="Backtest end date")
    initial_capital: Decimal = Field(description="Starting capital", gt=0)

    # Portfolio evolution
    portfolio_snapshots: list[PortfolioSnapshot] = Field(
        description="Portfolio state at each iteration", default_factory=list
    )

    # Trade history
    trades: list[TradeRecord] = Field(description="All trades executed", default_factory=list)

    # Performance metrics (calculated after backtest)
    final_value: Decimal | None = Field(description="Final portfolio value", default=None)
    total_return: Decimal | None = Field(description="Total return (%)", default=None)
    sharpe_ratio: Decimal | None = Field(description="Sharpe ratio", default=None)
    max_drawdown: Decimal | None = Field(description="Maximum drawdown (%)", default=None)
    win_rate: Decimal | None = Field(description="Win rate (%)", default=None)
    total_trades: int = Field(description="Total number of trades", default=0)


class BacktestConfig(BaseModel):
    """Configuration for a backtesting run."""

    model_config = ConfigDict(frozen=True, strict=True)

    strategy_files: list[str] = Field(description="List of strategy files to run", min_length=1)
    start_date: datetime = Field(description="Backtest start date")
    end_date: datetime = Field(description="Backtest end date")
    initial_capital: Decimal = Field(description="Starting capital", gt=0)
    commission_per_trade: Decimal = Field(
        description="Commission per trade", ge=0, default=Decimal("0")
    )
    symbols: list[str] | None = Field(
        description="Explicit symbol list (overrides strategy)", default=None
    )
