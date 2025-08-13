# Complete Dependency Injection Audit & Implementation Plan

## 🔍 Executive Summary

**Current Status**: DI system is fundamentally misaligned - wrong objects provided to wrong consumers.

**Root Cause**: TradingEngine expects specialized providers implementing specific protocols, but DI container provides general-purpose objects that don't implement those protocols.

**Solution Approach**: Either extend objects to implement missing interfaces OR redesign DI wiring to provide correct object types.

---

## 📋 Consumer Interface Requirements Analysis

### 1. TradingEngine Protocol Requirements (trading_engine.py:59-120)

```python
class AccountInfoProvider(Protocol):
    def get_account_info(self) -> AccountInfo: ...

class PositionProvider(Protocol):
    def get_positions_dict(self) -> PositionsDict: ...

class PriceProvider(Protocol):
    def get_current_price(self, symbol: str) -> float: ...
    def get_current_prices(self, symbols: list[str]) -> dict[str, float]: ...
```

**Expected in DI Mode:**

- `self.account_service` → Must implement AccountInfoProvider
- `self.account_service` → Must implement PositionProvider  
- `self.account_service` → Must implement PriceProvider

### 2. Strategy Engine Data Provider Requirements

All strategy engines (Nuclear, TECL, KLM) expect:

```python
class StrategyDataProvider(Protocol):
    def get_data(self, symbol: str) -> pd.DataFrame: ...
```

**Expected for strategies:**

- `data_provider` parameter → Must implement get_data() method

### 3. TradingEngine Multi-Strategy Requirements

```python
# From _init_with_container() method:
self.data_provider = container.infrastructure.data_provider()
self.trading_client = container.infrastructure.alpaca_manager()

# Used for strategy initialization:
nuclear_strategy = NuclearSignalsGenerator(data_provider=self.data_provider)
tecl_strategy = TECLSignalGenerator(data_provider=self.data_provider) 
klm_strategy = KLMTradingBot(data_provider=self.data_provider)
```

---

## 🏗️ Current DI Container Providers

### Infrastructure Layer (infrastructure_providers.py)

```python
alpaca_manager = providers.Singleton(AlpacaManager, ...)  # ✅ Correct
data_provider = providers.Singleton(UnifiedDataProvider, ...)  # ✅ Correct

# Aliases (backward compatibility)
trading_repository = alpaca_manager  # ✅ Correct
market_data_repository = alpaca_manager  # ✅ Correct  
account_repository = alpaca_manager  # ✅ Correct
```

### Service Layer (service_providers.py)

```python
account_service = providers.Factory(AccountService, account_repository=infrastructure.account_repository)
trading_service_manager = providers.Factory(TradingServiceManager, ...)  # ❌ Problem source
```

---

## ⚠️ Critical Interface Mismatches

### Issue 1: TradingServiceManager Missing Protocol Methods

**TradingServiceManager Available Methods:**

- ✅ `get_account_summary()` → but expected `get_account_info()`
- ❌ Missing `get_positions_dict()` → has `get_position_summary()`
- ✅ `get_latest_price()` → but expected `get_current_price()`
- ❌ Missing `get_current_prices()` → has `get_multi_symbol_quotes()`

### Issue 2: Strategy Data Provider Interface

**UnifiedDataProvider:**

- ✅ `get_data(symbol: str) -> pd.DataFrame` ✅ CORRECT

**TradingServiceManager:**

- ❌ Missing `get_data()` method ❌ WRONG OBJECT

### Issue 3: Wrong Service Injection in DI Mode

**Current DI Wiring (WRONG):**

```python
# trading_engine.py:_init_with_container()
self.account_service = container.services.trading_service_manager()  # ❌ Wrong!
```

**Expected DI Wiring:**

```python
self.account_service = container.services.account_service()  # ✅ Correct
```

---

## 🎯 Solution Options

### Option A: Fix DI Container Wiring (RECOMMENDED)

**Change container to provide correct objects:**

```python
# In _init_with_container():
self.account_service = container.services.account_service()  # AccountService implements protocols
self.data_provider = container.infrastructure.data_provider()  # UnifiedDataProvider has get_data()
self.trading_client = container.infrastructure.alpaca_manager()  # AlpacaManager for trading
```

**Required Changes:**

1. **Extend AccountService** to implement missing protocol methods
2. **Update DI wiring** to use account_service instead of trading_service_manager
3. **Test interface compliance** - ensure all protocols satisfied

### Option B: Extend TradingServiceManager (NOT RECOMMENDED)

**Add missing methods to TradingServiceManager:**

- `get_account_info()` → delegate to `get_account_summary()`
- `get_positions_dict()` → delegate to position service
- `get_current_price()` → delegate to `get_latest_price()`  
- `get_current_prices()` → delegate to `get_multi_symbol_quotes()`
- `get_data()` → NEW METHOD for strategy compatibility

**Problems with this approach:**

- Bloats TradingServiceManager with inappropriate responsibilities
- Violates single responsibility principle
- Creates circular dependencies

---

## 🔧 Implementation Plan (Option A)

### Phase 1: Extend AccountService for Protocol Compliance

**File: `the_alchemiser/services/enhanced/account_service.py`**

Add missing protocol methods:

```python
def get_account_info(self) -> AccountInfo:
    """Protocol-compliant account info method."""
    summary = self.get_account_summary()
    return {
        "account_id": summary["account_id"],
        "equity": summary["equity"],
        "cash": summary["cash"],
        "buying_power": summary["buying_power"],
        # ... map all fields
    }

def get_positions_dict(self) -> PositionsDict:
    """Protocol-compliant positions method."""
    return self.account_repository.get_positions()

def get_current_price(self, symbol: str) -> float:
    """Protocol-compliant price method."""
    return self.account_repository.get_current_price(symbol)

def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
    """Protocol-compliant prices method."""
    return self.account_repository.get_current_prices(symbols)
```

### Phase 2: Fix DI Container Wiring

**File: `the_alchemiser/application/trading_engine.py`**

Update `_init_with_container()`:

```python
def _init_with_container(self, container, strategy_allocations, ignore_market_hours):
    self._container = container
    
    # Use correct service providers
    self.account_service = container.services.account_service()  # ✅ Implements protocols
    self.data_provider = container.infrastructure.data_provider()  # ✅ Has get_data()
    self.trading_client = container.infrastructure.alpaca_manager()  # ✅ Trading operations
    
    # Rest of initialization...
```

### Phase 3: Add Missing Repository Methods

**File: `the_alchemiser/services/alpaca_manager.py`**

Ensure AlpacaManager implements all required methods:

```python
def get_current_prices(self, symbols: list[str]) -> dict[str, float]:
    """Get current prices for multiple symbols."""
    # Implementation needed if missing
```

### Phase 4: Integration Testing

**Test Protocol Compliance:**

```python
def test_account_service_protocols():
    account_service = container.services.account_service()
    
    # Test AccountInfoProvider protocol
    assert hasattr(account_service, 'get_account_info')
    
    # Test PositionProvider protocol  
    assert hasattr(account_service, 'get_positions_dict')
    
    # Test PriceProvider protocol
    assert hasattr(account_service, 'get_current_price')
    assert hasattr(account_service, 'get_current_prices')
```

---

## 📊 Interface Compliance Matrix

| Consumer | Required Interface | Current DI Object | Status | Fix Required |
|----------|------------------|------------------|---------|--------------|
| TradingEngine.account_service | AccountInfoProvider | TradingServiceManager | ❌ MISMATCH | Use AccountService |
| TradingEngine.account_service | PositionProvider | TradingServiceManager | ❌ MISMATCH | Use AccountService |  
| TradingEngine.account_service | PriceProvider | TradingServiceManager | ❌ MISMATCH | Use AccountService |
| Strategy.data_provider | get_data() method | UnifiedDataProvider | ✅ CORRECT | None |
| TradingEngine.trading_client | AlpacaManager | AlpacaManager | ✅ CORRECT | None |

---

## 🚀 Next Actions

1. **PRIORITY 1**: Extend AccountService with missing protocol methods
2. **PRIORITY 2**: Update DI container wiring in TradingEngine._init_with_container()
3. **PRIORITY 3**: Test DI mode with `alchemiser trade --verbose`
4. **PRIORITY 4**: Remove TradingServiceManager from DI pipeline (use only for traditional mode)
5. **PRIORITY 5**: Add comprehensive integration tests for DI mode

---

## 📝 Implementation Checklist

- [ ] Extend AccountService to implement AccountInfoProvider protocol
- [ ] Extend AccountService to implement PositionProvider protocol  
- [ ] Extend AccountService to implement PriceProvider protocol
- [ ] Update TradingEngine._init_with_container() DI wiring
- [ ] Test all protocol methods work correctly
- [ ] Test strategy initialization with correct data_provider
- [ ] Test full trading workflow in DI mode
- [ ] Add integration tests for DI container compliance
- [ ] Update documentation with correct DI architecture

This comprehensive audit shows that the DI system needs surgical fixes to the container wiring and service interfaces, not a complete rewrite. The core architecture is sound - we just need to wire the right objects to the right consumers.
