# DTO Migration Plan

## Overview
This document provides a comprehensive, phased migration plan for standardizing DTO/Schema classes across the alchemiser-quant repository, based on the inventory and usage analysis completed in Phase 1.

**Migration Scope**: 62+ DTO/Schema classes, 130+ import statements, 28 backward compatibility aliases  
**Estimated Timeline**: 4-6 weeks across 4 phases  
**Risk Level**: Medium-High due to cross-module dependencies  

## Executive Summary

### Migration Goals
1. **Standardize Naming**: Consistent DTO suffix usage across all data transfer objects
2. **Consolidate Locations**: Clear separation between DTOs (`shared/dto/`) and Schemas (`shared/schemas/`)
3. **Remove Aliases**: Eliminate backward compatibility aliases to reduce import confusion
4. **Improve Consistency**: Align naming conventions within each category

### Success Criteria
- [ ] All DTO classes follow consistent naming convention (`*DTO` suffix)
- [ ] All schema classes follow descriptive naming (no DTO suffix)
- [ ] Zero backward compatibility aliases remaining
- [ ] All imports updated to use canonical class names
- [ ] No breaking changes to public APIs
- [ ] Comprehensive test coverage maintained

## 1. Migration Strategy

### 1.1 Four-Phase Approach

| Phase | Focus | Risk Level | Duration | Dependencies |
| --- | --- | --- | --- | --- |
| **Phase 1** | Inventory & Planning | Low | 1 week | None |
| **Phase 2** | Schema Consolidation | Medium | 1-2 weeks | Phase 1 complete |
| **Phase 3** | Alias Removal | High | 2-3 weeks | Phase 2 complete |
| **Phase 4** | Import Updates & Cleanup | High | 1-2 weeks | Phase 3 complete |

### 1.2 Guiding Principles

1. **Backward Compatibility**: Maintain aliases during transition
2. **Incremental Changes**: Small, testable changes per PR
3. **High Test Coverage**: Comprehensive testing before any changes
4. **Clear Communication**: Document all changes and impact
5. **Rollback Ready**: Each phase can be independently rolled back

## 2. Phase 1: Inventory & Planning ✅ COMPLETE

### 2.1 Deliverables (Complete)
- [x] DTO/Schema inventory document
- [x] Usage analysis with dependency mapping  
- [x] Migration plan with risk assessment
- [x] Baseline test coverage assessment

### 2.2 Key Findings
- **62+ classes** across dto/ and schemas/ directories
- **28 active aliases** providing backward compatibility
- **130+ import statements** across all modules
- **High-impact DTOs** identified: `ASTNodeDTO`, `RebalancePlanDTO`

## 3. Phase 2: Schema Consolidation & Standardization

### 3.1 Objectives
- Resolve naming inconsistencies within schema files
- Standardize schema class naming conventions
- Prepare for alias removal in Phase 3

### 3.2 Target Changes

#### 3.2.1 Schema Naming Standardization

**Current Inconsistencies to Fix**:

| File | Current Name | Issue | Proposed Action |
| --- | --- | --- | --- |
| `schemas/common.py` | `MultiStrategyExecutionResultDTO` | DTO suffix in schema | Remove DTO suffix |
| `schemas/common.py` | `AllocationComparisonDTO` | DTO suffix in schema | Remove DTO suffix |
| `schemas/common.py` | `MultiStrategySummaryDTO` | DTO suffix in schema | Remove DTO suffix |

**Proposed Changes**:
```python
# BEFORE (schemas/common.py)
class MultiStrategyExecutionResultDTO(BaseModel): ...
class AllocationComparisonDTO(BaseModel): ...  
class MultiStrategySummaryDTO(BaseModel): ...

# AFTER (schemas/common.py)
class MultiStrategyExecutionResult(BaseModel): ...
class AllocationComparison(BaseModel): ...
class MultiStrategySummary(BaseModel): ...

# Maintain aliases temporarily
MultiStrategyExecutionResultDTO = MultiStrategyExecutionResult
AllocationComparisonDTO = AllocationComparison
MultiStrategySummaryDTO = MultiStrategySummary
```

#### 3.2.2 DTO File Standardization

**Missing DTO Suffixes to Add**:

| File | Current Name | Issue | Proposed Action |
| --- | --- | --- | --- |
| `dto/broker_dto.py` | `WebSocketResult` | Missing DTO suffix | Add DTO suffix |
| `dto/broker_dto.py` | `OrderExecutionResult` | Missing DTO suffix | Add DTO suffix |
| `dto/execution_dto.py` | `ExecutionResult` | Missing DTO suffix | Add DTO suffix |

**Proposed Changes**:
```python
# BEFORE (dto/broker_dto.py)
class WebSocketResult(BaseModel): ...
class OrderExecutionResult(Result): ...

# AFTER (dto/broker_dto.py)  
class WebSocketResultDTO(BaseModel): ...
class OrderExecutionResultDTO(Result): ...

# Maintain aliases temporarily
WebSocketResult = WebSocketResultDTO
OrderExecutionResult = OrderExecutionResultDTO
```

### 3.3 Implementation Plan

#### Week 1: Schema Files
- [ ] **Day 1-2**: Update `schemas/common.py` naming
- [ ] **Day 3-4**: Add comprehensive tests for schema changes
- [ ] **Day 5**: Validate no breaking changes, deploy

#### Week 2: DTO Files  
- [ ] **Day 1-2**: Update DTO files with missing suffixes
- [ ] **Day 3-4**: Add comprehensive tests for DTO changes
- [ ] **Day 5**: Validate no breaking changes, deploy

### 3.4 Risk Assessment

**Risk Level**: Medium
- **Impact**: Name changes affect imports, but aliases maintain compatibility
- **Mitigation**: Comprehensive testing, gradual rollout
- **Rollback**: Simple revert of naming changes

**Success Metrics**:
- All schema classes use descriptive naming (no DTO suffix)
- All DTO classes use DTO suffix consistently
- Zero breaking changes to existing imports
- 100% test coverage maintained

## 4. Phase 3: Alias Removal & Import Migration

### 4.1 Objectives
- Remove all 28 backward compatibility aliases
- Update all import statements to use canonical names
- Maintain zero breaking changes to public APIs

### 4.2 Staged Alias Removal Strategy

#### 4.2.1 Tier-Based Removal (3 weeks)

**Tier 1 - Low Risk** (Week 1): Single-use aliases
- Schema aliases with 1-2 import usages
- Utility and reporting aliases
- TypedDict aliases (non-breaking)

**Tier 2 - Medium Risk** (Week 2): Moderate usage aliases  
- Schema aliases with 3-5 import usages
- Cross-module but non-critical aliases
- Internal module aliases

**Tier 3 - High Risk** (Week 3): Critical aliases
- High-usage aliases (5+ imports)
- Core execution flow aliases
- Event payload aliases

#### 4.2.2 Detailed Removal Plan

**Tier 1 Aliases** (Low Risk - Week 1):
```python
# Remove these aliases first:
ResultDTO = Result  # 1 usage
PriceDTO = PriceResult  # 1 usage
PriceHistoryDTO = PriceHistoryResult  # 1 usage
SpreadAnalysisDTO = SpreadAnalysisResult  # 1 usage
MarketStatusDTO = MarketStatusResult  # 1 usage
MultiSymbolQuotesDTO = MultiSymbolQuotesResult  # 1 usage
OperationResultDTO = OperationResult  # 1 usage
OrderCancellationDTO = OrderCancellationResult  # 1 usage
OrderStatusDTO = OrderStatusResult  # 1 usage
```

**Tier 2 Aliases** (Medium Risk - Week 2):
```python
# Remove these aliases second:
AccountMetricsDTO = AccountMetrics  # 2-3 usages
BuyingPowerDTO = BuyingPowerResult  # 2-3 usages
RiskMetricsDTO = RiskMetricsResult  # 2-3 usages
TradeEligibilityDTO = TradeEligibilityResult  # 2-3 usages
PortfolioAllocationDTO = PortfolioAllocationResult  # 2-3 usages
EnrichedOrderDTO = EnrichedOrderView  # 2-3 usages
OpenOrdersDTO = OpenOrdersView  # 2-3 usages
EnrichedPositionDTO = EnrichedPositionView  # 2-3 usages
EnrichedPositionsDTO = EnrichedPositionsView  # 2-3 usages
```

**Tier 3 Aliases** (High Risk - Week 3):
```python
# Remove these aliases last:
AccountSummaryDTO = AccountSummary  # 5+ usages
AllocationComparisonDTO = AllocationComparison  # 3+ usages (after Phase 2)
MultiStrategyExecutionResultDTO = MultiStrategyExecutionResult  # 2+ usages
EnrichedAccountSummaryDTO = EnrichedAccountSummaryView  # 3+ usages
# Execution summary aliases (6 total)
AllocationSummaryDTO = AllocationSummary
StrategyPnLSummaryDTO = StrategyPnLSummary
StrategySummaryDTO = StrategySummary
TradingSummaryDTO = TradingSummary
ExecutionSummaryDTO = ExecutionSummary
PortfolioStateDTO = PortfolioState  # High usage in schemas
```

### 4.3 Import Update Process

#### 4.3.1 Automated Import Updates

**Tool-Based Updates**:
```bash
# Example sed commands for bulk updates
find . -name "*.py" -exec sed -i 's/ResultDTO/Result/g' {} \;
find . -name "*.py" -exec sed -i 's/PriceDTO/PriceResult/g' {} \;
```

**Validation Script**:
```python
# Create validation script to ensure no broken imports
import ast
import os

def validate_imports(file_path):
    """Validate all imports in a Python file."""
    # Implementation to check import validity
```

#### 4.3.2 Import Update Strategy by Module

**Week 1**: Update imports in non-critical modules
- Reporting and notification modules
- Utility modules  
- CLI modules

**Week 2**: Update imports in business modules
- Strategy v2 (coordinate with DSL team)
- Portfolio v2 (coordinate with portfolio team)  
- Execution v2 (coordinate with execution team)

**Week 3**: Update imports in orchestration
- Event handlers
- Workflow coordinators
- Cross-module interfaces

### 4.4 Risk Assessment

**Risk Level**: High
- **Breaking Changes**: High potential for import failures
- **Cross-Module Impact**: Changes affect all business modules
- **Testing Complexity**: Requires comprehensive integration testing

**Mitigation Strategies**:
1. **Comprehensive Testing**: 100% test coverage before changes
2. **Staged Rollout**: Tier-based removal reduces blast radius
3. **Automated Validation**: Scripts to validate import correctness
4. **Quick Rollback**: Ability to restore aliases rapidly
5. **Team Coordination**: Close coordination with all module owners

### 4.5 Testing Strategy

**Pre-Migration Testing**:
- [ ] Full test suite passes (100% success rate)
- [ ] Import validation scripts created and tested
- [ ] Rollback procedures tested and documented

**Per-Tier Testing**:
- [ ] Unit tests for affected modules
- [ ] Integration tests for cross-module interactions
- [ ] End-to-end tests for critical workflows
- [ ] Import validation after each tier

**Post-Migration Testing**:
- [ ] Full regression test suite
- [ ] Performance validation
- [ ] Memory usage validation
- [ ] Production smoke tests

## 5. Phase 4: Import Updates & Final Cleanup

### 5.1 Objectives
- Complete migration of all import statements
- Remove temporary aliases and transitional code
- Validate system integrity and performance
- Update documentation and type hints

### 5.2 Final Cleanup Tasks

#### 5.2.1 Code Cleanup (Week 1)
- [ ] Remove all temporary aliases
- [ ] Update all docstrings and comments
- [ ] Validate consistent imports across all files
- [ ] Remove unused imports

#### 5.2.2 Documentation Updates (Week 2)
- [ ] Update API documentation
- [ ] Update developer guides
- [ ] Update migration documentation
- [ ] Create final migration report

### 5.3 Validation & Sign-off

**Final Validation Checklist**:
- [ ] Zero import errors across entire codebase
- [ ] All tests pass (unit, integration, end-to-end)
- [ ] No performance regressions
- [ ] Documentation updated and accurate
- [ ] Code review and approval from all teams

## 6. Risk Management

### 6.1 Risk Assessment Matrix

| Risk Category | Probability | Impact | Mitigation |
| --- | --- | --- | --- |
| Import Failures | High | High | Comprehensive testing, staged rollout |
| Cross-Module Breaking Changes | Medium | High | Team coordination, parallel imports |
| Performance Degradation | Low | Medium | Performance testing, monitoring |
| Test Coverage Gaps | Medium | High | Pre-migration test audits |
| Team Coordination Issues | Medium | Medium | Clear communication, documentation |

### 6.2 Contingency Plans

**Import Failure Recovery**:
1. Immediate rollback to previous aliases
2. Hotfix for critical import issues
3. Phased re-rollout with fixes

**Cross-Module Integration Issues**:
1. Module-by-module rollback capability
2. Temporary parallel import support
3. Emergency bypass procedures

**Performance Issues**:
1. Performance monitoring during rollout
2. Rollback triggers for performance degradation
3. Optimization patches ready

### 6.3 Success Metrics & KPIs

**Technical Metrics**:
- Zero import errors in production
- 100% test suite pass rate maintained
- No performance regression >5%
- Code complexity metrics maintained or improved

**Process Metrics**:
- Migration completed within planned timeline
- Zero unplanned rollbacks
- Team satisfaction scores >4/5
- Documentation completeness >95%

## 7. Communication Plan

### 7.1 Stakeholder Communication

**Weekly Updates**: Progress reports to all teams
**Milestone Reviews**: End-of-phase demos and assessments  
**Risk Alerts**: Immediate notification of high-risk issues
**Final Report**: Complete migration summary and lessons learned

### 7.2 Documentation Deliverables

**Phase 2**: Schema standardization guide
**Phase 3**: Import migration guide and automation scripts
**Phase 4**: Final migration report and best practices
**Ongoing**: Updated developer onboarding materials

## 8. Timeline Summary

### 8.1 Detailed Schedule

| Week | Phase | Activities | Deliverables |
| --- | --- | --- | --- |
| 1 | Phase 1 | Inventory & Analysis | ✅ Complete |
| 2-3 | Phase 2 | Schema Consolidation | Standardized schemas |
| 4-6 | Phase 3 | Alias Removal | Updated imports |
| 7-8 | Phase 4 | Final Cleanup | Migration complete |

### 8.2 Milestones & Gates

**Phase 2 Gate**: Schema naming standardized, no breaking changes
**Phase 3 Gate**: All aliases removed, imports updated, tests passing
**Phase 4 Gate**: Final validation complete, documentation updated
**Final Gate**: Production deployment successful, monitoring healthy

## 9. Post-Migration

### 9.1 Monitoring Plan

**Immediate (First Week)**:
- Import error monitoring
- Performance metrics tracking
- Test suite health monitoring

**Short-term (First Month)**:
- Developer experience feedback
- Code quality metrics
- System stability monitoring

**Long-term (Ongoing)**:
- Naming convention compliance
- New DTO creation guidelines
- Periodic consistency audits

### 9.2 Lessons Learned & Process Improvement

**Success Factors**:
- Comprehensive upfront analysis
- Staged, risk-based approach
- Strong team coordination
- Automated validation tools

**Areas for Improvement**:
- Earlier stakeholder engagement
- More granular testing automation
- Better rollback automation
- Improved change communication

---

*Generated: Phase 1 DTO Migration Plan*