# Alchemiser Copilot Instructions

## Core guardrails
- **Floats:** Never use `==`/`!=` on floats. Use `Decimal` for money; `math.isclose` for ratios; set explicit tolerances.
- **Module header:** Every new module begins with `"""Business Unit: <name> | Status: current."""`.
- **Typing:** Enforce strict typing (`mypy --config-file=pyproject.toml`). No `Any` in domain logic. DTOs are frozen.
- **Idempotency & traceability:** Event handlers must be idempotent; propagate `correlation_id` and `causation_id`; tolerate replays.
- **Tooling:** Use Poetry for everything. Example: `poetry run python -m the_alchemiser` (no system Python).
- **Version Management (MANDATORY):** AI agents MUST update version numbers for every code change using semantic versioning:
  - **PATCH** (`make bump-patch`): Bug fixes, documentation updates, minor refactoring, test additions
  - **MINOR** (`make bump-minor`): New features, new modules, significant refactoring, API additions (backward compatible)
  - **MAJOR** (`make bump-major`): Breaking changes, API changes, architectural overhauls, removed features
  - **Workflow:** Stage your code changes first (`git add <files>`), then run the appropriate bump command. The bump will commit both your staged changes AND the version bump together.

## Python Coding Rules for AI Agents

### 1. Single Responsibility Principle (SRP)
- Each file/module has one clear purpose. No mixing concerns (e.g. DB, HTTP, trading logic in one file).

### 2. File Size Discipline
- Target **≤ 500 lines per module**.
- Split when **> 800 lines** or **> 20 functions/classes**.

### 3. Function/Method Size
- **≤ 50 lines** per function (aim 10–30).
- **≤ 5 parameters** (excluding `self`). Extract objects/params if exceeded.

### 4. Complexity
- Cyclomatic complexity **≤ 10** per function (radon/mccabe).
- Cognitive complexity **≤ 15**. Flatten nesting; early returns preferred.

### 5. Naming & Cohesion
- Group related code into purposeful modules (e.g. `data_parsers.py`, `risk_controls.py`).
- Ban `misc.py`, `helpers.py`, and grab-bag modules.

### 6. Imports
- No `from x import *`.
- Order: stdlib → third-party → local; keep import sections separated.
- Absolute imports inside business modules; no deep relative spelunking.

### 7. Tests
- Every public function/class has at least one test.
- Mirror source structure (`tests/test_<module>.py`).
- Include **property-based tests** (Hypothesis) for critical maths/strategies.
- Deterministic tests: freeze time and seed RNG (`random`, `numpy`).

### 8. Error Handling
- No silent `except`. Catch narrow exceptions; re-raise as module-specific errors from `shared.errors`.
- Retries for I/O with bounded backoff; no infinite loops.

### 9. Documentation
- Docstrings on all public APIs (purpose, args, returns, raises, examples).
- Module docstring explains responsibility and invariants.

### 10. No Hardcoding
- No magic numbers/paths/secrets in code.
- Use constants, config, or environment variables; 12-factor friendly.

## Architecture boundaries
- Business modules under `the_alchemiser/`: `strategy_v2`, `portfolio_v2`, `execution_v2`, `orchestration`, `shared`.
- Allowed imports: business modules → `shared`.
- Orchestrators may import business **APIs via their `__init__`** only.
- **No cross business-module imports** or deep path imports.
- Shared utilities live in `shared/` and **must have zero** dependencies on business modules.
- Event contracts and schemas: `shared/events`, `shared/schemas` (extend, don’t duplicate).

## Event-driven workflow
- **Strategy** emits `SignalGenerated` after adapter data pull; payload includes `schema_version`, correlation/causation IDs, and DTO dumps.
- **Portfolio** consumes `SignalGenerated`, creates `RebalancePlan`, publishes `RebalancePlanned` with allocation deltas and plan metadata.
- **Execution** consumes `RebalancePlanned`, executes via broker adapters, publishes `TradeExecuted` + `WorkflowCompleted`/`WorkflowFailed`.
- **Orchestration** wires handlers via `EventBus` (`orchestration/event_driven_orchestrator.py`). Prefer registry/event wiring over direct imports.

## Typing & DTO policy
- DTOs in `shared/schemas/` with `ConfigDict(strict=True, frozen=True)`, explicit field types, and versioned via `schema_version`.
- Convert external SDK objects to DTOs at adapter boundaries; never leak raw dicts into domain logic.
- Event serialisation uses `.model_dump()`. Add deterministic idempotency keys (hash of DTO payload + schema version) where dedupe is required.

## Security & compliance
- **No secrets in code or logs.** Redact tokens, API keys, account IDs.
- Validate all external data at boundaries with DTOs (fail-closed).
- Forbid `eval`, dynamic `exec`, and unvetted dynamic imports.
- Use least privilege for AWS Lambda roles; environment variable allow-list in config loader.
- Run static analysis (`bandit`) and secret scanning (`gitleaks`) in CI.

## Data & time-series discipline
- Money: `Decimal` with explicit contexts; never mix with float.
- Market data: indexing is by `UTC` timestamps; always timezone-aware (`datetime.timezone.utc`).
- Avoid in-place Pandas mutations in domain logic; prefer pure transforms returning new frames/series.
- Vectorise hot paths; avoid Python loops over rows.
- Handle missing data explicitly (forward-fill/back-fill rules documented at call-site).

## Concurrency & I/O
- I/O boundaries are **async** where possible; pure computation stays sync.
- No hidden I/O in strategies/portfolio logic; all side-effects live in adapters.
- Centralise HTTP sessions/clients; respect rate limits; backoff with jitter.

## Developer workflows
- Install: `poetry install` (or `make dev` for optional groups).
- Format/lint/type-check: `make format && make type-check`.
- Type-check only: `make type-check`.
- Import boundaries: `poetry run importlinter --config pyproject.toml`.
- Local trading: `poetry run python -m the_alchemiser` (paper/live via config).
- **Deployment (CRITICAL - READ CAREFULLY):**
  - **DEV/BETA deployment:** `make release-beta` - ALWAYS use this for testing changes
  - **PRODUCTION deployment:** `make release` - ONLY after thorough testing in dev
  - **NEVER run `sam deploy` directly** - it defaults to production!
  - **NEVER run `sam deploy --no-confirm-changeset`** without `--config-env dev`
- **Version management (recommended workflow):**
  1. Make your code changes
  2. Run `make format && make type-check` to verify changes
  3. Stage your changes: `git add <files>`
  4. Run appropriate bump command: `make bump-patch` / `make bump-minor` / `make bump-major`
  5. The bump command commits both your staged changes and the version bump together
- **Releases**: Create releases with `make release` (auto-version) or `make release v=x.y.z` (custom version).

## Observability
- Use `shared.logging` for structured JSON logs; include `module`, `event_id`, `correlation_id`, and key business facts (symbol, qty, price).
- Emit one log line per state change; avoid noisy debug spam in hot loops.

## Pull request & CI gates
- CI must pass: format, lint, type, imports, security (bandit), secrets (gitleaks), tests.
- Max PR size: **~400 lines diff** unless refactor flagged with `#refactor` label.
- No failing or skipped tests on `main`.
- Lockfile changes justified in PR description.

## Hard limits (enforced targets)
- **Module lines:** ≤ 500 (soft), split at > 800.
- **Function lines:** ≤ 50. **Params:** ≤ 5.
- **Cyclomatic complexity:** ≤ 10. **Cognitive:** ≤ 15.
- **Public API test coverage:** ≥ 90% for strategy/portfolio; ≥ 80% overall until raised.
- **Latency budgets:** adapter calls must expose timeouts; no call without a timeout.

## Implementation tips
- Use `shared.logging` and `shared.errors`; never catch `Exception` without re-raising a typed error.
- Keep handlers stateless; state is managed via Alpaca API for P&L tracking.
- Follow module READMEs (`strategy_v2/README.md`, `portfolio_v2/README.md`, …) for migration status before moving code.
- When responsibility is unclear, map it to a business unit above **before** writing code.
