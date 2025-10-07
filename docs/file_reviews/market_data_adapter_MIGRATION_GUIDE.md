# Migration Guide: StrategyMarketDataAdapter Breaking Changes

**Version**: 2.9.1  
**Date**: 2025-01-05  
**Status**: Required for any code using `get_current_prices()`

---

## Overview

The `StrategyMarketDataAdapter` has undergone critical financial-grade improvements to ensure correctness and safety in trading operations. This guide helps you migrate code that uses the adapter.

## Breaking Changes Summary

| Change | Old Behavior | New Behavior | Impact |
|--------|-------------|--------------|--------|
| **Return Type** | `dict[str, float]` | `dict[str, Decimal \| None]` | **BREAKING** |
| **Error Handling** | Returns `0.0` on error | Returns `None` on error | **BREAKING** |
| **Constructor** | Single parameter | Optional `correlation_id` | **Non-breaking** |

---

## Change 1: Return Type - `float` → `Decimal | None`

### Why This Change?

**Financial Correctness**: Floating-point arithmetic has precision errors:
```python
# Float precision problem
>>> 0.1 + 0.2
0.30000000000000004  # ❌ Wrong!

# Decimal precision (correct)
>>> Decimal("0.1") + Decimal("0.2")
Decimal('0.3')  # ✅ Correct!
```

**Industry Standard**: All financial systems must use `Decimal` for money calculations to avoid accumulating rounding errors across thousands of trades.

### Migration Steps

#### Before (Old Code)
```python
from the_alchemiser.strategy_v2.adapters.market_data_adapter import StrategyMarketDataAdapter

adapter = StrategyMarketDataAdapter(alpaca_manager)
prices = adapter.get_current_prices(["AAPL", "GOOGL"])

# Old: prices is dict[str, float]
apple_price = prices["AAPL"]  # float
portfolio_value = apple_price * 100  # float arithmetic
```

#### After (New Code)
```python
from decimal import Decimal
from the_alchemiser.strategy_v2.adapters.market_data_adapter import StrategyMarketDataAdapter

adapter = StrategyMarketDataAdapter(alpaca_manager)
prices = adapter.get_current_prices(["AAPL", "GOOGL"])

# New: prices is dict[str, Decimal | None]
apple_price = prices["AAPL"]  # Decimal | None

# REQUIRED: Handle None case
if apple_price is None:
    logger.warning("Price unavailable for AAPL")
    # Choose one of the strategies below
else:
    # Use Decimal arithmetic
    portfolio_value = apple_price * Decimal("100")
```

---

## Change 2: Error Handling - `0.0` → `None`

### Why This Change?

**Safety**: Returning `0.0` on errors could cause:
- Zero-price trade orders (invalid)
- Division by zero errors
- Silent failures in calculations

**Explicit Handling**: `None` forces callers to explicitly handle missing data.

### Migration Strategies

#### Strategy 1: Skip Missing Prices (Recommended for Portfolio Allocation)
```python
prices = adapter.get_current_prices(["AAPL", "GOOGL", "MSFT"])

# Calculate portfolio value, skipping unavailable prices
portfolio_value = Decimal("0")
for symbol, price in prices.items():
    if price is not None:  # ✅ Skip missing data
        quantity = positions[symbol]
        portfolio_value += price * Decimal(str(quantity))
    else:
        logger.warning(f"Skipping {symbol} - price unavailable")
```

#### Strategy 2: Use Fallback Price (Use with Caution)
```python
prices = adapter.get_current_prices(["AAPL"])
apple_price = prices["AAPL"]

if apple_price is None:
    # Fallback to last known price (from cache/database)
    apple_price = get_last_known_price("AAPL")
    logger.warning(f"Using fallback price for AAPL: {apple_price}")
```

#### Strategy 3: Fail-Fast (Recommended for Critical Operations)
```python
from the_alchemiser.shared.types.exceptions import MarketDataError

prices = adapter.get_current_prices(["AAPL"])
apple_price = prices["AAPL"]

if apple_price is None:
    # Fail immediately - cannot proceed without price
    raise MarketDataError(
        "Cannot execute trade without current price for AAPL",
        symbol="AAPL",
        data_type="price"
    )

# Proceed with trade
execute_order("AAPL", apple_price, quantity)
```

#### Strategy 4: Filter Out Missing Prices
```python
prices = adapter.get_current_prices(["AAPL", "GOOGL", "MSFT"])

# Get only symbols with available prices
available_prices = {
    symbol: price 
    for symbol, price in prices.items() 
    if price is not None
}

# Calculate allocations only for available prices
allocations = calculate_allocations(available_prices)
```

---

## Change 3: Constructor - Optional `correlation_id`

### Why This Change?

**Traceability**: Enables end-to-end tracing across system boundaries for debugging and compliance.

### Migration Steps

**This change is NON-BREAKING**. Existing code continues to work:

#### Old Code (Still Works)
```python
adapter = StrategyMarketDataAdapter(alpaca_manager)
```

#### New Code (Recommended)
```python
import uuid

correlation_id = str(uuid.uuid4())
adapter = StrategyMarketDataAdapter(alpaca_manager, correlation_id=correlation_id)

# correlation_id will appear in all logs from this adapter
prices = adapter.get_current_prices(["AAPL"])
```

---

## Type Annotations Update

### Before
```python
def calculate_portfolio_value(
    adapter: StrategyMarketDataAdapter,
    positions: dict[str, int]
) -> float:
    prices = adapter.get_current_prices(list(positions.keys()))
    total = 0.0
    for symbol, quantity in positions.items():
        total += prices[symbol] * quantity
    return total
```

### After
```python
from decimal import Decimal

def calculate_portfolio_value(
    adapter: StrategyMarketDataAdapter,
    positions: dict[str, int]
) -> Decimal:
    prices = adapter.get_current_prices(list(positions.keys()))
    total = Decimal("0")
    
    for symbol, quantity in positions.items():
        price = prices[symbol]
        if price is None:
            logger.warning(f"Skipping {symbol} - price unavailable")
            continue
        total += price * Decimal(str(quantity))
    
    return total
```

---

## Decimal Arithmetic Best Practices

### ✅ DO: Use Decimal for All Money Calculations
```python
from decimal import Decimal

# Convert from float/int to Decimal
price = Decimal("150.50")  # ✅ String conversion (preferred)
quantity = Decimal(str(100))  # ✅ Convert via string

# Arithmetic
total = price * quantity  # ✅ Returns Decimal

# Constants
percentage = Decimal("0.05")  # ✅ 5%
```

### ❌ DON'T: Mix Decimal and Float
```python
price = Decimal("150.50")
quantity = 100.0  # float

total = price * quantity  # ❌ ERROR: Cannot multiply Decimal by float
```

### ✅ DO: Convert at Boundaries
```python
# Input from API (float)
api_price = 150.50  # float from JSON

# Convert immediately to Decimal
price = Decimal(str(api_price))  # ✅

# Do calculations
total = price * Decimal("100")

# Output to API (if needed)
output_price = float(total)  # Only at boundary
```

### ❌ DON'T: Use Float Division
```python
price = Decimal("100")
result = price / 2  # ❌ Can introduce float

# ✅ DO: Use Decimal division
result = price / Decimal("2")
```

---

## Common Patterns

### Pattern 1: Price Dictionary with Defaults
```python
from decimal import Decimal

def get_prices_with_defaults(
    adapter: StrategyMarketDataAdapter,
    symbols: list[str],
    default_price: Decimal | None = None
) -> dict[str, Decimal]:
    """Get prices, using default for missing values."""
    prices = adapter.get_current_prices(symbols)
    
    result = {}
    for symbol, price in prices.items():
        if price is not None:
            result[symbol] = price
        elif default_price is not None:
            result[symbol] = default_price
            logger.warning(f"Using default price for {symbol}: {default_price}")
        else:
            raise ValueError(f"No price available for {symbol}")
    
    return result
```

### Pattern 2: Retry on Missing Prices
```python
import time
from decimal import Decimal

def get_prices_with_retry(
    adapter: StrategyMarketDataAdapter,
    symbols: list[str],
    max_retries: int = 3
) -> dict[str, Decimal]:
    """Get prices with retry logic."""
    for attempt in range(max_retries):
        prices = adapter.get_current_prices(symbols)
        
        # Check for missing prices
        missing = [s for s, p in prices.items() if p is None]
        
        if not missing:
            # All prices available - cast to non-optional
            return {s: p for s, p in prices.items() if p is not None}
        
        if attempt < max_retries - 1:
            logger.warning(f"Missing prices for {missing}, retrying...")
            time.sleep(1)
        else:
            raise ValueError(f"Could not get prices for {missing} after {max_retries} attempts")
    
    # Should never reach here
    raise RuntimeError("Unexpected error in retry logic")
```

### Pattern 3: Percentage Calculations
```python
from decimal import Decimal

prices = adapter.get_current_prices(["AAPL"])
apple_price = prices["AAPL"]

if apple_price is not None:
    # Calculate 5% above current price
    target_price = apple_price * Decimal("1.05")
    
    # Calculate percentage change
    old_price = Decimal("140.00")
    change = (apple_price - old_price) / old_price
    change_pct = change * Decimal("100")
```

---

## Testing Your Migration

### Unit Test Example
```python
from decimal import Decimal
from unittest.mock import Mock, patch
import pytest

def test_handle_none_prices():
    """Test that None prices are handled correctly."""
    mock_alpaca = Mock()
    adapter = StrategyMarketDataAdapter(mock_alpaca)
    
    # Mock service to return None for one symbol
    with patch.object(adapter._market_data_service, 'get_quote') as mock_get_quote:
        mock_get_quote.side_effect = lambda s: {
            "ask_price": 150.0, "bid_price": 149.0
        } if s == "AAPL" else None
        
        prices = adapter.get_current_prices(["AAPL", "GOOGL"])
        
        assert isinstance(prices["AAPL"], Decimal)
        assert prices["GOOGL"] is None  # ✅ Correctly returns None
```

---

## FAQ

### Q: Why not just raise an exception instead of returning None?

**A**: Returning `None` for individual symbols allows partial success. If you're fetching prices for 100 symbols and 1 fails, you can still use the other 99. Raising an exception would fail the entire batch.

### Q: Can I convert Decimal back to float?

**A**: Only at output boundaries (e.g., API responses, UI display). Never convert back to float for internal calculations.

```python
# ✅ OK: Output to API
price_decimal = Decimal("150.50")
api_response = {"price": float(price_decimal)}

# ❌ NOT OK: Internal calculation
total = float(price_decimal) * 100  # Precision loss!
```

### Q: How do I compare Decimal values?

**A**: Use standard comparison operators - they work correctly:

```python
price1 = Decimal("150.50")
price2 = Decimal("150.51")

assert price1 < price2  # ✅ Works correctly
assert price1 != price2  # ✅ Works correctly
```

### Q: What if my database returns float prices?

**A**: Convert immediately after retrieving:

```python
# From database
db_price = 150.50  # float

# Convert to Decimal immediately
price = Decimal(str(db_price))
```

### Q: Do I need to update all my type hints?

**A**: Yes, for any function that uses `get_current_prices()` or passes prices around:

```python
# Before
def calculate_value(prices: dict[str, float]) -> float: ...

# After
def calculate_value(prices: dict[str, Decimal | None]) -> Decimal: ...
```

---

## Checklist for Migration

- [ ] Update all calls to `get_current_prices()` to handle `Decimal | None`
- [ ] Add explicit None checks for all price values
- [ ] Convert all float arithmetic to Decimal arithmetic
- [ ] Update type annotations to use `Decimal` instead of `float`
- [ ] Update tests to verify None handling
- [ ] Add `correlation_id` to adapter initialization (optional but recommended)
- [ ] Run mypy/type checker to catch any missed conversions
- [ ] Review all calculations to ensure no float mixing

---

## Current Usage Analysis

**Good News**: As of version 2.9.1, `get_current_prices()` is **NOT** currently called anywhere in the `strategy_v2` module, so there are zero production impacts from this breaking change.

**Future Usage**: When you do need to use `get_current_prices()`, follow this migration guide to ensure correct implementation from the start.

---

## Support

For questions or issues with migration:
1. Review the audit report: `docs/audits/market_data_adapter_audit_2025-01-05.md`
2. Check test examples: `tests/strategy_v2/adapters/test_market_data_adapter.py`
3. Review Copilot instructions: `.github/copilot-instructions.md`

---

**Document Version**: 1.0  
**Last Updated**: 2025-01-05  
**Status**: Active
