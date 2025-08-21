# Fix Failing pytest Suite - Strategy Engine Constructor and Method Signature Issues

## Problem Summary

The test suite is currently failing with **18 failed tests and 14 errors** due to constructor and method signature mismatches in our strategy engines. We need to determine whether the tests are incorrect or if our code has breaking changes that need to be fixed.

## Error Categories

### 1. Missing Required Constructor Arguments (14 errors + 7 failures)

**Strategy Engines Affected:**
- `NuclearTypedEngine` (8 instances)
- `TypedKLMStrategyEngine` (13 instances)

**Error Pattern:**
```
TypeError: NuclearTypedEngine.__init__() missing 1 required positional argument: 'market_data_port'
TypeError: TypedKLMStrategyEngine.__init__() missing 1 required positional argument: 'market_data_port'
```

**Affected Test Files:**
- `tests/contracts/test_klm_strategy_parity.py` (7 failures)
- `tests/contracts/test_nuclear_strategy_parity.py` (4 failures)
- `tests/unit/domain/strategies/test_strategy_error_handling.py` (9 errors)
- `tests/performance/conftest.py` (5 errors)

### 2. Missing Method Arguments (6 failures)

**Strategy Engine Affected:**
- `TECLStrategyEngine.generate_signals()`

**Error Pattern:**
```
TypeError: TECLStrategyEngine.generate_signals() missing 1 required positional argument: 'now'
```

**Affected Test Files:**
- `tests/contracts/test_tecl_strategy_parity.py` (6 failures)
- `tests/performance/test_strategy_performance.py` (1 failure)

## Root Cause Analysis COMPLETE ✅

**INVESTIGATION COMPLETE**: The issue is that legacy and typed strategy implementations have diverged constructor signatures during the Typed Domain V2 migration:

- **Legacy strategies**: Take `data_provider` parameter (e.g., `KLMStrategyEnsemble(data_provider=...)`)
- **Typed strategies**: Take `market_data_port` parameter (e.g., `TypedKLMStrategyEngine(market_data_port=...)`)

The parity tests were written when signatures matched, but the typed domain migration changed the typed strategy constructors without updating the tests. This is confirmed by examining:
1. `typed_strategy_manager.py` - shows all typed engines constructed with `market_data_port`
2. Legacy strategy files - show constructors taking `data_provider` parameter
3. Test failures - all missing the required `market_data_port` parameter

## Investigation Tasks ✅ COMPLETE

### ✅ Phase 1: Code Inspection COMPLETE
- ✅ **`NuclearTypedEngine.__init__()`**: Requires `market_data_port` parameter (confirmed in `typed_strategy_manager.py`)
- ✅ **`TypedKLMStrategyEngine.__init__()`**: Requires `market_data_port` parameter (confirmed in `typed_strategy_manager.py`)
- ✅ **`TECLStrategyEngine.generate_signals()`**: Requires `now` parameter (method signature analysis needed)
- ✅ **These changes are intentional**: Part of Typed Domain V2 migration - typed strategies use `MarketDataPort` protocol

### ✅ Phase 2: Test Pattern Analysis COMPLETE
- ✅ **Successful patterns**: `typed_strategy_manager.py` shows proper construction with `self.market_data_port`
- ✅ **Factory usage**: Typed strategies should be constructed through `TypedStrategyManager`
- ✅ **Legacy vs Typed**: Different constructor patterns are expected - not a bug

### ✅ Phase 3: Parity Test Validation COMPLETE
- ✅ **Root issue**: Parity tests try to construct both legacy and typed with same parameters
- ✅ **Fix needed**: Tests must handle different constructor signatures for legacy vs typed
- ✅ **Pattern**: Similar to `test_data_provider_parity.py` which was skipped due to architectural divergence

## IMPLEMENTATION PLAN ✅ IN PROGRESS

### ✅ 1. Update Strategy Parity Tests (Priority: HIGH)
- ✅ **Fixed `base_strategy_parity.py`** to handle different constructor signatures for legacy vs typed
- ✅ **Updated KLM parity test** to pass `market_data_port` to constructor and use correct `generate_signals` signature
- ✅ **Updated Nuclear parity test** to pass `market_data_port` to constructor (fixed all 4 instances)
- ✅ **Updated TECL parity test** to pass `market_data_port` correctly and add missing `now` parameter to `generate_signals`

### ✅ 2. Fix Method Signatures (Priority: HIGH)
- ✅ **Fixed KLM `generate_signals()` call** - removed incorrect `market_data_port` parameter
- ✅ **Fixed TECL `generate_signals()` call** - added missing `now` parameter
- ✅ **Verified actual method signatures** in strategy engine implementations

### 🔄 3. Testing Results (✅ MAJOR PROGRESS)
- ✅ **TECL strategy**: ALL 6 TESTS PASSING! 🎉
  - ✅ `test_flag_switching_basic_functionality`
  - ✅ `test_numerical_precision_with_decimals`
  - ✅ `test_signal_parity_with_feature_flag_off`
  - ✅ `test_signal_parity_with_feature_flag_on`
  - ✅ `test_bull_market_scenario_parity`
  - ✅ `test_portfolio_allocation_scenario_parity`

- ✅ **Base parity tests**: Both KLM and Nuclear base tests passing
  - ✅ `test_flag_switching_basic_functionality`
  - ✅ `test_numerical_precision_with_decimals`

- 🔄 **Additional fixes applied**:
  - ✅ **Fixed Nuclear `generate_signals()` calls** - removed incorrect `market_data_port` parameter in 4 test methods
  - ✅ **Fixed KLM `create_typed_engine()` calls** - added missing `market_data_port` parameter in 5 test methods

**Current Status**:
- **Before fixes**: 17 collected, 9 failed, 8 passed
- **After fixes**: Testing in progress - expect significant improvement
- **Expected Result**: Should fix majority of the 32 originally failing tests

**Impact**: These fixes address the core constructor and method signature mismatches that were causing the bulk of test failures in the GitHub issue.## Specific Files Needing Investigation

### Constructor Issues:
```
tests/contracts/test_klm_strategy_parity.py:80
tests/contracts/test_nuclear_strategy_parity.py:109,142,182,242
tests/unit/domain/strategies/test_strategy_error_handling.py:22,123
tests/performance/conftest.py:64,76
```

### Method Signature Issues:
```
tests/contracts/test_tecl_strategy_parity.py:91
tests/performance/test_strategy_performance.py:122
```

## Expected Resolution Approach: Fix Tests (Code is Correct)

**DECISION**: The code is correct - this is intentional architecture from Typed Domain V2 migration. Tests need updating.

### Implementation Steps:
1. **Update parity test base class** to handle different constructor signatures
2. **Add mock fixtures** for `MarketDataPort` protocol
3. **Update test instantiation** to pass correct parameters to legacy vs typed strategies
4. **Fix TECL method calls** to include required `now` parameter
5. **Consider skipping obsolete parity tests** that no longer provide value due to architectural divergence

### Code Changes Needed:
- Modify `base_strategy_parity.py` strategy factory methods
- Add `mock_market_data_port` fixture to conftest.py
- Update each parity test to use appropriate constructor patterns
- Update TECL test calls to match actual method signature

## Acceptance Criteria

- [ ] All 32 failing/error tests pass
- [ ] No regression in the 440 currently passing tests
- [ ] Strategy engine APIs are consistent and well-documented
- [ ] Parity tests actually verify functional equivalence between legacy and typed implementations
- [ ] Test patterns are clear and reusable for future strategy development

## Context Notes

- This appears related to the Typed Domain V2 migration (`TYPES_V2_ENABLED` feature flag)
- The parity tests were added in PR #174 to ensure legacy and typed strategy compatibility
- Current test coverage is 36% - this fix should maintain or improve coverage
- Performance tests are also affected, suggesting the issues impact production code paths

## Priority

**High** - These test failures block development and deployment confidence. The large number of failures (32 total) suggests systematic issues that need immediate resolution.
