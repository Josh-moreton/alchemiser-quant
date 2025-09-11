# Execution Module Rebuild Plan

## Executive Summary

The current execution module is fundamentally flawed due to architectural violations. Instead of consuming the clean portfolio DTOs directly, it attempts to recalculate trades, fetch additional position data, and apply complex filtering logic. This plan outlines a complete rebuild focused on the core principle: **the execution module should simply iterate through RebalancePlanDTO items and place orders - nothing more.**

## Problem Statement

### Current Issues

1. **Architectural Violation**: Execution module recalculates trades instead of consuming portfolio DTOs
2. **Dependency Hell**: Execution depends on position data, market data, and portfolio recalculation
3. **Circular Logic**: Portfolio calculates trades → Execution ignores them → Execution recalculates trades
4. **Broker API Failures**: All orders return `None` IDs due to broken integration
5. **Complex Filtering**: Unnecessary filtering logic that should be in portfolio module
6. **Silent Failures**: Orders fail but system continues without proper error handling
7. **Massive Code Bloat**: 10,000+ lines of complex execution logic when 200 lines should suffice
8. **Legacy Architecture**: Current execution module built with outdated patterns and dependencies

### Root Cause

The execution module violates the fundamental principle of modular architecture by doing portfolio calculations instead of simple order execution.

### Deprecation Strategy

**COMPLETE DEPRECATION**: The entire current `execution/` module will be marked as legacy and replaced with a clean, minimal implementation. This includes:

- `execution/core/manager.py` - 2,000+ lines of complex recalculation logic
- `execution/strategies/` - Unnecessary execution strategies
- `execution/orders/` - Overly complex order management
- `execution/analytics/` - Portfolio analytics (belongs in portfolio module)
- `execution/pricing/` - Market data logic (use shared Alpaca capabilities)
- `execution/monitoring/` - Complex monitoring that adds no value
- All other execution subdirectories containing architectural violations

## Core Design Principle

> **The execution module's ONLY job is to iterate through `RebalancePlanDTO.items` and place orders with the broker. It should not calculate, validate, or filter trades - those are portfolio module responsibilities.**

## Architecture Vision

**CLEAN SLATE APPROACH**: Build a completely new, minimal execution module alongside the existing one, then deprecate the old module entirely.

```mermaid
Portfolio Module → RebalancePlanDTO → NEW Execution Module → Shared Alpaca Manager
      ↓                   ↓                    ↓                     ↓
   Calculate          Transport            Execute               Place Orders
     Trades            DTO Only             Orders                  Only
```

### New Module Structure

```
execution_v2/                          # NEW: Clean execution module
├── __init__.py
├── core/
│   ├── executor.py                    # NEW: 50 lines of core logic
│   ├── execution_manager.py           # NEW: Simple coordinator
│   └── execution_tracker.py           # NEW: Basic result tracking
├── adapters/
│   ├── alpaca_adapter.py              # NEW: Thin wrapper around shared.brokers.AlpacaManager
├── models/
│   ├── execution_result.py            # NEW: Simple result models
│   └── order_status.py                # NEW: Order status tracking


execution/                             # LEGACY: Mark for deprecation
├── README_DEPRECATED.md               # NEW: Deprecation notice
├── core/manager.py                    # DEPRECATED: 2,000+ lines of complexity
├── strategies/                        # DEPRECATED: Unnecessary complexity
├── orders/                           # DEPRECATED: Over-engineered
├── analytics/                        # DEPRECATED: Belongs in portfolio
└── ... (all other subdirectories)    # DEPRECATED: Architectural violations
```

### What Execution Module SHOULD Do

1. Receive `RebalancePlanDTO` from portfolio module
2. Iterate through `RebalancePlanDTO.items`
3. For each item where `action != "HOLD"`:
   - Get current market price
   - Calculate shares from `trade_amount`
   - Place order with broker
   - Track execution results
4. Return execution summary

### What Execution Module SHOULD NOT Do

- Calculate trade amounts (portfolio module's job)
- Fetch position data (portfolio module's job)
- Validate target weights (portfolio module's job)
- Filter trades by criteria (portfolio module's job)
- Recalculate anything (portfolio module's job)

## Implementation Plan

### Phase 1: Clean Slate - New Simple Execution Core (Week 1)

#### 1.1 Create New Simple Execution Module

**Directory**: `execution_v2/` (completely separate from legacy `execution/`)

```text
execution_v2/
├── core/
│   ├── executor.py          # NEW: Core execution logic (~50 lines)
│   ├── execution_manager.py        # NEW: Simple coordinator (~30 lines)
│   └── execution_tracker.py        # NEW: Basic result tracking (~40 lines)
├── adapters/
│   ├── alpaca_adapter.py            # NEW: Wrapper around shared.brokers.AlpacaManager
├── models/
│   ├── execution_result.py         # NEW: Simple result models
│   └── order_status.py             # NEW: Order status tracking
```

#### 1.2 Mark Legacy Module for Deprecation

Create deprecation notices and prepare migration path:

```text
execution/
├── README_DEPRECATED.md            # NEW: "This module is deprecated, use execution_v2"
├── MIGRATION_GUIDE.md              # NEW: How to migrate from old to new
└── ... (existing files marked as legacy in docstrings)
```

#### 1.3 Simple Executor Using Shared Alpaca Manager

```python
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.dto.rebalance_plan_dto import RebalancePlanDTO, RebalancePlanItemDTO

class SimpleExecutor:
    """Ultra-simple executor that only places orders from DTOs."""

    def __init__(self, alpaca_manager: AlpacaManager):
        """Initialize with shared Alpaca manager."""
        self.alpaca = alpaca_manager

    def execute_rebalance_plan(
        self,
        plan: RebalancePlanDTO
    ) -> ExecutionResultDTO:
        """Execute a rebalance plan by placing orders."""
        results = []

        for item in plan.items:
            if item.action == "HOLD":
                continue

            result = self._place_single_order(item)
            results.append(result)

        return ExecutionResultDTO(
            correlation_id=plan.correlation_id,
            orders=results,
            success=all(r.success for r in results)
        )

    def _place_single_order(self, item: RebalancePlanItemDTO) -> OrderResult:
        """Place a single order from plan item."""
        # 1. Get market price using shared Alpaca manager
        price = self.alpaca.get_current_price(item.symbol)
        if not price:
            return OrderResult(
                symbol=item.symbol,
                order_id=None,
                success=False,
                error="Could not get current price"
            )

        # 2. Calculate shares
        shares = abs(item.trade_amount) / Decimal(str(price))

        # 3. Place order using shared Alpaca manager
        envelope = self.alpaca.place_market_order(
            symbol=item.symbol,
            side=item.action.lower(),  # BUY -> buy, SELL -> sell
            qty=float(shares)
        )

        # 4. Extract order ID from envelope
        order_id = None
        if envelope.success and envelope.raw_order:
            order_id = getattr(envelope.raw_order, 'id', None)

        return OrderResult(
            symbol=item.symbol,
            order_id=order_id,
            success=envelope.success,
            error=envelope.error_message
        )
```

#### 1.4 Alpaca Adapter (Thin Wrapper)

```python
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager

class AlpacaAdapter:
    """Thin adapter around shared AlpacaManager for execution module."""

    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        """Initialize adapter with shared Alpaca manager."""
        self.alpaca = AlpacaManager(
            api_key=api_key,
            secret_key=secret_key,
            paper=paper
        )

    def get_current_price(self, symbol: str) -> float | None:
        """Get current price using shared manager."""
        return self.alpaca.get_current_price(symbol)

    def place_market_order(
        self,
        symbol: str,
        side: str,
        qty: float
    ) -> OrderExecutionResult:
        """Place market order using shared manager."""
        envelope = self.alpaca.place_market_order(symbol, side, qty)

        return OrderExecutionResult(
            success=envelope.success,
            order_id=getattr(envelope.raw_order, 'id', None) if envelope.raw_order else None,
            error=envelope.error_message,
            raw_response=envelope.raw_order
        )

    def validate_connection(self) -> bool:
        """Validate connection using shared manager."""
        return self.alpaca.validate_connection()
```

### Phase 2: Integration with Shared Alpaca Capabilities (Week 2)

#### 2.1 Leverage Existing Shared Alpaca Manager

**NO CUSTOM BROKER NEEDED**: Use the existing `shared.brokers.AlpacaManager` which already provides:

- ✅ `place_market_order()` - Returns `RawOrderEnvelope` with order details
- ✅ `place_limit_order()` - For more sophisticated order types
- ✅ `get_current_price()` - Market price discovery
- ✅ `get_positions()` - Position data (not needed for execution, but available)
- ✅ `validate_connection()` - Connection health checks
- ✅ `get_account()` - Account information
- ✅ Paper trading support via `paper=True` parameter
- ✅ Comprehensive error handling and logging
- ✅ Protocol implementations for `TradingRepository`, `MarketDataRepository`, `AccountRepository`

#### 2.2 Debug Current Alpaca Integration Issues

The existing `AlpacaManager` already handles:

- API credentials and authentication
- Paper vs live trading configuration
- Order placement and status tracking
- Error handling and logging

**Investigation needed**: Why are orders returning `None` IDs?

- Check if API credentials are valid
- Verify paper trading environment setup
- Test with minimal order amounts
- Check Alpaca account status and permissions

#### 2.3 Create Mock Adapter for Testing

```python
from the_alchemiser.execution_v2.adapters.alpaca_adapter import AlpacaAdapter

class MockAdapter(AlpacaAdapter):
    """Mock adapter for testing execution logic."""

    def __init__(self):
        # Don't call super().__init__ to avoid real Alpaca connection
        self.mock_prices = {
            "SPY": 400.0,
            "QQQ": 350.0,
            "TECL": 45.0,
            "FNGO": 25.0,
        }
        self.order_counter = 0

    def get_current_price(self, symbol: str) -> float | None:
        """Mock price lookup."""
        return self.mock_prices.get(symbol, 100.0)  # Default $100

    def place_market_order(self, symbol: str, side: str, qty: float) -> OrderExecutionResult:
        """Mock order placement - always succeeds."""
        self.order_counter += 1
        order_id = f"MOCK_{self.order_counter:06d}"

        logger.info(f"🧪 MOCK ORDER: {side.upper()} {qty} {symbol}, ID: {order_id}")

        return OrderExecutionResult(
            success=True,
            order_id=order_id,
            error=None,
            raw_response={"mock": True, "symbol": symbol, "qty": qty, "side": side}
        )

    def validate_connection(self) -> bool:
        """Mock connection validation."""
        return True
```

### Phase 3: Integration with Trading Engine (Week 3)

#### 3.1 Replace Legacy Execution Manager

**DO NOT MODIFY** existing `execution/core/manager.py` (2,000+ lines). Instead, create a new simple manager:

```python
# execution_v2/core/execution_manager.py
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
from the_alchemiser.shared.dto.rebalance_plan_dto import RebalancePlanDTO
from the_alchemiser.execution_v2.core.executor import SimpleExecutor

class ExecutionManager:
    """Simple execution manager that delegates to SimpleExecutor."""

    def __init__(self, alpaca_manager: AlpacaManager):
        """Initialize with shared Alpaca manager."""
        self.executor = SimpleExecutor(alpaca_manager)

    def execute_rebalance_plan(self, plan: RebalancePlanDTO) -> ExecutionResultDTO:
        """Execute rebalance plan using simple executor."""
        logger.info(f"🚀 NEW EXECUTION: {len(plan.items)} items (using execution_v2)")

        result = self.executor.execute_rebalance_plan(plan)

        logger.info(f"✅ Execution complete: {result.success} ({result.orders_placed} orders)")
        return result

    @classmethod
    def create_with_config(cls, api_key: str, secret_key: str, paper: bool = True):
        """Factory method for easy creation."""
        alpaca_manager = AlpacaManager(
            api_key=api_key,
            secret_key=secret_key,
            paper=paper
        )
        return cls(alpaca_manager)
```

#### 3.2 Update Trading Engine Integration

Modify `trading_engine.py` to use the NEW execution manager while keeping legacy as fallback:

```python
# In TradingEngine.__init__()
def __init__(self, ...):
    # ... existing initialization ...

    # NEW: Initialize execution_v2 manager
    try:
        from the_alchemiser.execution_v2.core.execution_manager import ExecutionManager as ExecutionManagerV2
        self.execution_manager_v2 = ExecutionManagerV2.create_with_config(
            api_key=config.api_key,
            secret_key=config.secret_key,
            paper=config.paper_trading
        )
        self.use_execution_v2 = True
        logger.info("✅ Using NEW execution_v2 module")
    except ImportError:
        logger.warning("⚠️ execution_v2 not available, using legacy execution")
        self.use_execution_v2 = False

# In TradingEngine.execute_multi_strategy()
def execute_multi_strategy(self, ...):
    # ... portfolio calculation ...

    # Get rebalance plan DTO from portfolio
    rebalance_plan = self.portfolio_rebalancer.rebalancing_service.create_rebalance_plan_dto(
        target_weights,
        correlation_id=correlation_id
    )

    if rebalance_plan:
        if self.use_execution_v2:
            # NEW: Simple execution - no recalculation
            logger.info("🚀 Using execution_v2 for order placement")
            execution_result = self.execution_manager_v2.execute_rebalance_plan(rebalance_plan)
        else:
            # LEGACY: Fallback to old execution module
            logger.warning("⚠️ Falling back to legacy execution module")
            execution_result = self._multi_strategy_executor.execute_multi_strategy(...)
    else:
        # No trades needed
        execution_result = ExecutionResultDTO(success=True, orders=[])

    # Return results...
```

#### 3.3 Create Legacy Deprecation Notice

```python
# execution/README_DEPRECATED.md
"""
# DEPRECATED EXECUTION MODULE

⚠️ **WARNING**: This execution module is deprecated and will be removed.

## Issues with Legacy Module
- 10,000+ lines of unnecessary complexity
- Recalculates trades instead of using portfolio DTOs
- Broken broker integration (orders return None IDs)
- Architectural violations (doing portfolio calculations)

## Migration Path
Use the new `execution_v2` module instead:

```python
# OLD (deprecated)
from the_alchemiser.execution.core.manager import ExecutionManager

# NEW (recommended)
from the_alchemiser.execution_v2.core.execution_manager import ExecutionManager
```

The new module:

- 200 lines vs 10,000+ lines
- Consumes portfolio DTOs directly
- Uses shared Alpaca capabilities
- Simple, focused, testable

## Timeline

- Phase 1: execution_v2 available alongside legacy
- Phase 2: Switch trading engine to execution_v2
- Phase 3: Remove legacy execution module entirely

"""

```markdown

### Phase 4: Error Handling & Monitoring (Week 4)

#### 4.1 Comprehensive Error Handling

```python
class ExecutionError(Exception):
    """Base execution error."""
    pass

class BrokerConnectionError(ExecutionError):
    """Broker API connection failed."""
    pass

```

### 4.1 Simple Error Recovery

```python
class OrderPlacementError(ExecutionError):
    """Order placement failed."""
    pass

class InsufficientFundsError(ExecutionError):
    """Insufficient funds for order."""
    pass
```

### 4.2 Execution Monitoring

```python
class ExecutionMonitor:
    """Monitor execution progress and failures."""

    def track_execution(self, plan: RebalancePlanDTO, result: ExecutionResultDTO):
        """Track execution metrics."""
        self.log_execution_summary(plan, result)
        self.check_execution_health(result)
        self.alert_on_failures(result)

    def check_execution_health(self, result: ExecutionResultDTO):
        """Check if execution is healthy."""
        failed_orders = [o for o in result.orders if not o.success]

        if len(failed_orders) > 0:
            failure_rate = len(failed_orders) / len(result.orders)
            if failure_rate > 0.5:  # >50% failure rate
                logger.critical(f"🚨 HIGH FAILURE RATE: {failure_rate:.1%}")
                # Trigger alerts
```

#### 4.3 Execution Logging

```python
class ExecutionLogger:
    """Detailed execution logging."""

    def log_plan_received(self, plan: RebalancePlanDTO):
        """Log when plan is received."""
        logger.info(f"📋 Plan received: {plan.plan_id}")
        logger.info(f"  Total value: ${plan.total_trade_value}")
        logger.info(f"  Items: {len(plan.items)}")

        for item in plan.items:
            logger.info(f"  📦 {item.action} ${item.trade_amount} {item.symbol}")

    def log_order_placed(self, item: RebalancePlanItemDTO, order_id: str | None):
        """Log order placement."""
        if order_id:
            logger.info(f"✅ Order placed: {item.action} ${item.trade_amount} {item.symbol} → {order_id}")
        else:
            logger.error(f"❌ Order failed: {item.action} ${item.trade_amount} {item.symbol}")
```

## Migration Strategy

### Phase A: Parallel Implementation (2 weeks)

- Build new simple execution module alongside existing
- Test new module with paper trading
- Compare results with current module

### Phase B: Staged Rollout (1 week)

- Switch to new module for paper trading
- Monitor for 1 week
- Validate all functionality works

### Phase C: Full Migration (1 week)

- Switch to new module for live trading
- Remove old execution module code
- Update documentation

## Success Metrics

### Primary Metrics

1. **Order Success Rate**: >95% of orders placed successfully
2. **Broker Integration Health**: No more `None` order IDs
3. **Execution Speed**: <5 seconds for typical rebalance
4. **Code Simplicity**: <200 lines for core execution logic

### Secondary Metrics

1. **Error Rate**: <5% execution errors
2. **Monitoring Coverage**: 100% of executions logged
3. **Test Coverage**: >90% code coverage
4. **Documentation**: Complete API documentation

## Risk Mitigation

### Technical Risks

1. **Broker API Issues**: Use mock broker for testing, gradual rollout
2. **Market Data Issues**: Implement price validation and fallbacks
3. **Order Failures**: Comprehensive error handling and retry logic

### Business Risks

1. **Trade Execution**: Start with paper trading, small amounts
2. **Financial Impact**: Use position sizing limits, stop-loss mechanisms
3. **Regulatory**: Ensure compliance with trading regulations

## File Structure

```text
execution/
├── __init__.py
├── core/
│   ├── __init__.py
│   ├── executor.py          # Main execution logic
│   ├── execution_manager.py        # Manager interface
│   └── execution_tracker.py        # Execution monitoring
├── brokers/
│   ├── __init__.py
│   ├── base_broker.py              # Broker interface
│   ├── alpaca_broker.py            # Alpaca implementation
├── models/
│   ├── __init__.py
│   ├── execution_result.py         # Result models
│   └── order_status.py             # Order status models
├── monitoring/
│   ├── __init__.py
│   ├── execution_monitor.py        # Health monitoring
│   └── execution_logger.py         # Detailed logging

```

## Implementation Timeline

| Week | Phase | Deliverables |
|------|-------|-------------|
| 1 | Clean Slate | Simple executor, broker interface, basic models |
| 2 | Broker Fix | Working Alpaca integration, mock broker, error handling |
| 3 | Integration | Trading engine integration, end-to-end flow |
| 4 | Monitoring | Error handling, logging, health monitoring |
| 5 | Testing | Unit tests, integration tests, validation |
| 6 | Migration | Parallel implementation, staged rollout |
| 7 | Production | Full migration, documentation, monitoring |

## Key Principles

1. **Simplicity First**: Execution module should be dead simple
2. **Single Responsibility**: Only execute orders, nothing else
3. **DTO-Driven**: Portfolio DTOs are the single source of truth
4. **Fail Fast**: Clear error messages, no silent failures
5. **Observable**: Comprehensive logging and monitoring
6. **Testable**: Mock brokers, isolated unit tests

## Conclusion

This plan completely rebuilds the execution module around the core principle of DTO consumption. By eliminating trade recalculation, position dependency, and complex filtering, we create a simple, reliable, and maintainable execution system that does exactly what it should: iterate through DTO items and place orders.

The new execution module will be:

- **50x simpler** (200 lines vs 10,000+ lines)
- **100% focused** on order placement only
- **Broker-agnostic** with clean interfaces
- **Fully testable** with mock implementations
- **Highly observable** with comprehensive logging

This architecture respects the modular boundaries and ensures the execution module serves its single purpose: executing trades as specified by the portfolio module.
