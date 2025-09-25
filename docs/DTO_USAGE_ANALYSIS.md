# Boundary Model Usage Analysis

## Overview
This document provides detailed analysis of boundary model import patterns and dependencies across the alchemiser-quant codebase, supporting the migration plan to remove DTO suffixes and use descriptive names following modern Python/Pydantic v2 best practices.

**Analysis Date**: Phase 1 Initial Assessment (Revised)  
**Repository**: Josh-moreton/alchemiser-quant  
**Total Import Statements Analyzed**: 130+  
**Migration Goal**: Remove DTO suffixes, use descriptive names, consolidate to `shared/schemas/`  

## 1. Module-Level Usage Distribution

### 1.1 Boundary Model Import Counts by Business Module

| Module | Model Imports | Primary Usage |
| --- | --- | --- |
| `strategy_v2/` | 32 | DSL engine, indicators, signal generation |
| `orchestration/` | 19 | Cross-module coordination, event handling |
| `execution_v2/` | 9 | Order execution, portfolio rebalancing |
| `portfolio_v2/` | 9 | Portfolio state management, analysis |
| `shared/` | 61+ | Model definitions, utilities, events |

### 1.2 Usage Intensity Analysis

**High Usage Modules** (20+ imports):
- `strategy_v2/` - Heavy DSL and indicator model usage
- `shared/` - Model definitions and cross-cutting utilities

**Medium Usage Modules** (10-19 imports):
- `orchestration/` - Event-driven coordination layer

**Lower Usage Modules** (<10 imports):
- `execution_v2/`, `portfolio_v2/` - Focused, domain-specific usage

## 2. Top Boundary Model Classes by Import Frequency

### 2.1 Most Frequently Imported Models (Rename Required)

| Rank | Current Name | Import Count | Proposed Name | Primary Modules | Usage Type |
| --- | --- | --- | --- | --- | --- |
| 1 | `ASTNodeDTO` | 11 | `ASTNode` | strategy_v2 | DSL parsing, evaluation |
| 2 | `RebalancePlanDTO` | 6 | `RebalancePlan` | execution_v2, orchestration | Portfolio rebalancing |
| 3 | `StrategyAllocationDTO` | 5 | `StrategyAllocation` | strategy_v2, orchestration | Strategy allocations |
| 3 | `ExecutionResultDTO` | 5 | `ExecutionResult` | execution_v2 | Trade execution results |
| 5 | `PortfolioFragmentDTO` | 4 | `PortfolioFragment` | strategy_v2 | DSL portfolio fragments |
| 6 | `AllocationComparisonDTO` | 3 | `AllocationComparison` | orchestration, shared | Portfolio comparisons |
| 6 | `TraceDTO` | 3 | `Trace` | strategy_v2 | DSL evaluation tracing |
| 6 | `TechnicalIndicatorDTO` | 3 | `TechnicalIndicator` | strategy_v2 | Technical indicators |
| 6 | `MarketBarDTO` | 3 | `MarketBar` | strategy_v2 | Market data |
| 6 | `AssetInfoDTO` | 3 | `AssetInfo` | execution_v2 | Asset validation |

### 2.2 Medium Usage Models (2 imports)

| Current Name | Proposed Name | Import Count | Usage Areas |
| --- | --- | --- | --- |
| `MultiStrategyExecutionResultDTO` | `MultiStrategyExecutionResult` | 2 | Execution results, notifications |
| `StrategySignalDTO` | `StrategySignal` | 2 | Signal generation, events |
| `PortfolioStateDTO` | `PortfolioState` | 2 | Portfolio management, schema refs |
| `IndicatorRequestDTO` | `IndicatorRequest` | 2 | Indicator requests, DSL |
| `ExecutedOrderDTO` | `ExecutedOrder` | 2 | Order execution tracking |

### 2.3 Single-Use Models (1 import)

Many models are used only once or in specialized contexts:
- `TradeRunResultDTO` → `TradeRunResult`
- `LambdaEventDTO` → `LambdaEvent`
- `ConsolidatedPortfolioDTO` → `ConsolidatedPortfolio`
- Most schema-based models (already have correct names)

## 3. Module-Specific Dependency Analysis

## 3. Module-Specific Dependency Analysis

### 3.1 Strategy v2 Module Dependencies

**Primary Model Dependencies** (32 total imports):
- **DSL Engine** (Heavy usage):
  - `ASTNodeDTO` → `ASTNode` - Core AST representation
  - `TraceDTO` → `Trace` - Evaluation tracing
  - `PortfolioFragmentDTO` → `PortfolioFragment` - Intermediate allocations
  - `IndicatorRequestDTO` → `IndicatorRequest` - Technical indicator requests

- **Market Data & Indicators**:
  - `TechnicalIndicatorDTO` → `TechnicalIndicator` - Indicator results
  - `MarketBarDTO` → `MarketBar` - OHLCV data
  - `StrategyAllocationDTO` → `StrategyAllocation` - Final allocations

**Migration Impact**: **HIGH** - Heavy model dependency, core to DSL functionality
**Naming Changes**: All major classes need DTO suffix removal

### 3.2 Execution v2 Module Dependencies

**Primary Model Dependencies** (9 total imports):
- **Core Execution**:
  - `RebalancePlanDTO` → `RebalancePlan` - Rebalancing instructions
  - `ExecutionResultDTO` → `ExecutionResult` - Internal execution results
  - `ExecutedOrderDTO` → `ExecutedOrder` - Individual order results
  - `AssetInfoDTO` → `AssetInfo` - Asset validation

**Migration Impact**: **MEDIUM** - Focused usage, critical for execution flow
**Naming Changes**: All imports need class name updates

### 3.3 Orchestration Module Dependencies

**Primary Model Dependencies** (19 total imports):
- **Cross-Module Coordination**:
  - `RebalancePlanDTO` → `RebalancePlan` - Portfolio rebalancing coordination
  - `StrategyAllocationDTO` → `StrategyAllocation` - Strategy output handling
  - `AllocationComparisonDTO` → `AllocationComparison` - Portfolio comparisons
  - `MultiStrategyExecutionResultDTO` → `MultiStrategyExecutionResult` - Execution results

**Migration Impact**: **HIGH** - Central coordination role, touches all modules
**Naming Changes**: All cross-module model imports need updates

### 3.4 Portfolio v2 Module Dependencies

**Primary Model Dependencies** (9 total imports):
- **Portfolio Management**:
  - `PortfolioStateDTO` → `PortfolioState` - Portfolio state representation
  - Related allocation and metrics models

**Migration Impact**: **MEDIUM** - Specialized usage, important for portfolio operations
**Naming Changes**: Portfolio-related model imports need updates

## 4. Import Pattern Analysis

### 4.1 Current Import Patterns (To Update)

**Direct Model Imports with DTO Suffixes** (85%):
```python
# CURRENT (problematic)
from the_alchemiser.shared.dto.rebalance_plan_dto import RebalancePlanDTO
from the_alchemiser.shared.dto.ast_node_dto import ASTNodeDTO

# TARGET (corrected)
from the_alchemiser.shared.schemas.portfolio import RebalancePlan
from the_alchemiser.shared.schemas.dsl import ASTNode
```

**Schema Imports via Aliases** (15%):
```python
# CURRENT (aliases to remove)
from the_alchemiser.shared.schemas.common import AllocationComparisonDTO
from the_alchemiser.shared.schemas.common import MultiStrategyExecutionResultDTO

# TARGET (direct descriptive names)
from the_alchemiser.shared.schemas.common import AllocationComparison
from the_alchemiser.shared.schemas.common import MultiStrategyExecutionResult
```

### 4.2 Target Import Path Patterns

1. **Consolidated Schema Imports**: `from the_alchemiser.shared.schemas.{domain} import {Model}`
2. **Domain Organization**: Models grouped by business domain, not technical classification
3. **Descriptive Names**: Class names describe domain purpose, not technical pattern

### 4.3 Import Update Strategy

**Phase 1**: Remove DTO suffixes from class names
**Phase 2**: Remove all backward compatibility aliases
**Phase 3**: Consolidate files by domain (optional optimization)
**Phase 4**: Update all import statements

### 4.4 Circular Import Risk Assessment

**Low Risk**: Proper layered architecture maintained
- Shared models imported by business modules
- Business modules don't import each other's models directly
- Event-driven communication reduces direct coupling

**Potential Issues**:
- Some orchestration imports could create tight coupling
- Internal module models (`ExecutionResultDTO`) may need attention during consolidation

## 5. High-Impact Change Assessment

### 5.1 Critical Models (High Breaking Risk)

**Tier 1 - Maximum Impact** (>5 imports, core functionality):
- `ASTNodeDTO` → `ASTNode` (11 imports) - Core DSL functionality
- `RebalancePlanDTO` → `RebalancePlan` (6 imports) - Core execution flow

**Tier 2 - High Impact** (3-5 imports, significant cross-module usage):
- `StrategyAllocationDTO` → `StrategyAllocation`
- `ExecutionResultDTO` → `ExecutionResult`
- `PortfolioFragmentDTO` → `PortfolioFragment`
- `AllocationComparisonDTO` → `AllocationComparison`
- `TraceDTO` → `Trace`
- `TechnicalIndicatorDTO` → `TechnicalIndicator`

**Tier 3 - Medium Impact** (2 imports, focused usage):
- `MultiStrategyExecutionResultDTO` → `MultiStrategyExecutionResult`
- `StrategySignalDTO` → `StrategySignal`
- `PortfolioStateDTO` → `PortfolioState`

### 5.2 Low-Risk Models

**Single Import Models**: Can be renamed with minimal coordination
- Specialized reporting models
- Lambda-specific models
- One-off utility models
- Models already using descriptive names

### 5.3 Migration Benefits vs. Risks

**Benefits**:
- **Semantic Clarity**: Names describe domain purpose, not technical pattern
- **Modern Compliance**: Follows Python/Pydantic v2 best practices
- **Reduced Confusion**: No more dual naming (class vs. alias)
- **Better Organization**: Domain-based grouping instead of technical classification

**Risks**:
- **Import Failures**: 130+ import statements need coordinated updates
- **Name Conflicts**: Some class names might conflict during consolidation
- **Team Coordination**: All modules affected simultaneously

## 6. Migration Dependency Graph

### 6.1 Migration Order Recommendations (Revised)

**Phase 1 - Remove DTO Suffixes** (Medium Risk):
- Rename all classes to remove DTO suffixes
- Keep aliases temporarily for backward compatibility
- Update class definitions but not imports yet

**Phase 2 - Remove Aliases** (High Risk, Staged):
- **Stage 1**: Low-impact aliases (single-use models)
- **Stage 2**: Medium-impact aliases (2-3 imports)
- **Stage 3**: High-impact aliases (core business models)

**Phase 3 - Consolidate Files** (Low Risk, Optional):
- Move models to domain-organized files
- Update import paths to new locations
- Remove empty dto/ files

**Phase 4 - Final Cleanup** (Low Risk):
- Remove dto/ directory
- Update documentation
- Validate all imports

### 6.2 Dependency Constraints

**Hard Dependencies** (Must be updated together):
- DSL cluster: `ASTNode`, `Trace`, `PortfolioFragment`
- Execution cluster: `RebalancePlan`, `ExecutionResult`, `ExecutedOrder`
- Allocation cluster: `StrategyAllocation`, `AllocationComparison`

**Soft Dependencies** (Can be updated independently):
- Reporting models
- Market data models
- Asset information models
- Infrastructure models

### 6.3 Rollback Strategy

**Granular Rollback**: Each phase can be independently rolled back
- **Phase 1 Rollback**: Restore DTO suffixes to class names
- **Phase 2 Rollback**: Restore specific aliases that caused issues
- **Phase 3 Rollback**: Move models back to original files
- **Phase 4 Rollback**: Restore documentation and directory structure

## 7. Testing Impact Analysis

### 7.1 Test Coverage Assessment

**High Test Impact Areas**:
- DSL engine tests (ASTNodeDTO usage)
- Execution flow tests (RebalancePlanDTO usage)
- Strategy tests (allocation DTOs)

**Medium Test Impact Areas**:
- Integration tests (cross-module DTO usage)
- Event handling tests (event payload DTOs)

**Low Test Impact Areas**:
- Utility function tests
- Single-purpose DTO tests

### 7.2 Testing Strategy Recommendations

1. **Pre-Migration Testing**: Establish comprehensive test coverage for high-impact DTOs
2. **Phased Testing**: Test each migration phase independently
3. **Integration Testing**: Focus on cross-module DTO interactions
4. **Rollback Testing**: Verify rollback scenarios for high-risk changes

## 8. Recommendations (Revised)

### 8.1 Migration Strategy

1. **Start with Class Renames**: Remove DTO suffixes from class names first
2. **Stage Alias Removal**: Remove aliases in order of usage impact (low to high)
3. **Coordinate Import Updates**: Update all imports for each model systematically
4. **Optional Consolidation**: Move to domain-organized files for better structure

### 8.2 Risk Mitigation

1. **Comprehensive Testing**: Full test coverage before any changes
2. **Automated Tooling**: Scripts to validate imports and detect naming conflicts
3. **Gradual Rollout**: Stage changes by impact level, not technical convenience
4. **Clear Communication**: Document semantic benefits, not just technical changes
5. **Team Coordination**: Ensure all module owners understand domain naming benefits

### 8.3 Success Metrics

**Technical Metrics**:
- Zero import errors after each phase
- All models follow descriptive naming convention
- No backward compatibility aliases remaining
- Consolidated schema organization

**Quality Metrics**:
- Improved code readability (semantic class names)
- Reduced cognitive overhead (single import path per model)
- Better domain organization
- Modern Python/Pydantic compliance

---

*Generated: Phase 1 Boundary Model Usage Analysis (Revised)*