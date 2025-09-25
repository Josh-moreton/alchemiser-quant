# DTO/Schema Migration Inventory

## Overview
This document provides a comprehensive inventory of all DTO and Schema classes in the alchemiser-quant repository as part of Phase 1 of the DTO standardization effort.

**Analysis Date**: Phase 1 Initial Assessment  
**Repository**: Josh-moreton/alchemiser-quant  
**Scope**: shared/dto/ and shared/schemas/ directories  

## Executive Summary

- **Total DTO Files**: 20 files in `shared/dto/`
- **Total Schema Files**: 11 files in `shared/schemas/`
- **Total Classes**: 62+ DTO/Schema classes
- **Backward Compatibility Aliases**: 28 identified aliases
- **Import Usage**: 130+ import statements across codebase

## 1. DTO Directory Inventory (`shared/dto/`)

### 1.1 Core DTOs with Naming Convention: `*DTO`

| File | Classes | Naming Pattern | Notes |
| --- | --- | --- | --- |
| `asset_info_dto.py` | `AssetInfoDTO` | DTO suffix | ✅ Consistent |
| `ast_node_dto.py` | `ASTNodeDTO` | DTO suffix | ✅ Consistent |
| `consolidated_portfolio_dto.py` | `ConsolidatedPortfolioDTO` | DTO suffix | ✅ Consistent |
| `execution_report_dto.py` | `ExecutedOrderDTO`, `ExecutionReportDTO` | DTO suffix | ✅ Consistent |
| `indicator_request_dto.py` | `IndicatorRequestDTO`, `PortfolioFragmentDTO` | DTO suffix | ✅ Consistent |
| `lambda_event_dto.py` | `LambdaEventDTO` | DTO suffix | ✅ Consistent |
| `market_bar_dto.py` | `MarketBarDTO` | DTO suffix | ✅ Consistent |
| `order_request_dto.py` | `OrderRequestDTO`, `MarketDataDTO` | DTO suffix | ✅ Consistent |
| `portfolio_state_dto.py` | `PositionDTO`, `PortfolioMetricsDTO`, `PortfolioStateDTO` | DTO suffix | ✅ Consistent |
| `rebalance_plan_dto.py` | `RebalancePlanItemDTO`, `RebalancePlanDTO` | DTO suffix | ✅ Consistent |
| `signal_dto.py` | `StrategySignalDTO` | DTO suffix | ✅ Consistent |
| `strategy_allocation_dto.py` | `StrategyAllocationDTO` | DTO suffix | ✅ Consistent |
| `technical_indicators_dto.py` | `TechnicalIndicatorDTO` | DTO suffix | ✅ Consistent |
| `trace_dto.py` | `TraceEntryDTO`, `TraceDTO` | DTO suffix | ✅ Consistent |
| `trade_run_result_dto.py` | `OrderResultSummaryDTO`, `ExecutionSummaryDTO`, `TradeRunResultDTO` | DTO suffix | ✅ Consistent |

### 1.2 Mixed Convention DTOs

| File | Classes | Naming Pattern | Issue |
| --- | --- | --- | --- |
| `broker_dto.py` | `WebSocketResult`, `OrderExecutionResult` | No DTO suffix | ⚠️ Inconsistent - with aliases |
| `execution_dto.py` | `ExecutionResult` | No DTO suffix | ⚠️ Inconsistent |
| `trade_ledger_dto.py` | `TradeSide`, `AssetType`, `TradeLedgerEntry`, `TradeLedgerQuery`, `Lot`, `PerformanceSummary` | Mixed | ⚠️ Enums + DTOs mixed |

### 1.3 Placeholder DTOs (`__init__.py`)

| Class | Status | Notes |
| --- | --- | --- |
| `ConfigurationDTO` | Placeholder | To be enhanced in Phase 2 |
| `ErrorDTO` | Placeholder | To be enhanced in Phase 2 |

## 2. Schema Directory Inventory (`shared/schemas/`)

### 2.1 Descriptive Naming Convention (No DTO suffix)

| File | Classes | Naming Pattern | Notes |
| --- | --- | --- | --- |
| `base.py` | `Result` | Base class | ✅ Core primitive |
| `accounts.py` | `AccountSummary`, `AccountMetrics`, `BuyingPowerResult`, `RiskMetricsResult`, `TradeEligibilityResult`, `PortfolioAllocationResult`, `EnrichedAccountSummaryView` | Descriptive | ✅ Consistent |
| `common.py` | `MultiStrategyExecutionResultDTO`, `AllocationComparisonDTO`, `MultiStrategySummaryDTO` | Mixed | ⚠️ Some have DTO suffix |
| `enriched_data.py` | `EnrichedOrderView`, `OpenOrdersView`, `EnrichedPositionView`, `EnrichedPositionsView` | View suffix | ✅ Consistent |
| `execution_summary.py` | `AllocationSummary`, `StrategyPnLSummary`, `StrategySummary`, `TradingSummary`, `ExecutionSummary`, `PortfolioState` | Descriptive | ✅ Consistent |
| `market_data.py` | `PriceResult`, `PriceHistoryResult`, `SpreadAnalysisResult`, `MarketStatusResult`, `MultiSymbolQuotesResult` | Result suffix | ✅ Consistent |
| `operations.py` | `OperationResult`, `OrderCancellationResult`, `OrderStatusResult` | Result suffix | ✅ Consistent |

### 2.2 TypedDict Classes (Non-DTO)

| File | Classes | Type | Notes |
| --- | --- | --- | --- |
| `cli.py` | `CLIOptions`, `CLICommandResult`, `CLISignalData`, `CLIAccountDisplay`, `CLIPortfolioData` | TypedDict | Not DTOs |
| `errors.py` | `ErrorDetailInfo`, `ErrorSummaryData`, `ErrorReportSummary`, `ErrorNotificationData`, `ErrorContextData` | TypedDict | Not DTOs |
| `reporting.py` | `DashboardMetrics`, `ReportingData`, `EmailReportData`, `EmailCredentials`, `EmailSummary` | TypedDict | Not DTOs |

## 3. Backward Compatibility Aliases

### 3.1 Schema to DTO Aliases (28 total)

| Original Class | Alias | Location | Status |
| --- | --- | --- | --- |
| `AccountSummary` | `AccountSummaryDTO` | `schemas/accounts.py` | Active |
| `AccountMetrics` | `AccountMetricsDTO` | `schemas/accounts.py` | Active |
| `BuyingPowerResult` | `BuyingPowerDTO` | `schemas/accounts.py` | Active |
| `RiskMetricsResult` | `RiskMetricsDTO` | `schemas/accounts.py` | Active |
| `TradeEligibilityResult` | `TradeEligibilityDTO` | `schemas/accounts.py` | Active |
| `PortfolioAllocationResult` | `PortfolioAllocationDTO` | `schemas/accounts.py` | Active |
| `EnrichedAccountSummaryView` | `EnrichedAccountSummaryDTO` | `schemas/accounts.py` | Active |
| `Result` | `ResultDTO` | `schemas/base.py` | Active |
| `EnrichedOrderView` | `EnrichedOrderDTO` | `schemas/enriched_data.py` | Active |
| `OpenOrdersView` | `OpenOrdersDTO` | `schemas/enriched_data.py` | Active |
| `EnrichedPositionView` | `EnrichedPositionDTO` | `schemas/enriched_data.py` | Active |
| `EnrichedPositionsView` | `EnrichedPositionsDTO` | `schemas/enriched_data.py` | Active |
| `AllocationSummary` | `AllocationSummaryDTO` | `schemas/execution_summary.py` | Active |
| `StrategyPnLSummary` | `StrategyPnLSummaryDTO` | `schemas/execution_summary.py` | Active |
| `StrategySummary` | `StrategySummaryDTO` | `schemas/execution_summary.py` | Active |
| `TradingSummary` | `TradingSummaryDTO` | `schemas/execution_summary.py` | Active |
| `ExecutionSummary` | `ExecutionSummaryDTO` | `schemas/execution_summary.py` | Active |
| `PortfolioState` | `PortfolioStateDTO` | `schemas/execution_summary.py` | Active |
| `PriceResult` | `PriceDTO` | `schemas/market_data.py` | Active |
| `PriceHistoryResult` | `PriceHistoryDTO` | `schemas/market_data.py` | Active |
| `SpreadAnalysisResult` | `SpreadAnalysisDTO` | `schemas/market_data.py` | Active |
| `MarketStatusResult` | `MarketStatusDTO` | `schemas/market_data.py` | Active |
| `MultiSymbolQuotesResult` | `MultiSymbolQuotesDTO` | `schemas/market_data.py` | Active |
| `OperationResult` | `OperationResultDTO` | `schemas/operations.py` | Active |
| `OrderCancellationResult` | `OrderCancellationDTO` | `schemas/operations.py` | Active |
| `OrderStatusResult` | `OrderStatusDTO` | `schemas/operations.py` | Active |
| `WebSocketResult` | `WebSocketResultDTO` | `dto/broker_dto.py` | Active |
| `OrderExecutionResult` | `OrderExecutionResultDTO` | `dto/broker_dto.py` | Active |

## 4. Naming Convention Analysis

### 4.1 Current Patterns

1. **DTO Suffix Pattern** (`shared/dto/`): Classes explicitly named with `DTO` suffix
   - Examples: `AssetInfoDTO`, `PortfolioStateDTO`, `StrategySignalDTO`
   - **Count**: ~25 classes
   - **Consistency**: High (95%)

2. **Descriptive Pattern** (`shared/schemas/`): Classes with descriptive names, no suffix
   - Examples: `AccountSummary`, `ExecutionSummary`, `AllocationSummary`
   - **Count**: ~15 classes
   - **Consistency**: High (90%)

3. **Result Suffix Pattern** (`shared/schemas/`): Classes ending with `Result`
   - Examples: `BuyingPowerResult`, `PriceResult`, `OperationResult`
   - **Count**: ~10 classes
   - **Consistency**: High (100% within pattern)

4. **View Suffix Pattern** (`shared/schemas/`): Classes ending with `View`
   - Examples: `EnrichedOrderView`, `EnrichedPositionView`
   - **Count**: ~4 classes
   - **Consistency**: High (100% within pattern)

### 4.2 Inconsistencies

1. **Mixed DTO Usage in Schemas**: Some schema files use DTO suffix inconsistently
   - `schemas/common.py`: `MultiStrategyExecutionResultDTO`, `AllocationComparisonDTO` have DTO suffix
   - **Impact**: Confuses the dto/ vs schemas/ separation

2. **Missing DTO Suffix in DTOs**: Some dto/ files don't use DTO suffix
   - `dto/broker_dto.py`: `WebSocketResult`, `OrderExecutionResult`
   - `dto/execution_dto.py`: `ExecutionResult`
   - **Impact**: Inconsistent with DTO naming convention

3. **Enum/Class Mixing**: Some DTO files contain both DTOs and enums
   - `dto/trade_ledger_dto.py`: `TradeSide`, `AssetType` (enums) + `TradeLedgerEntry` (DTO)
   - **Impact**: Unclear module purpose

## 5. Import Dependencies Summary

### 5.1 High-Impact Classes (Most Imported)

Based on grep analysis of import statements:

1. **Top 10 Most Imported DTOs**:
   - `RebalancePlanDTO` - Used in execution, orchestration
   - `PortfolioStateDTO` - Used in portfolio, strategy modules  
   - `StrategySignalDTO` - Used in strategy, orchestration
   - `ASTNodeDTO` - Used extensively in DSL engine
   - `TraceDTO` - Used in DSL evaluation
   - `AssetInfoDTO` - Used in execution validation
   - `TechnicalIndicatorDTO` - Used in strategy engines
   - `ExecutionReportDTO` - Used in execution tracking
   - `MarketBarDTO` - Used in strategy adapters
   - `StrategyAllocationDTO` - Used in DSL events

### 5.2 Module Dependencies

- **Strategy Module**: Heavy usage of `ASTNodeDTO`, `TraceDTO`, `IndicatorRequestDTO`
- **Execution Module**: Heavy usage of `RebalancePlanDTO`, `ExecutedOrderDTO`, `AssetInfoDTO`
- **Portfolio Module**: Heavy usage of `PortfolioStateDTO`, `PortfolioMetricsDTO`
- **Orchestration**: Uses DTOs from all modules for coordination

## 6. Assessment Summary

### 6.1 Current State Assessment

**Strengths**:
- Clear separation between `dto/` and `schemas/` directories
- Most files follow consistent naming within their directory
- Comprehensive backward compatibility through aliases
- Good Pydantic v2 adoption with proper config

**Issues**:
- Naming inconsistencies between directories cause confusion
- Some schema files inappropriately use DTO suffix  
- Some DTO files don't use DTO suffix
- Aliases create import confusion
- Mixed class types in some files (enums + DTOs)

### 6.2 Migration Complexity Assessment

**Risk Level**: Medium-High
- **High Import Volume**: 130+ imports across codebase
- **Active Aliases**: 28 backward compatibility aliases in use
- **Cross-Module Dependencies**: Heavy usage across all business modules

**Impact Areas**:
- Strategy v2 module (heavy DSL DTO usage)
- Execution v2 module (execution and portfolio DTOs)
- Orchestration layer (cross-module DTO coordination)
- Event system (DTO payloads in events)

## Next Steps

This inventory serves as the foundation for:
1. **Usage Analysis Document** - Detailed dependency mapping
2. **Migration Plan Document** - Phased approach with risk mitigation
3. **Implementation Phases** - Systematic alias removal and standardization

---

*Generated: Phase 1 DTO/Schema Inventory Analysis*