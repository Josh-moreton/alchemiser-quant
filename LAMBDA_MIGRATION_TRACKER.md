# Lambda CodeUri Migration Tracker

## Migration Status

| Function | Complexity | Files | Status | Notes |
|----------|-----------|-------|--------|-------|
| NotificationsFunction | Very Low | 3 | ✅ COMPLETE | Proof of concept |
| MetricsFunction | Very Low | 1 | 🔄 IN PROGRESS | |
| TradeAggregatorFunction | Low | 3 | ⏳ PENDING | |
| StrategyAggregatorFunction | Low | 3 | ⏳ PENDING | |
| StrategyOrchestratorFunction | Low | 3 | ⏳ PENDING | |
| PortfolioFunction | Medium | 8 | ⏳ PENDING | |
| DataFunction | Medium | 10 | 🔄 IN PROGRESS | Imports adjusted in functions/data/; build/test pending |
| StrategyFunction | High | 24 | ⏳ PENDING | |
| ExecutionFunction | High | 23 | ⏳ PENDING | Most critical |

**Progress**: 1/9 complete (11%)

---

## Tier 1: Very Low Complexity

### 1. MetricsFunction ✅ PATTERN VALIDATED

**Module**: `the_alchemiser/metrics_v2/`
**Target**: `functions/metrics/`
**Files**: 1 file (lambda_handler.py)

**Steps**:
- [x] Create functions/metrics/ directory
- [x] Copy lambda_handler.py
- [x] Update template.yaml (CodeUri, Handler, Layers)
- [x] Build and test
- [x] Verify deployment

**template.yaml changes**:
```yaml
MetricsFunction:
  Properties:
    CodeUri: functions/metrics/
    Handler: lambda_handler.lambda_handler
    Layers:
      - !Ref SharedCodeLayer
      - !Ref NotificationsLayer
```

---

### 2. TradeAggregatorFunction

**Module**: `the_alchemiser/trade_aggregator/`
**Target**: `functions/trade-aggregator/`
**Files**: 3 files

**Structure**:
```
functions/trade-aggregator/
├── lambda_handler.py
├── config.py (flatten from config/__init__.py)
└── service.py (flatten from services/__init__.py)
```

**Steps**:
- [ ] Create functions/trade-aggregator/ directory
- [ ] Copy and flatten files
- [ ] Update imports in lambda_handler.py (`.config` → `config`, `.services` → `service`)
- [ ] Update template.yaml
- [ ] Build and test
- [ ] Verify deployment

**Import changes**:
```python
# Before
from .config import TradeAggregatorSettings
from .services import TradeAggregatorService

# After
from config import TradeAggregatorSettings
from service import TradeAggregatorService
```

---

### 3. StrategyAggregatorFunction

**Module**: `the_alchemiser/aggregator_v2/`
**Target**: `functions/strategy-aggregator/`
**Files**: 3 files

**Structure**:
```
functions/strategy-aggregator/
├── lambda_handler.py
├── aggregator_settings.py (from config/)
└── portfolio_merger.py (from services/)
```

**Steps**:
- [ ] Create functions/strategy-aggregator/ directory
- [ ] Copy and flatten files
- [ ] Update imports in lambda_handler.py
- [ ] Update template.yaml
- [ ] Build and test
- [ ] Verify deployment

**Import changes**:
```python
# Before
from .config.aggregator_settings import AggregatorSettings
from .services.portfolio_merger import PortfolioMerger

# After
from aggregator_settings import AggregatorSettings
from portfolio_merger import PortfolioMerger
```

---

### 4. StrategyOrchestratorFunction

**Module**: `the_alchemiser/coordinator_v2/`
**Target**: `functions/strategy-orchestrator/`
**Files**: 3 files

**Structure**:
```
functions/strategy-orchestrator/
├── lambda_handler.py
├── coordinator_settings.py (from config/)
└── strategy_invoker.py (from services/)
```

**Steps**:
- [ ] Create functions/strategy-orchestrator/ directory
- [ ] Copy and flatten files
- [ ] Update imports in lambda_handler.py
- [ ] Update template.yaml
- [ ] Build and test
- [ ] Verify deployment

**Import changes**:
```python
# Before
from .config.coordinator_settings import CoordinatorSettings
from .services.strategy_invoker import StrategyInvoker

# After
from coordinator_settings import CoordinatorSettings
from strategy_invoker import StrategyInvoker
```

---

## Tier 2: Medium Complexity

### 5. PortfolioFunction

**Module**: `the_alchemiser/portfolio_v2/`
**Target**: `functions/portfolio/`
**Files**: 8 files (preserve subdirectories)

**Structure**:
```
functions/portfolio/
├── lambda_handler.py
├── handlers/portfolio_analysis_handler.py
├── adapters/ (2 files)
├── core/ (3 files)
└── models/portfolio_snapshot.py
```

**Steps**:
- [ ] Create functions/portfolio/ directory structure
- [ ] Copy entire module tree
- [ ] Update all relative imports (`.handlers` → `handlers`, etc.)
- [ ] Update template.yaml
- [ ] Build and test
- [ ] Verify deployment

**Import pattern**: Remove leading dots from all relative imports

---

### 6. DataFunction

**Module**: `the_alchemiser/data_v2/`
**Target**: `functions/data/`
**Files**: 10 files (flat structure)

**Structure**:
```
functions/data/
├── lambda_handler.py
├── data_refresh_service.py
├── market_data_store.py
├── fetch_request_service.py
├── data_freshness_validator.py
├── bad_data_marker_service.py
├── cached_market_data_adapter.py
├── live_bar_provider.py
└── symbol_extractor.py
```

**Steps**:
- [ ] Create functions/data/ directory
- [ ] Copy all files to root
- [ ] Update all relative imports (remove leading dots)
- [ ] Update template.yaml
- [ ] Build and test
- [ ] Verify deployment

---

## Tier 3: High Complexity

### 7. StrategyFunction

**Module**: `the_alchemiser/strategy_v2/`
**Target**: `functions/strategy/`
**Files**: 24 files (deep nesting with subdirectories)

**Structure**:
```
functions/strategy/
├── lambda_handler.py
├── handlers/ (1 file)
├── adapters/ (4 files)
├── engines/dsl/ (9 files + operators/ subdirectory)
├── indicators/ (3 files)
├── core/ (3 files)
└── models/ (1 file)
```

**Steps**:
- [ ] Create functions/strategy/ directory structure
- [ ] Copy entire module tree (preserving all subdirectories)
- [ ] Update all relative imports across all files
- [ ] Update template.yaml
- [ ] Build and test (large pandas/numpy layer)
- [ ] Verify deployment

**Notes**: Most complex DSL engine, requires careful import updates

---

### 8. ExecutionFunction

**Module**: `the_alchemiser/execution_v2/`
**Target**: `functions/execution/`
**Files**: 23 files (deep nesting, most critical)

**Structure**:
```
functions/execution/
├── lambda_handler.py
├── handlers/ (1 file)
├── core/ (8 files)
├── unified/ (5 files)
├── services/ (2 files)
├── models/ (2 files)
├── adapters/ (1 file)
└── utils/ (3 files)
```

**Steps**:
- [ ] Create functions/execution/ directory structure
- [ ] Copy entire module tree (preserving all subdirectories)
- [ ] Update all relative imports across all files
- [ ] Update template.yaml
- [ ] Build and test (SQS-triggered, WebSocket management)
- [ ] Verify deployment
- [ ] **CRITICAL**: Test thoroughly - this is the most critical Lambda

**Notes**: Most critical function, migrate last after all patterns validated

---

## Standard Migration Procedure

For each function:

1. **Create directory**: `mkdir -p functions/<name>/`
2. **Copy files**: Copy module files to function directory
3. **Update imports**: Change relative imports to absolute within function
4. **Update template.yaml**: Change CodeUri, Handler, add SharedCodeLayer
5. **Build**: `sam build <FunctionName>`
6. **Deploy**: `sam deploy`
7. **Test**: Invoke Lambda and verify CloudWatch logs
8. **Mark complete**: Update this tracker

## Import Update Pattern

**Before** (relative imports):
```python
from .service import MyService
from ..core.engine import Engine
from .config.settings import Settings
```

**After** (absolute within function):
```python
from service import MyService
from core.engine import Engine
from config.settings import Settings
```

**Keep unchanged** (shared imports):
```python
from the_alchemiser.shared.config import ApplicationContainer
from the_alchemiser.shared.events import EventBus
```

## template.yaml Update Pattern

**Before**:
```yaml
FunctionName:
  Properties:
    CodeUri: ./   # legacy - migrate to CodeUri: functions/<name>/ and attach SharedCodeLayer
    Handler: the_alchemiser.module_v2.lambda_handler.lambda_handler
    Layers:
      - !Ref DependencyLayer
  Metadata:
    BuildMethod: python3.12
    BuildProperties:
      Include:
        - the_alchemiser/module_v2/**
        - the_alchemiser/shared/**
```

**After**:
```yaml
FunctionName:
  Properties:
    CodeUri: functions/<name>/
    Handler: lambda_handler.lambda_handler
    Layers:
      - !Ref SharedCodeLayer  # ADD THIS FIRST
      - !Ref DependencyLayer
  Metadata:
    BuildMethod: python3.12
    # Remove BuildProperties - SAM auto-includes
```

---

## Post-Migration Cleanup

After ALL 9 functions migrated:
-
- [ ] Remove any temporary local copies of `the_alchemiser/shared/` used during migration; ensure the shared layer content remains in `layers/shared/` and is validated before deleting the source of truth.
- [ ] Remove all old module directories (`the_alchemiser/metrics_v2/`, etc.)
- [ ] Update .gitignore if needed
- [ ] Verify all Lambdas still work
- [ ] Delete old failed branch: `feat/dedicated-codeuris-and-shared-lambda-layer`

---

## Issues & Solutions Log

### Issue 1: Double Nesting in Layer (RESOLVED)
**Problem**: Layer had `python/python/the_alchemiser/` nesting
**Solution**: Remove extra `python/` directory - SAM adds it during build

### Issue 2: Missing the_alchemiser.config (RESOLVED)
**Problem**: Strategy JSON files weren't in layer
**Solution**: Move to `layers/shared/the_alchemiser/shared/config/` and update config.py reference

### Issue 3: Pre-commit Hook Poetry PATH (RESOLVED)
**Problem**: Git hooks couldn't find poetry
**Solution**: Use absolute path in .pre-commit-config.yaml
