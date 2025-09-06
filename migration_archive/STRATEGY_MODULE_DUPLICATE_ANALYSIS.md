# Strategy Module Duplicate Analysis Report

## CLI Entry Point

- **File**: `the_alchemiser/shared/cli/cli.py`
- **Function**: `trade()` command (line ~356)
- **Entry Point Configuration**: `pyproject.toml` defines `alchemiser = "the_alchemiser.shared.cli.cli:app"`

## Execution Flow (into Strategy Module)

The execution flow for `poetry run alchemiser trade` follows this path:

1. **CLI Layer** (`shared/cli/cli.py`)
   - `trade()` function calls `main()` from `the_alchemiser.main`
   - Builds argument list and passes to main entry point

2. **Main Orchestrator** (`main.py`)
   - `TradingSystem.execute_trading()` creates `TradingExecutor`
   - Initializes dependency injection container
   - Handles top-level error boundaries

3. **Trading Executor** (`shared/cli/trading_executor.py`)
   - `TradingExecutor.run()` creates `TradingEngine` via modern bootstrap
   - Checks market hours using `is_market_open()`
   - Calls `trader.execute_multi_strategy()`

4. **Trading Engine** (`strategy/engines/core/trading_engine.py`)
   - Creates `AlpacaClient` and `SmartExecution` for order management
   - Initializes `PortfolioManagementFacade` and `RebalancingOrchestratorFacade`
   - Executes multi-strategy workflow via `execute_multi_strategy()`

5. **Strategy Module Integration Points**:
   - **TypedStrategyManager** → Manages multiple strategy engines
   - **Nuclear/TECL/KLM Strategy Engines** → Generate trading signals
   - **StrategyRegistry** → Factory for creating strategy instances
   - **Signal Mapping** → Converts signals between formats
   - **Market Data Services** → Provides price data to strategies

### Key Strategy Files in Execution Path

The following strategy module files are directly invoked during `alchemiser trade`:

- `strategy/engines/core/trading_engine.py` - Main orchestrator
- `strategy/engines/typed_strategy_manager.py` - Strategy coordination
- `strategy/engines/nuclear_typed_engine.py` - Nuclear strategy implementation
- `strategy/engines/tecl_strategy_engine.py` - TECL strategy implementation  
- `strategy/engines/typed_klm_ensemble_engine.py` - KLM ensemble strategy
- `strategy/registry/strategy_registry.py` - Strategy factory
- `strategy/mappers/strategy_signal_mapping.py` - Signal conversion
- `strategy/signals/strategy_signal.py` - Core signal types
- `strategy/schemas/strategies.py` - Strategy DTOs and schemas
- `strategy/data/market_data_service.py` - Market data access

## Duplicate / Overlapping Capabilities

### AST-Based Duplicate Detection Results

**Analysis Summary:**
- **Total Functions Analyzed**: 509
- **Total Classes Analyzed**: 93
- **Function Duplicates Found**: 194
- **Class Duplicates Found**: 20
- **Duplicate Function Names**: 68
- **Duplicate Class Names**: 10

### Critical Duplicates Within Active Execution Path

The following duplicates appear within the traced `alchemiser trade` execution path:

#### 1. Complete File Duplication - TypedStrategyManager

**100% Duplicate Implementation**:
- `/strategy/managers/typed_strategy_manager.py`
- `/strategy/engines/typed_strategy_manager.py`

**Functions Duplicated**:
- `__init__()` - Constructor
- `get_typed_strategies()` - Strategy factory
- `_create_typed_engine()` - Engine creation
- `generate_all_signals()` - Signal generation
- `_aggregate_signals()` - Signal aggregation
- `_resolve_signal_conflict()` - Conflict resolution
- `_combine_agreeing_signals()` - Signal combination
- `_select_highest_confidence_signal()` - Confidence-based selection
- `get_strategy_allocations()` - Portfolio allocation
- `get_enabled_strategies()` - Strategy filtering

**Impact**: Complete duplication of ~400 lines of critical strategy management code

#### 2. KLM Ensemble Engine Duplication

**95%+ Similar Implementation**:
- `/strategy/engines/klm_ensemble_engine.py`
- `/strategy/engines/typed_klm_ensemble_engine.py`

**Duplicate Functions**:
- `get_required_symbols()` - Symbol requirements
- `_get_market_data()` - Data retrieval
- `_calculate_indicators()` - Technical indicators
- `_evaluate_ensemble()` - Ensemble evaluation
- `_evaluate_all_variants()` - Variant analysis
- `_select_best_variant()` - Best variant selection
- `_calculate_variant_performance()` - Performance metrics
- `_build_detailed_klm_analysis()` - Analysis building
- `_convert_to_strategy_signals()` - Signal conversion
- `_calculate_confidence()` - Confidence calculation
- `_create_hold_signal()` - Hold signal creation

**Impact**: Near-complete duplication of KLM strategy logic (~600 lines)

#### 3. Strategy Signal and Position Model Duplication

**Overlapping Capabilities**:
- `/strategy/types/strategy.py`
- `/strategy/engines/models/strategy_signal_model.py`
- `/strategy/engines/models/strategy_position_model.py`

**Duplicate Methods**:
- `is_buy_signal()` / `is_sell_signal()` / `is_hold_signal()`
- `is_high_confidence()` / `confidence_level()`
- `unrealized_pnl()` / `unrealized_pnl_percentage()`
- `from_dict()` / `to_dict()`

**Impact**: Overlapping signal analysis logic across multiple files

#### 4. Error Handling Duplication

**Exact Duplicate Classes**:
- `/strategy/errors/strategy_errors.py`
- `/strategy/engines/errors/strategy_errors.py`

**Duplicate Error Classes**:
- `StrategyError` - Base strategy error
- `StrategyExecutionError` - Execution failures
- `StrategyConfigurationError` - Configuration issues
- `StrategyDataError` - Data-related errors

**Impact**: Complete duplication of error handling infrastructure

### Similarity Analysis

**High Similarity (90-100%)**:
- TypedStrategyManager files: 100% identical structure
- KLM Ensemble engines: ~95% overlapping functionality
- Error handling classes: 100% identical implementations

**Medium Similarity (80-90%)**:
- Strategy signal utility functions: ~85% similar structure
- Market data access patterns: ~80% overlapping functionality

### Cross-Module Impact Assessment

**Files Used in Actual Trade Execution**:
- ✅ `TypedStrategyManager` (both duplicates used)
- ✅ `KLM Ensemble Engine` (both versions available)
- ✅ `Strategy Signal Models` (overlapping implementations)
- ✅ `Error Handling` (duplicate error classes)
- ❌ DSL components (not in main execution path)
- ❌ Validation utilities (auxiliary functionality)

**Execution Flow Complexity**:
The presence of multiple similar implementations creates decision complexity:
- Strategy manager exists in two locations with identical functionality
- KLM engine has two nearly identical implementations
- Signal processing can use multiple overlapping approaches
- Error handling has redundant class definitions

## Summary & Recommendations

### Priority 1: Remove Exact Duplicates

**Critical Actions**:
1. **Consolidate TypedStrategyManager** - Remove one of the identical implementations
   - Keep: `/strategy/engines/typed_strategy_manager.py` (within engine module)
   - Remove: `/strategy/managers/typed_strategy_manager.py` (redundant location)

2. **Merge KLM Ensemble Engines** - Consolidate the two KLM implementations
   - Choose: `/strategy/engines/typed_klm_ensemble_engine.py` (typed version)
   - Migrate any unique features from `/strategy/engines/klm_ensemble_engine.py`

3. **Unify Error Handling** - Remove duplicate error classes
   - Keep: `/strategy/errors/strategy_errors.py` (main location)
   - Remove: `/strategy/engines/errors/strategy_errors.py` (redundant)

### Priority 2: Clarify Strategy Signal Architecture

**Signal Model Consolidation**:
- Consolidate overlapping signal methods into a single canonical implementation
- Choose between `/strategy/types/strategy.py` vs `/strategy/engines/models/`
- Establish clear separation between domain types and engine-specific models

### Priority 3: Clean Architecture

**Module Organization**:
- Establish clear boundaries between strategy engines, managers, and utilities
- Remove cross-module duplication of common functionality
- Implement shared base classes for common patterns

### Priority 4: Documentation and Testing

**Code Quality**:
- Document the chosen canonical implementations
- Add tests to prevent regression of consolidated functionality
- Establish import linting rules to prevent future duplication

### Estimated Impact

**Code Reduction Potential**:
- **Immediate**: ~1,000 lines of duplicate code can be removed
- **Functions**: 68 duplicate function names can be consolidated
- **Classes**: 10 duplicate class names can be unified
- **Maintenance**: Significant reduction in code maintenance burden

**Risk Assessment**:
- **Low Risk**: Exact duplicates can be safely removed
- **Medium Risk**: Near-duplicates may have subtle differences requiring careful analysis
- **High Risk**: Signal processing changes require thorough testing across all strategies

This analysis shows significant duplication within the strategy module, particularly in core execution paths. Consolidating these duplicates would substantially improve code maintainability and reduce the risk of inconsistent behavior across different execution paths.