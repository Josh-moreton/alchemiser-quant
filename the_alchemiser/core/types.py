"""Core type definitions for The Alchemiser trading system."""

from typing import Any, Literal, Protocol, TypedDict


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


class PositionsDict(TypedDict):
    positions: dict[str, PositionInfo]


# Order Types
class OrderDetails(TypedDict):
    id: str
    symbol: str
    qty: str | float
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit", "stop", "stop_limit"]
    time_in_force: Literal["day", "gtc", "ioc", "fok"]
    status: Literal["new", "partially_filled", "filled", "canceled", "expired", "rejected"]
    filled_qty: str | float
    filled_avg_price: str | float | None
    created_at: str
    updated_at: str


# Strategy Types
class StrategySignal(TypedDict):
    symbol: str
    action: Literal["BUY", "SELL", "HOLD"]
    confidence: float
    reasoning: str
    allocation_percentage: float


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


# Trading Execution Types
class ExecutionResult(TypedDict):
    orders_executed: list[OrderDetails]
    account_info_before: AccountInfo
    account_info_after: AccountInfo
    execution_summary: dict[str, Any]  # Will be refined in Phase 2
    final_portfolio_state: dict[str, Any] | None


# Phase 5: Execution Layer Types
class TradingPlan(TypedDict):
    symbol: str
    action: Literal["BUY", "SELL"]
    quantity: float
    estimated_price: float
    reasoning: str


class QuoteData(TypedDict):
    bid_price: float
    ask_price: float
    bid_size: float
    ask_size: float
    timestamp: str


# Error Reporting Types
class ErrorContext(TypedDict):
    timestamp: str
    component: str
    operation: str
    additional_data: dict[str, Any]


# Email Configuration Types
class EmailCredentials(TypedDict):
    smtp_server: str
    smtp_port: int
    email_address: str
    email_password: str
    recipient_email: str


# Lambda Integration Types
class LambdaEvent(TypedDict, total=False):
    mode: str | None
    trading_mode: str | None
    ignore_market_hours: bool | None
    arguments: list[str] | None


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


# Tracking and Monitoring Types
class OrderHistoryData(TypedDict):
    orders: list[OrderDetails]
    metadata: dict[str, Any]


class EmailSummary(TypedDict):
    total_orders: int
    recent_orders: list[OrderDetails]
    performance_metrics: dict[str, float]
    strategy_summaries: dict[str, StrategyPnLSummary]
