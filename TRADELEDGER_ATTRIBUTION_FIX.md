# TradeLedger Strategy Attribution Fix

## Issue Summary
The TradeLedger system was attributing all trades to "unknown" strategy instead of the specific strategy that generated them, causing loss of per-strategy performance tracking.

## Root Cause
The `ExecutionManager._record_execution_in_ledger()` method defaulted to `strategy_name = "unknown"` when `ExecutionResultDTO.metadata` lacked proper strategy information. The strategy name was being lost in the flow from strategy evaluation → portfolio planning → execution.

## Solution Implemented

### 1. Enhanced StrategyAllocationDTO
- **Added required `strategy_name` field** to ensure strategy identification at allocation creation
- **Updated field validation** to enforce non-empty strategy names
- **Breaking change** that ensures all strategy allocations are properly attributed

### 2. Updated Strategy Evaluation Flow
- **DSL Engine**: Extracts strategy name from .clj file paths (e.g., "KLM.clj" → "KLM")
- **Strategy Orchestrator**: Uses strategy_id as strategy_name for proper attribution
- **Portfolio Orchestrator**: Uses first strategy from `source_strategies` or "Consolidated"

### 3. Enhanced Portfolio Planning
- **Portfolio Planner**: Includes `strategy_name` in RebalancePlanDTO metadata from allocation
- **Analysis Handler**: Uses "PortfolioAnalysis" for external allocation comparisons

### 4. Improved Execution Attribution
- **ExecutionManager**: Prioritizes `plan.metadata['strategy_name']` over `result.metadata['strategy_name']`
- **Fallback logic**: Only uses "unknown" as last resort when no strategy information is available

## Files Modified
1. `the_alchemiser/shared/dto/strategy_allocation_dto.py` - Added strategy_name field
2. `the_alchemiser/strategy_v2/engines/dsl/dsl_evaluator.py` - Pass strategy_name through evaluation
3. `the_alchemiser/strategy_v2/engines/dsl/engine.py` - Extract strategy name from file path
4. `the_alchemiser/strategy_v2/core/orchestrator.py` - Use strategy_id as strategy_name
5. `the_alchemiser/orchestration/portfolio_orchestrator.py` - Use source_strategies for naming
6. `the_alchemiser/portfolio_v2/core/planner.py` - Include strategy_name in plan metadata
7. `the_alchemiser/portfolio_v2/handlers/portfolio_analysis_handler.py` - Add strategy attribution
8. `the_alchemiser/execution_v2/core/execution_manager.py` - Prioritize plan metadata

## Testing
- ✅ StrategyAllocationDTO correctly requires and validates strategy_name
- ✅ Trade ledger entries preserve strategy attribution correctly  
- ✅ No more "unknown" strategy attributions in normal execution flow
- ✅ Type checking passes (mypy)
- ✅ Linting passes (ruff)

## Impact
- **Enables** per-strategy performance diagnostics
- **Allows** reconciling strategy-configured limits vs actual executions  
- **Provides** granular grouping in reporting dashboards
- **Supports** strategy deprecation and A/B testing
- **Prevents** misallocation of fees or risk limits

## Backwards Compatibility
This is a **breaking change** for code that creates `StrategyAllocationDTO` objects, as `strategy_name` is now required. However, this ensures proper attribution and prevents the "unknown" strategy problem.

## Migration Guide
If you have code that creates `StrategyAllocationDTO`:

```python
# Before (will now fail)
allocation = StrategyAllocationDTO(
    target_weights=weights,
    correlation_id=correlation_id
)

# After (required)
allocation = StrategyAllocationDTO(
    target_weights=weights,
    correlation_id=correlation_id,
    strategy_name="YourStrategyName"  # Now required
)
```