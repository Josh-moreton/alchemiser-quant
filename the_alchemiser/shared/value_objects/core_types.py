"""Business Unit: shared | Status: current.

Core type definitions for The Alchemiser trading system.

This module contains domain-appropriate TypedDict definitions that represent
core business entities and concepts. All monetary values use Decimal for
precision in financial calculations per the Alchemiser guardrails.

⚠️ IMPORTANT:
These TypedDict definitions enforce `Decimal` for all monetary values to prevent
float precision issues in financial calculations. When receiving data from external
APIs that return `str` or `float`, convert to `Decimal` immediately at the adapter
boundary before creating these TypedDict instances.

Example conversion:
    from decimal import Decimal

    # From API response
    api_data = {"equity": "10000.50", "cash": 5000.0}

    # Convert to proper types
    account_info: AccountInfo = {
        "account_id": "123",
        "equity": Decimal(str(api_data["equity"])),
        "cash": Decimal(str(api_data["cash"])),
        ...
    }
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Literal, TypedDict

# Type aliases for commonly repeated patterns
MonetaryValue = Decimal  # All monetary values use Decimal for precision
QuantityValue = Decimal  # All quantity values use Decimal for precision
ISO8601Timestamp = str  # ISO 8601 format in UTC (e.g., "2025-01-15T10:30:00Z")
ISO8601Date = str  # ISO 8601 date format (e.g., "2025-01-15")

# Order Status Literals - moved here to break circular dependency
OrderStatusLiteral = Literal[
    "new",
    "partially_filled",
    "filled",
    "canceled",
    "expired",
    "rejected",
]

# Side literals for positions and orders
SideLiteral = Literal["long", "short"]
OrderSideLiteral = Literal["buy", "sell"]


# Account Information Types
class AccountInfo(TypedDict):
    """Trading account information and balances.

    All monetary values are Decimal types for precision in financial calculations.
    Convert from API string/float responses to Decimal at the adapter boundary.

    Fields:
        account_id: Unique account identifier
        equity: Total account equity (cash + market value of positions) in USD
        cash: Available cash balance in USD
        buying_power: Available buying power in USD (considers margin/leverage)
        day_trades_remaining: Number of day trades remaining (PDT rule)
        portfolio_value: Total portfolio value in USD (same as equity)
        last_equity: Previous day's closing equity in USD
        daytrading_buying_power: Buying power for day trading in USD
        regt_buying_power: Regulation T buying power in USD
        status: Account status (ACTIVE or INACTIVE)
    """

    account_id: str
    equity: MonetaryValue
    cash: MonetaryValue
    buying_power: MonetaryValue
    day_trades_remaining: int
    portfolio_value: MonetaryValue
    last_equity: MonetaryValue
    daytrading_buying_power: MonetaryValue
    regt_buying_power: MonetaryValue
    status: Literal["ACTIVE", "INACTIVE"]


# Enriched Account Types for Display/Reporting
class PortfolioHistoryData(TypedDict, total=False):
    """Portfolio history data for P&L tracking.

    All fields are optional (total=False). Typically populated from broker API
    with historical portfolio performance data. Monetary values use Decimal.

    Fields:
        profit_loss: List of profit/loss values in USD (Decimal for precision)
        profit_loss_pct: List of profit/loss percentages as Decimal (0.01 = 1%)
        equity: List of equity values in USD (Decimal for precision)
        timestamp: List of ISO 8601 UTC timestamps for each data point
    """

    profit_loss: list[Decimal]
    profit_loss_pct: list[Decimal]
    equity: list[Decimal]
    timestamp: list[ISO8601Timestamp]


class ClosedPositionData(TypedDict, total=False):
    """Closed position P&L data.

    All fields are optional (total=False). Represents a closed trading position
    with realized profit/loss information. Monetary values use Decimal.

    Fields:
        symbol: Trading symbol
        realized_pnl: Realized profit/loss in USD (Decimal for precision)
        realized_pnl_pct: Realized profit/loss percentage as Decimal (0.01 = 1%)
        trade_count: Number of trades executed for this position
    """

    symbol: str
    realized_pnl: Decimal
    realized_pnl_pct: Decimal
    trade_count: int


class EnrichedAccountInfo(AccountInfo, total=False):
    """Extended account info with portfolio history and performance data.

    Inherits all required fields from AccountInfo. Additional fields are optional
    (total=False) and typically populated for reporting/dashboard display.

    Additional Fields:
        portfolio_history: Historical portfolio performance data
        recent_closed_pnl: List of recently closed positions with P&L
        trading_mode: Current trading mode (e.g., "PAPER", "LIVE")
        market_hours_ignored: Whether trading outside market hours is enabled
    """

    portfolio_history: PortfolioHistoryData
    recent_closed_pnl: list[ClosedPositionData]
    trading_mode: str
    market_hours_ignored: bool


# Position Information Types
class PositionInfo(TypedDict):
    """Current position details from broker API.

    Represents an open position in the trading account. All monetary and quantity
    values use Decimal for precision. Convert from API responses at the adapter boundary.

    Fields:
        symbol: Trading symbol (e.g., "AAPL", "BTC/USD")
        qty: Position quantity (shares or units) as Decimal
        market_value: Current market value in USD as Decimal
        avg_entry_price: Average entry price per unit in USD as Decimal
        unrealized_pl: Unrealized profit/loss in USD as Decimal
        unrealized_plpc: Unrealized profit/loss percentage as Decimal (0.01 = 1%)
        side: Position direction (long or short)
        asset_id: Unique asset identifier from broker
        asset_class: Asset classification (crypto or us_equity)
        exchange: Exchange where asset is traded
        qty_available: Quantity available for trading (not locked in orders) as Decimal
    """

    symbol: str
    qty: QuantityValue
    market_value: MonetaryValue
    avg_entry_price: MonetaryValue
    unrealized_pl: MonetaryValue
    unrealized_plpc: MonetaryValue  # Percentage as decimal (0.01 = 1%)
    side: SideLiteral
    asset_id: str
    asset_class: Literal["crypto", "us_equity"]
    exchange: str
    qty_available: QuantityValue


# Position Collections
PositionsDict = dict[str, PositionInfo]  # Symbol -> Position mapping


# Order Types
class OrderDetails(TypedDict):
    """Complete order information with execution status.

    Represents an order with its current state and fill information from the broker.
    All quantity and price values use Decimal for precision.

    Fields:
        id: Unique order identifier from broker
        symbol: Trading symbol
        qty: Order quantity as Decimal
        side: Order side (buy or sell)
        order_type: Order type (market, limit, stop, stop_limit)
        time_in_force: Time in force constraint (day, gtc, ioc, fok)
        status: Current order status
        filled_qty: Quantity filled so far as Decimal
        filled_avg_price: Average fill price as Decimal (None if not filled)
        created_at: Order creation timestamp (ISO 8601 UTC)
        updated_at: Last update timestamp (ISO 8601 UTC)
    """

    id: str
    symbol: str
    qty: QuantityValue
    side: OrderSideLiteral
    order_type: Literal["market", "limit", "stop", "stop_limit"]
    time_in_force: Literal["day", "gtc", "ioc", "fok"]
    status: OrderStatusLiteral
    filled_qty: QuantityValue
    filled_avg_price: MonetaryValue | None
    created_at: ISO8601Timestamp
    updated_at: ISO8601Timestamp


# Strategy Types
class StrategySignalBase(TypedDict):
    """Base strategy signal type with core fields.

    Note: The symbol field allows both single symbols and portfolio allocations
    for compatibility with different strategy types. For portfolio strategies,
    symbol is a dict mapping symbols to allocation weights (using Decimal).

    Fields:
        symbol: Single symbol string OR dict of {symbol: weight as Decimal} for portfolios
        action: Trading action (BUY, SELL, or HOLD)
    """

    symbol: str | dict[str, Decimal]  # Single symbol or portfolio allocation
    action: Literal["BUY", "SELL", "HOLD"]


class StrategySignal(StrategySignalBase, total=False):
    """Extended strategy signal with optional fields.

    Additional optional fields provide context for the trading decision.

    Optional Fields:
        reasoning: Explanation of the signal decision
        allocation_percentage: Portfolio allocation percentage as Decimal (0.5 = 50%)
        reason: Deprecated alias for reasoning (use reasoning instead)
    """

    reasoning: str
    allocation_percentage: Decimal  # 0.0 to 1.0 (0.5 = 50%)
    reason: str  # Deprecated: use reasoning instead


class StrategyPnLSummary(TypedDict):
    """Strategy performance summary and statistics.

    Aggregated performance metrics for a trading strategy. All monetary values
    and percentages use Decimal for precision.

    Fields:
        strategy_name: Name/identifier of the strategy
        total_pnl: Total profit/loss in USD as Decimal
        realized_pnl: Realized profit/loss in USD as Decimal (closed positions)
        unrealized_pnl: Unrealized profit/loss in USD as Decimal (open positions)
        total_trades: Total number of trades executed
        win_rate: Win rate as Decimal (0.6 = 60%)
        positions_count: Current number of open positions
    """

    strategy_name: str
    total_pnl: Decimal
    realized_pnl: Decimal
    unrealized_pnl: Decimal
    total_trades: int
    win_rate: Decimal  # 0.0 to 1.0
    positions_count: int


# Phase 6: Strategy Layer Types
class StrategyPositionData(TypedDict):
    """Position data specific to strategy analysis.

    Simplified position representation for strategy-level analysis.
    All quantity and price values use Decimal for precision.

    Fields:
        symbol: Trading symbol
        quantity: Position quantity as Decimal
        entry_price: Average entry price in USD as Decimal
        current_price: Current market price in USD as Decimal
        strategy_type: Strategy identifier/name
    """

    symbol: str
    quantity: Decimal
    entry_price: Decimal
    current_price: Decimal
    strategy_type: str


class KLMVariantResult(TypedDict):
    """KLM variant analysis result.

    Result from KLM (Kelly-Leverage-Momentum) variant strategy analysis.

    Fields:
        variant: KLM variant instance (Any to avoid circular import)
        signal: Generated trading signal from the variant

    Note: Uses Any for variant to avoid circular dependency with strategy modules.
    The variant should implement BaseKLMVariant protocol.
    """

    variant: Any  # BaseKLMVariant - using Any to avoid circular import
    signal: StrategySignal


# ============================================================================
# Backward Compatibility Notes
# ============================================================================
#
# The following type definitions have been moved to Pydantic models in:
# - interfaces/schemas/execution.py (Trading/Execution types)
# - interfaces/schemas/reporting.py (Reporting/Dashboard types)
# - interfaces/schemas/cli.py (CLI types)
# - interfaces/schemas/errors.py (Error Handler types)
# - shared/protocols/alpaca.py (Alpaca Integration Protocols)
#
# These TypedDict definitions now use Decimal for all monetary values to enforce
# precision at the type level. When integrating with external APIs:
# 1. Convert API responses (str/float) to Decimal at the adapter boundary
# 2. Use these TypedDict definitions for type safety in internal communication
# 3. For new code, consider using Pydantic models from shared/types/ or shared/schemas/
#    which provide additional benefits:
#    - Frozen/immutable models
#    - Field validators for business rules
#    - Better IDE support and type safety
# ============================================================================


# Phase 9: KLM Variants Types
class KLMDecision(TypedDict):
    """KLM decision result with symbol allocation and reasoning.

    Decision output from KLM (Kelly-Leverage-Momentum) strategy variants.

    Fields:
        symbol: Single symbol string OR dict of {symbol: allocation as Decimal} for portfolios
        action: Trading action (BUY, SELL, or HOLD)
        reasoning: Explanation of the decision logic
    """

    symbol: str | dict[str, Decimal]  # Single symbol or allocation dict
    action: Literal["BUY", "SELL", "HOLD"]
    reasoning: str


# Phase 11: Data Layer Types
class MarketDataPoint(TypedDict):
    """Market data point with OHLCV information.

    Standard OHLCV (Open, High, Low, Close, Volume) candlestick data.
    All price values use Decimal for precision.

    Fields:
        timestamp: Data point timestamp (ISO 8601 UTC)
        open: Opening price in USD as Decimal
        high: Highest price in USD as Decimal
        low: Lowest price in USD as Decimal
        close: Closing price in USD as Decimal
        volume: Trading volume (number of shares/units)
        symbol: Trading symbol
    """

    timestamp: ISO8601Timestamp
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: int
    symbol: str


class IndicatorData(TypedDict):
    """Technical indicator calculation result.

    Result of a technical analysis indicator calculation (e.g., RSI, MACD).
    Indicator values use Decimal for precision.

    Fields:
        symbol: Trading symbol
        indicator_name: Name of the indicator (e.g., "RSI", "MACD")
        value: Calculated indicator value as Decimal
        timestamp: Calculation timestamp (ISO 8601 UTC)
        parameters: Indicator parameters used (e.g., {"period": 14})

    Note: Uses dict[str, Any] for parameters to support various indicator configs.
    Common parameters include period, fast_period, slow_period, etc.
    """

    symbol: str
    indicator_name: str
    value: Decimal
    timestamp: ISO8601Timestamp
    parameters: dict[str, Any]


class PriceData(TypedDict):
    """Real-time price data with bid/ask information.

    Current market price with optional bid/ask spread and volume.
    All price values use Decimal for precision.

    Fields:
        symbol: Trading symbol
        price: Current price in USD as Decimal
        timestamp: Price timestamp (ISO 8601 UTC)
        bid: Bid price in USD as Decimal (None if not available)
        ask: Ask price in USD as Decimal (None if not available)
        volume: Current volume (None if not available)
    """

    symbol: str
    price: Decimal
    timestamp: ISO8601Timestamp
    bid: Decimal | None
    ask: Decimal | None
    volume: int | None


class QuoteData(TypedDict):
    """Market quote with bid/ask spreads and sizes.

    Level 1 market data quote with bid/ask prices and sizes.
    All price and size values use Decimal for precision.

    Fields:
        bid_price: Best bid price in USD as Decimal
        ask_price: Best ask price in USD as Decimal
        bid_size: Bid size (shares/units at bid price) as Decimal
        ask_size: Ask size (shares/units at ask price) as Decimal
        timestamp: Quote timestamp (ISO 8601 UTC)
    """

    bid_price: Decimal
    ask_price: Decimal
    bid_size: Decimal
    ask_size: Decimal
    timestamp: ISO8601Timestamp


class DataProviderResult(TypedDict):
    """Generic result wrapper for data provider responses.

    Standardized response format for data provider operations.

    Fields:
        success: Whether the operation succeeded
        data: Response data (None if error)
        error_message: Error message (None if success)
        timestamp: Response timestamp (ISO 8601 UTC)

    Note: Uses dict[str, Any] for data to support various provider response types.
    """

    success: bool
    data: dict[str, Any] | None
    error_message: str | None
    timestamp: ISO8601Timestamp


class TradeAnalysis(TypedDict):
    """Individual trade performance analysis.

    Analysis of a completed trade with entry/exit details and P&L.
    All monetary values and quantities use Decimal for precision.

    Fields:
        symbol: Trading symbol
        entry_date: Entry date (ISO 8601 date: YYYY-MM-DD)
        exit_date: Exit date (ISO 8601 date: YYYY-MM-DD)
        entry_price: Average entry price in USD as Decimal
        exit_price: Average exit price in USD as Decimal
        quantity: Trade quantity (shares/units) as Decimal
        pnl: Profit/loss in USD as Decimal (exit_value - entry_value)
        return_pct: Return percentage as Decimal (0.01 = 1%)
        strategy: Strategy name/identifier that generated the trade
    """

    symbol: str
    entry_date: ISO8601Date
    exit_date: ISO8601Date
    entry_price: Decimal
    exit_price: Decimal
    quantity: Decimal
    pnl: Decimal
    return_pct: Decimal  # Decimal format: 0.01 = 1%
    strategy: str


class PortfolioSnapshot(TypedDict):
    """Point-in-time portfolio state and valuation.

    Snapshot of the portfolio at a specific moment, including all positions
    and P&L information. All monetary values use Decimal for precision.

    Fields:
        timestamp: Snapshot timestamp (ISO 8601 UTC)
        total_value: Total portfolio value in USD as Decimal
        positions: Dict of all positions keyed by symbol
        cash_balance: Available cash in USD as Decimal
        unrealized_pnl: Total unrealized P&L in USD as Decimal
        realized_pnl: Total realized P&L in USD as Decimal

    Note: positions dict contains mutable PositionInfo dicts; consumers should
    make a shallow copy if modifications are needed to avoid shared state issues.
    """

    timestamp: ISO8601Timestamp
    total_value: Decimal
    positions: dict[str, PositionInfo]
    cash_balance: Decimal
    unrealized_pnl: Decimal
    realized_pnl: Decimal


# Error Reporting Types
class ErrorContext(TypedDict):
    """Error context information for debugging and monitoring.

    Structured error context for logging and observability.

    Fields:
        timestamp: Error timestamp (ISO 8601 UTC)
        component: Component/module where error occurred
        operation: Operation being performed when error occurred
        additional_data: Additional context data (error-specific)

    Note: additional_data uses dict[str, Any] to support flexible error contexts.
    Common keys include: error_type, stack_trace, correlation_id, request_id.
    """

    timestamp: ISO8601Timestamp
    component: str
    operation: str
    additional_data: dict[str, Any]
