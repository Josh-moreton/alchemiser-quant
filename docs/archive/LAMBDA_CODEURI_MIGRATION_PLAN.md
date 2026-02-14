# Lambda CodeUri Migration Plan

## Executive Summary

This document outlines the plan to migrate each Lambda function from the current monolithic `CodeUri: ./` approach to dedicated per-Lambda `CodeUri` directories. This change aims to:

1. **Reduce deployment package sizes** - Each Lambda only packages its own code
2. **Improve build times** - Faster SAM builds with smaller scope
3. **Enable independent deployments** - Change one Lambda without rebuilding others
4. **Clearer ownership** - Each Lambda's code is fully self-contained

## Current State Analysis

## Final Configuration (post-migration)

After migration, the repository uses per-function CodeUri paths and a shared layer for common runtime code:

- Function code: `functions/<name>/` (each Lambda's SAM `CodeUri` points here)
- Shared runtime/business code: `shared_layer/` (published as `SharedCodeLayer` and referenced by each Lambda via `!Ref SharedCodeLayer`)
- Handler convention: function-level `lambda_handler.lambda_handler` (function code flattened under `functions/<name>/`)

Do NOT copy `the_alchemiser/shared/` into each function's CodeUri; use the shared layer instead.


### Lambda Inventory (10 Functions)

| Lambda | Template | Handler | Layer | Shared Dependencies |
|--------|----------|---------|-------|---------------------|
| StrategyFunction | template.yaml | `the_alchemiser.strategy_v2.lambda_handler` | StrategyLayer | 16 submodules (heaviest) |
| StrategyOrchestratorFunction | template.yaml | `the_alchemiser.coordinator_v2.lambda_handler` | NotificationsLayer | 5 submodules |
| StrategyAggregatorFunction | template.yaml | `the_alchemiser.aggregator_v2.lambda_handler` | NotificationsLayer | 6 submodules |
| PortfolioFunction | template.yaml | `the_alchemiser.portfolio_v2.lambda_handler` | PortfolioLayer | 13 submodules |
| ExecutionFunction | template.yaml | `the_alchemiser.execution_v2.lambda_handler` | ExecutionLayer | 15 submodules |
| TradeAggregatorFunction | template.yaml | `the_alchemiser.trade_aggregator.lambda_handler` | NotificationsLayer | TBD |
| NotificationsFunction | template.yaml | `the_alchemiser.notifications_v2.lambda_handler` | NotificationsLayer | 8 submodules |
| MetricsFunction | template.yaml | `the_alchemiser.metrics_v2.lambda_handler` | NotificationsLayer | TBD |
| SharedDataFunction | data-template.yaml | `the_alchemiser.data_v2.lambda_handler` | SharedDataLayer | TBD |
| DataQualityMonitorFunction | data-template.yaml | `the_alchemiser.data_quality_monitor.lambda_handler` | DataQualityMonitorLayer | TBD |

### Current CodeUri Configuration

All Lambdas currently use:
```yaml
CodeUri: ./   # legacy (before migration). Final pattern: CodeUri: functions/<name>/ and use shared_layer/ for shared code
Metadata:
  BuildMethod: python3.12
  BuildProperties:
    Include:
      - 'the_alchemiser/**/*.py'
      - 'the_alchemiser/**/*.clj'
      - 'the_alchemiser/config/*.json'
      - 'the_alchemiser/py.typed'
    Exclude:
      - '.env*'
      - '**/__pycache__/**'
      # ... etc
```

### Shared Code Structure (`the_alchemiser/shared/`)

The shared module contains **21 subdirectories** with **135+ Python files**:

| Submodule | Purpose | Used By |
|-----------|---------|---------|
| `events/` | Event schemas, EventBridge publisher | ALL (6/6) |
| `logging/` | Structured logging infrastructure | ALL (6/6) |
| `config/` | Settings, DI container | 5/6 |
| `schemas/` | DTOs (60+ classes) | 5/6 |
| `services/` | Business services (16+ classes) | 5/6 |
| `errors/` | Exception types, error handling | 4/6 |
| `brokers/` | Alpaca integration | 3/6 |
| `repositories/` | DynamoDB persistence | 3/6 |
| `types/` | Protocol definitions | 2/6 |
| `value_objects/` | Domain value objects | 1/6 |
| `reasoning/` | NL generation | 1/6 |
| `notifications/` | SNS publisher | 1/6 |
| `constants/` | Global constants | 3/6 |
| `utils/` | Utility functions | 2/6 |
| `math/` | Math utilities | 0/6 (internal) |
| `mappers/` | Data transformations | 0/6 (internal) |
| `metrics/` | CloudWatch metrics | 0/6 (internal) |
| `protocols/` | Interface definitions | 0/6 (internal) |
| `adapters/` | Protocol implementations | 0/6 (internal) |
| `reporting/` | Report generation | 0/6 (internal) |

---

## Migration Options Analysis

### Option 1: Shared Code as Lambda Layer (RECOMMENDED)

**Approach**: Create a new Lambda Layer containing the entire `shared/` module. Each Lambda's `CodeUri` points to its own module directory.

```
functions/
├── strategy_v2/
│   ├── __init__.py
│   ├── lambda_handler.py
│   └── ... (module-specific code)
├── execution_v2/
│   └── ...
└── ...

layers/
├── shared/              # NEW - shared code layer
│   └── python/
│       └── the_alchemiser/
│           └── shared/
├── strategy/            # existing - third-party deps
├── execution/           # existing - third-party deps
└── ...
```

**template.yaml changes**:
```yaml
# New Shared Layer
SharedCodeLayer:
  Type: AWS::Serverless::LayerVersion
  Properties:
    LayerName: !Sub "${StackName}-shared-code"
    ContentUri: shared_layer/
    CompatibleRuntimes:
      - python3.12
  Metadata:
    BuildMethod: python3.12

# Each Lambda function
StrategyFunction:
  Type: AWS::Serverless::Function
  Properties:
    CodeUri: functions/strategy_v2/
    Handler: lambda_handler.lambda_handler
    Layers:
      - !Ref StrategyLayer        # Third-party deps
      - !Ref SharedCodeLayer      # Shared code
```

**Pros**:
- Single source of truth for shared code
- Smallest Lambda package sizes
- Clear separation of concerns
- Layer versioning provides rollback capability
- Matches AWS best practices for shared code

**Cons**:
- Layer must be deployed before Lambdas
- Total unzipped size limit (250MB) must account for layer
- Layer changes require redeployment of referencing Lambdas

**Size Impact** (estimated):
- SharedCodeLayer: ~5-10MB (Python code only)
- Each Lambda function: ~1-3MB (module-specific code)

---

### Option 2: Copy Shared Code During Build

**Approach**: Keep shared code in central location. Build process copies shared to each Lambda's CodeUri directory before SAM build.

```
the_alchemiser/
├── shared/              # Source of truth
├── strategy_v2/
├── execution_v2/
└── ...

functions/               # Generated at build time
├── strategy_v2/
│   ├── the_alchemiser/
│   │   ├── shared/      # Copied from source
│   │   └── strategy_v2/
│   └── lambda_handler.py
└── ...
```

**Build script** (`scripts/prepare-lambdas.sh`):
```bash
#!/bin/bash
for module in strategy_v2 execution_v2 portfolio_v2 ...; do
    mkdir -p functions/$module/the_alchemiser
    cp -r the_alchemiser/shared functions/$module/the_alchemiser/
    cp -r the_alchemiser/$module functions/$module/the_alchemiser/
done
```

**Pros**:
- No layer management complexity
- Each Lambda is fully self-contained
- Works with existing SAM build process

**Cons**:
- Code duplication (10 copies of shared)
- Larger total deployment artifact size
- Build process complexity
- Must regenerate on every change to shared

---

### Option 3: Python Package Installation

**Approach**: Make `the_alchemiser` a pip-installable package. Each Lambda's requirements.txt includes it.

```
# pyproject.toml - already exists
[tool.poetry]
name = "the_alchemiser"
version = "x.y.z"

# Each Lambda's requirements.txt
-e file:../../  # or publish to private PyPI
```

**Pros**:
- Standard Python packaging
- Clear dependency management
- Works well with local development

**Cons**:
- Requires private PyPI or complex build process
- Not ideal for SAM's build system
- Adds deployment complexity

---

### Option 4: Symlinks with SAM Build

**Approach**: Use symlinks during build to reference shared code.

**Note**: SAM does not follow symlinks during build. This option is **NOT VIABLE**.

---

## Recommended Approach: Option 1 (Lambda Layer)

### Implementation Plan

#### Phase 1: Create Shared Code Layer Structure

1. Create new layer directory:
   ```
   layers/shared/
   └── python/
       └── the_alchemiser/
           ├── __init__.py
           └── shared/
               └── ... (copy of current shared)
   ```

2. Add layer to template.yaml:
   ```yaml
   SharedCodeLayer:
     Type: AWS::Serverless::LayerVersion
     Properties:
       LayerName: !Sub "alchemiser-${Stage}-shared-code"
       Description: Shared business logic and utilities
       ContentUri: shared_layer/
       CompatibleRuntimes:
         - python3.12
     Metadata:
       BuildMethod: python3.12
   ```

3. Update Makefile to sync shared code to layer:
   ```makefile
   sync-shared-layer:
       rm -rf shared_layer/python/the_alchemiser/shared
       mkdir -p shared_layer/python/the_alchemiser
       cp the_alchemiser/__init__.py shared_layer/python/the_alchemiser/
       cp -r the_alchemiser/shared shared_layer/python/the_alchemiser/
   ```

#### Phase 2: Create Per-Lambda Function Directories

1. Create function directories:
   ```
   functions/
   ├── strategy_v2/
   │   └── the_alchemiser/
   │       └── strategy_v2/
   │           └── ... (move from current location)
   ├── coordinator_v2/
   ├── aggregator_v2/
   ├── portfolio_v2/
   ├── execution_v2/
   ├── notifications_v2/
   ├── trade_aggregator/
   ├── metrics_v2/
   ├── data_v2/
   └── data_quality_monitor/
   ```

2. Each function directory contains ONLY:
   - Its own module code
   - Module-specific configuration files (e.g., `.clj` strategy files)

#### Phase 3: Update template.yaml

For each Lambda, update:
```yaml
StrategyFunction:
  Type: AWS::Serverless::Function
  Properties:
    CodeUri: functions/strategy_v2/
    Handler: the_alchemiser.strategy_v2.lambda_handler.lambda_handler
    Layers:
      - !Ref StrategyLayer
      - !Ref SharedCodeLayer  # Add shared layer
    # ... rest unchanged
  Metadata:
    BuildMethod: python3.12
    BuildProperties:
      Include:
        - 'the_alchemiser/**/*.py'
        - 'the_alchemiser/**/*.clj'
```

#### Phase 4: Update data-template.yaml

Same pattern for data Lambdas:
- SharedDataFunction → `functions/data_v2/`
- DataQualityMonitorFunction → `functions/data_quality_monitor/`

#### Phase 5: Update Tests and CI/CD

1. Update import paths in tests if needed
2. Update CI/CD to build shared layer first
3. Update deployment scripts

---

## Directory Structure After Migration

```
alchemiser-quant/
├── functions/                      # NEW - Lambda function code
│   ├── strategy_v2/
│   │   └── the_alchemiser/
│   │       └── strategy_v2/
│   │           ├── __init__.py
│   │           ├── lambda_handler.py
│   │           ├── handlers/
│   │           ├── engines/
│   │           └── ...
│   ├── coordinator_v2/
│   │   └── the_alchemiser/
│   │       └── coordinator_v2/
│   │           └── ...
│   ├── aggregator_v2/
│   ├── portfolio_v2/
│   ├── execution_v2/
│   ├── notifications_v2/
│   ├── trade_aggregator/
│   ├── metrics_v2/
│   ├── data_v2/
│   └── data_quality_monitor/
│
├── layers/
│   ├── shared/                     # NEW - shared code layer
│   │   ├── requirements.txt        # Empty or minimal
│   │   └── python/
│   │       └── the_alchemiser/
│   │           ├── __init__.py
│   │           └── shared/
│   │               ├── __init__.py
│   │               ├── events/
│   │               ├── logging/
│   │               ├── schemas/
│   │               └── ...
│   ├── strategy/                   # Existing - third-party deps
│   ├── portfolio/
│   ├── execution/
│   ├── notifications/
│   └── data/
│
├── the_alchemiser/                 # Keep for local dev & tests
│   ├── __init__.py
│   ├── shared/                     # Source of truth
│   └── ...                         # Module stubs or symlinks
│
├── template.yaml
├── data-template.yaml
└── ...
```

---

## Handler Path Considerations

### Option A: Keep Existing Handler Paths (Recommended)

Keep handler as `the_alchemiser.strategy_v2.lambda_handler.lambda_handler`:
- **Pro**: No code changes needed
- **Pro**: Import paths remain consistent
- **Con**: Directory structure must match (`functions/strategy_v2/the_alchemiser/strategy_v2/`)

### Option B: Simplify Handler Paths

Change handler to `lambda_handler.lambda_handler`:
- **Pro**: Simpler directory structure (`functions/strategy_v2/lambda_handler.py`)
- **Con**: Requires updating all internal imports to be relative or layer-based
- **Con**: Breaking change to existing code

**Recommendation**: Keep Option A to minimize code changes.

---

## Shared Module Import Strategy

When a Lambda imports from shared:
```python
from the_alchemiser.shared.logging import get_logger
```

This works because:
1. Lambda Layer mounts at `/opt/python/` which is in `PYTHONPATH`
2. Layer contains `the_alchemiser/shared/` package
3. Function code contains `the_alchemiser/strategy_v2/` package
4. Python resolves imports from combined paths

**Important**: Both layer and function code must have matching `the_alchemiser/__init__.py` for proper namespace package resolution.

---

## Migration Checklist

### Pre-Migration
- [ ] Audit all shared module dependencies per Lambda
- [ ] Measure current Lambda package sizes
- [ ] Create backup of current working state
- [ ] Set up feature branch for migration

### Phase 1: Shared Layer
- [ ] Create `shared_layer/` directory structure
- [ ] Copy shared code to layer location
- [ ] Add SharedCodeLayer to template.yaml
- [ ] Test layer builds correctly
- [ ] Deploy layer to dev environment

### Phase 2: First Lambda (Coordinator - simplest)
- [ ] Create `functions/coordinator_v2/` structure
- [ ] Move/copy coordinator code
- [ ] Update template.yaml CodeUri
- [ ] Add SharedCodeLayer reference
- [ ] Test locally with `sam local invoke`
- [ ] Deploy to dev
- [ ] Verify functionality

### Phase 3: Remaining Lambdas
- [ ] Repeat Phase 2 for each Lambda:
  - [ ] strategy_v2 (complex - has DSL files)
  - [ ] aggregator_v2
  - [ ] portfolio_v2
  - [ ] execution_v2
  - [ ] notifications_v2
  - [ ] trade_aggregator
  - [ ] metrics_v2

### Phase 4: Data Template Lambdas
- [ ] data_v2
- [ ] data_quality_monitor

### Phase 5: Cleanup
- [ ] Update CI/CD pipelines
- [ ] Update Makefile targets
- [ ] Update documentation
- [ ] Remove old structure references
- [ ] Performance testing

---

## Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Import resolution failures | High | Medium | Comprehensive testing, proper `__init__.py` setup |
| Layer size exceeds limits | Medium | Low | Layer is only Python code (~5-10MB) |
| Deployment ordering issues | Medium | Medium | Document deployment order, update CI/CD |
| DSL file path issues | Medium | Medium | Update strategy file discovery logic |
| Test suite failures | Medium | Medium | Run full test suite before each phase |
| Cold start latency increase | Low | Low | Monitor CloudWatch metrics post-deploy |

---

## Open Questions

1. **Should shared code remain in original location for local development?**
   - Option: Keep `the_alchemiser/shared/` as source of truth, sync to layer at build time
   - Recommendation: Yes, maintain single source of truth

2. **How to handle strategy DSL files (`.clj`)?**
   - Currently in `the_alchemiser/config/*.clj`
   - Options: Include in strategy function CodeUri, or put in S3
   - Recommendation: Include in `functions/strategy_v2/`

3. **Should we use namespace packages or regular packages?**
   - Namespace packages: Allow `the_alchemiser` to span layer + function
   - Regular packages: Need identical `__init__.py` in both
   - Recommendation: Use implicit namespace packages (no `__init__.py` at top level)

4. **Deployment order constraints?**
   - SharedCodeLayer must deploy before functions
   - Current CI/CD may need updates
   - Recommendation: Document and test deployment sequence

---

## Appendix: Size Estimates

### Current State (all Lambdas use `./`)
- Estimated package size: ~15-25MB each (depends on excludes)
- Total deployment: ~150-250MB

### After Migration
- SharedCodeLayer: ~5-10MB
- Per-Lambda packages: ~1-3MB each
- Total deployment: ~20-40MB (significant reduction)

### Layer Limits
- Max unzipped size per layer: 250MB
- Max 5 layers per function
- Current layers: 1-2 per function
- After migration: 2-3 per function (within limits)
