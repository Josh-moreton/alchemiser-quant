# Any Usage Refinement - Implementation Summary

## Overview

Successfully implemented refined Any usage patterns across the Alchemiser codebase, addressing issue #352 by replacing unsafe cases and justifying necessary dynamic typing.

## Key Accomplishments

### ✅ Interface Stability Maintained
- **AccountRepository.get_account()** already correctly returns `dict[str, Any] | None`
- **OrderExecutionResultDTO** used consistently throughout execution paths
- No harmful interface drift found from PR #355 - interfaces were already correct

### ✅ Created Type-Safe Protocols
**OrderLikeProtocol** (`shared/protocols/order_like.py`):
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

Applied to `normalize_order_details()` function for type-safe order mapping while maintaining flexibility.

### ✅ Fixed Type Mismatches
- **SmartExecution config**: `config: Any` → `config: ExecutionConfig | None`
- Proper type annotation for legacy config parameter with deprecation note

### ✅ Added Comprehensive Justifications
Added `# noqa: ANN401` comments with clear rationales for all justified Any usage:

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

### ✅ Created Comprehensive Documentation
1. **`docs/types_any_inventory.md`** - Detailed classification of all Any usage
2. **`docs/any_usage_guidelines.md`** - Guidelines for acceptable Any patterns

## Classification Results

### Category A: Justified Dynamic Boundaries (Kept with noqa)
- External SDK objects (Alpaca trading client, order objects)
- Decorator passthroughs (*args, **kwargs)
- Value normalization utilities 
- Repository protocol methods

### Category B: Replaceable Types (Fixed)
- SmartExecution config typing mismatch

### Category C: Protocol Opportunities (Implemented)
- Created OrderLikeProtocol for order mapping functions

### Category D: Future Enhancements (Documented)
- Strategy signal schema tightening
- Stronger domain wrappers for external entities

## Quality Improvements

1. **Type Safety**: Significantly improved through protocols and concrete types
2. **Code Clarity**: All Any usage now has explicit justification
3. **Maintainability**: Clear guidelines for future Any usage decisions
4. **Developer Experience**: Better IDE support through protocols

## Testing Results

- ✅ MyPy passes on all modified files
- ✅ All ANN401 violations either fixed or justified with noqa comments
- ✅ No breaking changes to existing interfaces
- ✅ OrderLikeProtocol provides type safety while maintaining flexibility

## Files Modified

1. `the_alchemiser/execution/strategies/smart_execution.py` - Fixed config typing, added noqa comments
2. `the_alchemiser/execution/mappers/core_execution_mappers.py` - Added protocol, noqa comments
3. `the_alchemiser/execution/mappers/broker_integration_mappers.py` - Added noqa comments
4. `the_alchemiser/shared/protocols/repository.py` - Added noqa comments
5. `the_alchemiser/strategy/registry/strategy_registry.py` - Added noqa comments
6. `the_alchemiser/shared/protocols/order_like.py` - Created new protocol

## Compliance Status

- **ANN401 Rule**: All violations either resolved or justified with noqa
- **Interface Stability**: No breaking changes introduced
- **Type Safety**: Improved through protocols and concrete types
- **Documentation**: Comprehensive guidelines and inventory created

## Acceptance Criteria - All Met ✅

- [x] Inventory committed (docs/types_any_inventory.md)
- [x] Interface drift checked (none found - already correct)
- [x] Protocols implemented & adopted (OrderLikeProtocol)
- [x] Mapping/tracking attr-defined mypy errors eliminated
- [x] Order execution returns unified DTO (already consistent)
- [x] SmartExecution config type mismatch resolved
- [x] All `object` placeholders addressed (none found)
- [x] mypy: 0 errors on modified files; Ruff: ANN401 only with justified noqa
- [x] Guidelines doc added (docs/any_usage_guidelines.md)

This implementation provides a sustainable foundation for type safety while maintaining the necessary flexibility at system boundaries.