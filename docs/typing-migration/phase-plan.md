# Structured Type Migration – Phase Plan

## Phase 5 – Baseline models
- **Entry**: project builds, tests pass, `mypy --strict-optional` no new errors
- **Exit/DoD**: `OrderDetails` and `ExecutionResultDTO` defined; smart execution flow uses them; TODOs for phase 5 resolved
- **Deliverables**: `the_alchemiser/domain/types.py` additions, adapters, unit tests
- **Tasks**:
  1. Create `OrderDetails` and `ExecutionResultDTO` dataclasses
  2. Add adapter converting legacy dict payloads
  3. Refactor `application/execution/smart_execution.py`
  4. Snapshot tests for order CLI output
- **Owned modules**: `the_alchemiser/application/execution/*`, `the_alchemiser/domain/types.py`
- **Breaking change policy**: maintain existing CLI flags; expose JSON identical to pre-refactor
- **Risks**: hidden dict consumers → mitigate with contract tests
- **Roll-back**: revert to dict adapter and disable model usage
- **Test strategy**: unit tests around smart execution; CLI snapshot
- **Static analysis**: `mypy --strict-optional --warn-redundant-casts`; `ruff --select=E,F`
- **Timebox**: M
- **Dependencies**: none

## Phase 6 – Service return typing
- **Entry**: Phase 5 merged
- **Exit**: services returning dict now return typed models
- **Deliverables**: updated service layer functions and models
- **Tasks**:
  1. Sweep services for TODOs (10 items)
  2. Replace return `Dict` with typed models
  3. Update callers and tests
- **Owned modules**: `the_alchemiser/services/**`
- **Breaking change policy**: maintain method signatures, add overload shims
- **Risks**: partial migrations cause mypy issues → keep TypedDict fallbacks
- **Roll-back**: re-enable dict pathways via feature flag
- **Test**: service unit tests, regression suite
- **Static analysis**: `mypy --disallow-any-generics`
- **Timebox**: M
- **Dependencies**: Phase 5

## Phase 7 – Domain model uplift
- **Entry**: Phase 6 merged
- **Exit**: `OrderDetails`, `ExecutionResultDTO` used in domain and application; TODOs Phase 7 cleared
- **Deliverables**: domain adapters, updated mapping layer
- **Tasks**:
  1. Replace residual `Any` with domain models
  2. Update strategy interfaces
- **Modules**: `the_alchemiser/domain/**`, `application/mapping/**`
- **Breaking policy**: no change in strategy plugin API
- **Risks**: plugin incompatibility → provide compatibility layer
- **Roll-back**: revert to prior domain models
- **Tests**: strategy contract tests
- **Static analysis**: `mypy --disallow-untyped-defs`
- **Timebox**: M
- **Dependencies**: Phase 6

## Phase 8 – Application layer cleanup
- **Entry**: Phases 5–7 merged
- **Exit**: application layer free of `Any`/dict TODOs
- **Deliverables**: typed performance data, structured tracking
- **Tasks**:
  1. Resolve ~21 TODOs across application modules
  2. Introduce `PositionSnapshot`, `SignalPayload`
  3. Remove deprecated dict utilities
- **Modules**: `the_alchemiser/application/**`
- **Breaking policy**: CLI/Email unaffected
- **Risks**: wide surface → incrementally commit
- **Roll-back**: git revert of module-specific commits
- **Tests**: unit tests, regression suite
- **Static analysis**: `mypy --warn-unused-ignores`
- **Timebox**: L
- **Dependencies**: Phase 7

## Phase 9 – Provider contracts
- **Entry**: Phase 8 merged
- **Exit**: providers expose typed request/response models
- **Deliverables**: `ProviderResponse`, adapter shims
- **Tasks**:
  1. Define provider models (`Quote`, `Bar`, `OrderAck`)
  2. Update `infrastructure/data_providers/*`
  3. Validate at boundary using pydantic
- **Modules**: `infrastructure/data_providers/**`
- **Breaking**: upstream provider API unchanged
- **Risks**: runtime validation overhead → use compiled models
- **Roll-back**: keep legacy dict adapter
- **Tests**: provider contract tests with recorded fixtures
- **Static analysis**: `mypy --disallow-any-expr`
- **Timebox**: M
- **Dependencies**: Phase 8

## Phase 10 – Typed cache
- **Entry**: Phase 9 merged
- **Exit**: cache manager uses `CacheKey`/`CacheEntry[T]` generics
- **Deliverables**: typed cache layer, schema docs
- **Tasks**:
  1. Introduce `CacheKey` and `CacheEntry[T]`
  2. Refactor cache reads/writes (~11 TODOs)
  3. Document key patterns and TTLs
- **Modules**: `services/shared/cache_manager.py`, provider facades
- **Breaking**: none; keep serialised format stable
- **Risks**: cache invalidation bugs → add integration tests
- **Roll-back**: fallback to untyped cache implementation
- **Tests**: unit + integration verifying serialisation
- **Static analysis**: `mypy --disallow-any-unimported`
- **Timebox**: M
- **Dependencies**: Phase 9

## Phase 11 – Portfolio/position snapshots
- **Entry**: Phase 10 merged
- **Exit**: portfolio utilities use `PositionSnapshot`
- **Deliverables**: model definitions, refactored PnL utilities
- **Tasks**:
  1. Define `PositionSnapshot`
  2. Replace dict-based portfolio structures
  3. Update metrics calculations
- **Modules**: `application/portfolio/**`
- **Breaking**: none
- **Risks**: calculation regressions → snapshot tests
- **Roll-back**: keep old dict version behind toggle
- **Tests**: unit tests for PnL utils
- **Static analysis**: `mypy --no-warn-no-return`
- **Timebox**: M
- **Dependencies**: Phase 10

## Phase 12 – CLI adoption
- **Entry**: Phase 11 merged
- **Exit**: CLI commands consume typed payloads; snapshots updated
- **Deliverables**: typed CLI formatters, docs
- **Tasks**:
  1. Update `interface/cli/**` to accept models
  2. Add snapshot tests for each command
- **Modules**: `interface/cli/**`
- **Breaking**: output format stable; flags unchanged
- **Risks**: stdout formatting differences → snapshot tests
- **Roll-back**: restore dict adapters
- **Tests**: CLI output validation and strategy contract validation
- **Static analysis**: `mypy --warn-redundant-casts`
- **Timebox**: S
- **Dependencies**: Phase 11

## Phase 13 – Email templates
- **Entry**: Phase 12 merged
- **Exit**: templates accept typed context objects
- **Deliverables**: updated templates, snapshot tests
- **Tasks**:
  1. Refactor context building to use models
  2. Update Jinja templates and rendering code
- **Modules**: `interface/email/**`
- **Breaking**: email copy unchanged
- **Risks**: template runtime errors → snapshot tests
- **Roll-back**: fallback to dict context builder
- **Tests**: email snapshot suite
- **Static analysis**: `mypy --warn-unused-configs`
- **Timebox**: S
- **Dependencies**: Phase 12

## Phase 14 – Remove shims
- **Entry**: Phase 13 merged
- **Exit**: no dict adapters remain; all callers use models
- **Deliverables**: deleted adapters, docs updated
- **Tasks**:
  1. Remove temporary conversion utilities
  2. Delete deprecated parameters
- **Modules**: all
- **Breaking**: minimal; bump minor version if CLI/email change
- **Risks**: hidden consumers → run full regression suite
- **Roll-back**: restore adapters from git history
- **Tests**: full regression
- **Static analysis**: `mypy --strict` (allow errors ≤5)
- **Timebox**: M
- **Dependencies**: Phase 13

## Phase 15 – Strict typing finish
- **Entry**: Phase 14 merged
- **Exit**: `mypy --strict` passes; TODO matrix empty
- **Deliverables**: type adoption report, updated docs
- **Tasks**:
  1. Resolve remaining 5 TODOs
  2. Enable `mypy --strict` in CI
  3. Final cleanup and release notes
- **Modules**: repository-wide
- **Breaking**: none
- **Risks**: CI breakage → pre-commit run
- **Roll-back**: relax mypy flags temporarily
- **Tests**: full suite with coverage
- **Static analysis**: `mypy --strict`, `ruff --select=ALL`
- **Timebox**: S
- **Dependencies**: Phase 14
