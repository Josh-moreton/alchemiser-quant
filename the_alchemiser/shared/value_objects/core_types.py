"""Business Unit: utilities; Status: current.

Core type definitions for The Alchemiser trading system.

This module contains domain-appropriate TypedDict definitions that represent
core business entities and concepts. Interface/UI types have been moved to
interfaces/schemas modules as part of the Pydantic migration.
"""

from __future__ import annotations

from typing import Any, Literal, Protocol, TypedDict

from the_alchemiser.shared.types.order_status import OrderStatusLiteral


# Account Information Types
class AccountInfo(TypedDict):
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
    """Portfolio history data for P&L tracking."""

    profit_loss: list[float]
    profit_loss_pct: list[float]
    equity: list[float]
    timestamp: list[str]


class ClosedPositionData(TypedDict, total=False):
    """Closed position P&L data."""

    symbol: str
    realized_pnl: float
    realized_pnl_pct: float
    trade_count: int


class EnrichedAccountInfo(AccountInfo, total=False):
    """Extended account info with portfolio history and performance data."""

    portfolio_history: PortfolioHistoryData
    recent_closed_pnl: list[ClosedPositionData]
    trading_mode: str
    market_hours_ignored: bool


# Position Types
class PositionInfo(TypedDict):
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
    symbol: str | dict[str, float]  # Allow both symbol string and portfolio dict
    action: Literal["BUY", "SELL", "HOLD"] | str  # Allow both strict and loose action values
    confidence: float


class StrategySignal(StrategySignalBase, total=False):
    reasoning: str
    allocation_percentage: float
    # Legacy field aliases for backward compatibility
    reason: str  # Alias for reasoning


class StrategyPnLSummary(TypedDict):
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
