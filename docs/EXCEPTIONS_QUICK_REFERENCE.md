# Exception System Quick Reference

## TL;DR

**Q: Are there two parallel exception systems?**
**A: No - there is one active exception system in `shared/types/exceptions.py`.**

**Q: Which one should I use?**
**A: Use `shared/types/exceptions.py` for all production code.**

---

## Import This

### ✅ Use This

```python
from the_alchemiser.shared.types.exceptions import (
    AlchemiserError,           # Base exception
    OrderExecutionError,       # Trading errors
    PortfolioError,           # Portfolio errors  
    DataProviderError,        # Data errors
    ConfigurationError,       # Config errors
    ValidationError,          # Validation errors
)

# Raise exceptions as normal
raise OrderExecutionError(
    "Order failed",
    symbol="AAPL",
    order_id="order-123",
)
```

---

## The Exception System

### Active: `shared/types/exceptions.py`
- **Status**: ✅ Production-ready
- **Usage**: 17 production files 
- **Coverage**: 25+ exception types
- **Features**: Context tracking and structured logging

---

## Exception Hierarchy

```
AlchemiserError (base)
├── ConfigurationError
├── DataProviderError (MarketDataError, etc.)
├── TradingClientError (OrderExecutionError, etc.)
├── PortfolioError
├── StrategyExecutionError
└── ... (25+ types total)
```

---

## When in Doubt

1. Import from `the_alchemiser.shared.types.exceptions`
2. Use the most specific exception type available
3. Provide context via constructor parameters
4. Check `shared/types/exceptions.py` for available types

---

## Need More Details?

See the full documentation: [docs/EXCEPTIONS_ANALYSIS.md](./EXCEPTIONS_ANALYSIS.md)
