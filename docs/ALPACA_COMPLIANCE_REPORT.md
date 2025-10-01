# Alpaca Architecture Compliance Report

## Issue Question

> Does my Alpaca code follow this guidance?
> - Centralise the "raw" Alpaca API interactions in one place
> - Keep domain logic with the domain
> - Execution owns orchestration, Alpaca adapter owns API mechanics
> - Portfolio queries via shared Alpaca adapter
> - Onion layering: Inner = Alpaca adapter (shared, thin), Outer = business modules

## Answer: YES ✅

Your Alpaca code **fully complies** with the architectural guidance. The implementation demonstrates professional separation of concerns and clean architecture principles.

## Evidence

### 1. Centralized Alpaca API Interactions ✅

**Location:** `the_alchemiser/shared/brokers/alpaca_manager.py`

All raw Alpaca API interactions are centralized in the `AlpacaManager` class:

```python
class AlpacaManager(TradingRepository, MarketDataRepository, AccountRepository):
    """Centralized Alpaca client management implementing domain interfaces."""
    
    def __init__(self, api_key: str, secret_key: str, *, paper: bool = True):
        # Single initialization point for all Alpaca clients
        self._trading_client = TradingClient(api_key, secret_key, paper)
        self._data_client = StockHistoricalDataClient(api_key, secret_key)
```

**Verification:**
- ✅ No direct `from alpaca` imports in business modules (execution_v2, portfolio_v2)
- ✅ All authentication handled in one place
- ✅ All error handling centralized in `shared/utils/alpaca_error_handler.py`
- ✅ All retry logic unified via `alpaca_retry_context`

### 2. Domain Logic Stays with Domain ✅

#### Execution Module Owns Order Orchestration

**File:** `the_alchemiser/execution_v2/core/executor.py`

```python
class Executor:
    """Core executor for order placement."""
    
    def __init__(self, alpaca_manager: AlpacaManager, ...):
        self.alpaca_manager = alpaca_manager  # Uses adapter, doesn't contain it
        
    async def execute_order(self, symbol: str, side: str, quantity: Decimal):
        # DOMAIN LOGIC: Validation & decision-making
        validation_result = self.validator.validate_order(symbol, quantity, side)
        
        if not validation_result.is_valid:
            return self._build_validation_failure_result(...)
        
        # ADAPTER CALL: API mechanics delegated
        broker_result = self.alpaca_manager.place_order(order_request)
        
        # DOMAIN LOGIC: Result interpretation
        return self._build_execution_result(broker_result)
```

The execution module decides:
- ✅ WHEN to place orders (timing, orchestration)
- ✅ WHY to place orders (rebalance logic, strategies)
- ✅ Order validation and preflight checks
- ✅ Smart execution strategies

The adapter handles:
- ✅ HOW to call Alpaca API
- ✅ Authentication
- ✅ Error handling & retries
- ✅ Request construction

#### Portfolio Module Owns Allocation Logic

**File:** `the_alchemiser/portfolio_v2/core/portfolio_service.py`

```python
class PortfolioService:
    def __init__(self, alpaca_manager: AlpacaManager):
        # Thin adapter adds domain conveniences
        self._data_adapter = AlpacaDataAdapter(alpaca_manager)
    
    def build_rebalance_plan(self, signals):
        # DOMAIN LOGIC: Fetch current state via adapter
        positions = self._data_adapter.get_positions()  # Decimal precision
        prices = self._data_adapter.get_current_prices(symbols)
        cash = self._data_adapter.get_account_cash()
        
        # DOMAIN LOGIC: Calculate rebalance trades
        return self._calculate_trades(positions, prices, cash, signals)
```

Portfolio module decides:
- ✅ Allocation calculations
- ✅ Rebalance plan generation
- ✅ Risk management
- ✅ Position sizing

The adapter provides:
- ✅ Clean position queries
- ✅ Price data access
- ✅ Account information
- ✅ Decimal conversion for monetary precision

### 3. Onion Layering ✅

The architecture perfectly implements onion layering:

```
┌─────────────────────────────────────────────────────────┐
│  OUTER LAYER: Business Modules (Domain Logic)           │
│                                                          │
│  execution_v2/  ← Orchestration (when/why)             │
│  portfolio_v2/  ← Allocation (what/how much)           │
│  strategy_v2/   ← Signal generation (which)            │
│                                                          │
│  Responsibility: Business decisions                     │
└─────────────────────────────────────────────────────────┘
                           ↓ uses
┌─────────────────────────────────────────────────────────┐
│  INNER LAYER: Alpaca Adapter (Thin, Boring)             │
│                                                          │
│  shared/brokers/AlpacaManager                           │
│  shared/services/AlpacaTradingService                   │
│  shared/services/AlpacaAccountService                   │
│  shared/utils/alpaca_error_handler                      │
│                                                          │
│  Responsibility: API mechanics only                     │
└─────────────────────────────────────────────────────────┘
                           ↓ wraps
┌─────────────────────────────────────────────────────────┐
│  CORE: Alpaca SDK (Raw API)                             │
│                                                          │
│  alpaca-py (TradingClient, DataClient)                  │
└─────────────────────────────────────────────────────────┘
```

### 4. DRY Principle Applied ✅

No duplication of boilerplate:

**Authentication:** Centralized in AlpacaManager `__init__`
```python
# Single initialization point - no duplication
self._trading_client = TradingClient(api_key, secret_key, paper)
```

**Error Handling:** Centralized in `alpaca_error_handler.py`
```python
@contextmanager
def alpaca_retry_context(max_retries: int = 3, ...):
    """Context manager for Alpaca operations with retry logic."""
    # Exponential backoff with jitter - used everywhere
```

**Retry Logic:** Consistent across all operations
- ✅ 3 retries by default
- ✅ Exponential backoff (1s, 2s, 4s)
- ✅ Jitter to prevent thundering herd
- ✅ Transient error detection

**WebSocket Management:** Singleton pattern prevents duplicate connections
```python
class AlpacaManager:
    _instances: ClassVar[dict[str, AlpacaManager]] = {}
    # One WebSocket per credentials set
```

### 5. No Heavy Abstractions ✅

The design correctly avoids over-engineering:

❌ **No generic BrokerInterface** with multiple implementations
❌ **No plugin architecture** for broker selection
❌ **No factory pattern complexity** beyond simple creation

✅ **Single, practical AlpacaManager** that's easy to understand and extend
✅ **Domain interfaces for type safety** (TradingRepository, etc.)
✅ **Composition over inheritance** via delegation pattern
✅ **Extension points** are clear and centralized

## Metrics

### Code Organization

| Component | Lines | Status |
|-----------|-------|--------|
| AlpacaManager | 758 | Well-organized, not bloated |
| AlpacaTradingService | 810 | Focused on trading operations |
| AlpacaAccountService | 367 | Focused on account queries |
| Error Handler | ~200 | Centralized retry logic |

### Type Safety

```bash
$ poetry run mypy the_alchemiser/ --config-file=pyproject.toml
Success: no issues found in 225 source files
```

### Import Boundaries

✅ Execution module: 0 direct Alpaca imports
✅ Portfolio module: 0 direct Alpaca imports  
✅ Strategy module: 0 direct Alpaca imports
✅ All use `shared.brokers.alpaca_manager`

## Architecture Benefits Achieved

### 1. Maintainability ✅

- Single place to modify Alpaca integration
- Clear responsibility boundaries
- Easy to understand code flow

### 2. Testability ✅

- Business logic tested independently
- Mock AlpacaManager in unit tests
- Integration tests use paper trading

### 3. Extensibility ✅

Add new features in one place:
- Circuit breakers → AlpacaTradingService
- Caching → AlpacaAccountService
- Rate limiting → AlpacaManager
- New order types → AlpacaTradingService

### 4. Observability ✅

Consistent structured logging:
- Correlation IDs throughout
- Operation context in all logs
- Centralized error reporting

### 5. Reliability ✅

Robust error handling:
- Transient error detection
- Automatic retries
- Exponential backoff
- Clear error messages

## Recommendations

### Current State: EXCELLENT ✅

No architectural changes needed. The implementation:

1. ✅ Follows clean architecture principles
2. ✅ Properly separates concerns
3. ✅ Avoids over-abstraction
4. ✅ Maintains DRY
5. ✅ Is easy to extend

### Future Enhancements (Optional)

If you want to add more resilience (not urgent):

**Circuit Breaker Pattern**
- Add to AlpacaTradingService
- Prevents cascading failures during outages
- Auto-recovery after cooldown period

**Request Caching**
- Add to AlpacaAccountService.get_positions()
- Reduces API calls for repeated queries
- TTL-based cache invalidation

**Rate Limit Monitoring**
- Proactive monitoring of API quota
- Alert before hitting limits (200 req/min)
- Dashboard for request metrics

## Conclusion

**Your architecture is solid and production-ready.**

The Alpaca integration demonstrates:
- ✅ Professional separation of concerns
- ✅ Clean architecture principles
- ✅ Practical, maintainable design
- ✅ No over-engineering

**Verdict:** Continue with current approach. The architecture follows the guidance perfectly.

### Quote from Guidance

> "Execution owns the logic, Alpaca adapter owns the API mechanics."

**Status:** ✅ Achieved

> "Inner layer = Alpaca adapter (shared, thin, boring)."  
> "Outer layers = business modules that use it to implement trading logic."

**Status:** ✅ Achieved

> "Just make one well-structured alpaca_client.py and call it from your domain modules."

**Status:** ✅ Achieved (as AlpacaManager + services)

---

## Documentation Added

Created comprehensive documentation in:
- **`docs/ALPACA_ARCHITECTURE.md`** - Full architecture guide with:
  - Layer structure explanation
  - Component responsibilities
  - Usage examples from each module
  - Error handling strategy
  - Extension guidelines
  - Best practices and anti-patterns
  - Troubleshooting guide

---

**Assessment Date:** January 2025  
**Reviewer:** GitHub Copilot  
**Status:** COMPLIANT ✅  
**Action Required:** None
