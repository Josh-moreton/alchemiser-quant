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
    status: Literal["new", "partially_filled", "filled", "canceled", "expired", "rejected"]
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


# Phase 7: Utility Functions Types
class LimitOrderResult(TypedDict):
    order_request: Any | None  # LimitOrderRequest - using Any to avoid import
    error_message: str | None


class WebSocketResult(TypedDict):
    status: Literal["completed", "timeout", "error"]
    message: str
    orders_completed: list[str]


# Phase 9: KLM Variants Types
class KLMDecision(TypedDict):
    symbol: str
    action: Literal["BUY", "SELL", "HOLD"]
    reasoning: str


# Phase 10: Reporting/Dashboard Types
class ReportingData(TypedDict):
    timestamp: str
    portfolio_summary: dict[str, Any]
    performance_metrics: dict[str, float]
    recent_trades: list[OrderDetails]


class DashboardMetrics(TypedDict):
    total_portfolio_value: float
    daily_pnl: float
    daily_pnl_percentage: float
    active_positions: int
    cash_balance: float


class EmailReportData(TypedDict):
    subject: str
    html_content: str
    recipient: str
    metadata: dict[str, Any]


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


class DataProviderResult(TypedDict):
    success: bool
    data: dict[str, Any] | None
    error_message: str | None
    timestamp: str


# Phase 12: Backtest/Performance Types
class BacktestResult(TypedDict):
    strategy_name: str
    start_date: str
    end_date: str
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    total_trades: int
    win_rate: float
    metadata: dict[str, Any]


class PerformanceMetrics(TypedDict):
    returns: list[float]
    cumulative_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    calmar_ratio: float
    sortino_ratio: float


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


# Phase 13: CLI Types
class CLIOptions(TypedDict):
    verbose: bool
    quiet: bool
    live: bool
    ignore_market_hours: bool
    force: bool
    no_header: bool


class CLICommandResult(TypedDict):
    success: bool
    message: str
    exit_code: int


class CLISignalData(TypedDict):
    strategy_type: str
    signals: dict[str, StrategySignal]
    indicators: dict[str, dict[str, float]]


class CLIAccountDisplay(TypedDict):
    account_info: AccountInfo
    positions: dict[str, PositionInfo]
    mode: Literal["live", "paper"]


class CLIPortfolioData(TypedDict):
    symbol: str
    allocation_percentage: float
    current_value: float
    target_value: float


class CLIOrderDisplay(TypedDict):
    order_details: OrderDetails
    display_style: str
    formatted_amount: str


# Phase 14: Error Handler Types
class ErrorDetailInfo(TypedDict):
    error_type: str
    error_message: str
    category: str
    context: str
    component: str
    timestamp: str
    traceback: str
    additional_data: dict[str, Any]
    suggested_action: str | None


class ErrorSummaryData(TypedDict):
    count: int
    errors: list[ErrorDetailInfo]


class ErrorReportSummary(TypedDict):
    critical: ErrorSummaryData | None
    trading: ErrorSummaryData | None
    data: ErrorSummaryData | None
    strategy: ErrorSummaryData | None
    configuration: ErrorSummaryData | None
    notification: ErrorSummaryData | None
    warning: ErrorSummaryData | None


class ErrorNotificationData(TypedDict):
    severity: str
    priority: str
    title: str
    error_report: str
    html_content: str


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
