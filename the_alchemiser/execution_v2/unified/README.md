# Unified Order Placement Service

**Status**: Current (Production)
**Business Unit**: Execution

## Overview

This package provides a **single, robust, testable order placement flow** that simplifies and consolidates all order placement logic in the trading platform.

## Key Features

### 1. **Single Entry Point**
- One service (`UnifiedOrderPlacementService`) for ALL order placement
- No more confusion about which path to use

### 2. **Clear Order Intent Semantics**
- `OrderIntent` abstraction with explicit types:
  - `BUY`: Buy shares
  - `SELL` + `PARTIAL`: Reduce position size
  - `SELL` + `FULL`: Fully close position
- Single translation point to Alpaca API parameters

### 3. **Unified Quote Acquisition**
- Streaming WebSocket quotes first (lowest latency)
- Automatic REST API fallback (reliability)
- Explicit 0 bid/ask handling (common Alpaca issue):
  - If bid=0 and ask>0: use ask for both sides
  - If ask=0 and bid>0: use bid for both sides
  - If both=0: treat as unusable quote
- Metrics and logging for observability

### 4. **Explicit "Walk the Book" Strategy**
- Clear price progression: **75% → 85% → 95% → market**
- For BUY orders: Start conservative (75% toward ask), get more aggressive
- For SELL orders: Start conservative (75% toward bid), get more aggressive
- Configurable wait times between steps
- Full audit trail of all attempts

### 5. **Portfolio Validation**
- Validate position changes after execution
- Confirm full closes actually closed the position
- Detect discrepancies between expected and actual state

## Usage Examples

### Basic Buy Order (Medium Urgency)

```python
from decimal import Decimal
from the_alchemiser.execution_v2.unified import (
    UnifiedOrderPlacementService,
    OrderIntent,
    OrderSide,
    CloseType,
    Urgency,
)

# Initialize service
service = UnifiedOrderPlacementService(
    alpaca_manager=alpaca_manager,
    pricing_service=pricing_service,
    enable_validation=True,
)

# Create order intent
intent = OrderIntent(
    side=OrderSide.BUY,
    close_type=CloseType.NONE,
    symbol="AAPL",
    quantity=Decimal("10"),
    urgency=Urgency.MEDIUM,
    correlation_id="trade-123",
)

# Place order
result = await service.place_order(intent)

# Check result
if result.success:
    print(result.describe())
    # ✅ BUY 10 shares of AAPL filled 10 shares @ $150.25 via walk-the-book (3 steps) in 45.2s

    print(f"Final order ID: {result.final_order_id}")
    print(f"Avg fill price: ${result.avg_fill_price}")
    print(f"Validation: {result.validation_result.describe()}")
else:
    print(f"Order failed: {result.error_message}")
```

### Partial Sell (Reduce Position)

```python
intent = OrderIntent(
    side=OrderSide.SELL,
    close_type=CloseType.PARTIAL,
    symbol="AAPL",
    quantity=Decimal("5"),  # Sell 5 out of 10 shares
    urgency=Urgency.LOW,  # Use full walk-the-book for best price
    correlation_id="trade-124",
)

result = await service.place_order(intent)
```

### Full Close (High Urgency)

```python
intent = OrderIntent(
    side=OrderSide.SELL,
    close_type=CloseType.FULL,
    symbol="AAPL",
    quantity=Decimal("10"),  # Close entire position
    urgency=Urgency.HIGH,  # Use market order immediately
    correlation_id="trade-125",
)

result = await service.place_order(intent)

# High urgency skips walk-the-book and uses market order
# Validation will confirm position is now 0
```

## Architecture

```
User Code
    ↓
UnifiedOrderPlacementService.place_order(intent)
    ↓
    ├─→ Preflight Validation (quantity, asset info)
    ├─→ Pre-execution Validation (get current position)
    ├─→ UnifiedQuoteService.get_best_quote()
    │       ├─→ Try streaming (WebSocket)
    │       ├─→ Handle 0 bids/asks
    │       └─→ Fallback to REST API
    ↓
    ├─→ Route by Urgency:
    │       ├─→ HIGH: Market order immediately
    │       └─→ MEDIUM/LOW: WalkTheBookStrategy
    │               ├─→ Step 1: Limit @ 75% toward aggressive side
    │               ├─→ Step 2: Limit @ 85% (if not filled)
    │               ├─→ Step 3: Limit @ 95% (if not filled)
    │               └─→ Step 4: Market order (final escalation)
    ↓
    ├─→ PortfolioValidator.validate_execution()
    │       ├─→ Wait for settlement
    │       ├─→ Fetch current position
    │       └─→ Compare expected vs actual
    ↓
    └─→ Return ExecutionResult
            ├─→ Full audit trail
            ├─→ Quote source and pricing
            ├─→ All order attempts
            └─→ Validation result
```

## Comparison: Old vs New

### Old Architecture (Problems)
- **Dual paths**: Smart execution vs market execution use different quote sources
- **Fragmented types**: BUY/SELL/CLOSE spread across multiple boolean flags
- **Implicit logic**: "Walk the book" buried in repeg manager
- **No validation**: Orders complete when Alpaca says "filled", no portfolio check

### New Architecture (Solutions)
- **Single path**: All orders use same quote service
- **Clear types**: `OrderIntent` with explicit `OrderSide` + `CloseType`
- **Explicit logic**: `WalkTheBookStrategy` with clear 75%→85%→95%→market steps
- **Full validation**: `PortfolioValidator` confirms position changed as expected

## Metrics and Observability

The unified service tracks and logs:

### Quote Metrics
- `streaming_success_count`: Quotes obtained from WebSocket
- `rest_fallback_count`: Quotes obtained from REST API
- `no_usable_quote_count`: Failed to get any quote
- `zero_bid_count`: Quotes with 0 bid (substituted with ask)
- `zero_ask_count`: Quotes with 0 ask (substituted with bid)
- `both_zero_count`: Quotes with both 0 (unusable)

### Execution Metrics
- Execution time per order
- Steps used in walk-the-book
- Fill rates at each price level
- Validation success/failure rates

## Testing

### Unit Tests

```python
import pytest
from decimal import Decimal
from the_alchemiser.execution_v2.unified import OrderIntent, OrderSide, CloseType, Urgency

def test_order_intent_validation():
    """Test order intent validation."""
    # Valid buy order
    intent = OrderIntent(
        side=OrderSide.BUY,
        close_type=CloseType.NONE,
        symbol="AAPL",
        quantity=Decimal("10"),
        urgency=Urgency.MEDIUM,
    )
    assert intent.is_buy
    assert not intent.is_sell
    assert not intent.is_full_close

    # Invalid: close with BUY side
    with pytest.raises(ValueError):
        OrderIntent(
            side=OrderSide.BUY,
            close_type=CloseType.FULL,  # Invalid combination
            symbol="AAPL",
            quantity=Decimal("10"),
            urgency=Urgency.MEDIUM,
        )
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_unified_placement_service_buy_order(alpaca_manager, pricing_service):
    """Test buying shares via unified service."""
    service = UnifiedOrderPlacementService(
        alpaca_manager=alpaca_manager,
        pricing_service=pricing_service,
    )

    intent = OrderIntent(
        side=OrderSide.BUY,
        close_type=CloseType.NONE,
        symbol="AAPL",
        quantity=Decimal("1"),
        urgency=Urgency.HIGH,  # Use market for test speed
    )

    result = await service.place_order(intent)

    assert result.success
    assert result.total_filled > 0
    assert result.final_order_id is not None
```

## Migration Guide

### Before (Old Code)

```python
# Scattered across multiple files
from the_alchemiser.execution_v2.core.smart_execution_strategy import SmartExecutionStrategy
from the_alchemiser.execution_v2.core.market_order_executor import MarketOrderExecutor

# Different paths for different order types
if use_smart:
    strategy = SmartExecutionStrategy(...)
    result = await strategy.place_smart_order(request)
else:
    executor = MarketOrderExecutor(...)
    result = executor.execute_market_order(symbol, side, quantity)

# Manual quote acquisition
quote = pricing_service.get_quote_data(symbol)
if not quote:
    quote = alpaca_manager.get_latest_quote(symbol)  # Different fallback path
```

### After (New Code)

```python
# Single import
from the_alchemiser.execution_v2.unified import (
    UnifiedOrderPlacementService,
    OrderIntent,
    OrderSide,
    CloseType,
    Urgency,
)

# Single service, single call
service = UnifiedOrderPlacementService(
    alpaca_manager=alpaca_manager,
    pricing_service=pricing_service,
)

intent = OrderIntent(
    side=OrderSide.BUY,
    close_type=CloseType.NONE,
    symbol="AAPL",
    quantity=Decimal("10"),
    urgency=Urgency.MEDIUM,
)

result = await service.place_order(intent)  # Handles everything
```

## Configuration

### Walk-the-Book Steps

Default: `[0.75, 0.85, 0.95]` then market

Can be customized:

```python
from the_alchemiser.execution_v2.unified import WalkTheBookStrategy

strategy = WalkTheBookStrategy(
    alpaca_manager=alpaca_manager,
    step_wait_seconds=20,  # Wait 20s at each step (default: 30s)
    price_steps=[0.70, 0.80, 0.90, 0.95],  # Custom progression
)
```

### Quote Timeouts

```python
from the_alchemiser.execution_v2.unified import UnifiedQuoteService

quote_service = UnifiedQuoteService(
    alpaca_manager=alpaca_manager,
    pricing_service=pricing_service,
    streaming_timeout_ms=3000,  # Wait 3s for streaming (default: 5s)
    quote_freshness_seconds=5.0,  # Max quote age (default: 10s)
)
```

### Portfolio Validation

```python
service = UnifiedOrderPlacementService(
    alpaca_manager=alpaca_manager,
    pricing_service=pricing_service,
    enable_validation=True,  # Enable validation (default: True)
)
```

## Troubleshooting

### Issue: "No usable quote available"

**Cause**: Both streaming and REST returned quotes with bid=0 and ask=0

**Solution**:
1. Check if market is open
2. Check if symbol is tradable
3. For HIGH urgency orders, system will proceed with market order anyway

### Issue: "Validation failed - position discrepancy"

**Cause**: Actual position doesn't match expected after execution

**Possible reasons**:
- Partial fill didn't fully complete
- Position update hasn't settled yet
- Corporate action (split, dividend) changed position

**Solution**:
1. Check `validation_result.discrepancy` - if small, may be fractional tolerance issue
2. Manually verify position via Alpaca UI
3. Adjust `fractional_tolerance` in `PortfolioValidator` if needed

## Migration Status

**Status: Complete** - The unified order placement service is now the primary execution path.

The old `SmartExecutionStrategy` and related modules have been removed:
- `smart_execution_strategy/strategy.py` → Replaced by `UnifiedOrderPlacementService`
- `smart_execution_strategy/quotes.py` → Replaced by `UnifiedQuoteService`
- `smart_execution_strategy/repeg.py` → Replaced by `WalkTheBookStrategy`
- `smart_execution_strategy/pricing.py` → Replaced by `WalkTheBookStrategy`
- `smart_execution_strategy/tracking.py` → Replaced by `WalkResult`
- `smart_execution_strategy/utils.py` → Integrated into unified components

Only `smart_execution_strategy/models.py` remains for `ExecutionConfig` compatibility.

## Future Enhancements

- [ ] Support for limit orders with explicit price (not just walk-the-book)
- [ ] Support for stop-loss and take-profit orders
- [ ] Retry logic for transient broker errors
- [ ] Dry-run mode for testing without actual execution
- [ ] Historical execution analytics and reporting
