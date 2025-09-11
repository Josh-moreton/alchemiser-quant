This PR implements a targeted refinement of `typing.Any` usage across the codebase, addressing type safety concerns while preserving necessary flexibility at system boundaries.

## Problem

Previous attempts to eliminate all `Any` usage caused interface drift and mypy regressions. This PR takes a balanced approach: replace only unsafe/unjustified `Any` usages while explicitly retaining justified dynamic cases with clear rationale.

## Solution

### 🛡️ Enhanced Type Safety

**Created OrderLikeProtocol** for type-safe order mapping:
```python
@runtime_checkable
class OrderLikeProtocol(Protocol):
    @property
    def id(self) -> str | None: ...
    @property  
    def symbol(self) -> str: ...
    @property
    def qty(self) -> float | int | str | None: ...
    # ... other order attributes
```

Applied to `normalize_order_details()` function, providing IDE support and attribute validation while maintaining flexibility for different order object sources (domain entities, Alpaca SDK objects, dicts).

**Fixed SmartExecution config type mismatch:**
```python
# Before
config: Any = None

# After  
config: ExecutionConfig | None = None  # Deprecated parameter, use execution_config instead
```

### 🏗️ Protocol Organization

**Consolidated and organized protocol definitions** following architecture guidelines:

**New Generic Protocol:**
- **`shared/protocols/order_like.py`** - Created new `OrderLikeProtocol` for cross-boundary order mapping
- Provides type safety for `normalize_order_details()` while maintaining flexibility for different order sources

**Moved Existing Alpaca Protocols:**
- **`shared/protocols/alpaca.py`** - Moved existing `AlpacaOrderProtocol` and `AlpacaOrderObject` from `shared/value_objects/core_types.py`
- These protocols already existed but were in the wrong location
- Now properly organized following the shared module architecture

**Clean separation achieved:**
- **Generic protocols**: `shared/protocols/order_like.py` - for cross-boundary mapping
- **Broker-specific protocols**: `shared/protocols/alpaca.py` - for Alpaca SDK integration
- **Removed duplicates**: Cleaned up `shared/value_objects/core_types.py` by removing protocol definitions

This addresses the protocol organization concerns and ensures proper separation between generic mapping protocols and broker-specific interfaces.

### 📝 Comprehensive Justification

Added `# noqa: ANN401` comments with clear rationales for all legitimate `Any` usage:

**External SDK Objects:**
```python
def alpaca_order_to_execution_result(order: Any) -> OrderExecutionResultDTO:  # noqa: ANN401  # Alpaca SDK order object
```

**Decorator Passthroughs:**
```python
def translate_service_errors(*args: Any, **kwargs: Any) -> Any:  # noqa: ANN401  # Decorator passthrough for any function signature
```

**Value Normalization:**
```python
def normalize_monetary_precision(value: Any) -> Decimal:  # noqa: ANN401  # Handles diverse numeric types from external sources
```

### 🏗️ Interface Stability

Verified that critical interfaces were already correctly typed:
- `AccountRepository.get_account()` returns `dict[str, Any] | None` ✅
- `OrderExecutionResultDTO` used consistently throughout execution paths ✅
- No harmful interface drift from previous PRs ✅

### 📚 Documentation

Created comprehensive guidelines:
- **`docs/types_any_inventory.md`** - Complete classification of all Any usage
- **`docs/any_usage_guidelines.md`** - Guidelines for acceptable Any patterns
- **`docs/implementation_summary.md`** - Implementation details and results

## Results

- **100% ANN401 compliance** - all violations either fixed or justified
- **Zero unjustified Any usage** remaining in modified files
- **Enhanced type safety** through protocols while preserving boundary flexibility
- **No breaking changes** to existing interfaces
- **Clear maintenance path** for future Any usage decisions
- **Proper protocol organization** following shared module architecture

## Files Modified

- `execution/strategies/smart_execution.py` - Fixed config typing, added justifications
- `execution/mappers/core_execution_mappers.py` - Applied protocol, added justifications  
- `execution/mappers/broker_integration_mappers.py` - Added justifications
- `shared/protocols/repository.py` - Added justifications
- `strategy/registry/strategy_registry.py` - Added justifications
- `shared/protocols/order_like.py` - **NEW** protocol for type-safe mapping
- `shared/protocols/alpaca.py` - **NEW** consolidated location for existing Alpaca-specific protocols (moved from core_types.py)
- `shared/value_objects/core_types.py` - Removed duplicate protocols (moved to alpaca.py)

This balanced approach maintains developer velocity and boundary flexibility while significantly improving internal type safety and code clarity.

Fixes #352.