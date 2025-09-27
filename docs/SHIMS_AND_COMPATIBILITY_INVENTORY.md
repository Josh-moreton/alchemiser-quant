# Shims and Backward Compatibility Features Inventory

**Analysis Date**: December 2024  
**Repository**: Josh-moreton/alchemiser-quant  
**Total Items Found**: 536+ patterns across 241 Python files

This document provides a comprehensive inventory of all shims, backward compatibility features, legacy code patterns, and migration-related code found in the repository.

## Executive Summary

- **DTO Aliases**: 55+ backward compatibility aliases for schema classes
- **Configuration Shims**: 1 config alias (`Config = Settings`)
- **Deprecated Functions**: 10+ deprecated methods and templates
- **Legacy Patterns**: 20+ legacy method references and compatibility layers  
- **Migration TODOs**: 30+ TODO items for removal in Phase 3
- **Error Handling Aliases**: 6 exception handling aliases
- **Service Aliases**: 2 service compatibility aliases

## 1. DTO Backward Compatibility Aliases

### 1.1 Core Model Aliases (High Usage)

These are the primary DTO suffix aliases that provide backward compatibility for the schema migration:

| File | Alias | Original Class | Status |
|------|--------|----------------|---------|
| `shared/schemas/rebalance_plan.py` | `RebalancePlanDTO` | `RebalancePlan` | TODO: Remove in Phase 3 |
| `shared/schemas/rebalance_plan.py` | `RebalancePlanItemDTO` | `RebalancePlanItem` | TODO: Remove in Phase 3 |
| `shared/schemas/portfolio_state.py` | `PortfolioStateDTO` | `PortfolioState` | TODO: Remove in Phase 3 |
| `shared/schemas/portfolio_state.py` | `PositionDTO` | `Position` | TODO: Remove in Phase 3 |
| `shared/schemas/strategy_signal.py` | `StrategySignalDTO` | `StrategySignal` | TODO: Remove in Phase 3 |
| `shared/schemas/strategy_allocation.py` | `StrategyAllocationDTO` | `StrategyAllocation` | TODO: Remove in Phase 3 |
| `shared/schemas/ast_node.py` | `ASTNodeDTO` | `ASTNode` | TODO: Remove in Phase 3 |
| `shared/schemas/execution_result.py` | `ExecutionResultDTO` | `ExecutionResult` | TODO: Remove in Phase 3 |

### 1.2 Execution Module Aliases

| File | Alias | Original Class | Status |
|------|--------|----------------|---------|
| `execution_v2/models/execution_result.py` | `OrderResultDTO` | `OrderResult` | TODO: Remove in Phase 3 |
| `execution_v2/models/execution_result.py` | `ExecutionResultDTO` | `ExecutionResult` | TODO: Remove in Phase 3 |
| `shared/schemas/execution_report.py` | `ExecutedOrderDTO` | `ExecutedOrder` | TODO: Remove in Phase 3 |
| `shared/schemas/execution_report.py` | `ExecutionReportDTO` | `ExecutionReport` | TODO: Remove in Phase 3 |

### 1.3 Market Data Aliases

| File | Alias | Original Class | Status |
|------|--------|----------------|---------|
| `shared/schemas/market_data.py` | `PriceDTO` | `PriceResult` | TODO: Remove in Phase 3 |
| `shared/schemas/market_data.py` | `PriceHistoryDTO` | `PriceHistoryResult` | TODO: Remove in Phase 3 |
| `shared/schemas/market_data.py` | `SpreadAnalysisDTO` | `SpreadAnalysisResult` | TODO: Remove in Phase 3 |
| `shared/schemas/market_data.py` | `MarketStatusDTO` | `MarketStatusResult` | TODO: Remove in Phase 3 |
| `shared/schemas/market_data.py` | `MultiSymbolQuotesDTO` | `MultiSymbolQuotesResult` | TODO: Remove in Phase 3 |
| `shared/schemas/market_bar.py` | `MarketBarDTO` | `MarketBar` | TODO: Remove in Phase 3 |

### 1.4 Account and Portfolio Aliases

| File | Alias | Original Class | Status |
|------|--------|----------------|---------|
| `shared/schemas/accounts.py` | `AccountSummaryDTO` | `AccountSummary` | TODO: Remove in Phase 3 |
| `shared/schemas/accounts.py` | `AccountMetricsDTO` | `AccountMetrics` | TODO: Remove in Phase 3 |
| `shared/schemas/accounts.py` | `BuyingPowerDTO` | `BuyingPowerResult` | TODO: Remove in Phase 3 |
| `shared/schemas/accounts.py` | `RiskMetricsDTO` | `RiskMetricsResult` | TODO: Remove in Phase 3 |
| `shared/schemas/accounts.py` | `TradeEligibilityDTO` | `TradeEligibilityResult` | TODO: Remove in Phase 3 |
| `shared/schemas/accounts.py` | `PortfolioAllocationDTO` | `PortfolioAllocationResult` | TODO: Remove in Phase 3 |
| `shared/schemas/accounts.py` | `EnrichedAccountSummaryDTO` | `EnrichedAccountSummaryView` | TODO: Remove in Phase 3 |

### 1.5 Additional Schema Aliases

| File | Alias | Original Class | Status |
|------|--------|----------------|---------|
| `shared/schemas/enriched_data.py` | `EnrichedOrderDTO` | `EnrichedOrderView` | TODO: Remove in Phase 3 |
| `shared/schemas/enriched_data.py` | `OpenOrdersDTO` | `OpenOrdersView` | TODO: Remove in Phase 3 |
| `shared/schemas/enriched_data.py` | `EnrichedPositionDTO` | `EnrichedPositionView` | TODO: Remove in Phase 3 |
| `shared/schemas/enriched_data.py` | `EnrichedPositionsDTO` | `EnrichedPositionsView` | TODO: Remove in Phase 3 |
| `shared/schemas/asset_info.py` | `AssetInfoDTO` | `AssetInfo` | TODO: Remove in Phase 3 |
| `shared/schemas/indicator_request.py` | `IndicatorRequestDTO` | `IndicatorRequest` | TODO: Remove in Phase 3 |
| `shared/schemas/indicator_request.py` | `PortfolioFragmentDTO` | `PortfolioFragment` | TODO: Remove in Phase 3 |
| `shared/schemas/trace.py` | `TraceEntryDTO` | `TraceEntry` | TODO: Remove in Phase 3 |
| `shared/schemas/trace.py` | `TraceDTO` | `Trace` | TODO: Remove in Phase 3 |
| `shared/schemas/common.py` | `ConfigurationDTO` | `Configuration` | TODO: Remove in Phase 3 |
| `shared/schemas/common.py` | `ErrorDTO` | `Error` | TODO: Remove in Phase 3 |
| `shared/schemas/operations.py` | `OperationResultDTO` | `OperationResult` | TODO: Remove in Phase 3 |
| `shared/schemas/operations.py` | `OrderCancellationDTO` | `OrderCancellationResult` | TODO: Remove in Phase 3 |
| `shared/schemas/operations.py` | `OrderStatusDTO` | `OrderStatusResult` | TODO: Remove in Phase 3 |
| `shared/schemas/lambda_event.py` | `LambdaEventDTO` | `LambdaEvent` | TODO: Remove in Phase 3 |
| `shared/schemas/trade_run_result.py` | `OrderResultSummaryDTO` | `OrderResultSummary` | TODO: Remove in Phase 3 |
| `shared/schemas/trade_run_result.py` | `ExecutionSummaryDTO` | `ExecutionSummary` | TODO: Remove in Phase 3 |
| `shared/schemas/trade_run_result.py` | `TradeRunResultDTO` | `TradeRunResult` | TODO: Remove in Phase 3 |
| `shared/schemas/consolidated_portfolio.py` | `ConsolidatedPortfolioDTO` | `ConsolidatedPortfolio` | TODO: Remove in Phase 3 |
| `shared/schemas/technical_indicator.py` | `TechnicalIndicatorDTO` | `TechnicalIndicator` | TODO: Remove in Phase 3 |
| `shared/schemas/base.py` | `ResultDTO` | `Result` | TODO: Remove in Phase 3 |
| `shared/schemas/execution_summary.py` | `AllocationSummaryDTO` | `AllocationSummary` | TODO: Remove in Phase 3 |
| `shared/schemas/execution_summary.py` | `StrategyPnLSummaryDTO` | `StrategyPnLSummary` | TODO: Remove in Phase 3 |
| `shared/schemas/execution_summary.py` | `StrategySummaryDTO` | `StrategySummary` | TODO: Remove in Phase 3 |
| `shared/schemas/execution_summary.py` | `TradingSummaryDTO` | `TradingSummary` | TODO: Remove in Phase 3 |
| `shared/schemas/order_request.py` | `OrderRequestDTO` | `OrderRequest` | TODO: Remove in Phase 3 |
| `shared/schemas/order_request.py` | `MarketDataDTO` | `MarketData` | TODO: Remove in Phase 3 |

## 2. Configuration Shims

### 2.1 Config Alias

**Location**: `the_alchemiser/shared/config/__init__.py:10`

```python
# Backward compatibility alias
Config = Settings
```

**Purpose**: Provides backward compatibility for code that imports `Config` instead of `Settings`.

**Status**: Active shim for backward compatibility

## 3. Deprecated Functions and Templates

### 3.1 Email Template Deprecations

**Location**: `shared/notifications/templates/email_facade.py`

Multiple deprecated email template functions that return deprecation notices:

```python
def build_trading_report_html(*_args: object, **_kwargs: object) -> str:  # Deprecated shim
    """Return deprecation notice for removed trading report (neutral mode only)."""

def trading_report(*_args: object, **_kwargs: object) -> str:  # Deprecated
    """Return deprecated trading report notice (financial view removed)."""

def monthly_performance_summary(*_args: object, **_kwargs: object) -> str:  # Deprecated
    """Return deprecated performance summary notice (neutral mode only)."""
```

**Status**: Active deprecated shims that return notices instead of real functionality

### 3.2 Real-Time Pricing Deprecation

**Location**: `shared/services/real_time_pricing.py`

```python
def get_real_time_quote(self, symbol: str) -> RealTimeQuote | None:
    """Get real-time quote data for a symbol (DEPRECATED).
    
    This method is deprecated. Use get_quote_data() for new code.
    """
    warnings.warn(
        "get_real_time_quote() is deprecated. Use get_quote_data() for new code.",
        DeprecationWarning,
        stacklevel=2,
    )
```

**Status**: Active deprecation warning for legacy method

### 3.3 Deprecated Module

**Location**: `orchestration/display_utils.py`

```python
"""Deprecated module placeholder.

This module has been replaced by new functionality and should not be used.
"""
```

**Status**: Deprecated module placeholder

## 4. Legacy Patterns and Compatibility Layers

### 4.1 Legacy Method References

**Location**: `execution_v2/core/smart_execution_strategy/strategy.py`

```python
# Legacy methods for backwards compatibility
```

**Location**: `strategy_v2/engines/dsl/engine.py`

```python
# Fallback to mock service for backward compatibility
```

### 4.2 Legacy Data Conversion

**Location**: `strategy_v2/adapters/market_data_adapter.py`

```python
# Convert legacy bar dictionaries to MarketBar objects
```

**Location**: `execution_v2/core/smart_execution_strategy/quotes.py`

```python
# Convert to dict format for compatibility
```

### 4.3 Legacy Storage

**Location**: `shared/services/real_time_pricing.py`

```python
# Legacy RealTimeQuote storage (for backward compatibility)
self._quotes.pop(symbol, None)  # Legacy storage
```

## 5. Exception Handling Aliases

### 5.1 Alpaca Error Handler Aliases

**Location**: `shared/utils/alpaca_error_handler.py`

```python
RetryException = _RetryExcImported
HTTPError = _HTTPErrorImported
RequestException = _RequestExcImported
```

**Location**: `shared/brokers/alpaca_manager.py`

```python
RetryException = _RetryExcImported
HTTPError = _HTTPErrorImported
RequestException = _RequestExcImported
```

**Purpose**: Provides consistent exception types across modules

## 6. Service Type Aliases

### 6.1 Service Factory Aliases

**Location**: `shared/utils/service_factory.py`

```python
ExecutionManagerType = ExecutionManagerProtocol
```

**Location**: `shared/services/tick_size_service.py`

```python
DynamicTickSizeService = TickSizeService
```

**Purpose**: Type aliases for service protocols and implementations

## 7. Timezone Compatibility

**Location**: `shared/types/market_data.py`

```python
# Legacy alias for backward compatibility  
_UTC_TIMEZONE_SUFFIX = UTC_TIMEZONE_SUFFIX
```

**Purpose**: Maintains compatibility for timezone constants

## 8. Schema Version Compatibility

**Location**: `shared/events/dsl_events.py`

Multiple events include schema version fields for backward compatibility:

```python
# Schema version for backward compatibility
schema_version: str = Field(default="1.0", description="Event schema version")
```

**Purpose**: Allows for event schema evolution while maintaining compatibility

## 9. Command Line Compatibility

**Location**: `main.py`

```python
"""Parse command line arguments for backward compatibility.

Args:
    argv: Command line arguments - supports ["trade"] for backward compatibility
          with legacy calls, but primarily for programmatic usage
"""
# Parse arguments for backward compatibility
```

**Purpose**: Maintains compatibility with legacy command line argument patterns

## 10. Legacy Field Aliases

**Location**: `shared/value_objects/core_types.py`

```python
# Legacy field aliases for backward compatibility
```

**Purpose**: Provides aliases for renamed fields in value objects

## 11. Migration Status and Next Steps

### 11.1 Current Migration Status

Based on the DTO Migration documentation:

- **Phase 3a**: ✅ **COMPLETED** - Namespace unification with compatibility shim
- **Phase 3b**: ✅ **COMPLETED** - Compatibility shim removed
- **Phase 3c**: 🔄 **IN PROGRESS** - Remove DTO suffix aliases (this inventory)

### 11.2 Next Steps

1. **Remove DTO Suffix Aliases**: All 55+ DTO aliases listed above should be removed
2. **Update Import Statements**: Replace any remaining `*DTO` imports with base class names
3. **Remove Legacy Methods**: Clean up deprecated methods and their compatibility layers
4. **Remove Configuration Shim**: Remove `Config = Settings` alias
5. **Clean Up TODO Comments**: Remove or update migration-related TODO items

### 11.3 Risk Assessment

- **High Risk**: Core model aliases (`RebalancePlanDTO`, `PortfolioStateDTO`, `StrategySignalDTO`)
- **Medium Risk**: Execution and market data aliases
- **Low Risk**: Configuration shims and service aliases

## 12. Documentation References

This inventory complements the existing migration documentation:

- `docs/DTO_MIGRATION_INVENTORY.md` - Original migration planning
- `docs/DTO_MIGRATION_PLAN.md` - Migration execution plan
- `CHANGELOG.md` - Records completed migration phases

---

*Generated: Comprehensive Shims and Backward Compatibility Inventory (December 2024)*