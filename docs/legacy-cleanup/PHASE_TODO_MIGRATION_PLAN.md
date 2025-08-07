# Phase TODO Migration Plan

## Overview

This document provides detailed migration instructions for all TODO Phase items (Phases 5-15) identified throughout the codebase. These represent incomplete type migrations that need to be completed to achieve full type safety and remove legacy patterns.

## Phase Categories Summary

| Phase | Focus Area | Items | Priority | Complexity |
|-------|------------|-------|----------|------------|
| 5 | Smart Execution & Orders | 4 | Critical | Medium |
| 6 | Strategy Management | 8 | Critical | High |
| 7 | WebSocket & Limits | 4 | High | Medium |
| 8-10 | UI & Email Templates | 15 | Medium | Low |
| 11 | Data Provider & Indicators | 6 | High | Medium |
| 12 | Performance & Math | 4 | Medium | Low |
| 13 | CLI Formatting | 12 | Low | Low |
| 14 | Error Handling | 2 | Medium | Medium |
| 15 | Tracking & Integration | 6 | High | High |

## Phase 5: Smart Execution & Order Validation

### Overview
Focus on completing type migrations for order processing and smart execution systems.

### Items to Address

#### 1. Smart Execution Engine
**Files**: `execution/smart_execution.py`
**TODO Items**:
- Line 30: `# TODO: Phase 5 - Added for gradual migration`
- Line 91: `) -> tuple[Any, ...]:  # TODO: Phase 5 - Migrate to QuoteData`
- Line 409: `)  # TODO: Phase 5 - Migrate to AlpacaOrderObject`

**Migration Strategy**:
```python
# Current
def get_quote(self, symbol: str) -> tuple[Any, ...]:  # TODO: Phase 5 - Migrate to QuoteData

# Target
def get_quote(self, symbol: str) -> QuoteData:
    """Get quote data with proper typing."""
```

**Implementation Steps**:
1. Define `QuoteData` type in `core/types.py`
2. Define `AlpacaOrderObject` type in `core/types.py`
3. Update method signatures to use proper types
4. Update all calling code to handle typed returns
5. Remove TODO comments

#### 2. Portfolio Rebalancer
**Files**: `execution/portfolio_rebalancer.py`
**TODO Items**:
- Line 194: `)  # TODO: Phase 5 - Will refactor to TradingPlan structure later`
- Line 415: `buy_plans: list[dict[str, Any]] = []  # TODO: Phase 5 - Migrate to list[TradingPlan]`

**Migration Strategy**:
```python
# Current
buy_plans: list[dict[str, Any]] = []  # TODO: Phase 5 - Migrate to list[TradingPlan]

# Target
buy_plans: list[TradingPlan] = []
```

**Implementation Steps**:
1. Define `TradingPlan` type in `core/types.py`
2. Update portfolio rebalancer to use typed plans
3. Update all consumers of trading plans
4. Remove TODO comments

### Types to Create for Phase 5

```python
# Add to core/types.py

@dataclass
class QuoteData:
    """Quote data structure for market prices."""
    symbol: str
    bid: float
    ask: float
    bid_size: int
    ask_size: int
    timestamp: datetime
    
@dataclass
class AlpacaOrderObject:
    """Typed structure for Alpaca order objects."""
    id: str
    symbol: str
    qty: float
    side: OrderSide
    order_type: OrderType
    status: OrderStatus
    filled_qty: float
    filled_avg_price: float | None
    created_at: datetime
    
@dataclass
class TradingPlan:
    """Trading plan structure for portfolio rebalancing."""
    symbol: str
    action: ActionType
    quantity: float
    target_allocation: float
    current_allocation: float
    reason: str
```

## Phase 6: Strategy Management & KLM Ensemble

### Overview
Complete type migrations for strategy management and KLM trading systems.

### Items to Address

#### 1. Strategy Manager
**Files**: `core/trading/strategy_manager.py`
**TODO Items**:
- Line 50: `def to_dict(self) -> dict[str, Any]:  # TODO: Phase 6 - Migrate to StrategyPositionData`
- Line 62: `) -> "StrategyPosition":  # TODO: Phase 6 - Migrate parameter to StrategyPositionData`
- Line 431: `) -> dict[str, float]:  # TODO: Phase 6 - Migrate parameter to StrategySignal`
- Line 685: `) -> dict[str, Any]:  # TODO: Phase 6 - Migrate to StrategyPnLSummary`
- Line 690: `}  # TODO: Phase 6 - Migrate to list[StrategyPositionData]`
- Line 692: `summary: dict[str, Any] = {  # TODO: Phase 6 - Migrate to StrategyPnLSummary`

#### 2. KLM Ensemble Engine
**Files**: `core/trading/klm_ensemble_engine.py`
**TODO Items**:
- Line 182: `]:  # TODO: Phase 6 - Migrate to list[KLMVariantResult]`
- Line 239: `],  # TODO: Phase 6 - Migrate to list[KLMVariantResult]`
- Line 242: `]:  # TODO: Phase 6 - Migrate to tuple[StrategySignal, BaseKLMVariant]`
- Line 315: `],  # TODO: Phase 6 - Migrate to list[KLMVariantResult]`

### Migration Strategy

```python
# Current strategy manager patterns
def calculate_bear_portfolio(self) -> dict[str, float]:  # TODO: Phase 6 - Migrate parameter to StrategySignal

# Target
def calculate_bear_portfolio(self) -> StrategySignal:
    """Calculate bear market portfolio with proper typing."""
```

### Types to Create for Phase 6

```python
# Add to core/types.py

@dataclass
class StrategyPositionData:
    """Structured data for strategy positions."""
    strategy_type: StrategyType
    symbol: str
    allocation: float
    reason: str
    timestamp: datetime
    confidence: float

@dataclass
class StrategySignal:
    """Strategy signal with typed structure."""
    positions: dict[str, float]
    strategy_type: StrategyType
    confidence: float
    reasoning: str
    metadata: dict[str, Any]

@dataclass
class StrategyPnLSummary:
    """P&L summary for strategy performance."""
    total_pnl: float
    daily_pnl: float
    positions: list[StrategyPositionData]
    period_start: datetime
    period_end: datetime

@dataclass
class KLMVariantResult:
    """Result from KLM variant execution."""
    variant_name: str
    symbol: str
    action: ActionType
    reasoning: str
    confidence: float
    metadata: dict[str, Any]
```

## Phase 7: WebSocket & Limit Order Handling

### Overview
Complete type migrations for WebSocket monitoring and limit order systems.

### Items to Address

#### 1. WebSocket Order Monitor
**Files**: `utils/websocket_order_monitor.py`
**TODO Items**:
- Line 255: `)  # TODO: Phase 7 - Return type updated to WebSocketResult`
- Line 258: `return self._create_new_websocket(  # TODO: Phase 7 - Return type updated to WebSocketResult`
- Line 268: `) -> dict[str, str]:  # TODO: Phase 7 - Migrate to return WebSocketResult`
- Line 320: `) -> dict[str, str]:  # TODO: Phase 7 - Migrate to return WebSocketResult`

#### 2. Limit Order Handler
**Files**: `utils/limit_order_handler.py`
**TODO Items**:
- Line 114: `) -> tuple[Any, ...]:  # TODO: Phase 7 - Migrate to LimitOrderResult`

### Types to Create for Phase 7

```python
# Add to core/types.py

@dataclass
class WebSocketResult:
    """Result from WebSocket operations."""
    success: bool
    order_statuses: dict[str, OrderStatus]
    error_message: str | None
    completion_time: float
    metadata: dict[str, Any]

@dataclass
class LimitOrderResult:
    """Result from limit order placement."""
    order: AlpacaOrderObject | None
    success: bool
    error_message: str | None
    execution_time: float
    retry_count: int
```

## Phase 8-10: UI & Email Templates

### Overview
Complete type migrations for email templates, UI formatting, and user interface systems.

### Items to Address

#### 1. Email Template Systems
**Files**: 
- `core/ui/email_utils.py`
- `core/ui/email/templates/portfolio.py`
- `core/ui/email/templates/performance.py`

**TODO Items** (15 total):
- Email template type migrations
- Account info structure updates
- Portfolio data formatting
- Performance metrics typing

### Migration Strategy

```python
# Current email template patterns
def build_portfolio_allocation(result: Any) -> str:  # TODO: Phase 8 - Migrate to ExecutionResult

# Target
def build_portfolio_allocation(result: ExecutionResult) -> str:
    """Build portfolio allocation with proper typing."""
```

### Types to Create for Phase 8-10

```python
# Add to core/types.py

@dataclass
class ExecutionResult:
    """Execution result with structured data."""
    success: bool
    portfolio_changes: dict[str, float]
    orders_executed: list[AlpacaOrderObject]
    account_before: AccountInfo
    account_after: AccountInfo
    execution_summary: dict[str, Any]

@dataclass
class EmailReportData:
    """Structured data for email reports."""
    report_type: str
    data: dict[str, Any]
    timestamp: datetime
    recipient: str
```

## Phase 11: Data Provider & Indicators

### Overview
Complete type migrations for data providers and technical indicators.

### Items to Address

#### 1. Data Provider Systems
**Files**:
- `core/data/data_provider.py`
- `core/data/unified_data_provider_v2.py`
- `core/indicators/indicators.py`

**TODO Items** (6 total):
- Market data point structures
- Indicator result typing
- Cache structure typing

### Types to Create for Phase 11

```python
# Add to core/types.py

@dataclass
class MarketDataPoint:
    """Single market data point."""
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int

@dataclass
class IndicatorData:
    """Technical indicator result."""
    indicator_type: str
    value: float
    signal: str  # 'buy', 'sell', 'hold'
    confidence: float
    calculation_timestamp: datetime
```

## Phase 12: Performance & Trading Math

### Overview
Complete type migrations for performance calculation and trading mathematics.

### Items to Address

#### 1. Trading Math & Performance
**Files**:
- `utils/trading_math.py`
- `utils/portfolio_pnl_utils.py`

### Types to Create for Phase 12

```python
# Add to core/types.py

@dataclass
class PerformanceMetrics:
    """Performance calculation results."""
    total_return: float
    daily_return: float
    volatility: float
    sharpe_ratio: float
    max_drawdown: float
    calculation_period: timedelta

@dataclass
class TradeAnalysis:
    """Analysis of individual trades."""
    symbol: str
    entry_price: float
    exit_price: float
    quantity: float
    pnl: float
    duration: timedelta
    strategy_type: StrategyType
```

## Phase 13: CLI Formatting

### Overview
Complete type migrations for command-line interface formatting.

### Items to Address

#### 1. CLI Formatter
**Files**: `core/ui/cli_formatter.py`

**TODO Items** (12 total):
- CLI signal data structures
- Order display formatting
- Portfolio display data

### Types to Create for Phase 13

```python
# Add to core/types.py

@dataclass
class CLISignalData:
    """Structured data for CLI signal display."""
    signals: dict[str, Any]
    timestamp: datetime
    display_format: str

@dataclass
class CLIOrderDisplay:
    """Order display data for CLI."""
    symbol: str
    action: ActionType
    quantity: float
    price: float
    status: OrderStatus
    timestamp: datetime

@dataclass
class CLIPortfolioData:
    """Portfolio data for CLI display."""
    positions: dict[str, float]
    total_value: float
    daily_change: float
    last_updated: datetime
```

## Phase 14: Error Handling

### Overview
Complete type migrations for error handling systems.

### Items to Address

#### 1. Error Handler Enhancement
**Files**: `docs/plans/error-handling-enhancement-plan.md`

**TODO Items** (2 total):
- Error handler type imports
- Structured error data

### Types to Create for Phase 14

```python
# Add to core/types.py

@dataclass
class ErrorData:
    """Structured error information."""
    error_type: str
    message: str
    context: dict[str, Any]
    timestamp: datetime
    severity: str
    stack_trace: str | None
```

## Phase 15: Tracking & Integration

### Overview
Complete type migrations for order tracking and system integration.

### Items to Address

#### 1. Order Tracking Integration
**Files**: `tracking/integration.py`

**TODO Items** (6 total):
- Alpaca order protocol types
- Order details structure alignment
- Trading engine type definitions

### Types to Create for Phase 15

```python
# Add to core/types.py

@dataclass
class AlpacaOrderProtocol:
    """Protocol for Alpaca order objects."""
    id: str
    symbol: str
    qty: Decimal
    side: OrderSide
    order_type: OrderType
    status: OrderStatus
    # ... other Alpaca-specific fields

@dataclass
class OrderDetails:
    """Standardized order details structure."""
    order_id: str
    symbol: str
    quantity: float
    side: OrderSide
    order_type: OrderType
    price: float | None
    status: OrderStatus
    created_at: datetime
    filled_at: datetime | None
```

## Implementation Guidelines

### Step-by-Step Process

1. **Create Types First**
   - Add all necessary types to `core/types.py`
   - Ensure proper imports and dependencies
   - Add docstrings and validation

2. **Update Method Signatures**
   - Change return types from `Any` to proper types
   - Update parameter types
   - Maintain backward compatibility where possible

3. **Update Implementation**
   - Modify method bodies to return typed objects
   - Update all calling code
   - Ensure type checker passes

4. **Update Tests**
   - Modify tests to work with new types
   - Add type-specific test cases
   - Ensure full coverage

5. **Remove TODO Comments**
   - Only after all related code is updated
   - Verify no remaining references
   - Update documentation

### Testing Strategy

For each phase:
1. **Unit Tests**: Verify individual method type compliance
2. **Integration Tests**: Ensure typed objects work end-to-end
3. **Type Checking**: Run mypy/pyright to verify type safety
4. **Performance Tests**: Ensure no performance regression
5. **Backward Compatibility**: Verify external APIs still work

### Rollback Strategy

1. **Git Tagging**: Tag before each phase begins
2. **Feature Flags**: Use configuration to enable/disable new types
3. **Gradual Migration**: Keep old and new code paths temporarily
4. **Monitoring**: Enhanced monitoring during migration
5. **Quick Revert**: Scripts to quickly revert type changes

## Status Tracking

### Phase 5: Smart Execution & Orders
- [ ] Define QuoteData, AlpacaOrderObject, TradingPlan types
- [ ] Update smart_execution.py method signatures
- [ ] Update portfolio_rebalancer.py typing
- [ ] Update all calling code
- [ ] Update tests
- [ ] Remove TODO comments

### Phase 6: Strategy Management
- [ ] Define StrategyPositionData, StrategySignal, etc. types
- [ ] Update strategy_manager.py typing
- [ ] Update klm_ensemble_engine.py typing
- [ ] Update all strategy-related code
- [ ] Update tests
- [ ] Remove TODO comments

### Phase 7: WebSocket & Limits
- [ ] Define WebSocketResult, LimitOrderResult types
- [ ] Update websocket_order_monitor.py typing
- [ ] Update limit_order_handler.py typing
- [ ] Update all calling code
- [ ] Update tests
- [ ] Remove TODO comments

### Phase 8-10: UI & Email
- [ ] Define ExecutionResult, EmailReportData types
- [ ] Update email template typing
- [ ] Update UI system typing
- [ ] Update all template code
- [ ] Update tests
- [ ] Remove TODO comments

### Phase 11: Data & Indicators
- [ ] Define MarketDataPoint, IndicatorData types
- [ ] Update data provider typing
- [ ] Update indicator system typing
- [ ] Update all data processing code
- [ ] Update tests
- [ ] Remove TODO comments

### Phase 12: Performance & Math
- [ ] Define PerformanceMetrics, TradeAnalysis types
- [ ] Update trading math typing
- [ ] Update performance calculation typing
- [ ] Update all math utilities
- [ ] Update tests
- [ ] Remove TODO comments

### Phase 13: CLI Formatting
- [ ] Define CLISignalData, CLIOrderDisplay types
- [ ] Update cli_formatter.py typing
- [ ] Update all CLI display code
- [ ] Update tests
- [ ] Remove TODO comments

### Phase 14: Error Handling
- [ ] Define ErrorData types
- [ ] Update error handling typing
- [ ] Update error processing code
- [ ] Update tests
- [ ] Remove TODO comments

### Phase 15: Tracking & Integration
- [ ] Define AlpacaOrderProtocol, OrderDetails types
- [ ] Update tracking integration typing
- [ ] Update all tracking code
- [ ] Update tests
- [ ] Remove TODO comments

## Conclusion

Completing these TODO Phase items will establish comprehensive type safety throughout The Alchemiser system. This foundation is critical for the success of subsequent legacy cleanup phases.

The structured approach ensures that each phase builds on the previous ones, minimizing risk and maximizing the benefits of the type system migration.
