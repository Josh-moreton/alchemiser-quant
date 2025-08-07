# Deprecated Methods Removal Plan

## Overview

This document outlines the systematic removal of all deprecated methods and functions throughout The Alchemiser codebase. These methods were marked as deprecated during refactoring but remain in the code for backward compatibility. Removing them will simplify the codebase and eliminate maintenance burden.

## Deprecated Method Inventory

### 1. Order Processing Deprecated Methods

#### Location: `execution/alpaca_client.py`

**Deprecated Method**: `get_pending_orders()`
```python
def get_pending_orders(self) -> list[dict[str, Any]]:
    """Get all pending orders from Alpaca.

    DEPRECATED: This function returns raw dict structures.
    Consider using get_pending_orders_validated() for type safety.

    Returns:
        List of pending order information dictionaries.
    """
    return self.position_manager.get_pending_orders()
```

**Issues**:
- Returns raw dictionary structures instead of typed objects
- Inconsistent with newer validation patterns
- No type safety or validation
- Replaced by `get_pending_orders_validated()`

**Usage Analysis**: Used in legacy order processing workflows

**Replacement**: `get_pending_orders_validated()` which returns `list[ValidatedOrder]`

#### Location: `execution/smart_execution.py`

**Deprecated Method**: `execute_sell_orders_parallel()`
```python
def execute_sell_orders_parallel(self, sell_orders: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Execute sell orders in parallel.
    
    DEPRECATED: This function is being migrated to use ValidatedOrder types.
    Use execute_validated_orders_parallel() for new code.
    """
    try:
        from the_alchemiser.execution.order_validation import convert_legacy_orders
        
        # Convert legacy orders to validated orders with error handling
        validated_orders = convert_legacy_orders(sell_orders)
        
        # Execute using new validated order system
        return self.execute_validated_orders_parallel(validated_orders)
    except Exception as e:
        logging.error(f"Error in parallel execution, falling back to sequential: {e}")
        return self.execute_sell_orders_sequential(sell_orders)
```

**Issues**:
- Uses legacy order dictionary format
- Contains conversion overhead
- Fallback to deprecated sequential method
- Replaced by `execute_validated_orders_parallel()`

**Usage Analysis**: Used in legacy trading execution paths

**Replacement**: `execute_validated_orders_parallel(validated_orders: list[ValidatedOrder])`

### 2. Asset Management Deprecated Methods

#### Location: `utils/asset_info.py`

**Deprecated Method**: `is_likely_non_fractionable()`
```python
def is_likely_non_fractionable(self, symbol: str) -> bool:
    """Legacy method for backward compatibility.
    
    DEPRECATED: Use is_fractionable() instead for API-based results.
    
    This method uses pattern-based prediction which is less accurate
    than the API-based approach in is_fractionable().
    """
    import warnings
    warnings.warn(
        "⚠️ is_likely_non_fractionable() is deprecated, use is_fractionable() instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return self._predict_non_fractionable_fallback(symbol)

def _predict_non_fractionable_fallback(self, symbol: str) -> bool:
    """Fallback prediction when API is unavailable (mostly deprecated)."""
    # Complex pattern-based prediction logic
    # This is deprecated in favor of API-based detection
    return symbol in self._known_non_fractionable_patterns
```

**Issues**:
- Pattern-based prediction is less accurate than API calls
- Deprecated warning indicates it should be removed
- Fallback logic is no longer needed with reliable API access
- Replaced by `is_fractionable()` with real API data

**Usage Analysis**: Used in legacy order placement code

**Replacement**: `is_fractionable()` which uses Alpaca API for accurate results

### 3. Legacy Smart Execution Methods

#### Location: `execution/smart_execution.py`

**Deprecated Legacy Compatibility Methods**:
```python
# Legacy compatibility methods - delegate to new composition-based methods
def get_position_quantity(self, symbol: str) -> float:
    """Legacy compatibility wrapper for position quantity."""
    return self._position_manager.get_position_quantity(symbol)

def liquidate_position(self, symbol: str) -> bool:
    """Legacy compatibility wrapper for liquidation."""
    return self._liquidation_service.liquidate_position(symbol)

def safe_sell_execution(self, *args, **kwargs):
    """Legacy compatibility wrapper for safe sell execution."""
    return self._sell_service.safe_sell_execution(*args, **kwargs)
```

**Issues**:
- Simple delegation wrappers with no added value
- Prevent direct access to improved service methods
- Add unnecessary method call overhead
- Replaced by direct service access

**Usage Analysis**: Used in legacy trading execution code

**Replacement**: Direct access to composition services (e.g., `self._position_manager.get_position_quantity()`)

### 4. Trading Engine Legacy Methods

#### Location: `execution/trading_engine.py`

**Deprecated Method**: `get_current_positions_dict()`
```python
def get_current_positions_dict(self) -> dict[str, float]:
    """Get current positions as dictionary.
    
    This is an alias for get_positions() to maintain backward compatibility.
    DEPRECATED: Use get_positions() directly.
    """
    return self.get_positions()
```

**Issues**:
- Simple alias method with no added functionality
- Maintains unnecessary naming inconsistency
- Replaced by `get_positions()` which has the same functionality

**Usage Analysis**: Used in legacy portfolio management code

**Replacement**: `get_positions()` - direct method call

### 5. Legacy Order Conversion Functions

#### Location: `execution/order_validation.py`

**Deprecated Function**: Legacy order processing patterns
```python
def convert_legacy_orders(orders: list[dict[str, Any]]) -> list[ValidatedOrder]:
    """Convert legacy order dictionaries to ValidatedOrder instances with error handling.
    
    DEPRECATED: New code should create ValidatedOrder instances directly.
    This function exists to support migration from legacy order formats.
    """
    validated_orders = []
    for order_dict in orders:
        try:
            validated_order = ValidatedOrder.from_dict(order_dict)
            validated_orders.append(validated_order)
        except ValidationError as e:
            logging.error(f"Order validation failed: {e}")
            # Skip invalid orders rather than failing entirely
            continue
    return validated_orders
```

**Issues**:
- Conversion function only needed during migration period
- New code should create ValidatedOrder directly
- Error handling and logging add overhead
- Replaced by direct ValidatedOrder creation

**Usage Analysis**: Used in migration code and legacy order processing

**Replacement**: Direct creation of `ValidatedOrder` instances

### 6. Data Provider Legacy Patterns

#### Location: `core/data/data_provider.py` (if still exists)

**Deprecated Legacy Import Patterns**:
```python
# Legacy import compatibility
try:
    from .unified_data_provider_facade import UnifiedDataProvider as LegacyProvider
    _LEGACY_PROVIDER_AVAILABLE = True
except ImportError:
    _LEGACY_PROVIDER_AVAILABLE = False

def get_legacy_provider(*args, **kwargs):
    """DEPRECATED: Use ServiceContainer instead."""
    if _LEGACY_PROVIDER_AVAILABLE:
        return LegacyProvider(*args, **kwargs)
    else:
        raise ImportError("Legacy provider not available, use ServiceContainer")
```

**Issues**:
- Maintains dependency on deprecated facade
- Complex import handling for legacy compatibility
- Error-prone conditional import logic
- Replaced by ServiceContainer direct usage

**Usage Analysis**: Used in legacy data access patterns

**Replacement**: Direct usage of `ServiceContainer` and individual services

### 7. Configuration Legacy Methods

#### Location: Various configuration modules

**Deprecated Configuration Access Patterns**:
```python
def get_legacy_config() -> dict[str, Any]:
    """DEPRECATED: Use ConfigService instead."""
    import warnings
    warnings.warn(
        "get_legacy_config() is deprecated, use ConfigService.get_settings()",
        DeprecationWarning,
        stacklevel=2
    )
    return {
        # Legacy configuration structure
        "api_key": os.getenv("ALPACA_API_KEY"),
        "secret_key": os.getenv("ALPACA_SECRET_KEY"),
        # ... other legacy config items
    }
```

**Issues**:
- Returns untyped dictionary instead of structured configuration
- Direct environment variable access without proper abstraction
- No validation or error handling
- Replaced by `ConfigService.get_settings()`

**Usage Analysis**: Used in legacy initialization code

**Replacement**: `ConfigService.get_settings()` which returns typed `Settings` object

## Removal Execution Plan

### Phase 1: Analysis and Usage Mapping (Week 1)

**Objectives**:
- Identify all usage of deprecated methods
- Create comprehensive replacement mapping
- Assess impact and dependencies
- Plan removal order

**Tasks**:
1. **Usage Analysis** (1 day)
   ```bash
   # Search for deprecated method usage
   grep -r "get_pending_orders()" --include="*.py" .
   grep -r "is_likely_non_fractionable" --include="*.py" .
   grep -r "get_current_positions_dict" --include="*.py" .
   grep -r "convert_legacy_orders" --include="*.py" .
   ```

2. **Impact Assessment** (1 day)
   - Identify critical vs non-critical usage
   - Map dependencies between deprecated methods
   - Assess testing requirements for each change

3. **Replacement Mapping** (1 day)
   - Document exact replacements for each deprecated method
   - Create automated refactoring scripts where possible
   - Identify manual refactoring requirements

4. **Test Planning** (1 day)
   - Create test plans for each deprecated method removal
   - Identify integration test requirements
   - Plan validation procedures

### Phase 2: Order Processing Method Removal (Week 1)

**Priority**: High (affects core trading functionality)

**Methods to Remove**:
- `get_pending_orders()` → `get_pending_orders_validated()`
- `execute_sell_orders_parallel()` → `execute_validated_orders_parallel()`
- `convert_legacy_orders()` → Direct `ValidatedOrder` creation

**Steps**:
1. **Update Order Processing Code** (1.5 days)
   ```python
   # Before
   pending_orders = client.get_pending_orders()
   
   # After
   pending_orders = client.get_pending_orders_validated()
   ```

2. **Update Execution Code** (1 day)
   ```python
   # Before
   results = executor.execute_sell_orders_parallel(legacy_orders)
   
   # After
   validated_orders = [ValidatedOrder.from_dict(order) for order in legacy_orders]
   results = executor.execute_validated_orders_parallel(validated_orders)
   ```

3. **Remove Deprecated Methods** (0.5 day)
   - Delete deprecated method implementations
   - Remove import statements
   - Update documentation

**Testing Requirements**:
- Full order processing test suite
- Integration tests with real order execution
- Performance validation

### Phase 3: Asset Management Method Removal (Week 1)

**Priority**: Medium (affects order placement accuracy)

**Methods to Remove**:
- `is_likely_non_fractionable()` → `is_fractionable()`
- `_predict_non_fractionable_fallback()` → Remove entirely

**Steps**:
1. **Update Asset Checking Code** (1 day)
   ```python
   # Before
   if detector.is_likely_non_fractionable(symbol):
       # Handle non-fractionable asset
   
   # After
   if not detector.is_fractionable(symbol):
       # Handle non-fractionable asset (note: inverted logic)
   ```

2. **Update Order Placement Logic** (0.5 day)
   - Update all asset fractionability checks
   - Ensure logic inversion is handled correctly
   - Test with various asset types

3. **Remove Deprecated Methods** (0.5 day)
   - Delete deprecated method implementations
   - Remove pattern-based prediction logic
   - Clean up imports and documentation

**Testing Requirements**:
- Asset fractionability detection tests
- Order placement integration tests
- Test with both fractionable and non-fractionable assets

### Phase 4: Smart Execution Legacy Method Removal (Week 2)

**Priority**: Medium (affects execution efficiency)

**Methods to Remove**:
- `get_position_quantity()` → Direct service access
- `liquidate_position()` → Direct service access
- `safe_sell_execution()` → Direct service access

**Steps**:
1. **Update Execution Code** (1 day)
   ```python
   # Before
   quantity = executor.get_position_quantity(symbol)
   
   # After
   quantity = executor._position_manager.get_position_quantity(symbol)
   ```

2. **Update Service Access Patterns** (1 day)
   - Replace wrapper method calls with direct service access
   - Update error handling to work with service methods
   - Ensure proper service initialization

3. **Remove Legacy Wrappers** (0.5 day)
   - Delete wrapper method implementations
   - Update documentation
   - Clean up method exports

**Testing Requirements**:
- Smart execution integration tests
- Service composition validation
- Performance testing

### Phase 5: Trading Engine and Configuration Cleanup (Week 2)

**Priority**: Low (minimal functional impact)

**Methods to Remove**:
- `get_current_positions_dict()` → `get_positions()`
- `get_legacy_config()` → `ConfigService.get_settings()`
- Legacy import compatibility patterns

**Steps**:
1. **Update Position Access** (0.5 day)
   ```python
   # Before
   positions = engine.get_current_positions_dict()
   
   # After
   positions = engine.get_positions()
   ```

2. **Update Configuration Access** (1 day)
   ```python
   # Before
   config = get_legacy_config()
   api_key = config["api_key"]
   
   # After
   settings = config_service.get_settings()
   api_key = settings.alpaca_api_key
   ```

3. **Clean Up Legacy Imports** (0.5 day)
   - Remove conditional import logic
   - Update import statements throughout codebase
   - Clean up compatibility code

**Testing Requirements**:
- Configuration system tests
- Position management tests
- Import and initialization tests

### Phase 6: Data Provider Legacy Cleanup (Week 2)

**Priority**: Low (should be completed after facade removal)

**Methods to Remove**:
- `get_legacy_provider()` → Direct `ServiceContainer` usage
- Legacy data access patterns
- Facade compatibility methods

**Steps**:
1. **Verify Facade Removal Complete** (0.5 day)
   - Ensure all facade usage has been migrated
   - Verify no remaining facade dependencies
   - Confirm ServiceContainer usage throughout

2. **Remove Legacy Data Access** (0.5 day)
   ```python
   # Before
   provider = get_legacy_provider(paper_trading=True)
   
   # After
   services = ServiceContainer(paper_trading=True)
   ```

3. **Clean Up Legacy Code** (0.5 day)
   - Remove legacy provider functions
   - Clean up compatibility imports
   - Update documentation

**Testing Requirements**:
- Data access integration tests
- Service container functionality tests
- Performance validation

### Phase 7: Final Cleanup and Validation (Week 3)

**Objectives**:
- Ensure all deprecated methods are removed
- Comprehensive testing and validation
- Documentation updates
- Performance verification

**Tasks**:
1. **Deprecated Method Audit** (0.5 day)
   ```bash
   # Search for any remaining deprecated patterns
   grep -r "DEPRECATED" --include="*.py" .
   grep -r "deprecated" --include="*.py" .
   grep -r "DeprecationWarning" --include="*.py" .
   ```

2. **Comprehensive Testing** (1.5 days)
   - Full test suite execution
   - Integration testing
   - Performance validation
   - Regression testing

3. **Documentation Updates** (1 day)
   - Update API documentation
   - Remove deprecated method references
   - Update examples and tutorials
   - Create migration guide updates

**Validation Checklist**:
- [ ] No `DEPRECATED` comments remain in codebase
- [ ] No `DeprecationWarning` imports or usage
- [ ] All tests pass with deprecated methods removed
- [ ] Performance maintained or improved
- [ ] Documentation updated and accurate

## Automated Refactoring Scripts

### Script 1: Method Call Replacement
```python
#!/usr/bin/env python3
"""Automated refactoring script for deprecated method removal."""

import re
import os
from pathlib import Path

def replace_deprecated_calls(file_path: Path) -> bool:
    """Replace deprecated method calls in a file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Replace deprecated method calls
    replacements = {
        r'\.get_pending_orders\(\)': '.get_pending_orders_validated()',
        r'\.get_current_positions_dict\(\)': '.get_positions()',
        r'\.is_likely_non_fractionable\(': '.is_fractionable(',
        r'convert_legacy_orders\(': '# MANUAL: Replace with direct ValidatedOrder creation',
    }
    
    for pattern, replacement in replacements.items():
        content = re.sub(pattern, replacement, content)
    
    if content != original_content:
        with open(file_path, 'w') as f:
            f.write(content)
        return True
    return False

def main():
    """Run automated refactoring."""
    project_root = Path(__file__).parent.parent
    python_files = list(project_root.rglob("*.py"))
    
    modified_files = []
    for file_path in python_files:
        if replace_deprecated_calls(file_path):
            modified_files.append(file_path)
    
    print(f"Modified {len(modified_files)} files:")
    for file_path in modified_files:
        print(f"  {file_path}")

if __name__ == "__main__":
    main()
```

### Script 2: Import Cleanup
```python
#!/usr/bin/env python3
"""Clean up deprecated imports and compatibility code."""

import ast
import os
from pathlib import Path

def remove_deprecated_imports(file_path: Path) -> bool:
    """Remove deprecated imports from a file."""
    with open(file_path, 'r') as f:
        content = f.read()
    
    original_content = content
    lines = content.split('\n')
    
    # Remove lines containing deprecated patterns
    deprecated_patterns = [
        'from .unified_data_provider_facade import',
        'DEPRECATED:',
        'DeprecationWarning',
        'warnings.warn',
        'convert_legacy_orders',
    ]
    
    filtered_lines = []
    skip_block = False
    
    for line in lines:
        # Skip deprecated code blocks
        if any(pattern in line for pattern in deprecated_patterns):
            skip_block = True
        elif skip_block and line.strip() == '':
            skip_block = False
        elif not skip_block:
            filtered_lines.append(line)
    
    new_content = '\n'.join(filtered_lines)
    
    if new_content != original_content:
        with open(file_path, 'w') as f:
            f.write(new_content)
        return True
    return False
```

## Testing Strategy

### 1. Incremental Testing
- Test each deprecated method removal individually
- Validate functionality before and after each change
- Ensure no regressions in system behavior

### 2. Integration Testing
- Full system integration tests after each phase
- End-to-end trading workflow validation
- Performance and reliability testing

### 3. Regression Testing
- Comprehensive test suite execution
- Comparison with baseline functionality
- Performance benchmarking

### 4. Edge Case Testing
- Test error handling with new method signatures
- Validate behavior under various market conditions
- Test system resilience and fallback mechanisms

## Risk Management

### High-Risk Removals
- **Order Processing Methods**: Core trading functionality
- **Asset Fractionability Detection**: Order placement accuracy

**Mitigation**:
- Extensive testing with real market data
- Gradual rollout with monitoring
- Quick rollback procedures
- Feature flags for new vs old behavior

### Medium-Risk Removals
- **Smart Execution Wrappers**: Execution efficiency
- **Configuration Access**: System initialization

**Mitigation**:
- Performance monitoring
- Configuration validation
- Integration testing

### Low-Risk Removals
- **Simple Aliases**: No functional changes
- **Import Compatibility**: Structural changes only

**Mitigation**:
- Standard testing procedures
- Documentation updates

## Expected Benefits

### Code Quality Benefits
- **Reduced Complexity**: Fewer code paths and methods to maintain
- **Improved Consistency**: Single pattern for each operation
- **Better Type Safety**: Elimination of untyped legacy patterns
- **Cleaner APIs**: Removal of deprecated method signatures

### Performance Benefits
- **Reduced Overhead**: Elimination of wrapper methods and conversion functions
- **Optimized Execution**: Direct access to optimal implementations
- **Lower Memory Usage**: Removal of compatibility objects and caching

### Maintainability Benefits
- **Simplified Debugging**: Fewer code paths to investigate
- **Easier Enhancement**: Clear, single implementation for each feature
- **Reduced Technical Debt**: Elimination of deprecated code patterns
- **Better Documentation**: Focus on current, supported methods

## Success Criteria

### Functional Criteria
- [ ] All deprecated methods removed from codebase
- [ ] System functionality preserved
- [ ] No regressions in trading performance
- [ ] All tests pass with new implementations

### Code Quality Criteria
- [ ] No `DEPRECATED` comments remain
- [ ] No `DeprecationWarning` usage
- [ ] Consistent method signatures throughout
- [ ] Complete type safety with new patterns

### Performance Criteria
- [ ] Method call overhead reduced
- [ ] Memory usage optimized
- [ ] Execution time maintained or improved
- [ ] System responsiveness preserved

## Status Tracking

### Phase 1: Analysis and Usage Mapping
- [ ] Complete usage analysis for all deprecated methods
- [ ] Create comprehensive replacement mapping
- [ ] Assess impact and dependencies
- [ ] Plan removal order and priority

### Phase 2: Order Processing Method Removal
- [ ] Update order processing code
- [ ] Update execution code
- [ ] Remove deprecated methods
- [ ] Validate order processing functionality

### Phase 3: Asset Management Method Removal
- [ ] Update asset checking code
- [ ] Update order placement logic
- [ ] Remove deprecated methods
- [ ] Validate asset detection functionality

### Phase 4: Smart Execution Legacy Method Removal
- [ ] Update execution code
- [ ] Update service access patterns
- [ ] Remove legacy wrappers
- [ ] Validate smart execution functionality

### Phase 5: Trading Engine and Configuration Cleanup
- [ ] Update position access
- [ ] Update configuration access
- [ ] Clean up legacy imports
- [ ] Validate configuration and position management

### Phase 6: Data Provider Legacy Cleanup
- [ ] Verify facade removal complete
- [ ] Remove legacy data access
- [ ] Clean up legacy code
- [ ] Validate data access functionality

### Phase 7: Final Cleanup and Validation
- [ ] Complete deprecated method audit
- [ ] Comprehensive testing
- [ ] Documentation updates
- [ ] Final validation and performance verification

## Conclusion

Removing deprecated methods will significantly simplify The Alchemiser codebase while eliminating maintenance burden and potential confusion. The systematic approach ensures that all deprecated patterns are properly replaced with their modern equivalents while maintaining full system functionality.

This cleanup represents the final step in the code modernization process, resulting in a clean, consistent, and maintainable codebase with no legacy baggage.
