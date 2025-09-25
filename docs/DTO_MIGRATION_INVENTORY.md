# DTO/Schema Migration Inventory

## Overview
This document provides a comprehensive inventory of all DTO and Schema classes in the alchemiser-quant repository as part of Phase 1 of the DTO standardization effort. The goal is to **remove DTO suffixes** and use descriptive, domain-relevant class names following modern Pydantic v2 best practices.

**Analysis Date**: Phase 1 Initial Assessment (Revised)  
**Repository**: Josh-moreton/alchemiser-quant  
**Scope**: shared/dto/ and shared/schemas/ directories  
**Update**: Phase 3a namespace unification completed (December 2024)

## Executive Summary

- **Total DTO Files**: ~~20 files in `shared/dto/`~~ → **Migrated to `shared/schemas/`**
- **Total Schema Files**: ~~11 files in `shared/schemas/`~~ → **31 files total**
- **Total Classes**: 90+ boundary model classes (all preserved)
- **Backward Compatibility Aliases**: 28 DTO suffix aliases (maintained for compatibility)
- **Import Usage**: 89+ import statements updated to use `shared.schemas`
- **Migration Goal**: ✅ **COMPLETED** - Single authoritative namespace achieved

## Migration Status: Phase 3a Complete ✅

### Namespace Unification Results
- **✅ All DTO files moved** to `shared/schemas/` with git history preservation
- **✅ Single canonical namespace** established: `the_alchemiser.shared.schemas`
- **✅ Compatibility maintained** via deprecation shim in `shared/dto/`
- **✅ All imports updated** from 89+ locations across codebase
- **✅ Quality gates maintained** (ruff ✓, mypy ✓, import-linter ✓)

### File Migration Mapping

| Original DTO File | New Schema File | Status |
|------------------|-----------------|--------|
| `asset_info_dto.py` | `asset_info.py` | ✅ Moved |
| `ast_node_dto.py` | `ast_node.py` | ✅ Moved |
| `consolidated_portfolio_dto.py` | `consolidated_portfolio.py` | ✅ Moved |
| `execution_dto.py` | `execution_result.py` | ✅ Moved (renamed) |
| `execution_report_dto.py` | `execution_report.py` | ✅ Moved |
| `indicator_request_dto.py` | `indicator_request.py` | ✅ Moved |
| `lambda_event_dto.py` | `lambda_event.py` | ✅ Moved |
| `market_bar_dto.py` | `market_bar.py` | ✅ Moved |
| `order_request_dto.py` | `order_request.py` | ✅ Moved |
| `portfolio_state_dto.py` | `portfolio_state.py` | ✅ Moved |
| `rebalance_plan_dto.py` | `rebalance_plan.py` | ✅ Moved |
| `result_factory.py` | `trade_result_factory.py` | ✅ Moved (renamed) |
| `signal_dto.py` | `strategy_signal.py` | ✅ Moved (renamed) |
| `strategy_allocation_dto.py` | `strategy_allocation.py` | ✅ Moved |
| `technical_indicators_dto.py` | `technical_indicator.py` | ✅ Moved |
| `trace_dto.py` | `trace.py` | ✅ Moved |
| `trade_ledger_dto.py` | `trade_ledger.py` | ✅ Moved |
| `trade_run_result_dto.py` | `trade_run_result.py` | ✅ Moved |
| `broker_dto.py` | `broker.py` | ✅ Moved |

### Compatibility Layer Status

**Deprecation Shim**: `shared/dto/__init__.py`
- ✅ Emits `DeprecationWarning` on first import
- ✅ Re-exports all classes from `shared.schemas`
- ✅ Full backward compatibility maintained
- 🔄 **Planned removal**: Phase 3 final cleanup

**Example Usage**:
```python
# NEW: Canonical import (recommended)
from the_alchemiser.shared.schemas import AssetInfo, RebalancePlan

# OLD: Still works but deprecated (emits warning)
from the_alchemiser.shared.dto import AssetInfo, RebalancePlan
```

## 1. Boundary Models Inventory

### 1.1 Models with DTO Suffixes (To Remove)

These classes currently have DTO suffixes but should be renamed to use descriptive, domain-relevant names:

| File | Current Name | Proposed Name | Migration Action |
| --- | --- | --- | --- |
| `asset_info_dto.py` | `AssetInfoDTO` | `AssetInfo` | Remove DTO suffix |
| `ast_node_dto.py` | `ASTNodeDTO` | `ASTNode` | Remove DTO suffix |
| `consolidated_portfolio_dto.py` | `ConsolidatedPortfolioDTO` | `ConsolidatedPortfolio` | Remove DTO suffix |
| `execution_report_dto.py` | `ExecutedOrderDTO` | `ExecutedOrder` | Remove DTO suffix |
| `execution_report_dto.py` | `ExecutionReportDTO` | `ExecutionReport` | Remove DTO suffix |
| `indicator_request_dto.py` | `IndicatorRequestDTO` | `IndicatorRequest` | Remove DTO suffix |
| `indicator_request_dto.py` | `PortfolioFragmentDTO` | `PortfolioFragment` | Remove DTO suffix |
| `lambda_event_dto.py` | `LambdaEventDTO` | `LambdaEvent` | Remove DTO suffix |
| `market_bar_dto.py` | `MarketBarDTO` | `MarketBar` | Remove DTO suffix |
| `order_request_dto.py` | `OrderRequestDTO` | `OrderRequest` | Remove DTO suffix |
| `order_request_dto.py` | `MarketDataDTO` | `MarketData` | Remove DTO suffix |
| `portfolio_state_dto.py` | `PositionDTO` | `Position` | Remove DTO suffix |
| `portfolio_state_dto.py` | `PortfolioMetricsDTO` | `PortfolioMetrics` | Remove DTO suffix |
| `portfolio_state_dto.py` | `PortfolioStateDTO` | `PortfolioState` | Remove DTO suffix |
| `rebalance_plan_dto.py` | `RebalancePlanItemDTO` | `RebalancePlanItem` | Remove DTO suffix |
| `rebalance_plan_dto.py` | `RebalancePlanDTO` | `RebalancePlan` | Remove DTO suffix |
| `signal_dto.py` | `StrategySignalDTO` | `StrategySignal` | Remove DTO suffix |
| `strategy_allocation_dto.py` | `StrategyAllocationDTO` | `StrategyAllocation` | Remove DTO suffix |
| `technical_indicators_dto.py` | `TechnicalIndicatorDTO` | `TechnicalIndicator` | Remove DTO suffix |
| `trace_dto.py` | `TraceEntryDTO` | `TraceEntry` | Remove DTO suffix |
| `trace_dto.py` | `TraceDTO` | `Trace` | Remove DTO suffix |
| `trade_run_result_dto.py` | `OrderResultSummaryDTO` | `OrderResultSummary` | Remove DTO suffix |
| `trade_run_result_dto.py` | `ExecutionSummaryDTO` | `ExecutionSummary` | Remove DTO suffix (Note: conflicts with schema) |
| `trade_run_result_dto.py` | `TradeRunResultDTO` | `TradeRunResult` | Remove DTO suffix |

### 1.2 Models with Correct Descriptive Names (Keep)

These classes already follow the desired naming pattern:

| File | Classes | Naming Pattern | Status |
| --- | --- | --- | --- |
| `broker_dto.py` | `WebSocketResult`, `OrderExecutionResult` | Descriptive | ✅ Correct naming |
| `execution_dto.py` | `ExecutionResult` | Descriptive | ✅ Correct naming |
| `trade_ledger_dto.py` | `TradeSide`, `AssetType`, `TradeLedgerEntry`, `TradeLedgerQuery`, `Lot`, `PerformanceSummary` | Mixed | ✅ Enums + descriptive names |

### 1.3 Placeholder Models (`__init__.py`)

| Current Name | Proposed Name | Action |
| --- | --- | --- |
| `ConfigurationDTO` | `Configuration` | Remove DTO suffix |
| `ErrorDTO` | `Error` | Remove DTO suffix |

## 2. Schema Directory Inventory (`shared/schemas/`)

### 2.1 Correctly Named Schema Classes (Keep)

These classes already follow the desired descriptive naming pattern:

| File | Classes | Naming Pattern | Status |
| --- | --- | --- | --- |
| `base.py` | `Result` | Base class | ✅ Correct |
| `accounts.py` | `AccountSummary`, `AccountMetrics`, `BuyingPowerResult`, `RiskMetricsResult`, `TradeEligibilityResult`, `PortfolioAllocationResult`, `EnrichedAccountSummaryView` | Descriptive | ✅ Correct |
| `enriched_data.py` | `EnrichedOrderView`, `OpenOrdersView`, `EnrichedPositionView`, `EnrichedPositionsView` | View suffix | ✅ Correct |
| `execution_summary.py` | `AllocationSummary`, `StrategyPnLSummary`, `StrategySummary`, `TradingSummary`, `ExecutionSummary`, `PortfolioState` | Descriptive | ✅ Correct |
| `market_data.py` | `PriceResult`, `PriceHistoryResult`, `SpreadAnalysisResult`, `MarketStatusResult`, `MultiSymbolQuotesResult` | Result suffix | ✅ Correct |
| `operations.py` | `OperationResult`, `OrderCancellationResult`, `OrderStatusResult` | Result suffix | ✅ Correct |

### 2.2 Schema Classes with DTO Suffixes (To Fix)

These schema classes inappropriately use DTO suffixes and should be renamed:

| File | Current Name | Proposed Name | Issue |
| --- | --- | --- | --- |
| `common.py` | `MultiStrategyExecutionResultDTO` | `MultiStrategyExecutionResult` | Remove DTO suffix |
| `common.py` | `AllocationComparisonDTO` | `AllocationComparison` | Remove DTO suffix |
| `common.py` | `MultiStrategySummaryDTO` | `MultiStrategySummary` | Remove DTO suffix |

### 2.3 TypedDict Classes (Keep Unchanged)

These are not boundary DTOs and should remain as-is:

| File | Classes | Type | Status |
| --- | --- | --- | --- |
| `cli.py` | `CLIOptions`, `CLICommandResult`, `CLISignalData`, `CLIAccountDisplay`, `CLIPortfolioData` | TypedDict | ✅ Keep as-is |
| `errors.py` | `ErrorDetailInfo`, `ErrorSummaryData`, `ErrorReportSummary`, `ErrorNotificationData`, `ErrorContextData` | TypedDict | ✅ Keep as-is |
| `reporting.py` | `DashboardMetrics`, `ReportingData`, `EmailReportData`, `EmailCredentials`, `EmailSummary` | TypedDict | ✅ Keep as-is |

## 3. Backward Compatibility Aliases (To Remove)

### 3.1 DTO Suffix Aliases (28 total to remove)

These aliases create the DTO suffix variants and should be completely removed:

| Original Class | Current Alias | Location | Action |
| --- | --- | --- | --- |
| `AccountSummary` | `AccountSummaryDTO` | `schemas/accounts.py` | Remove alias |
| `AccountMetrics` | `AccountMetricsDTO` | `schemas/accounts.py` | Remove alias |
| `BuyingPowerResult` | `BuyingPowerDTO` | `schemas/accounts.py` | Remove alias |
| `RiskMetricsResult` | `RiskMetricsDTO` | `schemas/accounts.py` | Remove alias |
| `TradeEligibilityResult` | `TradeEligibilityDTO` | `schemas/accounts.py` | Remove alias |
| `PortfolioAllocationResult` | `PortfolioAllocationDTO` | `schemas/accounts.py` | Remove alias |
| `EnrichedAccountSummaryView` | `EnrichedAccountSummaryDTO` | `schemas/accounts.py` | Remove alias |
| `Result` | `ResultDTO` | `schemas/base.py` | Remove alias |
| `EnrichedOrderView` | `EnrichedOrderDTO` | `schemas/enriched_data.py` | Remove alias |
| `OpenOrdersView` | `OpenOrdersDTO` | `schemas/enriched_data.py` | Remove alias |
| `EnrichedPositionView` | `EnrichedPositionDTO` | `schemas/enriched_data.py` | Remove alias |
| `EnrichedPositionsView` | `EnrichedPositionsDTO` | `schemas/enriched_data.py` | Remove alias |
| `AllocationSummary` | `AllocationSummaryDTO` | `schemas/execution_summary.py` | Remove alias |
| `StrategyPnLSummary` | `StrategyPnLSummaryDTO` | `schemas/execution_summary.py` | Remove alias |
| `StrategySummary` | `StrategySummaryDTO` | `schemas/execution_summary.py` | Remove alias |
| `TradingSummary` | `TradingSummaryDTO` | `schemas/execution_summary.py` | Remove alias |
| `ExecutionSummary` | `ExecutionSummaryDTO` | `schemas/execution_summary.py` | Remove alias |
| `PortfolioState` | `PortfolioStateDTO` | `schemas/execution_summary.py` | Remove alias |
| `PriceResult` | `PriceDTO` | `schemas/market_data.py` | Remove alias |
| `PriceHistoryResult` | `PriceHistoryDTO` | `schemas/market_data.py` | Remove alias |
| `SpreadAnalysisResult` | `SpreadAnalysisDTO` | `schemas/market_data.py` | Remove alias |
| `MarketStatusResult` | `MarketStatusDTO` | `schemas/market_data.py` | Remove alias |
| `MultiSymbolQuotesResult` | `MultiSymbolQuotesDTO` | `schemas/market_data.py` | Remove alias |
| `OperationResult` | `OperationResultDTO` | `schemas/operations.py` | Remove alias |
| `OrderCancellationResult` | `OrderCancellationDTO` | `schemas/operations.py` | Remove alias |
| `OrderStatusResult` | `OrderStatusDTO` | `schemas/operations.py` | Remove alias |
| `WebSocketResult` | `WebSocketResultDTO` | `dto/broker_dto.py` | Remove alias |
| `OrderExecutionResult` | `OrderExecutionResultDTO` | `dto/broker_dto.py` | Remove alias |

## 4. Naming Convention Analysis

### 4.1 Current State vs. Desired State

**Current Problem**: Mixed naming conventions create confusion and violate modern Python/Pydantic best practices.

**Desired State**: All boundary models use descriptive, domain-relevant names without generic DTO suffixes.

### 4.2 Current Patterns (To Change)

1. **DTO Suffix Pattern** (25+ classes): Generic suffixes that don't add semantic value
   - Examples: `AssetInfoDTO` → `AssetInfo`, `PortfolioStateDTO` → `PortfolioState`
   - **Problem**: DTO is a pattern, not a type. Suffixes add no domain meaning.

2. **Backward Compatibility Aliases** (28 aliases): Create import confusion
   - Examples: `AccountSummaryDTO = AccountSummary`
   - **Problem**: Multiple ways to import the same class

### 4.3 Correct Patterns (To Keep/Adopt)

1. **Descriptive Naming**: Classes named for their domain purpose
   - Examples: `AccountSummary`, `ExecutionSummary`, `AllocationSummary`
   - **Benefit**: Clear domain meaning, follows Python naming conventions

2. **Functional Suffixes**: When suffix adds semantic value
   - Examples: `BuyingPowerResult`, `EnrichedOrderView`
   - **Benefit**: Suffixes like `Result`, `View` indicate specific purposes

### 4.4 Modern Python/Pydantic Best Practices

**Technical Rationale**:
- DTO describes a *pattern* (data transfer object), not a specific class type
- Modern Python favors descriptive names over generic technical suffixes
- Pydantic v2 handles serialization through configuration, not naming
- Single location (`shared/schemas/`) reduces cognitive overhead

**Examples from Other Projects**:
```python
# Modern approach (preferred)
class User(BaseModel): ...
class Order(BaseModel): ...
class PaymentRequest(BaseModel): ...

# Anti-pattern (avoid)
class UserDTO(BaseModel): ...
class OrderDTO(BaseModel): ...  
class PaymentRequestDTO(BaseModel): ...
```

## 5. Directory Consolidation Plan

### 5.1 Current Directory Structure Issues

**Problem**: Split between `dto/` and `schemas/` creates confusion about where to place boundary models.

**Current State**:
- `shared/dto/`: 20 files, mostly with DTO suffixes
- `shared/schemas/`: 11 files, mixed naming patterns

### 5.2 Proposed Consolidation

**Target State**: Consolidate all boundary models into `shared/schemas/` with descriptive names.

**Migration Plan**:
1. **Move all models** from `shared/dto/` to appropriate files in `shared/schemas/`
2. **Remove DTO suffixes** from class names during the move
3. **Organize by domain** rather than technical classification
4. **Remove the `dto/` directory** entirely

**Example Consolidation**:
```python
# BEFORE: scattered across dto/ and schemas/
shared/dto/portfolio_state_dto.py → PortfolioStateDTO, PositionDTO, PortfolioMetricsDTO
shared/schemas/execution_summary.py → PortfolioState (different class!)

# AFTER: consolidated in schemas/ with clear names
shared/schemas/portfolio.py → PortfolioState, Position, PortfolioMetrics
shared/schemas/execution.py → ExecutionSummary, TradingSummary
```

### 5.3 Proposed File Organization

| Domain | New File | Classes to Include |
| --- | --- | --- |
| `schemas/portfolio.py` | Portfolio models | `PortfolioState`, `Position`, `PortfolioMetrics`, `RebalancePlan`, `RebalancePlanItem` |
| `schemas/execution.py` | Execution models | `ExecutedOrder`, `ExecutionReport`, `ExecutionResult`, `OrderRequest` |
| `schemas/strategy.py` | Strategy models | `StrategySignal`, `StrategyAllocation`, `TechnicalIndicator` |
| `schemas/market_data.py` | Market models | `MarketBar`, `MarketData` (extend existing) |
| `schemas/assets.py` | Asset models | `AssetInfo` |
| `schemas/events.py` | Event models | `LambdaEvent` |
| `schemas/dsl.py` | DSL models | `ASTNode`, `Trace`, `TraceEntry`, `IndicatorRequest`, `PortfolioFragment` |
| `schemas/trading.py` | Trading models | `TradeLedgerEntry`, `TradeLedgerQuery`, `Lot`, `PerformanceSummary` |
| `schemas/results.py` | Result models | `TradeRunResult`, `OrderResultSummary` |
| `schemas/infrastructure.py` | Infrastructure models | `Configuration`, `Error` (from placeholders) |

## 6. Assessment Summary

### 6.1 Current State Assessment

**Problems Identified**:
- **Generic DTO suffixes**: 25+ classes with meaningless DTO suffixes
- **Naming inconsistency**: Mixed patterns across files and directories
- **Directory confusion**: Split between dto/ and schemas/ with unclear boundaries
- **Alias burden**: 28 backward compatibility aliases create import confusion
- **Technical debt**: Pattern violates modern Python/Pydantic best practices

**Root Cause**: The DTO suffix pattern treats "DTO" as a type rather than a design pattern.

### 6.2 Migration Benefits

**Post-Migration Benefits**:
- **Clear semantics**: Class names describe domain purpose, not technical implementation
- **Reduced cognitive load**: Single location for all boundary models
- **Better maintainability**: No confusion about where to put new models
- **Modern compliance**: Follows Python/Pydantic v2 best practices
- **Import clarity**: One canonical name per class, no aliases

### 6.3 Migration Complexity Assessment

**Risk Level**: Medium-High (due to import volume and cross-module usage)
- **High Import Volume**: 130+ imports across codebase need updating
- **Cross-Module Dependencies**: Changes affect all business modules
- **Name Conflicts**: Some classes may have naming conflicts during consolidation

**Mitigation Strategies**:
- **Staged approach**: Remove aliases first, then rename classes, then consolidate files
- **Comprehensive testing**: Full test coverage before any changes
- **Automated tooling**: Scripts to validate imports and detect conflicts
- **Clear communication**: Document all changes and coordinate with teams

## 7. Next Steps

This inventory provides the foundation for the corrected migration approach:

1. **Phase 2**: Remove DTO suffixes from class names and update imports
2. **Phase 3**: Remove all backward compatibility aliases  
3. **Phase 4**: Consolidate all models into `shared/schemas/` with domain organization
4. **Phase 5**: Update documentation to clarify boundary model patterns

The revised approach aligns with modern Python practices and will result in a cleaner, more maintainable codebase.

---

*Generated: Phase 1 DTO/Schema Inventory Analysis (Revised)*