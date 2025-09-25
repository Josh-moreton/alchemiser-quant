# Boundary Model Usage Analysis

**Business Unit:** shared | **Status:** analysis  
**Generated:** Phase 1 of Boundary Model Standardization Migration  
**Target:** Import dependency analysis and usage patterns for modernization

## Overview

This document analyzes how boundary model classes are imported and used across the entire codebase, identifying high-impact classes, dependency patterns, and migration risks. The analysis supports the transition to modern Python/Pydantic v2 practices with descriptive class names and consolidated schema organization.

## Import Distribution Analysis

### Current DTO Imports by Module (Top Consumers)

| Module | Import Count | Risk Level | Description |
|--------|-------------|------------|-------------|
| `shared/dto/__init__.py` | 12 | 🔴 **Critical** | Central aggregation point - highest migration impact |
| `orchestration/trading_orchestrator.py` | 5 | 🟡 **High** | Core orchestration - many boundary model dependencies |
| `orchestration/portfolio_orchestrator.py` | 5 | 🟡 **High** | Core orchestration - many boundary model dependencies |
| `strategy_v2/engines/dsl/dsl_evaluator.py` | 4 | 🟡 **High** | DSL engine - core functionality with ASTNode dependency |
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

## High-Impact Boundary Model Classes

### Most Frequently Imported Classes (To Be Renamed)

| Current Class Name | Target Name | Import Count | Files Using | Migration Risk |
|-------------------|-------------|-------------|-------------|----------------|
| `ASTNodeDTO` | `ASTNode` | 11 | 8 files | 🔴 **Critical** - Core DSL functionality |
| `RebalancePlanDTO` | `RebalancePlan` | 6 | 5 files | 🟡 **High** - Portfolio rebalancing |
| `StrategyAllocationDTO` | `StrategyAllocation` | 5 | 4 files | 🟡 **High** - Strategy allocation |
| `PortfolioFragmentDTO` | `PortfolioFragment` | 4 | 3 files | 🟠 **Medium** - DSL portfolio operations |
| `AllocationComparisonDTO` | `AllocationComparison` | 3 | 3 files | 🟠 **Medium** - Portfolio analysis |
| `TraceDTO` | `Trace` | 3 | 3 files | 🟠 **Medium** - DSL debugging |
| `TechnicalIndicatorDTO` | `TechnicalIndicator` | 3 | 3 files | 🟠 **Medium** - Technical analysis |
| `MarketBarDTO` | `MarketBar` | 3 | 3 files | 🟠 **Medium** - Market data |
| `AssetInfoDTO` | `AssetInfo` | 3 | 3 files | 🟠 **Medium** - Asset information |

### Critical Dependencies by Business Unit

#### Strategy Module Dependencies
```
strategy_v2/ (Highest boundary model usage - descriptive names needed)
├── ASTNodeDTO → ASTNode (11 imports) - DSL core
├── IndicatorRequestDTO → IndicatorRequest (4 imports) - Technical analysis
├── TraceDTO → Trace (3 imports) - Debugging
├── TechnicalIndicatorDTO → TechnicalIndicator (3 imports) - Indicators
└── StrategySignalDTO → StrategySignal (2 imports) - Signal generation
```

#### Orchestration Module Dependencies
```
orchestration/ (Cross-module coordination - needs descriptive imports)
├── RebalancePlanDTO → RebalancePlan (6 imports) - Portfolio changes
├── StrategyAllocationDTO → StrategyAllocation (5 imports) - Allocation data
├── AllocationComparisonDTO → AllocationComparison (3 imports) - Comparison logic
└── PortfolioStateDTO → PortfolioState (2 imports) - Portfolio state
```

#### Execution Module Dependencies
```
execution_v2/ (Order execution - clean renames needed)
├── RebalancePlanDTO → RebalancePlan (4 imports) - Execution plans
├── ExecutedOrderDTO → ExecutedOrder (2 imports) - Order results
└── AssetInfoDTO → AssetInfo (1 import) - Asset validation
```

## Import Patterns Analysis

### Pattern 1: Direct Model Imports (Target Pattern)
```python
# Target pattern - direct imports with descriptive names
from the_alchemiser.shared.schemas.portfolio import RebalancePlan
from the_alchemiser.shared.schemas.strategy import StrategyAllocation
from the_alchemiser.shared.schemas.accounts import AccountSummary
```
**Usage:** Target for 100% of imports  
**Risk:** 🟢 **Low** - Clean, explicit dependencies with descriptive names

### Pattern 2: Current DTO Suffix Imports (To Be Updated)
```python
# Current pattern - DTO suffixes to be removed
from the_alchemiser.shared.dto.rebalance_plan_dto import RebalancePlanDTO
from the_alchemiser.shared.dto.strategy_allocation_dto import StrategyAllocationDTO
```
**Usage:** 85% of current DTO imports  
**Risk:** 🟡 **Medium** - Requires systematic renaming and import updates

### Pattern 3: Schema with Alias Usage (To Be Eliminated)
```python
# Schema import with backward compatibility alias - to be removed
from the_alchemiser.shared.schemas.accounts import AccountSummaryDTO  # alias
from the_alchemiser.shared.schemas.execution_summary import ExecutionSummaryDTO  # alias
```
**Usage:** 10% of current imports  
**Risk:** 🟡 **Medium** - Aliases to be removed, imports updated to descriptive names

### Pattern 4: Mixed Import Styles (To Be Standardized)
```python
# Current problematic mixing - to be eliminated
from the_alchemiser.shared.dto.portfolio_state_dto import PortfolioStateDTO
from the_alchemiser.shared.schemas.execution_summary import PortfolioStateDTO  # Alias conflict
```
**Usage:** 5% of imports  
**Risk:** 🔴 **High** - Name conflicts, duplicate concepts to be resolved

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

### By Class Renaming Complexity

| Current Class Name | Target Name | Files Affected | Current Pattern | Complexity | Migration Effort |
|-------------------|-------------|----------------|-----------------|------------|------------------|
| `ASTNodeDTO` | `ASTNode` | 8 | Direct imports | 🔴 **High** | 3-4 days |
| `RebalancePlanDTO` | `RebalancePlan` | 5 | Direct imports | 🟡 **Medium** | 2-3 days |
| `StrategyAllocationDTO` | `StrategyAllocation` | 4 | Direct imports | 🟡 **Medium** | 2 days |
| `AllocationComparisonDTO` | `AllocationComparison` | 3 | Schema-based | 🟠 **Low** | 1 day |
| `MarketBarDTO` | `MarketBar` | 3 | Direct imports | 🟠 **Low** | 1 day |
| `TechnicalIndicatorDTO` | `TechnicalIndicator` | 3 | Direct imports | 🟠 **Low** | 1 day |
| Other DTO classes | Descriptive names | 1-2 | Mixed | 🟢 **Low** | 0.5-1 day each |

## Recommendations

### Migration Order by Risk (Modern Python Approach)
1. **Phase 1:** Consolidate into `shared/schemas/` with domain organization
2. **Phase 2:** Rename low-risk classes (1-2 imports) to descriptive names
3. **Phase 3:** Rename medium-risk classes with coordination
4. **Phase 4:** Rename critical classes (`ASTNode`) with comprehensive testing
5. **Phase 5:** Remove all backward compatibility aliases

### Modern Python Benefits
1. **Better Code Readability** - `AccountSummary` vs `AccountSummaryDTO`
2. **Domain-Focused Names** - Business concepts over technical patterns  
3. **Reduced Cognitive Load** - Fewer suffixes to remember
4. **Ecosystem Alignment** - Follows Pydantic v2 best practices
5. **Single Source of Truth** - All boundary models in organized `shared/schemas/`

### Risk Mitigation Strategies
1. **Maintain temporary aliases** during each rename phase
2. **Migrate in dependency order** - Leaf dependencies first
3. **Batch related changes** - Group by business domain
4. **Comprehensive testing** - Validate each boundary model rename
5. **Clear documentation** - Mark boundary models and their usage

This analysis provides the foundation for creating a detailed, low-risk migration plan to modern Python practices with descriptive class names and organized schema structure.