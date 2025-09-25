# DTO Usage Analysis

**Business Unit:** shared | **Status:** analysis  
**Generated:** Phase 1 of DTO Standardization Migration  
**Target:** Import dependency analysis and usage patterns

## Overview

This document analyzes how DTO and Schema classes are imported and used across the entire codebase, identifying high-impact classes, dependency patterns, and migration risks.

## Import Distribution Analysis

### DTO Imports by Module (Top Consumers)

| Module | Import Count | Risk Level | Description |
|--------|-------------|------------|-------------|
| `shared/dto/__init__.py` | 12 | 🔴 **Critical** | Central aggregation point - high impact |
| `orchestration/trading_orchestrator.py` | 5 | 🟡 **High** | Core orchestration - many dependencies |
| `orchestration/portfolio_orchestrator.py` | 5 | 🟡 **High** | Core orchestration - many dependencies |
| `strategy_v2/engines/dsl/dsl_evaluator.py` | 4 | 🟡 **High** | DSL engine - core functionality |
| `portfolio_v2/handlers/portfolio_analysis_handler.py` | 4 | 🟡 **High** | Portfolio analysis core |
| `strategy_v2/engines/dsl/events.py` | 3 | 🟠 **Medium** | Event system integration |
| `strategy_v2/engines/dsl/engine.py` | 3 | 🟠 **Medium** | Strategy engine core |
| `shared/brokers/alpaca_manager.py` | 3 | 🟠 **Medium** | Broker integration |

### Schema Imports by Module (Top Consumers)

| Module | Import Count | Risk Level | Description |
|--------|-------------|------------|-------------|
| `shared/mappers/execution_summary_mapping.py` | 5 | 🟡 **High** | Execution mapping - critical for summaries |
| `shared/notifications/*` | 4 | 🟠 **Medium** | Notification system |
| `orchestration/*_orchestrator.py` | 2 | 🟠 **Medium** | Cross-module orchestration |

## High-Impact DTO Classes

### Most Frequently Imported DTOs

| DTO Class | Import Count | Files Using | Risk Assessment |
|-----------|-------------|-------------|------------------|
| `ASTNodeDTO` | 11 | 8 files | 🔴 **Critical** - Core DSL functionality |
| `RebalancePlanDTO` | 6 | 5 files | 🟡 **High** - Portfolio rebalancing |
| `StrategyAllocationDTO` | 5 | 4 files | 🟡 **High** - Strategy allocation |
| `PortfolioFragmentDTO` | 4 | 3 files | 🟠 **Medium** - DSL portfolio operations |
| `AllocationComparisonDTO` | 3 | 3 files | 🟠 **Medium** - Portfolio analysis |
| `TraceDTO` | 3 | 3 files | 🟠 **Medium** - DSL debugging |
| `TechnicalIndicatorDTO` | 3 | 3 files | 🟠 **Medium** - Technical analysis |
| `MarketBarDTO` | 3 | 3 files | 🟠 **Medium** - Market data |
| `AssetInfoDTO` | 3 | 3 files | 🟠 **Medium** - Asset information |

### Critical Dependencies by Business Unit

#### Strategy Module Dependencies
```
strategy_v2/ (Highest DTO usage)
├── ASTNodeDTO (11 imports) - DSL core
├── IndicatorRequestDTO (4 imports) - Technical analysis
├── TraceDTO (3 imports) - Debugging
├── TechnicalIndicatorDTO (3 imports) - Indicators
└── StrategySignalDTO (2 imports) - Signal generation
```

#### Orchestration Module Dependencies
```
orchestration/ (Cross-module coordination)
├── RebalancePlanDTO (6 imports) - Portfolio changes
├── StrategyAllocationDTO (5 imports) - Allocation data
├── AllocationComparisonDTO (3 imports) - Comparison logic
└── PortfolioStateDTO (2 imports) - Portfolio state
```

#### Execution Module Dependencies
```
execution_v2/ (Order execution)
├── RebalancePlanDTO (4 imports) - Execution plans
├── ExecutedOrderDTO (2 imports) - Order results
└── AssetInfoDTO (1 import) - Asset validation
```

## Import Patterns Analysis

### Pattern 1: Direct DTO Imports (Preferred)
```python
# Most common pattern - direct imports
from the_alchemiser.shared.dto.rebalance_plan_dto import RebalancePlanDTO
from the_alchemiser.shared.dto.strategy_allocation_dto import StrategyAllocationDTO
```
**Usage:** 85% of imports  
**Risk:** 🟢 **Low** - Clean, explicit dependencies

### Pattern 2: Schema with Alias Usage
```python
# Schema import with backward compatibility alias
from the_alchemiser.shared.schemas.common import AllocationComparisonDTO
from the_alchemiser.shared.schemas.execution_summary import ExecutionSummaryDTO
```
**Usage:** 10% of imports  
**Risk:** 🟡 **Medium** - Depends on alias maintenance

### Pattern 3: Mixed Import Styles
```python
# Mixing DTO and Schema imports in same file
from the_alchemiser.shared.dto.portfolio_state_dto import PortfolioStateDTO
from the_alchemiser.shared.schemas.execution_summary import PortfolioStateDTO  # Alias
```
**Usage:** 5% of imports  
**Risk:** 🔴 **High** - Potential naming conflicts

## Dependency Graph Analysis

### Core Dependency Chains

#### DSL Engine Chain (High Risk)
```
DSL Engine → ASTNodeDTO → Multiple Operators → Context → Events
                ↓
        TraceDTO + IndicatorRequestDTO
                ↓
        Strategy Signal Generation
```
**Impact:** Changes to `ASTNodeDTO` affect 8+ modules

#### Portfolio Orchestration Chain (High Risk)
```
Trading Orchestrator → RebalancePlanDTO → Execution Manager
        ↓                    ↓
Portfolio Orchestrator → StrategyAllocationDTO → Portfolio Handler
        ↓
AllocationComparisonDTO → Analysis Handler
```
**Impact:** Changes affect core trading workflow

#### Event System Dependencies (Medium Risk)
```
Event Schemas → Multiple DTOs → Cross-Module Communication
     ↓
Strategy Events → DSL Events → Orchestration Events
```
**Impact:** Event system relies heavily on DTO contracts

## Module-by-Module Usage Patterns

### Strategy Module (`strategy_v2/`)
- **Primary DTOs:** DSL-related (`ASTNodeDTO`, `TraceDTO`, `IndicatorRequestDTO`)
- **Secondary DTOs:** Signal and allocation (`StrategySignalDTO`, `StrategyAllocationDTO`)
- **Pattern:** Heavy DTO usage, minimal schema imports
- **Risk:** 🟡 **High** - Core business logic depends on DTOs

### Orchestration Module (`orchestration/`)
- **Primary DTOs:** Cross-module coordination (`RebalancePlanDTO`, `AllocationComparisonDTO`)
- **Pattern:** Mix of DTO and schema imports
- **Risk:** 🟡 **High** - Coordinates between modules

### Execution Module (`execution_v2/`)
- **Primary DTOs:** Execution-focused (`RebalancePlanDTO`, `ExecutedOrderDTO`)
- **Pattern:** Focused DTO usage, clean dependencies
- **Risk:** 🟠 **Medium** - Well-isolated dependencies

### Portfolio Module (`portfolio_v2/`)
- **Primary DTOs:** Portfolio state and analysis
- **Pattern:** Balanced DTO and schema usage
- **Risk:** 🟠 **Medium** - Manageable dependencies

### Shared Module (`shared/`)
- **Primary DTOs:** Infrastructure and utilities
- **Pattern:** Heavy aggregation in `__init__.py`
- **Risk:** 🔴 **Critical** - Central aggregation point

## Import Conflict Analysis

### Identified Conflicts

1. **PortfolioStateDTO Duplication:**
   ```python
   # Two sources for same concept
   from the_alchemiser.shared.dto.portfolio_state_dto import PortfolioStateDTO
   from the_alchemiser.shared.schemas.execution_summary import PortfolioStateDTO  # Alias
   ```

2. **ExecutionSummaryDTO Duplication:**
   ```python
   # Available from multiple locations
   from the_alchemiser.shared.dto.trade_run_result_dto import ExecutionSummaryDTO
   from the_alchemiser.shared.schemas.execution_summary import ExecutionSummaryDTO  # Alias
   ```

3. **Result vs ResultDTO:**
   ```python
   # Inconsistent naming
   from the_alchemiser.shared.schemas.base import Result
   from the_alchemiser.shared.schemas.base import ResultDTO  # Alias
   ```

## High-Risk Migration Areas

### 🔴 Critical Risk Areas
1. **`shared/dto/__init__.py`** - Central aggregation affects all imports
2. **DSL Engine** - `ASTNodeDTO` used in 8+ files
3. **Orchestration** - Multiple cross-module dependencies

### 🟡 High Risk Areas
1. **Portfolio/Trading Orchestrators** - Core business workflow
2. **Execution Summary Mapping** - Multiple schema dependencies
3. **Event System** - Cross-cutting concerns

### 🟠 Medium Risk Areas
1. **Strategy Engines** - Focused but critical functionality
2. **Broker Integration** - External API boundaries
3. **Notification System** - Schema-dependent templates

## Migration Complexity Assessment

### By DTO Class Complexity

| DTO Class | Files Affected | Import Pattern | Complexity | Migration Effort |
|-----------|----------------|----------------|------------|------------------|
| `ASTNodeDTO` | 8 | Direct | 🔴 **High** | 3-4 days |
| `RebalancePlanDTO` | 5 | Direct | 🟡 **Medium** | 2-3 days |
| `StrategyAllocationDTO` | 4 | Direct | 🟡 **Medium** | 2 days |
| `AllocationComparisonDTO` | 3 | Schema alias | 🟠 **Low** | 1 day |
| Others | 1-2 | Mixed | 🟢 **Low** | 0.5-1 day |

## Recommendations

### Migration Order by Risk
1. **Phase 1:** Low-risk, single-file DTOs (1-2 imports)
2. **Phase 2:** Medium-risk schema aliases (clean single-concept)
3. **Phase 3:** High-risk multi-file DTOs (careful coordination)
4. **Phase 4:** Critical infrastructure (`__init__.py`, DSL core)

### Risk Mitigation Strategies
1. **Maintain aliases during migration** - Backward compatibility
2. **Migrate in dependency order** - Leaf dependencies first
3. **Batch related changes** - Minimize intermediate states
4. **Comprehensive testing** - Validate each migration step

This analysis provides the foundation for creating a detailed, low-risk migration plan with appropriate sequencing and rollback strategies.