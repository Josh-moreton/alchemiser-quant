# DTO Migration Inventory

**Business Unit:** shared | **Status:** inventory  
**Generated:** Phase 1 of DTO Standardization Migration  
**Target:** Comprehensive inventory of all DTO/Schema classes

## Overview

This document provides a complete inventory of all DTO and Schema classes across `shared/dto/` and `shared/schemas/` directories, including their current naming patterns, locations, and backward compatibility relationships.

## DTO Classes (`shared/dto/` - 20 files)

### Naming Pattern: DTO Suffix Convention
All classes in `shared/dto/` follow the proper `*DTO` suffix naming convention.

| File | Primary Classes | Status | Description |
|------|----------------|--------|-------------|
| `asset_info_dto.py` | `AssetInfoDTO` | ✅ Current | Asset information data transfer |
| `ast_node_dto.py` | `ASTNodeDTO` | ✅ Current | DSL AST node representation |
| `broker_dto.py` | `WebSocketResult`, `OrderExecutionResult` | ⚠️ Mixed | Broker API responses + aliases |
| `consolidated_portfolio_dto.py` | `ConsolidatedPortfolioDTO` | ✅ Current | Portfolio consolidation data |
| `execution_dto.py` | `ExecutionResult` | ⚠️ No DTO suffix | Execution result data |
| `execution_report_dto.py` | `ExecutedOrderDTO`, `ExecutionReportDTO` | ✅ Current | Order execution reporting |
| `indicator_request_dto.py` | `IndicatorRequestDTO`, `PortfolioFragmentDTO` | ✅ Current | Technical indicator requests |
| `lambda_event_dto.py` | `LambdaEventDTO` | ✅ Current | AWS Lambda event handling |
| `market_bar_dto.py` | `MarketBarDTO` | ✅ Current | Market data bars |
| `order_request_dto.py` | `OrderRequestDTO`, `MarketDataDTO` | ✅ Current | Order placement requests |
| `portfolio_state_dto.py` | `PortfolioStateDTO`, `PositionDTO`, `PortfolioMetricsDTO` | ✅ Current | Portfolio state management |
| `rebalance_plan_dto.py` | `RebalancePlanDTO`, `RebalancePlanItemDTO` | ✅ Current | Portfolio rebalancing plans |
| `result_factory.py` | Factory functions | ✅ Current | DTO factory utilities |
| `signal_dto.py` | `StrategySignalDTO` | ✅ Current | Strategy signal data |
| `strategy_allocation_dto.py` | `StrategyAllocationDTO` | ✅ Current | Strategy allocation data |
| `technical_indicators_dto.py` | `TechnicalIndicatorDTO` | ✅ Current | Technical indicator results |
| `trace_dto.py` | `TraceDTO` | ✅ Current | DSL execution tracing |
| `trade_ledger_dto.py` | `TradeLedgerEntry`, `TradeLedgerQuery`, `PerformanceSummary`, `Lot`, `AssetType`, `TradeSide` | ✅ Current | Trade ledger and enums |
| `trade_run_result_dto.py` | `TradeRunResultDTO`, `ExecutionSummaryDTO`, `OrderResultSummaryDTO` | ✅ Current | Trade execution results |

### DTO Summary
- **Total Files:** 20
- **Total Classes:** ~35+ (including enums and sub-DTOs)
- **Naming Compliance:** 90% (18/20 files fully compliant)
- **Issues:** 2 files with naming inconsistencies

## Schema Classes (`shared/schemas/` - 11 files)

### Naming Pattern: Descriptive Names (No DTO suffix)
Schema classes use descriptive names without DTO suffixes but include backward compatibility aliases.

| File | Primary Classes | Aliases | Status |
|------|----------------|---------|--------|
| `accounts.py` | `AccountSummary`, `AccountMetrics`, `BuyingPowerResult`, `RiskMetricsResult`, `TradeEligibilityResult`, `PortfolioAllocationResult`, `EnrichedAccountSummaryView` | 7 aliases | ✅ Current |
| `base.py` | `Result` | `ResultDTO = Result` | ✅ Current |
| `cli.py` | CLI-related schemas | TBD | ✅ Current |
| `common.py` | `AllocationComparisonDTO`, `MultiStrategyExecutionResultDTO`, `MultiStrategySummaryDTO` | No aliases needed | ✅ Current |
| `enriched_data.py` | `EnrichedOrderView`, `OpenOrdersView`, `EnrichedPositionView`, `EnrichedPositionsView` | 4 aliases | ✅ Current |
| `errors.py` | `ErrorContextData`, `ErrorDetailInfo`, `ErrorNotificationData`, `ErrorReportSummary`, `ErrorSummaryData` | No aliases | ✅ Current |
| `execution_summary.py` | `AllocationSummary`, `StrategyPnLSummary`, `StrategySummary`, `TradingSummary`, `ExecutionSummary`, `PortfolioState` | 6 aliases | ✅ Current |
| `market_data.py` | `PriceResult`, `PriceHistoryResult`, `SpreadAnalysisResult`, `MarketStatusResult`, `MultiSymbolQuotesResult` | 5 aliases | ✅ Current |
| `operations.py` | `OperationResult`, `OrderCancellationResult`, `OrderStatusResult` | 3 aliases | ✅ Current |
| `reporting.py` | Email/reporting schemas | TBD | ✅ Current |

### Schema Summary
- **Total Files:** 11
- **Total Classes:** ~40+ (including nested schemas)
- **Backward Compatibility Aliases:** 25+ identified
- **Pattern:** Schema name → `SchemaNameDTO = SchemaName`

## Backward Compatibility Aliases

### Complete Alias Mapping

#### From `accounts.py`:
```python
AccountSummaryDTO = AccountSummary
AccountMetricsDTO = AccountMetrics
BuyingPowerDTO = BuyingPowerResult
RiskMetricsDTO = RiskMetricsResult
TradeEligibilityDTO = TradeEligibilityResult
PortfolioAllocationDTO = PortfolioAllocationResult
EnrichedAccountSummaryDTO = EnrichedAccountSummaryView
```

#### From `execution_summary.py`:
```python
AllocationSummaryDTO = AllocationSummary
StrategyPnLSummaryDTO = StrategyPnLSummary
StrategySummaryDTO = StrategySummary
TradingSummaryDTO = TradingSummary
ExecutionSummaryDTO = ExecutionSummary
PortfolioStateDTO = PortfolioState
```

#### From `market_data.py`:
```python
PriceDTO = PriceResult
PriceHistoryDTO = PriceHistoryResult
SpreadAnalysisDTO = SpreadAnalysisResult
MarketStatusDTO = MarketStatusResult
MultiSymbolQuotesDTO = MultiSymbolQuotesResult
```

#### From `enriched_data.py`:
```python
EnrichedOrderDTO = EnrichedOrderView
OpenOrdersDTO = OpenOrdersView
EnrichedPositionDTO = EnrichedPositionView
EnrichedPositionsDTO = EnrichedPositionsView
```

#### From `operations.py`:
```python
OperationResultDTO = OperationResult
OrderCancellationDTO = OrderCancellationResult
OrderStatusDTO = OrderStatusResult
```

#### From `base.py`:
```python
ResultDTO = Result
```

#### From `broker_dto.py`:
```python
WebSocketResultDTO = WebSocketResult
OrderExecutionResultDTO = OrderExecutionResult
```

## Naming Convention Analysis

### Current Patterns

1. **DTO Directory Pattern** (`shared/dto/`):
   - ✅ **Consistent:** `*DTO` suffix for all classes
   - ✅ **Example:** `AssetInfoDTO`, `StrategySignalDTO`, `RebalancePlanDTO`
   - ⚠️ **Exceptions:** `ExecutionResult` (should be `ExecutionResultDTO`)

2. **Schema Directory Pattern** (`shared/schemas/`):
   - ✅ **Descriptive Names:** `AccountSummary`, `ExecutionSummary`, `PriceResult`
   - ✅ **Consistent Aliasing:** All provide `*DTO` aliases for backward compatibility
   - ✅ **Clear Intent:** Schema classes represent domain concepts

### Inconsistencies Identified

1. **Mixed Naming in DTO Directory:**
   - `ExecutionResult` should be `ExecutionResultDTO`
   - Some classes in `broker_dto.py` don't follow DTO convention

2. **Duplicate Concepts:**
   - `PortfolioStateDTO` exists in both `dto/portfolio_state_dto.py` and as alias in `schemas/execution_summary.py`
   - `ExecutionSummaryDTO` exists in both locations

3. **Import Confusion:**
   - Some modules import from `dto`, others from `schemas`
   - Inconsistent usage of aliases vs. direct schema imports

## Location Mapping

### DTO Files by Business Domain

| Domain | Files | Classes |
|--------|-------|---------|
| **Execution** | `execution_dto.py`, `execution_report_dto.py`, `trade_run_result_dto.py` | 6 classes |
| **Portfolio** | `portfolio_state_dto.py`, `rebalance_plan_dto.py`, `consolidated_portfolio_dto.py` | 7 classes |
| **Strategy** | `signal_dto.py`, `strategy_allocation_dto.py` | 2 classes |
| **Market Data** | `market_bar_dto.py`, `technical_indicators_dto.py` | 2 classes |
| **Orders** | `order_request_dto.py` | 2 classes |
| **Infrastructure** | `lambda_event_dto.py`, `broker_dto.py`, `asset_info_dto.py` | 4 classes |
| **DSL** | `ast_node_dto.py`, `trace_dto.py`, `indicator_request_dto.py` | 4 classes |
| **Trading** | `trade_ledger_dto.py` | 6 classes (including enums) |
| **Utilities** | `result_factory.py` | Factory functions |

### Schema Files by Business Domain

| Domain | Files | Classes |
|--------|-------|---------|
| **Account Management** | `accounts.py` | 7 classes + 7 aliases |
| **Market Data** | `market_data.py` | 5 classes + 5 aliases |
| **Execution** | `execution_summary.py`, `operations.py` | 9 classes + 9 aliases |
| **Data Enrichment** | `enriched_data.py` | 4 classes + 4 aliases |
| **Error Handling** | `errors.py` | 5 classes |
| **Common/Shared** | `common.py`, `base.py` | 4 classes + 1 alias |
| **Reporting** | `reporting.py` | TBD classes |
| **CLI** | `cli.py` | TBD classes |

## Key Findings

1. **Clear Separation:** DTO vs Schema files serve different purposes but have overlapping concepts
2. **Backward Compatibility:** Extensive alias system exists to support migration
3. **Naming Inconsistency:** Mixed conventions between directories
4. **Import Patterns:** Multiple ways to import the same conceptual data structures
5. **Duplication Risk:** Some concepts exist in both directories

## Next Steps

This inventory forms the foundation for:
1. **Usage Analysis** - Map all imports and dependencies
2. **Migration Planning** - Create phased approach for consolidation
3. **Risk Assessment** - Identify high-impact changes
4. **Rollback Strategy** - Plan for safe migration with fallbacks