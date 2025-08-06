# Typing Migration Plan - The Alchemiser Trading System

## Overview

This document outlines a comprehensive plan to complete the type safety migration for The Alchemiser trading system. The codebase currently has 50+ TODO comments related to typing across different phases, indicating partial implementation of a structured type system.

## Current State Analysis

### Existing Type Infrastructure
- ✅ **Core Types Defined**: Comprehensive type definitions in `the_alchemiser/core/types.py`
- ✅ **Phase Structure**: Well-organized phased approach with numbered TODO comments
- ✅ **MyPy Configuration**: Strict typing rules already configured in `pyproject.toml`
- ⚠️ **Partial Implementation**: Many components still use `Any` or generic dicts

### TODO Inventory by Phase

#### Phase 6: Strategy Layer Types
- **Location**: `core/trading/strategy_manager.py`
- **Issues**: 
  - `dict[StrategyType, Any]` → `dict[StrategyType, StrategySignal]`
  - Missing `StrategySignal` imports and usage
- **Files**: 1 file, 2 TODO items

#### Phase 7: Utility Functions Types
- **Location**: `utils/websocket_order_monitor.py`
- **Issues**: 
  - Missing `WebSocketResult` return types
  - Function signature improvements needed
- **Files**: 1 file, 2 TODO items

#### Phase 9: KLM Variants Types
- **Location**: `core/trading/klm_workers/`
- **Issues**: 
  - `KLMDecision` type not imported/used
  - Multiple type ignore statements to remove
- **Files**: 2 files, 8 TODO items

#### Phase 10: Email/Reporting Types
- **Location**: `core/ui/email/`, `execution/reporting.py`
- **Issues**: 
  - Missing structured email data types
  - Generic `dict[str, Any]` usage throughout
- **Files**: 5 files, 10 TODO items

#### Phase 11: Data Layer Types
- **Location**: `core/data/`, `core/indicators/`
- **Issues**: 
  - Missing `IndicatorData`, `MarketDataPoint` usage
  - Data provider configuration types
- **Files**: 3 files, 5 TODO items

#### Phase 12: Performance/Analytics Types
- **Location**: `utils/trading_math.py`, `utils/portfolio_pnl_utils.py`
- **Issues**: 
  - Missing `PerformanceMetrics`, `BacktestResult` usage
  - Trading calculation type safety
- **Files**: 2 files, 4 TODO items

#### Phase 13: CLI Types
- **Location**: `core/ui/cli_formatter.py`
- **Issues**: 
  - Missing `CLISignalData`, `AccountInfo` usage
  - Generic display types
- **Files**: 1 file, 4 TODO items

#### Phase 14: Error Handler Types
- **Location**: `core/error_handler.py`, `core/ui/email/templates/error_report.py`
- **Issues**: 
  - Missing `ErrorDetailInfo`, `ErrorNotificationData` usage
  - Commented out imports
- **Files**: 2 files, 6 TODO items

#### Phase 15: Infrastructure Types
- **Location**: `execution/trading_engine.py`, `tracking/`
- **Issues**: 
  - Missing `TradingEngine` type definitions
  - Configuration object types
- **Files**: 3 files, 4 TODO items

## Migration Strategy

### Phase 1: Foundation Cleanup (Week 1)
**Priority: Critical**

#### 1.1 Enable All Core Type Imports
```python
# In affected files, enable these imports:
from the_alchemiser.core.types import (
    ErrorDetailInfo, ErrorNotificationData, ErrorReportSummary,
    StrategySignal, KLMDecision, WebSocketResult,
    IndicatorData, MarketDataPoint, PerformanceMetrics,
    CLISignalData, AccountInfo, BacktestResult,
    EmailReportData, TradingPlan
)
```

#### 1.2 Address Import Cycles
- Move interface definitions to separate modules if needed
- Use `TYPE_CHECKING` imports where necessary
- Create protocol definitions for complex dependencies

#### 1.3 Fix Critical Type Errors
- Replace `Any` with proper types in function signatures
- Add missing return type annotations
- Fix parameter type annotations

### Phase 2: Strategy Layer Migration (Week 1-2)
**Files: `core/trading/strategy_manager.py`, `core/trading/klm_workers/`**

#### 2.1 Strategy Manager Types
```python
# Before
def run_all_strategies(
    self,
) -> tuple[
    dict[StrategyType, Any], dict[str, float], dict[str, list[StrategyType]]
]:

# After  
def run_all_strategies(
    self,
) -> tuple[
    dict[StrategyType, StrategySignal], dict[str, float], dict[str, list[StrategyType]]
]:
```

#### 2.2 KLM Variants Migration
- Replace all `type: ignore` comments with proper `KLMDecision` types
- Update return types in evaluation methods
- Ensure proper type checking for variant results

### Phase 3: Data Layer Migration (Week 2)
**Files: `core/data/`, `core/indicators/`**

#### 3.1 Data Provider Types
```python
# Before
def get_historical_data(self, symbol: str, period: str) -> dict[str, Any]:

# After
def get_historical_data(self, symbol: str, period: str) -> list[MarketDataPoint]:
```

#### 3.2 Indicators Migration
```python
# Before
def calculate_rsi(self, prices: list[float]) -> dict[str, Any]:

# After
def calculate_rsi(self, prices: list[float]) -> IndicatorData:
```

### Phase 4: Email/Reporting Migration (Week 2-3)
**Files: `core/ui/email/`, `execution/reporting.py`**

#### 4.1 Email Template Types
```python
# Before
def build_error_report(title: str, error_message: str) -> str:

# After
def build_error_report(data: ErrorNotificationData) -> str:
```

#### 4.2 Reporting Infrastructure
```python
# Before
def create_execution_summary(engine: Any, ...) -> dict[str, Any]:

# After
def create_execution_summary(engine: TradingEngine, ...) -> ReportingData:
```

### Phase 5: Error Handler Migration (Week 3)
**Files: `core/error_handler.py`, `core/error_reporter.py`**

#### 5.1 Error Handler Types
```python
# Before
def handle_error(
    self,
    error: Exception,
    context: str,
    component: str,
    additional_data: dict[str, Any] | None = None,
) -> ErrorDetails:

# After
def handle_error(
    self,
    error: Exception,
    context: str,
    component: str,
    additional_data: ErrorDetailInfo | None = None,
) -> ErrorDetails:
```

#### 5.2 Error Reporting Integration
- Update all error reporting calls to use structured types
- Ensure proper type safety in error categorization
- Implement proper type checking for error notifications

### Phase 6: Utilities and Infrastructure (Week 3-4)
**Files: `utils/`, `execution/`, `tracking/`**

#### 6.1 Trading Math Types
```python
# Before
def calculate_position_size(...) -> float:

# After
def calculate_position_size(...) -> TradingPlan:
```

#### 6.2 WebSocket Monitor Types
```python
# Before
def _wait_for_order_completion_stream(...) -> dict[str, str]:

# After
def _wait_for_order_completion_stream(...) -> WebSocketResult:
```

### Phase 7: CLI and Display Types (Week 4)
**Files: `core/ui/cli_formatter.py`, `main.py`**

#### 7.1 CLI Formatter Migration
```python
# Before
def render_technical_indicators(
    strategy_signals: dict[Any, Any],
    console: Console | None = None,
) -> None:

# After
def render_technical_indicators(
    strategy_signals: CLISignalData,
    console: Console | None = None,
) -> None:
```

## Implementation Guidelines

### Type Safety Best Practices

#### 1. Progressive Enablement
- Start with leaf modules (no dependencies)
- Work upward through dependency tree
- Enable mypy checks incrementally

#### 2. Backward Compatibility
- Use union types during transition: `str | float`
- Provide type adapters for complex migrations
- Maintain runtime compatibility

#### 3. Error Handling
```python
# Good: Structured error handling with types
try:
    result = process_data(input_data)
except ValidationError as e:
    error_handler.handle_error(
        error=e,
        context="data_processing",
        component="data_processor",
        additional_data=ErrorDetailInfo({
            "input_data": str(input_data),
            "validation_field": e.field_name
        })
    )
```

#### 4. Type Guards and Validation
```python
def is_valid_strategy_signal(data: Any) -> TypeGuard[StrategySignal]:
    """Type guard for StrategySignal validation."""
    return (
        isinstance(data, dict) and
        "symbol" in data and
        "action" in data and
        data["action"] in ["BUY", "SELL", "HOLD"]
    )
```

### Testing Strategy

#### 1. Type Validation Tests
```python
def test_strategy_signal_type_safety():
    """Test strategy signal type validation."""
    signal = create_test_signal()
    assert isinstance(signal, dict)
    assert "symbol" in signal
    assert signal["action"] in ["BUY", "SELL", "HOLD"]
```

#### 2. MyPy Integration
- Run mypy checks in CI/CD pipeline
- Incremental mypy enabling per module
- Type coverage reporting

#### 3. Runtime Type Checking
- Use `typeguard` for critical paths
- Validate external API responses
- Type checking in development mode

## Validation and Testing

### Pre-Migration Checks
1. **Current MyPy Status**: Run `mypy the_alchemiser/` to establish baseline
2. **Test Coverage**: Ensure >90% test coverage before migration
3. **Dependency Analysis**: Map all inter-module dependencies

### Migration Validation
1. **Incremental MyPy**: Enable strict checking per module
2. **Type Coverage**: Track type annotation coverage
3. **Runtime Testing**: Comprehensive integration tests
4. **Performance Testing**: Ensure no regression in performance

### Post-Migration Verification
1. **Complete MyPy Pass**: All modules pass strict type checking
2. **Integration Tests**: All tests pass with new types
3. **Performance Benchmarks**: No performance degradation
4. **Documentation**: All types documented and examples updated

## Risk Mitigation

### High-Risk Areas
1. **Circular Imports**: Strategy manager ↔ Trading engine
2. **External APIs**: Alpaca API response types
3. **Dynamic Data**: Market data with varying structures
4. **Legacy Code**: Existing deployed systems

### Mitigation Strategies
1. **Feature Flags**: Enable new types gradually
2. **Fallback Types**: Maintain `Any` fallbacks during transition
3. **Validation Layers**: Runtime type checking at boundaries
4. **Rollback Plan**: Quick revert capability for each phase

## Success Criteria

### Technical Metrics
- [ ] Zero mypy errors with strict configuration
- [ ] >95% type annotation coverage
- [ ] All TODO comments resolved
- [ ] All tests passing

### Quality Metrics
- [ ] No runtime type errors in production
- [ ] Improved IDE experience (autocomplete, error detection)
- [ ] Better error messages and debugging
- [ ] Reduced bug reports related to type issues

### Performance Metrics
- [ ] No degradation in execution speed
- [ ] Startup time remains acceptable
- [ ] Memory usage stable or improved

## Timeline and Resources

### Estimated Timeline: 4 weeks
- **Week 1**: Foundation and Strategy Layer (Phases 1-2)
- **Week 2**: Data Layer and Email/Reporting (Phases 3-4)  
- **Week 3**: Error Handling and Utilities (Phases 5-6)
- **Week 4**: CLI, Final Testing and Documentation (Phase 7)

### Resource Requirements
- **Developer Time**: 1 full-time developer, 4 weeks
- **Testing Time**: 2-3 days per phase for validation
- **Code Review**: 1-2 days per phase
- **Documentation**: 1 week final documentation update

### Dependencies
- Complete understanding of existing type definitions
- Access to production data for validation
- Testing environment for regression testing
- CI/CD pipeline for automated type checking

## Conclusion

This typing migration plan provides a systematic approach to completing the type safety implementation in The Alchemiser trading system. By following this phased approach and maintaining strict testing standards, we can achieve full type safety while minimizing risk to the production system.

The plan addresses all 50+ TODO comments related to typing and provides a clear path to a fully typed codebase that will improve maintainability, reduce bugs, and enhance the developer experience.
