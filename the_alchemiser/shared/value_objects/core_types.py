"""Business Unit: shared | Status: current..

Core type definitions for The Alchemiser trading system.

This module contains domain-appropriate TypedDict definitions that represent
core business entities and concepts. These types provide structured data
contracts for account information, orders, positions, and market data.
Interface/UI types have been moved to interfaces/schemas modules as part
of the Pydantic migration.
"""

from __future__ import annotations

from typing import Any, Literal, Protocol, TypedDict

from the_alchemiser.shared.types.order_status import OrderStatusLiteral


# Account Information Types
class AccountInfo(TypedDict):
    """Account information and financial metrics.
    
    Contains comprehensive account details including equity, cash, buying power,
    and regulatory status information used for portfolio management and
    risk assessment.
    
    Attributes:
        account_id: Unique identifier for the trading account.
        equity: Total account equity value.
        cash: Available cash balance.
        buying_power: Total buying power available for trades.
        day_trades_remaining: Number of day trades remaining in current period.
        portfolio_value: Total value of all holdings.
        last_equity: Previous day's equity value.
        daytrading_buying_power: Buying power specifically for day trading.
        regt_buying_power: Regulation T buying power.
        status: Account status ("ACTIVE" or "INACTIVE").
    """
    account_id: str
    equity: str | float
    cash: str | float
    buying_power: str | float
    day_trades_remaining: int
    portfolio_value: str | float
    last_equity: str | float
    daytrading_buying_power: str | float
    regt_buying_power: str | float
    status: Literal["ACTIVE", "INACTIVE"]


# Enriched Account Types for Display/Reporting
class PortfolioHistoryData(TypedDict, total=False):
    """Portfolio history data for performance tracking and analysis.
    
    Contains historical portfolio metrics used for profit/loss tracking,
    performance analysis, and reporting. All fields are optional to support
    partial data scenarios.
    
    Attributes:
        profit_loss: Historical profit/loss values in absolute terms.
        profit_loss_pct: Historical profit/loss as percentage changes.
        equity: Historical equity values over time.
        timestamp: Corresponding timestamps for each data point.
    """

    profit_loss: list[float]
    profit_loss_pct: list[float]
    equity: list[float]
    timestamp: list[str]


class ClosedPositionData(TypedDict, total=False):
    """Closed position profit and loss data.
    
    Contains summary data for completed trades including realized P&L,
    performance metrics, and trade statistics. Used for performance
    analysis and reporting.
    
    Attributes:
        symbol: The ticker symbol of the closed position.
        realized_pnl: Realized profit/loss in absolute currency terms.
        realized_pnl_pct: Realized profit/loss as a percentage.
        trade_count: Number of individual trades that made up this position.
    """

    symbol: str
    realized_pnl: float
    realized_pnl_pct: float
    trade_count: int


class EnrichedAccountInfo(AccountInfo, total=False):
    """Extended account information with portfolio history and performance data.
    
    Extends the base AccountInfo with additional historical and performance
    data used for comprehensive portfolio analysis and reporting. All
    additional fields are optional to support gradual data enrichment.
    
    Attributes:
        portfolio_history: Historical portfolio performance data.
        recent_closed_pnl: List of recently closed position P&L data.
        trading_mode: Current trading mode (e.g., "paper", "live").
        market_hours_ignored: Whether market hours restrictions are ignored.
    """

    portfolio_history: PortfolioHistoryData
    recent_closed_pnl: list[ClosedPositionData]
    trading_mode: str
    market_hours_ignored: bool


# Position Types
class PositionInfo(TypedDict):
    """Current position information and metrics.
    
    Contains comprehensive data about an active position including
    quantity, valuation, and profit/loss calculations. Used for
    portfolio tracking and position management.
    
    Attributes:
        symbol: The ticker symbol of the position.
        qty: Current quantity held (positive for long, negative for short).
        side: Position side ("long" or "short").
        market_value: Current market value of the position.
        cost_basis: Original cost basis of the position.
        unrealized_pl: Unrealized profit/loss in absolute terms.
        unrealized_plpc: Unrealized profit/loss as a percentage.
        current_price: Current market price per share.
    """
    symbol: str
    qty: str | float
    side: Literal["long", "short"]
    market_value: str | float
    cost_basis: str | float
    unrealized_pl: str | float
    unrealized_plpc: str | float
    current_price: str | float


# Position Collections
PositionsDict = dict[str, PositionInfo]  # Symbol -> Position mapping


# Order Types
class OrderDetails(TypedDict):
    """Complete order information and status.
    
    Contains comprehensive order data including identification, execution
    details, timing, and current status. Used for order tracking and
    execution monitoring.
    
    Attributes:
        id: Unique order identifier.
        symbol: Ticker symbol for the order.
        qty: Order quantity.
        side: Order side ("buy" or "sell").
        order_type: Type of order (market, limit, stop, stop_limit).
        time_in_force: Order duration (day, gtc, ioc, fok).
        status: Current order status.
        filled_qty: Quantity that has been filled.
        filled_avg_price: Average price of filled portions (None if unfilled).
        created_at: Order creation timestamp.
        updated_at: Last update timestamp.
    """
    id: str
    symbol: str
    qty: str | float
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit", "stop", "stop_limit"]
    time_in_force: Literal["day", "gtc", "ioc", "fok"]
    status: OrderStatusLiteral
    filled_qty: str | float
    filled_avg_price: str | float | None
    created_at: str
    updated_at: str


# Strategy Types
class StrategySignalBase(TypedDict):
    """Base strategy signal information.
    
    Contains the essential components of a trading signal generated by
    a strategy engine. Supports both individual symbols and portfolio
    allocations.
    
    Attributes:
        symbol: Target symbol or portfolio allocation dictionary.
        action: Trading action (BUY, SELL, HOLD).
        confidence: Signal confidence level (0.0 to 1.0).
    """
    symbol: str | dict[str, float]  # Allow both symbol string and portfolio dict
    action: Literal["BUY", "SELL", "HOLD"] | str  # Allow both strict and loose action values
    confidence: float


class StrategySignal(StrategySignalBase, total=False):
    """Extended strategy signal with optional metadata.
    
    Extends the base signal with optional reasoning and allocation
    information. Includes legacy field aliases for backward compatibility.
    
    Attributes:
        reasoning: Human-readable explanation of the signal.
        allocation_percentage: Target allocation percentage for the signal.
        reason: Legacy alias for reasoning field.
    """
    reasoning: str
    allocation_percentage: float
    # Legacy field aliases for backward compatibility
    reason: str  # Alias for reasoning


class StrategyPnLSummary(TypedDict):
    """Strategy performance and profit/loss summary.
    
    Contains comprehensive performance metrics for a specific strategy
    including P&L calculations, trade statistics, and position counts.
    
    Attributes:
        strategy_name: Name of the strategy.
        total_pnl: Total profit/loss (realized + unrealized).
        realized_pnl: Realized profit/loss from closed positions.
        unrealized_pnl: Unrealized profit/loss from open positions.
        total_trades: Total number of trades executed.
        win_rate: Percentage of profitable trades.
        positions_count: Current number of open positions.
    """
    strategy_name: str
    total_pnl: float
    realized_pnl: float
    unrealized_pnl: float
    total_trades: int
    win_rate: float
    positions_count: int


# Phase 6: Strategy Layer Types
class StrategyPositionData(TypedDict):
    symbol: str
    quantity: float
    entry_price: float
    current_price: float
    strategy_type: str


class KLMVariantResult(TypedDict):
    variant: Any  # BaseKLMVariant - using Any to avoid circular import
    signal: StrategySignal
    confidence: float


# Trading Execution Types (moved to interfaces/schemas/execution.py)
# Import for backward compatibility


# Phase 5: Execution Layer Types (moved to interfaces/schemas/execution.py)
# Import for backward compatibility


# Phase 7: Utility Functions Types (moved to interfaces/schemas/execution.py)
# Import for backward compatibility


# Phase 9: KLM Variants Types
class KLMDecision(TypedDict):
    symbol: str
    action: Literal["BUY", "SELL", "HOLD"]
    reasoning: str


# Phase 10: Reporting/Dashboard Types (moved to interfaces/schemas/reporting.py)
# Import for backward compatibility


# Phase 11: Data Layer Types
class MarketDataPoint(TypedDict):
    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    symbol: str


class IndicatorData(TypedDict):
    symbol: str
    indicator_name: str
    value: float
    timestamp: str
    parameters: dict[str, Any]


class PriceData(TypedDict):
    symbol: str
    price: float
    timestamp: str
    bid: float | None
    ask: float | None
    volume: int | None


class QuoteData(TypedDict):
    bid_price: float
    ask_price: float
    bid_size: float
    ask_size: float
    timestamp: str


class DataProviderResult(TypedDict):
    success: bool
    data: dict[str, Any] | None
    error_message: str | None
    timestamp: str


# Phase 12: Backtest/Performance Types (moved to interfaces/schemas/reporting.py)
# Import for backward compatibility


class TradeAnalysis(TypedDict):
    symbol: str
    entry_date: str
    exit_date: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    return_pct: float
    strategy: str


class PortfolioSnapshot(TypedDict):
    timestamp: str
    total_value: float
    positions: dict[str, PositionInfo]
    cash_balance: float
    unrealized_pnl: float
    realized_pnl: float


# Error Reporting Types
class ErrorContext(TypedDict):
    timestamp: str
    component: str
    operation: str
    additional_data: dict[str, Any]


# Phase 13: CLI Types (moved to interfaces/schemas/cli.py)
# Import for backward compatibility


# Phase 14: Error Handler Types (moved to interfaces/schemas/errors.py)
# Import for backward compatibility


# Email Configuration Types (moved to interfaces/schemas/reporting.py)
# Import for backward compatibility


# Lambda Integration Types (moved to interfaces/schemas/execution.py)
# Import for backward compatibility


# Alpaca Integration Protocols
class AlpacaOrderProtocol(Protocol):
    """Protocol for Alpaca order objects."""

    id: str
    symbol: str
    qty: str
    side: str
    order_type: str
    time_in_force: str
    status: str
    filled_qty: str
    filled_avg_price: str | None
    created_at: str
    updated_at: str


class AlpacaOrderObject(Protocol):
    """Protocol for Alpaca order objects used in monitoring."""

    id: str
    status: str
    filled_qty: str


# Tracking and Monitoring Types (moved to interfaces/schemas/execution.py and reporting.py)
# Import for backward compatibility
