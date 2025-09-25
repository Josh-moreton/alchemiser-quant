# Boundary Model Migration Inventory

**Business Unit:** shared | **Status:** inventory  
**Generated:** Phase 1 of Boundary Model Standardization Migration  
**Target:** Comprehensive inventory of all boundary model classes

## Overview

This document provides a complete inventory of all boundary model classes across `shared/dto/` and `shared/schemas/` directories. Following modern Python and Pydantic v2 best practices, the goal is to consolidate all boundary models into `shared/schemas/` with descriptive, domain-relevant names (removing generic "DTO" suffixes).

## Current DTO Classes (`shared/dto/` - 20 files)

### Current Pattern: DTO Suffix Convention (To Be Removed)
Classes in `shared/dto/` currently use `*DTO` suffix naming, which will be migrated to descriptive names.

| File | Current Classes | Proposed Names | Migration Target | Description |
|------|-----------------|----------------|------------------|-------------|
| `asset_info_dto.py` | `AssetInfoDTO` | `AssetInfo` | `schemas/assets.py` | Asset information and trading characteristics |
| `ast_node_dto.py` | `ASTNodeDTO` | `ASTNode` | `schemas/dsl.py` | DSL abstract syntax tree node |
| `broker_dto.py` | `WebSocketResult`, `OrderExecutionResult` | Keep current names | `schemas/broker.py` | Broker API responses (already descriptive) |
| `consolidated_portfolio_dto.py` | `ConsolidatedPortfolioDTO` | `ConsolidatedPortfolio` | `schemas/portfolio.py` | Portfolio consolidation data |
| `execution_dto.py` | `ExecutionResult` | Keep current name | `schemas/execution.py` | Execution result data (already descriptive) |
| `execution_report_dto.py` | `ExecutedOrderDTO`, `ExecutionReportDTO` | `ExecutedOrder`, `ExecutionReport` | `schemas/execution.py` | Order execution reporting |
| `indicator_request_dto.py` | `IndicatorRequestDTO`, `PortfolioFragmentDTO` | `IndicatorRequest`, `PortfolioFragment` | `schemas/indicators.py` | Technical indicator requests |
| `lambda_event_dto.py` | `LambdaEventDTO` | `LambdaEvent` | `schemas/events.py` | AWS Lambda event handling |
| `market_bar_dto.py` | `MarketBarDTO` | `MarketBar` | `schemas/market_data.py` | Market data bars |
| `order_request_dto.py` | `OrderRequestDTO`, `MarketDataDTO` | `OrderRequest`, `MarketData` | `schemas/orders.py` | Order placement requests |
| `portfolio_state_dto.py` | `PortfolioStateDTO`, `PositionDTO`, `PortfolioMetricsDTO` | `PortfolioState`, `Position`, `PortfolioMetrics` | `schemas/portfolio.py` | Portfolio state management |
| `rebalance_plan_dto.py` | `RebalancePlanDTO`, `RebalancePlanItemDTO` | `RebalancePlan`, `RebalancePlanItem` | `schemas/portfolio.py` | Portfolio rebalancing plans |
| `result_factory.py` | Factory functions | Migrate to schemas | `schemas/common.py` | Model factory utilities |
| `signal_dto.py` | `StrategySignalDTO` | `StrategySignal` | `schemas/strategy.py` | Strategy signal data |
| `strategy_allocation_dto.py` | `StrategyAllocationDTO` | `StrategyAllocation` | `schemas/strategy.py` | Strategy allocation data |
| `technical_indicators_dto.py` | `TechnicalIndicatorDTO` | `TechnicalIndicator` | `schemas/indicators.py` | Technical indicator results |
| `trace_dto.py` | `TraceDTO` | `Trace` | `schemas/dsl.py` | DSL execution tracing |
| `trade_ledger_dto.py` | `TradeLedgerEntry`, `TradeLedgerQuery`, `PerformanceSummary`, `Lot`, `AssetType`, `TradeSide` | Keep current names | `schemas/trading.py` | Trade ledger and enums (already descriptive) |
| `trade_run_result_dto.py` | `TradeRunResultDTO`, `ExecutionSummaryDTO`, `OrderResultSummaryDTO` | `TradeRunResult`, `ExecutionSummary`, `OrderResultSummary` | `schemas/execution.py` | Trade execution results |

### Migration Summary
- **Total Files to Migrate:** 20
- **Total Classes to Rename:** ~25 (classes with DTO suffix)
- **Classes Already Descriptive:** ~10 (already follow best practices)
- **Target Location:** All models consolidated in `shared/schemas/`

## Current Schema Classes (`shared/schemas/` - 11 files)

### Current Pattern: Descriptive Names (Best Practice) 
Schema classes already use descriptive names and represent the target pattern.

| File | Primary Classes | Current Aliases (To Remove) | Status |
|------|----------------|---------------------------|--------|
| `accounts.py` | `AccountSummary`, `AccountMetrics`, `BuyingPowerResult`, `RiskMetricsResult`, `TradeEligibilityResult`, `PortfolioAllocationResult`, `EnrichedAccountSummaryView` | 7 aliases with DTO suffix | ✅ Target pattern |
| `base.py` | `Result` | `ResultDTO = Result` | ✅ Target pattern |
| `cli.py` | CLI-related schemas | None identified | ✅ Target pattern |
| `common.py` | `AllocationComparisonDTO`, `MultiStrategyExecutionResultDTO`, `MultiStrategySummaryDTO` | None (already have DTO suffix - to be renamed) | ⚠️ Need renaming |
| `enriched_data.py` | `EnrichedOrderView`, `OpenOrdersView`, `EnrichedPositionView`, `EnrichedPositionsView` | 4 aliases with DTO suffix | ✅ Target pattern |
| `errors.py` | `ErrorContextData`, `ErrorDetailInfo`, `ErrorNotificationData`, `ErrorReportSummary`, `ErrorSummaryData` | None | ✅ Target pattern |
| `execution_summary.py` | `AllocationSummary`, `StrategyPnLSummary`, `StrategySummary`, `TradingSummary`, `ExecutionSummary`, `PortfolioState` | 6 aliases with DTO suffix | ✅ Target pattern |
| `market_data.py` | `PriceResult`, `PriceHistoryResult`, `SpreadAnalysisResult`, `MarketStatusResult`, `MultiSymbolQuotesResult` | 5 aliases with DTO suffix | ✅ Target pattern |
| `operations.py` | `OperationResult`, `OrderCancellationResult`, `OrderStatusResult` | 3 aliases with DTO suffix | ✅ Target pattern |
| `reporting.py` | Email/reporting schemas | TBD | ✅ Target pattern |

### Schema Summary
- **Total Files:** 11
- **Classes Following Best Practice:** ~35+ (descriptive names)
- **Aliases to Remove:** 20+ backward compatibility aliases
- **Classes Needing Rename:** 3 (in `common.py` with DTO suffix)

## Proposed Consolidated Structure

The migration will consolidate all boundary models into `shared/schemas/` organized by domain:

```
shared/schemas/
├── __init__.py           # Central exports
├── accounts.py          # Account, AccountMetrics, BuyingPowerResult, etc.
├── assets.py            # AssetInfo (from AssetInfoDTO)
├── base.py              # Result, common base classes
├── broker.py            # WebSocketResult, OrderExecutionResult
├── common.py            # AllocationComparison, MultiStrategyExecutionResult, etc. (renamed)
├── dsl.py               # ASTNode, Trace (DSL-related)
├── errors.py            # ErrorContextData, ErrorDetailInfo, etc.
├── events.py            # LambdaEvent (from LambdaEventDTO)
├── execution.py         # ExecutionResult, ExecutedOrder, ExecutionReport, etc.
├── indicators.py        # IndicatorRequest, TechnicalIndicator, PortfolioFragment
├── market_data.py       # PriceResult, MarketBar, etc.
├── operations.py        # OperationResult, OrderCancellationResult, etc.
├── orders.py            # OrderRequest, MarketData
├── portfolio.py         # PortfolioState, Position, RebalancePlan, etc.
├── reporting.py         # Email/reporting schemas
├── strategy.py          # StrategySignal, StrategyAllocation
└── trading.py           # TradeLedgerEntry, PerformanceSummary, enums
```

## Backward Compatibility Aliases (To Be Removed)

All current aliases will be systematically removed as part of the migration:

### Current Aliases (To Be Removed)

#### From `accounts.py`:
```python
# These aliases will be removed - imports updated to use descriptive names directly
AccountSummaryDTO = AccountSummary          # Remove alias, use AccountSummary
AccountMetricsDTO = AccountMetrics          # Remove alias, use AccountMetrics  
BuyingPowerDTO = BuyingPowerResult          # Remove alias, use BuyingPowerResult
RiskMetricsDTO = RiskMetricsResult          # Remove alias, use RiskMetricsResult
TradeEligibilityDTO = TradeEligibilityResult # Remove alias, use TradeEligibilityResult
PortfolioAllocationDTO = PortfolioAllocationResult # Remove alias, use PortfolioAllocationResult
EnrichedAccountSummaryDTO = EnrichedAccountSummaryView # Remove alias, use EnrichedAccountSummaryView
```

#### From `execution_summary.py`:
```python
# These aliases will be removed - imports updated to use descriptive names directly
AllocationSummaryDTO = AllocationSummary      # Remove alias, use AllocationSummary
StrategyPnLSummaryDTO = StrategyPnLSummary    # Remove alias, use StrategyPnLSummary
StrategySummaryDTO = StrategySummary          # Remove alias, use StrategySummary
TradingSummaryDTO = TradingSummary            # Remove alias, use TradingSummary
ExecutionSummaryDTO = ExecutionSummary        # Remove alias, use ExecutionSummary
PortfolioStateDTO = PortfolioState            # Remove alias, use PortfolioState
```

#### From `market_data.py`:
```python
# These aliases will be removed - imports updated to use descriptive names directly
PriceDTO = PriceResult                        # Remove alias, use PriceResult
PriceHistoryDTO = PriceHistoryResult         # Remove alias, use PriceHistoryResult
SpreadAnalysisDTO = SpreadAnalysisResult     # Remove alias, use SpreadAnalysisResult
MarketStatusDTO = MarketStatusResult         # Remove alias, use MarketStatusResult
MultiSymbolQuotesDTO = MultiSymbolQuotesResult # Remove alias, use MultiSymbolQuotesResult
```

#### Other aliases to remove:
```python
# From enriched_data.py
EnrichedOrderDTO = EnrichedOrderView         # Remove alias, use EnrichedOrderView
OpenOrdersDTO = OpenOrdersView               # Remove alias, use OpenOrdersView
EnrichedPositionDTO = EnrichedPositionView   # Remove alias, use EnrichedPositionView
EnrichedPositionsDTO = EnrichedPositionsView # Remove alias, use EnrichedPositionsView

# From operations.py
OperationResultDTO = OperationResult         # Remove alias, use OperationResult
OrderCancellationDTO = OrderCancellationResult # Remove alias, use OrderCancellationResult
OrderStatusDTO = OrderStatusResult           # Remove alias, use OrderStatusResult

# From base.py
ResultDTO = Result                           # Remove alias, use Result

# From broker_dto.py
WebSocketResultDTO = WebSocketResult         # Remove alias, use WebSocketResult
OrderExecutionResultDTO = OrderExecutionResult # Remove alias, use OrderExecutionResult
```

## Naming Convention Analysis

### Target Pattern: Descriptive, Domain-Relevant Names

1. **✅ Best Practice Examples** (Keep these patterns):
   - `AccountSummary`, `ExecutionResult`, `TradingSummary`
   - `AllocationSummary`, `StrategyPnLSummary`
   - `PriceResult`, `MarketStatusResult`
   - `ErrorContextData`, `ErrorDetailInfo`

2. **🔄 Classes to Rename** (Remove DTO suffix):
   - `AssetInfoDTO` → `AssetInfo`
   - `ASTNodeDTO` → `ASTNode`
   - `RebalancePlanDTO` → `RebalancePlan`
   - `StrategySignalDTO` → `StrategySignal`
   - `MarketBarDTO` → `MarketBar`
   - `TechnicalIndicatorDTO` → `TechnicalIndicator`
   - `TraceDTO` → `Trace`

3. **🔄 Schema Classes Needing Rename** (Remove DTO suffix):
   - `AllocationComparisonDTO` → `AllocationComparison`
   - `MultiStrategyExecutionResultDTO` → `MultiStrategyExecutionResult`
   - `MultiStrategySummaryDTO` → `MultiStrategySummary`

## Boundary Model Documentation

### What Makes a Boundary Model

Following Pydantic v2 best practices, boundary models in `shared/schemas/` should have:

1. **Descriptive, Domain-Relevant Names**
   ```python
   # ✅ Good - descriptive and domain-focused
   class AccountSummary(BaseModel): ...
   class ExecutionResult(BaseModel): ...
   class RebalancePlan(BaseModel): ...
   
   # ❌ Avoid - generic DTO suffix
   class AccountSummaryDTO(BaseModel): ...
   class ExecutionResultDTO(BaseModel): ...
   ```

2. **Strict Pydantic v2 Configuration**
   ```python
   class AccountSummary(BaseModel):
       model_config = ConfigDict(
           strict=True,
           frozen=True,
           validate_assignment=True,
           str_strip_whitespace=True,
       )
   ```

3. **Clear Documentation of Boundary Usage**
   ```python
   class AccountSummary(BaseModel):
       """Boundary model for account data transfer between modules.
       
       Used for:
       - API responses from broker integration
       - Inter-module communication in orchestration
       - Serialization for event publishing
       """
   ```

4. **Appropriate Serialization Helpers**
   ```python
   @classmethod
   def from_dict(cls, data: dict[str, Any]) -> AccountSummary:
       """Create from dictionary data (e.g., API responses)."""
       return cls.model_validate(data)
   
   def to_dict(self) -> dict[str, Any]:
       """Serialize for transport/storage."""
       return self.model_dump()
   ```

## Migration Benefits

### Advantages of Descriptive Names
1. **Better Code Readability**: `AccountSummary` is clearer than `AccountSummaryDTO`
2. **Domain Focus**: Names reflect business concepts, not technical patterns
3. **Reduced Cognitive Overhead**: Fewer suffixes to remember
4. **Modern Python Practice**: Aligns with current Pydantic v2 conventions
5. **Import Clarity**: Single source of truth eliminates alias confusion

### Risk Mitigation
- **Comprehensive Testing**: All boundary crossings validated
- **Incremental Migration**: Gradual transition with rollback points
- **Documentation Updates**: Clear marking of boundary models
- **Import Standardization**: Consistent import paths across codebase

## Key Findings

1. **Well-Structured Foundation**: Current schema classes already follow best practices
2. **Minimal Breaking Changes**: Mostly import updates and class renames
3. **Clear Migration Path**: Consolidate into `shared/schemas/` with descriptive names
4. **Alias Removal Opportunity**: Eliminate 20+ backward compatibility aliases
5. **Import Simplification**: Single location reduces complexity

## Next Steps

This inventory provides the foundation for:
1. **Usage Analysis** - Map all import dependencies for safe migration
2. **Migration Planning** - Create phased approach for class renames and consolidation
3. **Testing Strategy** - Ensure all boundary model usage is validated
4. **Documentation Updates** - Mark boundary models and update import guidance