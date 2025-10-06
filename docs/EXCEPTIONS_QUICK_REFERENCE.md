# Exception System Quick Reference

## TL;DR

**Q: Are there two parallel exception systems?**
**A: Yes, but they're not truly "parallel" - the enhanced system extends the legacy one.**

**Q: Which one should I use?**
**A: Use the LEGACY system (`shared/types/exceptions.py`) for all production code.**

---

## Import This, Not That

### ✅ DO: Use Legacy System

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

### ❌ DON'T: Use Enhanced System (Yet)

```python
# DON'T use these in production code yet
from the_alchemiser.shared.errors.enhanced_exceptions import (
    EnhancedAlchemiserError,
    EnhancedTradingError,
    EnhancedDataError,
)
```

**Why not?**: The enhanced system is incomplete and not used anywhere in production.

---

## The Two Systems

### Legacy: `shared/types/exceptions.py`
- **Status**: ✅ Active, production-ready
- **Usage**: 17 production files 
- **Coverage**: 25+ exception types
- **Features**: Basic error handling with context

### Enhanced: `shared/errors/enhanced_exceptions.py`  
- **Status**: ⚠️ Implemented but unused
- **Usage**: 0 production files
- **Coverage**: 3 exception types
- **Features**: Advanced (retry logic, severity levels, error IDs)

---

## Exception Hierarchy

```
AlchemiserError (base - from legacy)
├── All legacy exceptions (25+ types)
└── EnhancedAlchemiserError (extends base)
    ├── EnhancedTradingError
    └── EnhancedDataError
```

---

## When in Doubt

1. Import from `the_alchemiser.shared.types.exceptions`
2. Use the most specific exception type available
3. Provide context via constructor parameters
4. Check `shared/types/exceptions.py` for available types

---

## Need More Details?

See the full analysis: [docs/EXCEPTIONS_ANALYSIS.md](./EXCEPTIONS_ANALYSIS.md)
