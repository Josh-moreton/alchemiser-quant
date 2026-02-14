# Marketability Algorithm Implementation

## Overview

This implementation replaces the fixed "limit at mid × 0.98" pricing with an adaptive marketability algorithm that improves fill rates while enforcing slippage controls.

## Key Features

### 1. Adaptive Limit Pricing
- **Start at mid**: Initial limit order placed at mid price
- **Step toward ask**: If not filled, progressively increase limit price toward ask
- **Market condition aware**: 
  - Calm markets (VIX < 28): 10% of spread per step
  - High IV (VIX >= 28): 20% of spread per step

### 2. Slippage Controls

#### Per-Trade Slippage Limits
- **Open positions**: Max 10% slippage from mid price
- **Close positions**: Max 5% slippage from mid price (tighter control)

#### Daily Slippage Limits
- **Max 3% of daily premium volume** in aggregate slippage
- Tracks all trades across the trading day
- Enforces before placing orders

### 3. Explicit No-Fill Handling

When orders don't fill:
- **Max attempts**: 5 pricing steps before giving up
- **Max time**: 180 seconds (3 minutes) timeout
- **Explicit logging**: "HEDGE NOT PLACED" message with alert
- **No-fill flag**: `no_fill_explicit=True` in ExecutionResult

### 4. Slippage Metrics

All execution results now include:
- `slippage_from_mid`: Dollar amount of slippage
- `slippage_pct`: Percentage slippage from mid
- `pricing_attempts`: Number of repricing attempts

## Implementation Details

### Core Module
`shared_layer/python/the_alchemiser/shared/options/marketability_pricing.py`

Key classes:
- `MarketabilityPricer`: Calculates adaptive limit prices
- `SlippageTracker`: Tracks daily aggregate slippage
- `OrderSide`: Enum for OPEN vs CLOSE orders
- `MarketCondition`: Enum for CALM vs HIGH_IV markets

### Configuration
`shared_layer/python/the_alchemiser/shared/options/constants/hedge_config.py`

New constants:
```python
# Per-trade slippage limits
MAX_SLIPPAGE_PER_TRADE_OPEN = Decimal("0.10")   # 10% for opens
MAX_SLIPPAGE_PER_TRADE_CLOSE = Decimal("0.05")  # 5% for closes

# Daily aggregate limit
MAX_DAILY_SLIPPAGE_PCT = Decimal("0.03")  # 3% of daily premium

# Price stepping
PRICE_STEP_PCT_CALM = Decimal("0.10")      # 10% of spread (calm)
PRICE_STEP_PCT_HIGH_IV = Decimal("0.20")   # 20% of spread (high IV)

# Fill limits
MAX_FILL_ATTEMPTS = 5              # Max repricing attempts
MAX_FILL_TIME_SECONDS = 180        # 3 minute timeout
PRICE_UPDATE_INTERVAL_SECONDS = 30  # 30 seconds between steps
```

### Integration
`functions/hedge_executor/core/options_execution_service.py`

The `OptionsExecutionService` now:
1. Uses `MarketabilityPricer` to calculate initial and stepped limit prices
2. Monitors orders with `_monitor_order_with_repricing()`
3. Cancels and replaces orders with updated prices if not filled
4. Records slippage metrics on fills
5. Explicitly logs "HEDGE NOT PLACED" on no-fill

## Testing

### Test Suite
`tests/test_marketability_pricing.py`

**11 comprehensive tests covering:**
- ✅ Initial limit price at mid
- ✅ Price stepping toward ask
- ✅ High IV larger steps
- ✅ Max slippage enforcement (open vs close)
- ✅ Pricing sequence generation
- ✅ Slippage recording and tracking
- ✅ Daily slippage limit enforcement
- ✅ Daily reset functionality
- ✅ Market snapshot recording
- ✅ Pricing with recorded snapshots

All tests use recorded market snapshots (bid/ask) for reproducibility.

### Running Tests
```bash
export PYTHONPATH="shared_layer/python:$PYTHONPATH"
python3 -m pytest tests/test_marketability_pricing.py -v
```

## Usage Example

### Execution with Marketability Algorithm

```python
from functions.hedge_executor.core.options_execution_service import (
    OptionsExecutionService,
    ExecutionResult,
)
from the_alchemiser.shared.options.marketability_pricing import (
    OrderSide,
    SlippageTracker,
)

# Initialize service with marketability enabled
tracker = SlippageTracker()
service = OptionsExecutionService(
    options_adapter=adapter,
    marketability_enabled=True,
    slippage_tracker=tracker,
)

# Execute hedge order
result = service.execute_hedge_order(
    selected_option=selected,
    underlying_symbol="QQQ",
    vix_level=Decimal("22.5"),  # Current VIX
    order_side=OrderSide.OPEN,  # Opening new position
)

# Check result
if result.success:
    print(f"Filled at ${result.filled_price}")
    print(f"Slippage: {result.slippage_pct:.2%}")
    print(f"Attempts: {result.pricing_attempts}")
else:
    if result.no_fill_explicit:
        print(f"HEDGE NOT PLACED: {result.error_message}")
```

### Market Snapshot for Testing

```python
from the_alchemiser.shared.options.marketability_pricing import MarketSnapshot

# Record real market conditions for testing
snapshot = MarketSnapshot(
    option_symbol="SPY241231P00450000",
    timestamp="2024-01-15T14:30:00Z",
    bid_price=Decimal("1.95"),
    ask_price=Decimal("2.05"),
    mid_price=Decimal("2.00"),
    spread_pct=Decimal("0.05"),  # 5% spread
    vix_level=Decimal("16.2"),
)

# Use in tests to reproduce pricing behavior
```

## Backward Compatibility

The implementation maintains backward compatibility:
- Old constant `LIMIT_PRICE_DISCOUNT_FACTOR` still exists (marked deprecated)
- Marketability can be disabled via `marketability_enabled=False`
- Existing execution flow unchanged when disabled

## Logging

All pricing decisions are logged with structured logging:

```python
# Initial pricing
logger.info("Executing hedge order with adaptive pricing", 
            initial_limit_price=..., 
            marketability_enabled=True,
            order_side="open")

# Repricing steps
logger.info("Stepping limit price toward ask",
            attempt=2,
            current_limit=...,
            next_limit=...,
            slippage_from_mid_pct=...)

# No-fill outcomes
logger.warning("EXPLICIT NO FILL - Max pricing attempts reached",
               pricing_attempts=5,
               alert_required=True)
```

## Monitoring

### Key Metrics to Track
1. **Fill rate**: Percentage of orders filled before timeout
2. **Average slippage**: Mean slippage across all fills
3. **Average attempts**: Mean number of repricing attempts
4. **No-fill rate**: Percentage hitting max attempts or timeout
5. **Daily slippage**: Percentage of daily premium spent on slippage

### Alerts
- No-fill events trigger `alert_required=True`
- Daily slippage limit breaches logged as warnings
- Max slippage per trade breaches logged

## Future Enhancements

1. **VIX integration**: Add VIX level to HedgeEvaluationCompleted event
2. **Dynamic thresholds**: Adjust slippage limits based on market volatility
3. **Spread-aware pricing**: Wider spreads get different treatment
4. **Time-of-day rules**: Different pricing for market open vs close
5. **Historical analysis**: Track fill rates by pricing strategy

## Security Considerations

- No secrets in logs (prices only, no account details)
- Slippage limits prevent runaway costs
- Explicit fail-closed on no-fill (hedge NOT placed)
- Daily limits prevent excessive cost accumulation

## References

- Issue: `[Options Hedging] Execution - make fills real, not aspirational`
- Module: `shared_layer/python/the_alchemiser/shared/options/marketability_pricing.py`
- Tests: `tests/test_marketability_pricing.py`
- Constants: `shared_layer/python/the_alchemiser/shared/options/constants/hedge_config.py`
