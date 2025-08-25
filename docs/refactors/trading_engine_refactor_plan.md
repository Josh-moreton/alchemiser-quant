# Trading Engine Refactor Plan

## Rationale
- `application/trading/trading_engine.py` had grown to ~1.4k lines mixing orchestration,
  infrastructure concerns and reporting.
- Moving toward a Domain‑Driven Design requires separating pure domain policies from
  adapter I/O and introducing typed ports.

## Phased Approach
1. **Extraction (completed)**
   - Moved `TradingEngine` to canonical location `application/trading/engine_service.py`.
   - Removed compatibility wrappers following No Legacy Fallback policy.
   - Introduced typed ports and placeholder domain services.
2. **Behaviour‑preserving refactors**
   - Gradually replace direct adapter imports with protocol‑driven dependencies.
   - Decompose orchestration into smaller application services.
3. **Consolidation & Cleanup**
   - Remove legacy adapters once callers migrate.
   - Strengthen typing and delete dead code.

## Risks & Mitigation
- **Integration drift**: imports now use canonical path `application/trading/engine_service`.
- **Type regressions**: mypy run added to pipeline.
- **Breaking changes**: minimal impact as all callers already used canonical path.

## Rollback Strategy
No rollback needed as compatibility wrapper was not in use. All imports already reference
the canonical path `application/trading/engine_service.py`.

## Quality Gates
```
$ poetry run mypy the_alchemiser
Success: no issues found in 188 source files

$ poetry run alchemiser --help
# Verify CLI functionality
```
