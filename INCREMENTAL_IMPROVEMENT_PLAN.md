# Incremental Alpaca Architecture Improvement Plan

## Current Reality Check

We have 47 mypy errors down from 162, and scattered Alpaca dependencies throughout the codebase. Instead of a complete nuclear redesign, we need incremental improvements that:

1. **Don't break existing functionality**
2. **Can be done in small, safe steps**
3. **Provide immediate value**
4. **Set us up for future improvements**

## Incremental Improvement Strategy

### Phase 1: Consolidation (Week 1) - LOW RISK
**Goal**: Reduce scattered Alpaca usage without changing interfaces

#### Step 1.1: Create a Simple Alpaca Manager (2 days)
Instead of full dependency injection, create one centralized class:

```python
# the_alchemiser/services/alpaca_manager.py
class AlpacaManager:
    """Centralized Alpaca client management - transitional approach."""
    
    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        self._trading_client = TradingClient(api_key, secret_key, paper=paper)
        self._data_client = StockHistoricalDataClient(api_key, secret_key)
    
    @property
    def trading_client(self) -> TradingClient:
        return self._trading_client
    
    @property
    def data_client(self) -> StockHistoricalDataClient:
        return self._data_client
    
    def get_positions(self):
        """Wrapper with consistent error handling."""
        try:
            return self._trading_client.get_all_positions()
        except Exception as e:
            logger.error(f"Failed to get positions: {e}")
            raise
    
    def place_order(self, order_request):
        """Wrapper with consistent error handling."""
        try:
            return self._trading_client.submit_order(order_request)
        except Exception as e:
            logger.error(f"Failed to place order: {e}")
            raise
    
    def get_current_price(self, symbol: str):
        """Wrapper for getting current price."""
        try:
            # Implementation here
            pass
        except Exception as e:
            logger.error(f"Failed to get price for {symbol}: {e}")
            raise
```

#### Step 1.2: Replace Direct Alpaca Imports (2 days)
Go through existing files and replace direct Alpaca client creation with AlpacaManager:

```python
# Before:
from alpaca.trading.client import TradingClient
client = TradingClient(api_key, secret_key)

# After:
from the_alchemiser.services.alpaca_manager import AlpacaManager
alpaca = AlpacaManager(api_key, secret_key)
client = alpaca.trading_client  # Backward compatible
```

#### Step 1.3: Fix Remaining mypy Errors (1 day)
Address the remaining 47 mypy errors now that we have better organization.

**Benefits**: Immediate reduction in scattered imports, better error handling, sets up for next phase.

### Phase 2: Interface Extraction (Week 2) - LOW RISK
**Goal**: Extract interfaces without changing implementations

#### Step 2.1: Create Simple Interfaces (2 days)
Create minimal interfaces that match current usage:

```python
# the_alchemiser/interfaces/trading_interface.py
from typing import Protocol

class TradingInterface(Protocol):
    """Interface matching current trading operations."""
    
    def get_positions(self): ...
    def place_order(self, order_request): ...
    def cancel_order(self, order_id: str): ...
    def get_orders(self): ...

# the_alchemiser/interfaces/market_data_interface.py
class MarketDataInterface(Protocol):
    """Interface matching current market data operations."""
    
    def get_current_price(self, symbol: str): ...
    def get_historical_data(self, symbol: str, start, end): ...
    def get_quote(self, symbol: str): ...
```

#### Step 2.2: Make AlpacaManager Implement Interfaces (1 day)
Update AlpacaManager to implement these interfaces without changing its methods.

#### Step 2.3: Update Type Hints (2 days)
Gradually update function signatures to use interfaces instead of concrete types:

```python
# Before:
def some_function(alpaca_manager: AlpacaManager):

# After:
def some_function(trading: TradingInterface):
```

**Benefits**: Better testability, type safety, preparation for dependency injection.

### Phase 3: Service Layer Introduction (Week 3) - MEDIUM RISK
**Goal**: Add service layer without removing existing code

#### Step 3.1: Create Optional Service Classes (3 days)
Create new service classes that wrap existing functionality:

```python
# the_alchemiser/services/enhanced/order_service.py
class OrderService:
    """Enhanced order service - optional upgrade."""
    
    def __init__(self, trading: TradingInterface):
        self._trading = trading
    
    def place_market_order(self, symbol: str, side: str, qty: float):
        """Type-safe market order placement."""
        # Validation
        if qty <= 0:
            raise ValueError("Quantity must be positive")
        
        # Create order request
        request = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL,
            time_in_force=TimeInForce.DAY
        )
        
        # Place order
        return self._trading.place_order(request)
```

#### Step 3.2: Optional Migration (2 days)
Start using new services in new code, keep old code working:

```python
# New code can use enhanced services:
order_service = OrderService(alpaca_manager)
order = order_service.place_market_order("AAPL", "buy", 1.0)

# Old code continues to work:
order = alpaca_manager.place_order(order_request)
```

**Benefits**: New code gets better patterns, old code keeps working, gradual migration.

### Phase 4: Validation and Safety (Week 4) - LOW RISK
**Goal**: Add validation and safety without breaking existing flows

#### Step 4.1: Add Validation Layer (2 days)
```python
# the_alchemiser/services/validation/order_validator.py
class OrderValidator:
    """Validates orders before submission."""
    
    @staticmethod
    def validate_market_order(symbol: str, side: str, quantity: float):
        """Validate market order parameters."""
        errors = []
        
        if not symbol or not symbol.isalpha():
            errors.append("Invalid symbol")
        
        if quantity <= 0:
            errors.append("Quantity must be positive")
        
        if side.lower() not in ['buy', 'sell']:
            errors.append("Side must be 'buy' or 'sell'")
        
        if errors:
            raise ValidationError("; ".join(errors))
```

#### Step 4.2: Add Safety Wrappers (2 days)
Wrap existing methods with safety checks:

```python
# Add to AlpacaManager
def place_order_safe(self, order_request, validate: bool = True):
    """Place order with optional validation."""
    if validate:
        # Add validation logic
        pass
    
    return self.place_order(order_request)
```

#### Step 4.3: Add Better Error Handling (1 day)
Standardize error handling across all Alpaca interactions.

**Benefits**: Safer operations, better error messages, optional validation.

### Phase 5: Testing Infrastructure (Week 5) - LOW RISK
**Goal**: Make testing easier without requiring it

#### Step 5.1: Create Mock-Friendly Interfaces (2 days)
Ensure all interfaces can be easily mocked:

```python
# the_alchemiser/testing/mocks.py
class MockTradingInterface:
    """Mock trading interface for testing."""
    
    def __init__(self):
        self.placed_orders = []
        self.positions = []
    
    def place_order(self, order_request):
        self.placed_orders.append(order_request)
        return MockOrder(...)
    
    def get_positions(self):
        return self.positions
```

#### Step 5.2: Add Testing Utilities (2 days)
Create utilities that make testing easier:

```python
# the_alchemiser/testing/fixtures.py
def create_test_alpaca_manager():
    """Create AlpacaManager for testing."""
    return AlpacaManager("test_key", "test_secret", paper=True)

def create_mock_position(symbol: str, qty: float):
    """Create a mock position for testing."""
    return MockPosition(symbol=symbol, qty=qty, ...)
```

#### Step 5.3: Document Testing Patterns (1 day)
Create examples of how to test with the new patterns.

**Benefits**: Easier testing, better code quality, documentation.

## Implementation Guidelines

### DO's:
1. **Keep existing code working** - Add new patterns alongside old ones
2. **Make new patterns optional** - Teams can adopt gradually
3. **Add incremental value** - Each step should provide immediate benefits
4. **Document everything** - Clear migration paths and examples
5. **Test thoroughly** - Validate each step before moving forward

### DON'Ts:
1. **Don't break existing imports** - Keep backward compatibility
2. **Don't force immediate migration** - Allow gradual adoption
3. **Don't remove old code** until everyone has migrated
4. **Don't change external interfaces** - Keep API contracts stable
5. **Don't optimize prematurely** - Focus on organization first

## Migration Example

Here's how a typical file would evolve:

### Current State:
```python
# services/some_service.py
from alpaca.trading.client import TradingClient

class SomeService:
    def __init__(self, api_key, secret_key):
        self.client = TradingClient(api_key, secret_key)
    
    def do_something(self):
        positions = self.client.get_all_positions()
        # ... business logic
```

### After Phase 1:
```python
# services/some_service.py
from the_alchemiser.services.alpaca_manager import AlpacaManager

class SomeService:
    def __init__(self, api_key, secret_key):
        self.alpaca = AlpacaManager(api_key, secret_key)
    
    def do_something(self):
        positions = self.alpaca.get_positions()  # Better error handling
        # ... business logic
```

### After Phase 2:
```python
# services/some_service.py
from the_alchemiser.interfaces.trading_interface import TradingInterface
from the_alchemiser.services.alpaca_manager import AlpacaManager

class SomeService:
    def __init__(self, trading: TradingInterface):
        self.trading = trading
    
    def do_something(self):
        positions = self.trading.get_positions()  # Testable interface
        # ... business logic

# Usage remains the same:
# service = SomeService(AlpacaManager(api_key, secret_key))
```

### After Phase 3:
```python
# services/some_service.py - Enhanced version available
from the_alchemiser.services.enhanced.position_service import PositionService
from the_alchemiser.interfaces.trading_interface import TradingInterface

class SomeService:
    def __init__(self, trading: TradingInterface):
        self.position_service = PositionService(trading)
    
    def do_something(self):
        positions = self.position_service.get_validated_positions()  # Enhanced
        # ... business logic
```

## Timeline Summary

- **Week 1**: Consolidate Alpaca usage, fix mypy errors
- **Week 2**: Extract interfaces, improve type safety
- **Week 3**: Add optional service layer
- **Week 4**: Add validation and safety features
- **Week 5**: Improve testing infrastructure

**Total**: 5 weeks of incremental improvements, each providing immediate value.

## Success Metrics

1. **mypy errors**: 47 → 0
2. **Direct Alpaca imports**: ~15 files → 1 file (AlpacaManager)
3. **Test coverage**: Add 20% more testable code
4. **Code duplication**: Reduce Alpaca-related duplication by 80%
5. **Error handling**: Standardized error handling across all operations

This approach gets us to a much better place incrementally, setting the foundation for the larger architectural improvements when we're ready.
