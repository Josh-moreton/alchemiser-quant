# Boundary Model Migration Plan

**Business Unit:** shared | **Status:** plan  
**Generated:** Phase 1 of Boundary Model Standardization Migration  
**Target:** Detailed phased migration to modern Python/Pydantic v2 practices

## Overview

This document outlines a comprehensive, phased approach to modernizing boundary models across the alchemiser-quant codebase. Following modern Python and Pydantic v2 best practices, we will consolidate all boundary models into `shared/schemas/` with descriptive, domain-relevant names (removing generic "DTO" suffixes).

## Migration Objectives

### Primary Goals
1. **Remove DTO Suffixes** from all Pydantic boundary model class names
2. **Consolidate Models** into single location (`shared/schemas/`)
3. **Remove Backward Compatibility Aliases** systematically
4. **Standardize Imports** to use descriptive class names directly
5. **Maintain Zero Breaking Changes** through careful phased approach

### Success Criteria
- [ ] All boundary models use descriptive, domain-relevant names (no DTO suffix)
- [ ] Single source of truth for each boundary model concept
- [ ] All backward compatibility aliases removed
- [ ] All imports updated to use descriptive names
- [ ] Comprehensive documentation of boundary models
- [ ] Zero breaking changes to existing functionality

## Migration Strategy

### Core Principles
1. **Modern Python Practices** - Use descriptive names, not generic suffixes
2. **Single Source of Truth** - Consolidate all boundary models in `shared/schemas/`
3. **Incremental Changes** - Small, validated steps with rollback points
4. **Dependency Order** - Migrate leaf dependencies before core components
5. **Comprehensive Testing** - Validate each phase before proceeding

### Risk Management Approach
- **Temporary Compatibility** maintained during transition phases
- **Rollback Points** at end of each phase
- **Comprehensive Testing** for all boundary model usage
- **Import Monitoring** to track migration progress

## Detailed Migration Phases

## Phase 2: Model Consolidation and Organization (Low Risk)
**Duration:** 2-3 weeks  
**Risk Level:** 🟢 **Low**  
**Objective:** Consolidate all boundary models into organized `shared/schemas/` structure

### Phase 2.1: Schema File Organization (Week 1)
Create organized schema structure and move models from `dto/` to appropriate schema files.

#### Target Structure:
```
shared/schemas/
├── assets.py          # AssetInfo (from asset_info_dto.py)
├── broker.py          # WebSocketResult, OrderExecutionResult (from broker_dto.py)
├── dsl.py             # ASTNode, Trace (from ast_node_dto.py, trace_dto.py)
├── events.py          # LambdaEvent (from lambda_event_dto.py)
├── execution.py       # ExecutionResult, ExecutedOrder, etc. (consolidate execution models)
├── indicators.py      # IndicatorRequest, TechnicalIndicator (from indicator DTOs)
├── orders.py          # OrderRequest, MarketData (from order_request_dto.py)
├── portfolio.py       # PortfolioState, RebalancePlan, etc. (consolidate portfolio models)
├── strategy.py        # StrategySignal, StrategyAllocation (from strategy DTOs)
└── trading.py         # TradeLedgerEntry, PerformanceSummary (from trade_ledger_dto.py)
```

#### Changes:
1. **Create new schema files** for logical domain groupings
2. **Move classes** from `dto/` files to appropriate schema files
3. **Keep original class names** initially (rename in next phase)
4. **Update `__init__.py`** to export from new locations
5. **Add temporary import aliases** in original dto files for compatibility

### Phase 2.2: Consolidate Duplicate Concepts (Week 2)
Identify and resolve duplicate model concepts between dto/ and schemas/.

#### Identified Duplicates:
```
PortfolioState:
- dto/portfolio_state_dto.py: PortfolioStateDTO, PositionDTO, PortfolioMetricsDTO
- schemas/execution_summary.py: PortfolioState (with alias PortfolioStateDTO)
Resolution: Keep dto/ versions, remove from execution_summary.py

ExecutionSummary:
- dto/trade_run_result_dto.py: ExecutionSummaryDTO
- schemas/execution_summary.py: ExecutionSummary (with alias ExecutionSummaryDTO)
Resolution: Consolidate into single ExecutionSummary in schemas/execution.py
```

### Phase 2.3: Schema Validation and Testing (Week 3) 
Complete consolidation phase with comprehensive validation.

#### Activities:
- [ ] Validate all imports work correctly
- [ ] Run comprehensive test suite
- [ ] Update temporary compatibility aliases
- [ ] Document new schema organization

## Phase 3: Class Renaming (Medium Risk)
**Duration:** 3-4 weeks  
**Risk Level:** 🟡 **Medium**  
**Objective:** Remove DTO suffixes and use descriptive, domain-relevant names

### Phase 3.1: Low-Impact Class Renames (Week 1)
Rename classes with minimal imports (1-2 files).

#### Target Renames:
```
Low-impact renames:
- LambdaEventDTO → LambdaEvent
- MarketBarDTO → MarketBar  
- TechnicalIndicatorDTO → TechnicalIndicator
- TraceDTO → Trace
- AssetInfoDTO → AssetInfo

Schema classes with DTO suffix:
- AllocationComparisonDTO → AllocationComparison
- MultiStrategyExecutionResultDTO → MultiStrategyExecutionResult
- MultiStrategySummaryDTO → MultiStrategySummary
```

#### Process:
1. **Rename classes** in schema files
2. **Update imports** in consuming modules
3. **Add temporary aliases** for transition period
4. **Run comprehensive tests**

### Phase 3.2: High-Impact Class Renames (Week 2-3)
Rename heavily used classes with careful coordination.

#### Target Renames:
```
High-impact renames (5+ imports):
- ASTNodeDTO → ASTNode (11 imports - critical DSL functionality)
- RebalancePlanDTO → RebalancePlan (6 imports - portfolio orchestration)
- StrategyAllocationDTO → StrategyAllocation (5 imports - strategy allocation)
- StrategySignalDTO → StrategySignal (3 imports - signal generation)

Medium-impact renames (2-4 imports):
- ExecutedOrderDTO → ExecutedOrder
- ExecutionReportDTO → ExecutionReport
- IndicatorRequestDTO → IndicatorRequest
- PortfolioFragmentDTO → PortfolioFragment
```

#### Coordination Required:
- **DSL Engine modules** (ASTNode critical for 8+ files)
- **Orchestration modules** (RebalancePlan, StrategyAllocation)
- **Strategy modules** (StrategySignal, IndicatorRequest)
- **Execution modules** (ExecutedOrder, ExecutionReport)

### Phase 3.3: Remaining Renames and Validation (Week 4)
Complete all remaining class renames and validate.

#### Remaining Renames:
```
Portfolio/State models:
- PortfolioStateDTO → PortfolioState
- PositionDTO → Position
- PortfolioMetricsDTO → PortfolioMetrics
- RebalancePlanItemDTO → RebalancePlanItem
- ConsolidatedPortfolioDTO → ConsolidatedPortfolio

Order/Execution models:
- OrderRequestDTO → OrderRequest
- MarketDataDTO → MarketData
- TradeRunResultDTO → TradeRunResult
- OrderResultSummaryDTO → OrderResultSummary
```

#### Activities:
- [ ] Complete all class renames
- [ ] Update all import statements
- [ ] Maintain temporary aliases during transition
- [ ] Comprehensive integration testing

## Phase 4: Alias Removal and Import Updates (High Risk)
**Duration:** 4-5 weeks  
**Risk Level:** 🟡 **High**  
**Objective:** Remove all backward compatibility aliases and update imports

### Phase 4.1: Low-Impact Alias Removal (Week 1-2)
Remove aliases for classes with minimal usage.

#### Target Aliases to Remove:
```
From enriched_data.py:
- EnrichedOrderDTO = EnrichedOrderView → Remove, use EnrichedOrderView directly
- OpenOrdersDTO = OpenOrdersView → Remove, use OpenOrdersView directly
- EnrichedPositionDTO = EnrichedPositionView → Remove, use EnrichedPositionView directly
- EnrichedPositionsDTO = EnrichedPositionsView → Remove, use EnrichedPositionsView directly

From operations.py:
- OperationResultDTO = OperationResult → Remove, use OperationResult directly
- OrderCancellationDTO = OrderCancellationResult → Remove, use OrderCancellationResult directly
- OrderStatusDTO = OrderStatusResult → Remove, use OrderStatusResult directly

From base.py:
- ResultDTO = Result → Remove, use Result directly
```

#### Process:
1. **Update all imports** to use descriptive names directly
2. **Remove aliases** from schema files
3. **Validate no breaking changes**
4. **Update tests and documentation**

### Phase 4.2: High-Impact Alias Removal (Week 3-4)
Remove aliases for heavily used classes with careful coordination.

#### Target Aliases to Remove:
```
From accounts.py (7 aliases):
- AccountSummaryDTO = AccountSummary → Remove, use AccountSummary directly
- AccountMetricsDTO = AccountMetrics → Remove, use AccountMetrics directly
- BuyingPowerDTO = BuyingPowerResult → Remove, use BuyingPowerResult directly
- RiskMetricsDTO = RiskMetricsResult → Remove, use RiskMetricsResult directly
- TradeEligibilityDTO = TradeEligibilityResult → Remove, use TradeEligibilityResult directly
- PortfolioAllocationDTO = PortfolioAllocationResult → Remove, use PortfolioAllocationResult directly
- EnrichedAccountSummaryDTO = EnrichedAccountSummaryView → Remove, use EnrichedAccountSummaryView directly

From execution_summary.py (6 aliases):
- AllocationSummaryDTO = AllocationSummary → Remove, use AllocationSummary directly
- StrategyPnLSummaryDTO = StrategyPnLSummary → Remove, use StrategyPnLSummary directly
- StrategySummaryDTO = StrategySummary → Remove, use StrategySummary directly
- TradingSummaryDTO = TradingSummary → Remove, use TradingSummary directly
- ExecutionSummaryDTO = ExecutionSummary → Remove, use ExecutionSummary directly
- PortfolioStateDTO = PortfolioState → Remove, use PortfolioState directly

From market_data.py (5 aliases):
- PriceDTO = PriceResult → Remove, use PriceResult directly
- PriceHistoryDTO = PriceHistoryResult → Remove, use PriceHistoryResult directly
- SpreadAnalysisDTO = SpreadAnalysisResult → Remove, use SpreadAnalysisResult directly
- MarketStatusDTO = MarketStatusResult → Remove, use MarketStatusResult directly
- MultiSymbolQuotesDTO = MultiSymbolQuotesResult → Remove, use MultiSymbolQuotesResult directly
```

#### Coordination Required:
- **Orchestration modules** (trading/portfolio orchestrators)
- **Mapping modules** (execution summary mapping)
- **Notification system** (email templates)
- **Broker integration** (account and market data usage)

### Phase 4.3: Final Cleanup and Validation (Week 5)
Complete alias removal and update central imports.

#### Activities:
- [ ] Remove all remaining aliases
- [ ] Update `shared/schemas/__init__.py` exports
- [ ] Remove `shared/dto/` directory (deprecated)
- [ ] Update all module imports to use `shared/schemas/`
- [ ] Comprehensive integration testing
- [ ] Performance validation

## Phase 5: Validation and Documentation (Low Risk)
**Duration:** 1-2 weeks  
**Risk Level:** 🟢 **Low**  
**Objective:** Comprehensive validation and documentation updates

### Phase 5.1: Testing and Validation (Week 1)
#### Activities:
- [ ] Full test suite execution
- [ ] Integration testing across all modules
- [ ] Performance benchmarking
- [ ] Import path validation
- [ ] Backward compatibility verification

### Phase 5.2: Documentation and Cleanup (Week 2)
#### Activities:
- [ ] Update all docstrings
- [ ] Create migration summary report
- [ ] Update architecture documentation
- [ ] Remove temporary migration artifacts
- [ ] Create maintenance guidelines

## Risk Assessment and Mitigation

### Critical Risk Areas

#### 🔴 **Critical Risk: DSL Engine (ASTNode)**
- **Impact:** Core strategy functionality depends on ASTNode (formerly ASTNodeDTO)
- **Files Affected:** 8 modules including DSL evaluator, operators, context
- **Mitigation:** 
  - Comprehensive DSL testing before/after rename
  - Staged rollout with temporary aliases
  - Immediate rollback procedures
  - Test all DSL expressions and evaluation paths

#### 🔴 **Critical Risk: Orchestration Dependencies**
- **Impact:** Cross-module coordination through RebalancePlan, StrategyAllocation
- **Files Affected:** Trading/Portfolio orchestrators, multiple handlers
- **Mitigation:**
  - Test all orchestration workflows thoroughly  
  - Maintain event system compatibility
  - Monitor execution metrics during transition
  - Validate end-to-end trade execution

### High Risk Areas

#### 🟡 **High Risk: Execution Summary Dependencies**
- **Impact:** Reporting and notifications depend on ExecutionSummary models
- **Files Affected:** Mapping modules, notification templates
- **Mitigation:**
  - Validate all report generation
  - Test notification delivery systems
  - Backup notification templates
  - Verify email formatting and data accuracy

#### 🟡 **High Risk: Account and Market Data Models**
- **Impact:** Broker integration and account management
- **Files Affected:** Alpaca manager, account handlers
- **Mitigation:**
  - Test broker API integration thoroughly
  - Validate account data accuracy
  - Monitor market data feeds
  - Ensure trading operations continue correctly

### Medium Risk Areas

#### 🟠 **Medium Risk: Portfolio State Models**
- **Impact:** Portfolio tracking and state management
- **Files Affected:** Portfolio handlers, state tracking
- **Mitigation:**
  - Validate portfolio calculations
  - Test position tracking accuracy
  - Monitor portfolio metrics
  - Ensure rebalancing logic works correctly

## Rollback Procedures

### Per-Phase Rollback Strategy

#### Phase 2 Rollback (Model Consolidation):
1. **Restore original file structure**
   ```bash
   git checkout HEAD~1 -- shared/dto/
   git checkout HEAD~1 -- shared/schemas/
   ```
2. **Remove new schema files** created during consolidation
3. **Restore original `__init__.py` exports**
4. **Validate original import paths work**

#### Phase 3 Rollback (Class Renaming):
1. **Revert class name changes**
   ```bash
   # Restore original class names in all schema files
   git checkout <pre-rename-commit> -- shared/schemas/
   ```
2. **Restore original imports** in consuming modules
3. **Remove temporary aliases** added during transition
4. **Validate all functionality works with original names**

#### Phase 4 Rollback (Alias Removal):
1. **Restore all backward compatibility aliases**
   ```python
   # Re-add all removed aliases
   AccountSummaryDTO = AccountSummary
   ExecutionSummaryDTO = ExecutionSummary
   # ... etc
   ```
2. **Revert import changes** back to using aliases
3. **Restore original `__init__.py` exports**
4. **Full integration testing to ensure compatibility**

### Emergency Rollback (Complete Migration Revert)
```bash
# Git-based rollback to pre-migration state
git revert <migration-commit-range>
git push origin main

# Validate system functionality
make test
make integration-test
```

## Success Metrics

### Quantitative Metrics
- [ ] **Zero breaking changes** to existing functionality
- [ ] **100% test pass rate** maintained throughout migration
- [ ] **Single source of truth** for each boundary model concept
- [ ] **Descriptive naming** across all boundary model classes (no DTO suffix)
- [ ] **Zero backward compatibility aliases** remaining
- [ ] **Consolidated location** - all boundary models in `shared/schemas/`

### Qualitative Metrics
- [ ] **Improved code readability** with descriptive class names
- [ ] **Reduced cognitive overhead** without generic DTO suffixes
- [ ] **Better maintainability** with single location for boundary models
- [ ] **Modern Python practices** following Pydantic v2 conventions
- [ ] **Enhanced developer experience** with clearer import paths
- [ ] **Simplified mental model** - one location, descriptive names

## Timeline Summary

| Phase | Duration | Risk | Key Activities |
|-------|----------|------|----------------|
| **Phase 2** | 2-3 weeks | 🟢 Low | Model consolidation into organized schema structure |
| **Phase 3** | 3-4 weeks | 🟡 Medium | Remove DTO suffixes, use descriptive names |
| **Phase 4** | 4-5 weeks | 🟡 High | Remove aliases, update all imports |
| **Phase 5** | 1-2 weeks | 🟢 Low | Validation, documentation, cleanup |
| **Total** | **10-14 weeks** | | **Complete boundary model modernization** |

## Resource Requirements

### Team Allocation
- **Lead Developer:** Full-time for critical phases (3, 4)
- **Supporting Developers:** Part-time for validation and testing  
- **QA Engineer:** Testing validation for each phase
- **DevOps Engineer:** Deployment and rollback procedures

### Infrastructure Requirements
- **Staging Environment:** Full testing of each phase
- **Monitoring:** Import usage and performance metrics
- **Backup Systems:** Rollback capability at each phase
- **Documentation Platform:** Updated migration tracking

This migration plan provides a comprehensive, low-risk approach to modernizing boundary models following Python and Pydantic v2 best practices, with appropriate safeguards, testing, and rollback procedures at every step.