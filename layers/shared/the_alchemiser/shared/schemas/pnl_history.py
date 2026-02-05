"""Business Unit: shared | Status: current.

Schemas for P&L history data stored in DynamoDB.
"""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class PnLHistoryRecord(BaseModel):
    """Daily P&L history record with deposit/withdrawal adjustments.
    
    Stores intelligently calculated P&L that accounts for capital flows,
    providing accurate trading performance metrics.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    # Identifiers
    account_id: str = Field(description="Alpaca account number")
    date: str = Field(description="Date in YYYY-MM-DD format")
    
    # Equity and P&L
    equity: Decimal = Field(description="End-of-day equity")
    profit_loss: Decimal = Field(description="Daily P&L in dollars (adjusted for deposits/withdrawals)")
    profit_loss_pct: Decimal = Field(description="Daily P&L as percentage (0.0-1.0)")
    
    # Cash flows
    deposit: Decimal = Field(default=Decimal("0"), description="Deposits for the day")
    withdrawal: Decimal = Field(default=Decimal("0"), description="Withdrawals for the day")
    
    # Optional metadata
    base_value: Decimal | None = Field(default=None, description="Starting portfolio value for the day")
    cumulative_pnl: Decimal | None = Field(default=None, description="Cumulative P&L since inception")
    
    # Timestamp
    timestamp: str = Field(description="ISO 8601 timestamp when record was captured")


class PnLSummaryMetrics(BaseModel):
    """Summary statistics for P&L performance.
    
    Aggregated metrics for dashboard display.
    """

    model_config = ConfigDict(strict=True, frozen=True)

    # Period identification
    period_label: str = Field(description="Human-readable period (e.g., '1M', '3M', '1Y')")
    start_date: str = Field(description="Period start date (YYYY-MM-DD)")
    end_date: str = Field(description="Period end date (YYYY-MM-DD)")
    
    # Performance metrics
    total_pnl: Decimal = Field(description="Total profit/loss for period")
    total_return_pct: Decimal = Field(description="Total return as percentage")
    annualized_return_pct: Decimal | None = Field(default=None, description="Annualized return")
    
    # Risk metrics
    sharpe_ratio: Decimal | None = Field(default=None, description="Sharpe ratio")
    max_drawdown_pct: Decimal | None = Field(default=None, description="Maximum drawdown percentage")
    volatility_pct: Decimal | None = Field(default=None, description="Annualized volatility")
    
    # Trade statistics
    win_rate_pct: Decimal | None = Field(default=None, description="Percentage of winning days")
    avg_win: Decimal | None = Field(default=None, description="Average winning day P&L")
    avg_loss: Decimal | None = Field(default=None, description="Average losing day P&L")
    
    # Capital flows
    total_deposits: Decimal = Field(default=Decimal("0"), description="Total deposits in period")
    total_withdrawals: Decimal = Field(default=Decimal("0"), description="Total withdrawals in period")
    
    # Portfolio metrics
    starting_equity: Decimal = Field(description="Equity at period start")
    ending_equity: Decimal = Field(description="Equity at period end")
    
    # Data quality
    trading_days: int = Field(description="Number of trading days in period")
