# Batch 15 Migration Plan

**Target**: 15 files (DSL components, portfolio components, policies)
**Expected Import Updates**: ~18 statements
**Focus**: Strategy DSL, portfolio domain logic, policy frameworks

## Files to Migrate

| File | Current Location | Target Location | Imports | Business Unit |
|------|------------------|-----------------|---------|---------------|
| `domain/dsl/__init__.py` | DSL module init | `strategy/dsl/legacy_init.py` | 3 | strategy |
| `domain/dsl/ast.py` | DSL AST | `strategy/dsl/ast.py` | 0 | strategy |
| `domain/dsl/interning.py` | DSL interning | `strategy/dsl/interning.py` | 1 | strategy |
| `domain/dsl/optimization_config.py` | DSL config | `strategy/dsl/optimization_config.py` | 0 | strategy |
| `domain/dsl/parser.py` | DSL parser | `strategy/dsl/parser.py` | 2 | strategy |
| `domain/dsl/strategy_loader.py` | DSL loader | `strategy/dsl/strategy_loader.py` | 5 | strategy |
| `domain/math/protocols/asset_metadata_provider.py` | Math protocols | `shared/protocols/asset_metadata.py` | 1 | shared |
| `domain/policies/position_policy.py` | Position policy | `portfolio/policies/position_policy.py` | 1 | portfolio |
| `domain/policies/protocols.py` | Policy protocols | `portfolio/policies/protocols.py` | 0 | portfolio |
| `domain/policies/risk_policy.py` | Risk policy | `portfolio/policies/risk_policy.py` | 1 | portfolio |
| `domain/portfolio/position/position_analyzer.py` | Position analyzer | `portfolio/analytics/position_analyzer.py` | 1 | portfolio |
| `domain/portfolio/position/position_delta.py` | Position delta | `portfolio/analytics/position_delta.py` | 1 | portfolio |
| `domain/portfolio/rebalancing/rebalance_calculator.py` | Rebalance calc | **DELETE** (deprecated shim) | 1 | N/A |
| `domain/portfolio/rebalancing/rebalance_plan.py` | Rebalance plan | `portfolio/rebalancing/rebalance_plan.py` | 1 | portfolio |
| `domain/portfolio/strategy_attribution/attribution_engine.py` | Attribution | `portfolio/analytics/attribution_engine.py` | 1 | portfolio |

## Migration Strategy

1. **DSL Components** → `strategy/dsl/` - Strategy-related domain specific language
2. **Portfolio Components** → `portfolio/` (analytics, policies, rebalancing)
3. **Shared Protocols** → `shared/protocols/`
4. **Remove Deprecated Shims** - Delete files that are just deprecation warnings

## Expected Outcomes

- 15 files migrated to proper business unit locations
- 1 deprecated shim file removed
- ~18 import statements updated
- Proper modular architecture alignment maintained