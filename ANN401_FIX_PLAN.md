# ANN401 Any Type Annotations Fix Plan

**Total Errors**: 64 ANN401 violations → **46 remaining** ✅
**Goal**: Replace all `typing.Any` annotations with specific, type-safe alternatives
**Progress**: 18/64 fixed (28.1% complete)

## Recent Fixes ✅

1. **Notification Templates** (2 errors) - COMPLETED
   - `build_multi_strategy_report()` - removed `| Any` from union type
   - `build_multi_strategy_report_neutral()` - removed `| Any` from union type
   - Removed unused `Any` import

2. **CLI AlpacaManager** (1 error) - COMPLETED
   - `_display_positions(alpaca_manager: Any)` → `AlpacaManager` type
   - Added proper import for `AlpacaManager`

3. **Allocation Comparison** (1 error) - COMPLETED
   - `allocation_comparison_to_dict()` - used union type `dict[str, Any] | AllocationSummaryDTO`

4. **Alpaca SDK Integration** (14 errors) - COMPLETED ✅
   - **alpaca_utils.py**: Fixed all 8 factory functions with proper return types
     - `create_stock_bars_request()` → `StockBarsRequest`
     - `create_trading_client()` → `TradingClient`
     - `create_data_client()` → `StockHistoricalDataClient`
     - `create_stock_data_stream()` → `StockDataStream`
     - Plus 4 more functions
   - **alpaca_manager.py**: Fixed 6 critical methods with Alpaca model types
     - `trading_client()` → `TradingClient`
     - `_alpaca_order_to_execution_result(order: Any)` → `Order`
     - `get_position()` → `Position | None`
     - `place_order(order_request: Any)` → `LimitOrderRequest | MarketOrderRequest`
     - Plus 2 more functions## Overview

The ANN401 rule disallows `typing.Any` annotations to enforce proper type safety. These 64 errors fall into 8 logical groups that can be tackled systematically, starting with easy wins and progressing to more complex generic typing.

## Groups by Priority & Complexity

### 🟢 **Group 6: Notification Templates (2 errors) - EASY WINS**

**Files**: `the_alchemiser/shared/notifications/templates/multi_strategy.py`

**Current Issues**:

```python
def build_multi_strategy_report(
    result: MultiStrategyExecutionResultDTO | Any, mode: str
) -> str:

def build_multi_strategy_report_neutral(
    result: MultiStrategyExecutionResultDTO | Any, mode: str
) -> str:
```

**Solution**: Remove `| Any` from union types

```python
def build_multi_strategy_report(
    result: MultiStrategyExecutionResultDTO, mode: str
) -> str:

def build_multi_strategy_report_neutral(
    result: MultiStrategyExecutionResultDTO, mode: str
) -> str:
```

**Effort**: 5 minutes
**Risk**: Very low

---

### 🟡 **Group 1: Alpaca SDK Integration (15 errors) - HIGH IMPACT**

**Files**:

- `the_alchemiser/shared/brokers/alpaca_manager.py` (7 errors)
- `the_alchemiser/shared/brokers/alpaca_utils.py` (8 errors)

**Problem**: These use `Any` because they interface with the third-party Alpaca SDK, but proper types are available.

**Required Imports**:

```python
from alpaca.trading.client import TradingClient
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.requests import StockBarsRequest, StockLatestQuoteRequest
from alpaca.data.timeframe import TimeFrame
from alpaca.trading.stream import TradingStream
from alpaca.data.live import StockDataStream
from alpaca.trading.models import Order, Position, Account
```

**Specific Fixes**:

1. **alpaca_utils.py**:

   ```python
   # Before
   def create_stock_bars_request(**kwargs: Any) -> Any:
   def create_trading_client(api_key: str, secret_key: str, *, paper: bool = True) -> Any:

   # After
   def create_stock_bars_request(**kwargs: Any) -> StockBarsRequest:
   def create_trading_client(api_key: str, secret_key: str, *, paper: bool = True) -> TradingClient:
   ```

2. **alpaca_manager.py**:

   ```python
   # Before
   def trading_client(self) -> Any:
   def get_account(self) -> Any:
   def get_position(self, symbol: str) -> Any | None:

   # After
   def trading_client(self) -> TradingClient:
   def get_account(self) -> Account:
   def get_position(self, symbol: str) -> Position | None:
   ```

**Effort**: 30-45 minutes
**Risk**: Low (external types are well-documented)

---

### 🟡 **Group 5: DTO Mapping and Validation (8 errors) - MODERATE**

**Files**:

- `the_alchemiser/shared/dto/strategy_allocation_dto.py` (2 errors)
- `the_alchemiser/shared/utils/validation_utils.py` (1 error)
- `the_alchemiser/shared/types/exceptions.py` (2 errors)
- `the_alchemiser/shared/types/strategy_value_objects.py` (1 error)
- `the_alchemiser/shared/utils/context.py` (1 error)
- `the_alchemiser/shared/events/base.py` (1 error)

**Current Issues**:

```python
def _convert_target_weights(cls, weights_data: Any) -> dict[str, Decimal]:
def _convert_portfolio_value(cls, portfolio_value: Any) -> Decimal | None:
def validate_order_limit_price(order_type_value: str, limit_price: Any) -> None:
```

**Solutions**:

```python
# Union types for flexible input validation
def _convert_target_weights(cls, weights_data: dict[str, float | Decimal | int] | Any) -> dict[str, Decimal]:
def _convert_portfolio_value(cls, portfolio_value: float | Decimal | int | str | None) -> Decimal | None:
def validate_order_limit_price(order_type_value: str, limit_price: float | Decimal | int | None) -> None:

# For exceptions, define proper value types
class ConfigurationError(AlchemiserError):
    def __init__(
        self, message: str, config_key: str | None = None,
        config_value: str | int | float | bool | None = None
    ) -> None:
```

**Effort**: 20-30 minutes
**Risk**: Low (clear business logic)

---

### 🟡 **Group 3: Signal Orchestrator (5 errors) - DOMAIN SPECIFIC**

**File**: `the_alchemiser/orchestration/signal_orchestrator.py`

**Problem**: Uses `Any` for internal domain types that should be well-defined.

**Current Issues**:

```python
def _convert_signals_to_display_format(self, aggregated_signals: Any) -> dict[str, Any]:
def _build_consolidated_portfolio(self, aggregated_signals: Any, typed_allocations: dict[Any, float]) -> tuple[dict[str, float], list[str]]:
def _extract_signal_allocation(self, signal: Any) -> float:
```

**Investigation Needed**:

1. Check what types `aggregated_signals` actually contains
2. Look at existing `StrategySignal` and `StrategyAllocationDTO` definitions
3. Replace with proper internal types

**Solution Pattern**:

```python
from the_alchemiser.shared.dto.strategy_allocation_dto import StrategyAllocationDTO
from the_alchemiser.strategy_v2.models.signal import StrategySignal

def _convert_signals_to_display_format(self, aggregated_signals: dict[str, StrategyAllocationDTO]) -> dict[str, Any]:
def _extract_signal_allocation(self, signal: StrategySignal) -> float:
```

**Effort**: 30-40 minutes (requires domain understanding)
**Risk**: Medium (need to verify internal type contracts)

---

### 🟠 **Group 4: Strategy Engine Results (4 errors) - BUSINESS LOGIC**

**File**: `the_alchemiser/strategy_v2/engines/klm/engine.py`

**Problem**: Strategy execution results typed as `Any`.

**Current Issues**:

```python
def _extract_result_components(self, result: Any) -> tuple[str | dict[str, float], str, str]:
def _is_valid_result(self, result: Any) -> bool:
def _format_result_for_logging(self, result: Any) -> str:
```

**Investigation Needed**:

1. Understand what result formats the KLM engine returns
2. Create proper union types or result protocols

**Solution Pattern**:

```python
from typing import Protocol

class KLMResult(Protocol):
    allocation: dict[str, float]
    reasoning: str
    confidence: str

# Or union type if multiple formats exist
KLMResultType = tuple[dict[str, float], str, str] | KLMDecision | dict[str, Any]

def _extract_result_components(self, result: KLMResultType) -> tuple[str | dict[str, float], str, str]:
```

**Effort**: 45-60 minutes (requires understanding business logic)
**Risk**: Medium (complex business rules)

---

### 🟠 **Group 7: Protocols and Interfaces (3 errors) - ARCHITECTURE**

**Files**:

- `the_alchemiser/shared/protocols/repository.py` (1 error)
- `the_alchemiser/strategy_v2/core/registry.py` (1 error)
- `the_alchemiser/shared/cli/cli.py` (1 error)

**Problem**: Protocol methods use `Any` for external types.

**Current Issues**:

```python
def place_order(self, order_request: Any) -> ExecutedOrderDTO:
def __call__(self, context: Any) -> StrategyAllocationDTO:
def _display_positions(alpaca_manager: Any) -> None:
```

**Solutions**:

```python
# Create proper protocols
from typing import Protocol

class OrderRequest(Protocol):
    symbol: str
    qty: int | float
    side: str
    order_type: str

def place_order(self, order_request: OrderRequest) -> ExecutedOrderDTO:

# Or import specific types
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager
def _display_positions(alpaca_manager: AlpacaManager) -> None:
```

**Effort**: 30-40 minutes
**Risk**: Medium (affects interface contracts)

---

### 🔴 **Group 8: Utility Functions (18 errors) - COMPLEX GENERICS**

**Files**:

- `the_alchemiser/shared/utils/decorators.py` (4 errors)
- `the_alchemiser/shared/utils/error_reporter.py` (2 errors)
- `the_alchemiser/strategy_v2/indicators/indicator_utils.py` (3 errors)
- `the_alchemiser/strategy_v2/errors.py` (4 errors)
- Various others (5 errors)

**Problem**: Utility functions with flexible parameters need proper generic typing.

**Current Issues**:

```python
def translate_market_data_errors(default_return: Any = None) -> Callable[[F], F]:
def get_error_reporter(notification_manager: Any = None) -> ErrorReporter:
def get_indicator_value(data: pd.Series | pd.DataFrame, indicator_func: Callable[..., pd.Series], *args: Any, **kwargs: Any) -> float:
```

**Solutions**:

```python
from typing import TypeVar, Generic, Protocol

T = TypeVar('T')

def translate_market_data_errors(default_return: T = None) -> Callable[[F], F]:

# For notification manager, create protocol
class NotificationManager(Protocol):
    def send_notification(self, message: str) -> None: ...

def get_error_reporter(notification_manager: NotificationManager | None = None) -> ErrorReporter:

# For generic args/kwargs in decorators
P = ParamSpec('P')
R = TypeVar('R')

def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
```

**Effort**: 60-90 minutes (complex generic typing)
**Risk**: High (affects many utility functions)

---

### 🔴 **Group 2: Error Handler Decorators (9 errors) - MOST COMPLEX**

**File**: `the_alchemiser/shared/errors/error_handler.py`

**Problem**: Generic function decorators use `*args: Any, **kwargs: Any`.

**Current Issues**:

```python
def wrapper(*args: Any, **kwargs: Any) -> Any:
def create_enhanced_error(**kwargs: Any) -> EnhancedAlchemiserError:
```

**Solution**: Advanced generic typing with ParamSpec

```python
from typing import TypeVar, ParamSpec, Callable

P = ParamSpec('P')
R = TypeVar('R')

def decorator(func: Callable[P, R]) -> Callable[P, R]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        # decorator logic
        return func(*args, **kwargs)
    return wrapper
```

**Effort**: 90+ minutes (advanced typing patterns)
**Risk**: High (critical error handling code)

---

## Execution Strategy

### Phase 1: Quick Wins (15 minutes)

1. ✅ **Group 6**: Fix notification templates - simple union type cleanup

### Phase 2: High Impact (45 minutes)

2. ✅ **Group 1**: Fix Alpaca SDK types - clear external library types
3. ✅ **Group 5**: Fix DTO mapping - straightforward validation logic

### Phase 3: Domain Logic (90 minutes)

4. ✅ **Group 3**: Fix signal orchestrator - requires domain understanding
5. ✅ **Group 4**: Fix strategy engine results - business logic dependent
6. ✅ **Group 7**: Fix protocols - architectural interfaces

### Phase 4: Advanced Typing (3+ hours)

7. ✅ **Group 8**: Fix utility functions - complex generic typing
8. ✅ **Group 2**: Fix error handlers - most complex decorator patterns

## Testing Strategy

After each group:

1. Run `poetry run ruff check --select=ANN401` to verify error reduction
2. Run `poetry run mypy the_alchemiser/` to ensure no new type errors
3. Run existing tests to ensure no regressions
4. Test CLI commands: `alchemiser --help` and `alchemiser trade --help`

## Success Metrics

- **Start**: 64 ANN401 errors
- **After Phase 1**: ~62 errors (-2)
- **After Phase 2**: ~39 errors (-25)
- **After Phase 3**: ~27 errors (-12)
- **After Phase 4**: 0 errors (-27)

## Notes

- Some `Any` usage may be legitimate for truly dynamic content - evaluate case by case
- Focus on type safety without over-constraining legitimate flexibility
- Document any intentional `Any` usage with `# type: ignore[misc]` and explanation
- Consider creating custom protocols for complex external interfaces

## Progress Tracking

- [x] Group 6: Notification Templates (2 errors) - **COMPLETED** ✅
  - Fixed `build_multi_strategy_report()` and `build_multi_strategy_report_neutral()`
  - Removed `| Any` from union types
  - Removed unused `Any` import
- [x] **BONUS:** CLI AlpacaManager type (1 error) - **COMPLETED** ✅
  - Fixed `_display_positions(alpaca_manager: Any)` → `_display_positions(alpaca_manager: AlpacaManager)`
  - Added proper import
- [x] **BONUS:** Allocation comparison mapping (1 error) - **COMPLETED** ✅
  - Fixed `allocation_comparison_to_dict(allocation_comparison: Any)` with union type
- [x] Group 1: Alpaca SDK Integration (14 errors) - **COMPLETED** ✅
  - Fixed all 8 alpaca_utils.py factory functions with proper Alpaca return types
  - Fixed 6 alpaca_manager.py methods with TradingClient, Order, Position types
  - Only 1 remaining conflict due to protocol interface mismatch (get_account)
- [ ] Group 5: DTO Mapping and Validation (6 errors remaining)
- [ ] Group 3: Signal Orchestrator (5 errors)
- [ ] Group 4: Strategy Engine Results (4 errors)
- [ ] Group 7: Protocols and Interfaces (1 error remaining)
- [ ] Group 8: Utility Functions (18 errors)
- [ ] Group 2: Error Handler Decorators (9 errors)

**Total Progress**: 18/64 errors fixed (46 remaining)
