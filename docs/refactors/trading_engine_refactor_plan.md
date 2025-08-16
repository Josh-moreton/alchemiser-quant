# Trading Engine Refactor Plan

## Rationale
- `application/trading/trading_engine.py` had grown to ~1.4k lines mixing orchestration,
  infrastructure concerns and reporting.
- Moving toward a Domain‑Driven Design requires separating pure domain policies from
  adapter I/O and introducing typed ports.

## Phased Approach
1. **Extraction (this commit)**
   - Move legacy `TradingEngine` to `application/trading/engine_service.py`.
   - Provide compatibility wrappers at previous paths for backwards compatibility.
   - Introduce typed ports and placeholder domain services.
2. **Behaviour‑preserving refactors**
   - Gradually replace direct adapter imports with protocol‑driven dependencies.
   - Decompose orchestration into smaller application services.
3. **Consolidation & Cleanup**
   - Remove obsolete wrappers and legacy adapters once callers migrate.
   - Strengthen typing and delete dead code.

## Risks & Mitigation
- **Integration drift**: wrapper ensures existing entry points keep working.
- **Type regressions**: mypy run added to pipeline.
- **Large merge conflicts**: follow phased approach and keep wrapper until callers
  adopt new service.

## Rollback Strategy
Revert `application/trading/engine_service.py` to previous location and remove
wrappers; imports in CLI/container can be pointed back if issues arise.

## Quality Gates
```
$ poetry run mypy the_alchemiser
Success: no issues found in 188 source files

$ poetry run pytest -q --maxfail=1 --disable-warnings
24 passed in 13.42s
```
