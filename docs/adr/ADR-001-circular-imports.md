# ADR-001: Circular Import Dependencies in AlpacaManager

## Status
Accepted

## Context

The `AlpacaManager` class in `the_alchemiser/shared/brokers/alpaca_manager.py` implements a singleton facade pattern that consolidates all Alpaca API interactions. During initialization, it imports two service classes inside the `__init__` method rather than at module level:

1. **`WebSocketConnectionManager`** (lines 248-250)
2. **`MarketDataService`** (lines 264-265)

This creates **circular import dependencies** because:
- `AlpacaManager` imports `WebSocketConnectionManager` and `MarketDataService`
- These services may transitively depend on repositories that `AlpacaManager` implements
- The circular dependency is broken by deferring imports to runtime (inside `__init__`)

### Why This Occurs

The circular dependency arises from the **singleton facade pattern** design:

1. `AlpacaManager` acts as a **unified facade** implementing three domain repository interfaces:
   - `TradingRepository`
   - `MarketDataRepository`
   - `AccountRepository`

2. `AlpacaManager` delegates operations to **specialized services**:
   - `WebSocketConnectionManager` for WebSocket connection lifecycle
   - `MarketDataService` for market data operations
   - `AlpacaTradingService` for trading operations
   - `AlpacaAccountService` for account operations

3. Some services need repository implementations that `AlpacaManager` provides:
   - `MarketDataService` takes a repository implementing `MarketDataRepository`
   - `AlpacaManager` implements `MarketDataRepository` and passes `self`

This creates a **chicken-and-egg problem** at module import time:
- To define `AlpacaManager`, Python needs to import `MarketDataService`
- `MarketDataService` expects a type that implements `MarketDataRepository`
- `AlpacaManager` is that type, but hasn't finished being defined yet

### Current Implementation

```python
# In __init__ method (lines 247-266):
def __init__(self, ...):
    # ... client initialization ...
    
    # Import INSIDE __init__ to break circular dependency
    from the_alchemiser.shared.services.websocket_manager import (
        WebSocketConnectionManager,
    )
    
    self._websocket_manager = WebSocketConnectionManager(
        self._api_key, self._secret_key, paper_trading=self._paper
    )
    
    # ... other service initialization ...
    
    # Import INSIDE __init__ to break circular dependency
    from the_alchemiser.shared.services.market_data_service import MarketDataService
    
    self._market_data_service = MarketDataService(self)
```

## Decision

**We accept the circular import dependencies as an intentional architectural trade-off** for the following reasons:

### Why We Keep It (Don't Refactor)

1. **Low Risk**: The imports only occur at runtime in `__init__`, after the module and class are fully defined. There's no import-time circular dependency.

2. **Singleton Pattern Safety**: `AlpacaManager` uses singleton-per-credentials, so `__init__` runs exactly once per credential set. The deferred imports are not performance-critical.

3. **Clear Architecture**: The facade pattern is appropriate here:
   - Single entry point for all Alpaca operations
   - Clean delegation to specialized services
   - Type-safe domain repository implementations
   - Prevents scattered client usage across the codebase

4. **Refactoring Risk vs Benefit**: Eliminating the circular dependency would require:
   - Breaking the facade pattern (high architectural churn)
   - Introducing complex dependency injection (added complexity)
   - Potential performance overhead from indirection layers
   - Risk of introducing bugs in critical trading path
   - **Not justified for a pattern that works safely**

5. **Precedent**: This pattern is common in Python for singleton facades and managers, and is explicitly supported by Python's import system.

### Constraints and Requirements

To maintain safety, the following constraints MUST be observed:

1. **Import Location**: Deferred imports MUST remain inside `__init__`, never at module level
2. **Import Order**: Services must be imported in dependency order (least dependent first)
3. **No Module-Level Side Effects**: Imported modules must not execute code at import time that depends on `AlpacaManager`
4. **Documentation**: This ADR and inline comments must be maintained
5. **Testing**: Singleton behavior and service delegation must have comprehensive tests

## Consequences

### Positive

- ✅ **Clean Architecture**: Maintains single-responsibility and separation of concerns
- ✅ **Type Safety**: Full type checking with mypy and proper protocol implementation
- ✅ **Testability**: Services can be tested independently with mocked dependencies
- ✅ **Maintainability**: Clear delegation pattern is easy to understand and extend
- ✅ **Performance**: No runtime overhead (imports happen once per credential set)

### Negative

- ⚠️ **Import Complexity**: Developers must understand why imports are inside `__init__`
- ⚠️ **Potential Pitfall**: Adding module-level code that depends on `AlpacaManager` in imported services would break imports
- ⚠️ **Refactoring Constraint**: Services cannot be moved to top-level imports without architectural changes

### Mitigation

1. **Documentation**: This ADR and inline comments explain the rationale
2. **Code Review**: PRs touching `AlpacaManager` or related services must verify import safety
3. **Testing**: Comprehensive tests verify singleton behavior and delegation correctness
4. **Linting**: Import order checker enforces correct ordering of non-circular imports

## Alternatives Considered

### Alternative 1: Dependency Injection Container
**Rejected**: Adds significant complexity for minimal benefit. Python doesn't have built-in DI, requiring third-party frameworks or custom implementation.

### Alternative 2: Break Facade Pattern
**Rejected**: Would scatter Alpaca client creation across the codebase, losing centralized management and increasing connection management complexity.

### Alternative 3: Protocol-Only Dependencies
**Rejected**: Services need concrete implementations at runtime. Moving to pure protocols would require additional indirection layers and factory complexity.

### Alternative 4: Lazy Property Loading
**Rejected**: Similar to current approach but more implicit. Current explicit imports in `__init__` are clearer.

## References

- **Implementation**: `the_alchemiser/shared/brokers/alpaca_manager.py` (lines 247-266)
- **Related Documentation**: 
  - `docs/WEBSOCKET_ARCHITECTURE.md` - Documents WebSocket management patterns
  - `docs/file_reviews/FILE_REVIEW_alpaca_manager.md` - Financial-grade audit report
- **Python Import System**: [PEP 302 - New Import Hooks](https://www.python.org/dev/peps/pep-0302/)
- **Design Patterns**: Gamma et al., "Design Patterns" - Facade Pattern (pg 185)

## Notes

- **Review Date**: 2025-10-13
- **Next Review**: 2025-Q2 (or when refactoring facade pattern)
- **Related Issues**: Josh-moreton/alchemiser-quant#2203 (this implementation)
- **Related PRs**: Josh-moreton/alchemiser-quant#2202 (high-priority security fixes)

---

**Decision made by**: Architecture Team  
**Date**: 2025-10-13  
**Supersedes**: None  
**Superseded by**: None (current)
