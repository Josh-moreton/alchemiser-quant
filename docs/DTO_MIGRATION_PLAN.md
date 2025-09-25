# DTO Migration Plan

**Business Unit:** shared | **Status:** plan  
**Generated:** Phase 1 of DTO Standardization Migration  
**Target:** Detailed phased migration approach with risk management

## Overview

This document outlines a comprehensive, phased approach to standardizing DTO/Schema classes across the alchemiser-quant codebase. The plan prioritizes risk mitigation, backward compatibility, and minimal disruption to business operations.

## Migration Objectives

### Primary Goals
1. **Consolidate** DTO/Schema classes into a unified structure
2. **Standardize** naming conventions across all data transfer objects
3. **Eliminate** backward compatibility aliases in a controlled manner
4. **Reduce** import complexity and potential conflicts
5. **Maintain** 100% backward compatibility during transition

### Success Criteria
- [ ] All DTO classes follow consistent naming convention (`*DTO` suffix)
- [ ] Single source of truth for each data concept
- [ ] Zero breaking changes to existing functionality
- [ ] Improved import clarity and reduced conflicts
- [ ] Comprehensive test coverage validates all changes
- [ ] Documentation reflects new structure

## Migration Strategy

### Core Principles
1. **Backward Compatibility First** - Maintain aliases until full migration
2. **Incremental Changes** - Small, validated steps with rollback points
3. **Dependency Order** - Migrate leaf dependencies before core components
4. **Comprehensive Testing** - Validate each phase before proceeding
5. **Documentation Driven** - Update docs alongside code changes

### Risk Management Approach
- **Aliases Maintained** throughout migration phases
- **Rollback Points** at end of each phase
- **Canary Testing** for high-risk changes
- **Monitoring** import usage patterns during migration

## Detailed Migration Phases

## Phase 2: Schema Consolidation (Low Risk)
**Duration:** 2-3 weeks  
**Risk Level:** 🟢 **Low**  
**Objective:** Consolidate and standardize schema definitions

### Phase 2.1: Single-Import Schema Classes (Week 1)
Classes imported by only 1-2 files - minimal impact.

#### Target Classes:
```
errors.py schemas:
- ErrorContextData
- ErrorDetailInfo  
- ErrorNotificationData
- ErrorReportSummary
- ErrorSummaryData

reporting.py schemas:
- EmailCredentials
- [Other reporting schemas]

cli.py schemas:
- [CLI-related schemas]
```

#### Changes:
1. **Standardize class names** to include `DTO` suffix where missing
2. **Update imports** in consuming files
3. **Maintain backward compatibility aliases**
4. **Update `shared/schemas/__init__.py`** exports

#### Validation Steps:
- [ ] Run full test suite
- [ ] Validate import paths
- [ ] Check no breaking changes
- [ ] Update documentation

### Phase 2.2: Medium-Import Schema Classes (Week 2)
Classes imported by 3-4 files - moderate coordination needed.

#### Target Classes:
```
market_data.py aliases:
- PriceDTO = PriceResult
- PriceHistoryDTO = PriceHistoryResult  
- SpreadAnalysisDTO = SpreadAnalysisResult
- MarketStatusDTO = MarketStatusResult
- MultiSymbolQuotesDTO = MultiSymbolQuotesResult

operations.py aliases:
- OperationResultDTO = OperationResult
- OrderCancellationDTO = OrderCancellationResult
- OrderStatusDTO = OrderStatusResult
```

#### Changes:
1. **Rename classes** to use DTO suffix: `PriceResult` → `PriceDTO`
2. **Update all imports** across consuming modules
3. **Maintain temporary aliases** for external compatibility
4. **Batch related changes** by schema file

### Phase 2.3: Schema Documentation and Cleanup (Week 3)
Complete schema phase with documentation and validation.

#### Activities:
- [ ] Update all schema docstrings
- [ ] Validate naming consistency
- [ ] Remove unused imports
- [ ] Update migration documentation
- [ ] Create rollback procedures

## Phase 3: Alias Removal (Medium Risk)
**Duration:** 3-4 weeks  
**Risk Level:** 🟡 **Medium**  
**Objective:** Remove backward compatibility aliases systematically

### Phase 3.1: Low-Impact Alias Removal (Week 1)
Remove aliases for classes with single import sources.

#### Target Aliases:
```
base.py:
- ResultDTO = Result → Remove alias, rename to ResultDTO

enriched_data.py:
- EnrichedOrderDTO = EnrichedOrderView → Rename and remove alias
- OpenOrdersDTO = OpenOrdersView → Rename and remove alias
- EnrichedPositionDTO = EnrichedPositionView → Rename and remove alias  
- EnrichedPositionsDTO = EnrichedPositionsView → Rename and remove alias
```

#### Process:
1. **Rename schema classes** to use DTO suffix
2. **Update imports** in all consuming files
3. **Remove aliases** after import updates
4. **Validate no breaking changes**

### Phase 3.2: High-Impact Alias Removal (Week 2-3)
Remove aliases for heavily used classes with coordination.

#### Target Aliases:
```
accounts.py:
- AccountSummaryDTO = AccountSummary
- AccountMetricsDTO = AccountMetrics
- BuyingPowerDTO = BuyingPowerResult
- RiskMetricsDTO = RiskMetricsResult
- TradeEligibilityDTO = TradeEligibilityResult  
- PortfolioAllocationDTO = PortfolioAllocationResult
- EnrichedAccountSummaryDTO = EnrichedAccountSummaryView

execution_summary.py:
- AllocationSummaryDTO = AllocationSummary
- StrategyPnLSummaryDTO = StrategyPnLSummary
- StrategySummaryDTO = StrategySummary
- TradingSummaryDTO = TradingSummary
- ExecutionSummaryDTO = ExecutionSummary
- PortfolioStateDTO = PortfolioState
```

#### Coordination Required:
- **Orchestration modules** (trading/portfolio orchestrators)
- **Mapping modules** (execution summary mapping)
- **Notification system** (email templates)

### Phase 3.3: Alias Cleanup and Validation (Week 4)
Final alias removal and comprehensive testing.

#### Activities:
- [ ] Remove all remaining aliases
- [ ] Update `__init__.py` exports
- [ ] Comprehensive integration testing
- [ ] Performance validation
- [ ] Update migration documentation

## Phase 4: Import Standardization (High Risk)
**Duration:** 4-5 weeks  
**Risk Level:** 🟡 **High**  
**Objective:** Standardize all import patterns and resolve conflicts

### Phase 4.1: DTO Import Consolidation (Week 1-2)
Standardize imports for existing DTO classes.

#### Focus Areas:
```
High-impact DTOs requiring careful migration:
- ASTNodeDTO (8 files) - DSL core functionality
- RebalancePlanDTO (5 files) - Portfolio orchestration  
- StrategyAllocationDTO (4 files) - Strategy allocation
- PortfolioFragmentDTO (3 files) - DSL operations
```

#### Process:
1. **Audit current imports** for each high-impact DTO
2. **Standardize import paths** to use consistent sources
3. **Update consuming modules** in dependency order
4. **Validate DSL functionality** (critical for ASTNodeDTO)

### Phase 4.2: Conflict Resolution (Week 3)
Resolve import conflicts and naming duplications.

#### Identified Conflicts:
```
1. PortfolioStateDTO duplication:
   - shared/dto/portfolio_state_dto.py (primary)
   - shared/schemas/execution_summary.py (alias)
   Resolution: Keep DTO version, remove schema alias

2. ExecutionSummaryDTO duplication:
   - shared/dto/trade_run_result_dto.py (primary)
   - shared/schemas/execution_summary.py (alias)  
   Resolution: Consolidate to single implementation

3. Result vs ResultDTO inconsistency:
   - shared/schemas/base.py
   Resolution: Standardize on ResultDTO naming
```

#### Resolution Process:
1. **Choose canonical implementation** for each conflicted class
2. **Update all imports** to use canonical source
3. **Remove duplicate implementations**
4. **Validate no functionality loss**

### Phase 4.3: Central Import Cleanup (Week 4-5)
Update central aggregation points and finalize imports.

#### Target Files:
- `shared/dto/__init__.py` (12 imports - highest impact)
- `shared/schemas/__init__.py` 
- Module-level `__init__.py` files

#### Activities:
- [ ] Consolidate exports in `__init__.py` files
- [ ] Remove unused imports
- [ ] Standardize export patterns
- [ ] Update dependency documentation
- [ ] Final integration testing

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

#### 🔴 **Critical Risk: DSL Engine (ASTNodeDTO)**
- **Impact:** Core strategy functionality
- **Files Affected:** 8 modules
- **Mitigation:** 
  - Comprehensive DSL testing before/after
  - Staged rollout with canary testing
  - Immediate rollback procedures

#### 🔴 **Critical Risk: Central Aggregation (`shared/dto/__init__.py`)**
- **Impact:** All DTO imports
- **Files Affected:** 40+ modules
- **Mitigation:**
  - Maintain backward compatibility aliases
  - Coordinate with all team members
  - Weekend deployment window

### High Risk Areas

#### 🟡 **High Risk: Orchestration Dependencies**
- **Impact:** Cross-module coordination
- **Files Affected:** Trading/Portfolio orchestrators
- **Mitigation:**
  - Test orchestration workflows thoroughly
  - Maintain event compatibility
  - Monitor execution metrics

#### 🟡 **High Risk: Execution Summary Dependencies**
- **Impact:** Reporting and notifications
- **Files Affected:** Mapping and notification modules
- **Mitigation:**
  - Validate all report formats
  - Test notification delivery
  - Backup notification templates

## Rollback Procedures

### Per-Phase Rollback Strategy

#### Phase 2 Rollback:
1. Revert schema class renames
2. Restore original import paths
3. Remove new aliases
4. Validate original functionality

#### Phase 3 Rollback:
1. Restore removed aliases
2. Revert class name changes
3. Update imports back to aliases
4. Validate backward compatibility

#### Phase 4 Rollback:
1. Restore duplicate implementations
2. Revert import standardization
3. Restore original `__init__.py` files
4. Full integration testing

### Emergency Rollback (Complete)
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
- [ ] **Single source of truth** for each DTO concept
- [ ] **Consistent naming** across all DTO classes (`*DTO` suffix)
- [ ] **Reduced import complexity** (eliminate conflicts)

### Qualitative Metrics
- [ ] **Improved developer experience** with clearer import paths
- [ ] **Better maintainability** with standardized structure
- [ ] **Enhanced documentation** reflecting new architecture
- [ ] **Reduced cognitive overhead** for new developers

## Timeline Summary

| Phase | Duration | Risk | Key Activities |
|-------|----------|------|----------------|
| **Phase 2** | 2-3 weeks | 🟢 Low | Schema consolidation and standardization |
| **Phase 3** | 3-4 weeks | 🟡 Medium | Systematic alias removal |
| **Phase 4** | 4-5 weeks | 🟡 High | Import standardization and conflict resolution |
| **Phase 5** | 1-2 weeks | 🟢 Low | Validation and documentation |
| **Total** | **10-14 weeks** | | **Complete DTO standardization** |

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

This migration plan provides a comprehensive, low-risk approach to DTO standardization with appropriate safeguards, testing, and rollback procedures at every step.