# DTO Usage Analysis

## Overview
This document provides detailed analysis of DTO/Schema import patterns and dependencies across the alchemiser-quant codebase, supporting the Phase 1 migration planning.

**Analysis Date**: Phase 1 Initial Assessment  
**Repository**: Josh-moreton/alchemiser-quant  
**Total Import Statements Analyzed**: 130+  

## 1. Module-Level Usage Distribution

### 1.1 DTO Import Counts by Business Module

| Module | DTO Imports | Primary Usage |
| --- | --- | --- |
| `strategy_v2/` | 32 | DSL engine, indicators, signal generation |
| `orchestration/` | 19 | Cross-module coordination, event handling |
| `execution_v2/` | 9 | Order execution, portfolio rebalancing |
| `portfolio_v2/` | 9 | Portfolio state management, analysis |
| `shared/` | 61+ | DTO definitions, utilities, events |

### 1.2 Usage Intensity Analysis

**High Usage Modules** (20+ imports):
- `strategy_v2/` - Heavy DSL and indicator DTO usage
- `shared/` - DTO definitions and cross-cutting utilities

**Medium Usage Modules** (10-19 imports):
- `orchestration/` - Event-driven coordination layer

**Lower Usage Modules** (<10 imports):
- `execution_v2/`, `portfolio_v2/` - Focused, domain-specific usage

## 2. Top DTO Classes by Import Frequency

### 2.1 Most Frequently Imported DTOs

| Rank | DTO Class | Import Count | Primary Modules | Usage Type |
| --- | --- | --- | --- | --- |
| 1 | `ASTNodeDTO` | 11 | strategy_v2 | DSL parsing, evaluation |
| 2 | `RebalancePlanDTO` | 6 | execution_v2, orchestration | Portfolio rebalancing |
| 3 | `StrategyAllocationDTO` | 5 | strategy_v2, orchestration | Strategy allocations |
| 3 | `ExecutionResultDTO` | 5 | execution_v2 | Trade execution results |
| 5 | `PortfolioFragmentDTO` | 4 | strategy_v2 | DSL portfolio fragments |
| 6 | `AllocationComparisonDTO` | 3 | orchestration, shared | Portfolio comparisons |
| 6 | `TraceDTO` | 3 | strategy_v2 | DSL evaluation tracing |
| 6 | `TechnicalIndicatorDTO` | 3 | strategy_v2 | Technical indicators |
| 6 | `MarketBarDTO` | 3 | strategy_v2 | Market data |
| 6 | `AssetInfoDTO` | 3 | execution_v2 | Asset validation |

### 2.2 Medium Usage DTOs (2 imports)

| DTO Class | Import Count | Usage Areas |
| --- | --- | --- |
| `MultiStrategyExecutionResultDTO` | 2 | Execution results, notifications |
| `StrategySignalDTO` | 2 | Signal generation, events |
| `PortfolioStateDTO` | 2 | Portfolio management, schema refs |
| `IndicatorRequestDTO` | 2 | Indicator requests, DSL |
| `ExecutedOrderDTO` | 2 | Order execution tracking |

### 2.3 Single-Use DTOs (1 import)

Many DTOs are used only once or in specialized contexts:
- `TradeRunResultDTO`, `LambdaEventDTO`, `ConsolidatedPortfolioDTO`
- Most schema-based DTOs through aliases
- Specialized execution and reporting DTOs

## 3. Module-Specific Dependency Analysis

### 3.1 Strategy v2 Module Dependencies

**Primary DTO Dependencies** (32 total imports):
- **DSL Engine** (Heavy usage):
  - `ASTNodeDTO` - Core AST representation
  - `TraceDTO` - Evaluation tracing
  - `PortfolioFragmentDTO` - Intermediate allocations
  - `IndicatorRequestDTO` - Technical indicator requests

- **Market Data & Indicators**:
  - `TechnicalIndicatorDTO` - Indicator results
  - `MarketBarDTO` - OHLCV data
  - `StrategyAllocationDTO` - Final allocations

**Risk Assessment**: **HIGH** - Heavy DTO dependency, core to DSL functionality

### 3.2 Execution v2 Module Dependencies

**Primary DTO Dependencies** (9 total imports):
- **Core Execution**:
  - `RebalancePlanDTO` - Rebalancing instructions
  - `ExecutionResultDTO` - Internal execution results
  - `ExecutedOrderDTO` - Individual order results
  - `AssetInfoDTO` - Asset validation

**Risk Assessment**: **MEDIUM** - Focused usage, critical for execution flow

### 3.3 Orchestration Module Dependencies

**Primary DTO Dependencies** (19 total imports):
- **Cross-Module Coordination**:
  - `RebalancePlanDTO` - Portfolio rebalancing coordination
  - `StrategyAllocationDTO` - Strategy output handling
  - `AllocationComparisonDTO` - Portfolio comparisons
  - `MultiStrategyExecutionResultDTO` - Execution results

**Risk Assessment**: **HIGH** - Central coordination role, touches all modules

### 3.4 Portfolio v2 Module Dependencies

**Primary DTO Dependencies** (9 total imports):
- **Portfolio Management**:
  - `PortfolioStateDTO` - Portfolio state representation
  - Related allocation and metrics DTOs

**Risk Assessment**: **MEDIUM** - Specialized usage, important for portfolio operations

## 4. Import Pattern Analysis

### 4.1 Direct vs. Aliased Imports

**Direct DTO Imports** (85%):
```python
from the_alchemiser.shared.dto.rebalance_plan_dto import RebalancePlanDTO
from the_alchemiser.shared.dto.ast_node_dto import ASTNodeDTO
```

**Schema Imports via Aliases** (15%):
```python
from the_alchemiser.shared.schemas.common import AllocationComparisonDTO
from the_alchemiser.shared.schemas.common import MultiStrategyExecutionResultDTO
```

### 4.2 Import Path Patterns

1. **DTO Imports**: `from the_alchemiser.shared.dto.{module} import {DTO}`
2. **Schema Imports**: `from the_alchemiser.shared.schemas.{module} import {DTO}`
3. **Internal Module Imports**: `from the_alchemiser.{module}.models.{file} import {DTO}`

### 4.3 Circular Import Risk Assessment

**Low Risk**: Most imports follow proper layered architecture
- Shared DTOs imported by business modules
- Business modules don't import each other's DTOs directly
- Event-driven communication reduces direct coupling

**Potential Issues**:
- Some orchestration imports could create tight coupling
- Internal module DTOs (`ExecutionResultDTO`) may need attention

## 5. High-Impact Change Assessment

### 5.1 Critical DTOs (High Breaking Risk)

**Tier 1 - Maximum Impact** (>5 imports):
- `ASTNodeDTO` (11 imports) - Core DSL functionality
- `RebalancePlanDTO` (6 imports) - Core execution flow

**Tier 2 - High Impact** (3-5 imports):
- `StrategyAllocationDTO`, `ExecutionResultDTO`, `PortfolioFragmentDTO`
- `AllocationComparisonDTO`, `TraceDTO`, `TechnicalIndicatorDTO`

**Tier 3 - Medium Impact** (2 imports):
- `MultiStrategyExecutionResultDTO`, `StrategySignalDTO`, `PortfolioStateDTO`

### 5.2 Low-Risk DTOs

**Single Import DTOs**: Can be migrated with minimal coordination
- Specialized reporting DTOs
- Lambda-specific DTOs  
- One-off utility DTOs

## 6. Migration Dependency Graph

### 6.1 Migration Order Recommendations

**Phase 1 - Foundation** (Low Risk):
- Single-use DTOs
- Reporting and utility DTOs
- Schema TypedDict classes (non-DTO)

**Phase 2 - Medium Impact** (Controlled Changes):
- Medium usage DTOs (2-3 imports)
- Schema result classes with aliases
- Internal module DTOs

**Phase 3 - High Impact** (Coordinated Changes):
- Core business DTOs (5+ imports)
- Cross-module coordination DTOs
- Event payload DTOs

**Phase 4 - Critical Path** (Full Testing Required):
- `ASTNodeDTO` and DSL-related DTOs
- `RebalancePlanDTO` and execution flow DTOs

### 6.2 Dependency Constraints

**Hard Dependencies** (Must be migrated together):
- DSL cluster: `ASTNodeDTO`, `TraceDTO`, `PortfolioFragmentDTO`
- Execution cluster: `RebalancePlanDTO`, `ExecutionResultDTO`, `ExecutedOrderDTO`
- Allocation cluster: `StrategyAllocationDTO`, `AllocationComparisonDTO`

**Soft Dependencies** (Can be migrated independently):
- Reporting DTOs
- Market data DTOs
- Asset information DTOs

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

## 8. Recommendations

### 8.1 Migration Strategy

1. **Start with Low-Impact DTOs**: Build confidence and process
2. **Group Related DTOs**: Migrate functional clusters together  
3. **Coordinate High-Impact Changes**: Plan carefully around critical DTOs
4. **Maintain Parallel Imports**: Use aliases during transition periods

### 8.2 Risk Mitigation

1. **Comprehensive Testing**: Ensure full test coverage before changes
2. **Gradual Rollout**: Use feature flags or gradual deployment
3. **Monitoring**: Track import failures and runtime errors
4. **Documentation**: Keep migration progress visible to all teams

---

*Generated: Phase 1 DTO Usage Analysis*