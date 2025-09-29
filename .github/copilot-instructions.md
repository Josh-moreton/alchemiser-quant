# Alchemiser Copilot Instructions

## Core guardrails
- Treat floats carefully: never use `==`/`!=`; use `Decimal` for money and `math.isclose` for ratios.
- Every new module file starts with `"""Business Unit: … | Status: current."""` to document ownership.
- Enforce strict typing (`mypy --config-file=pyproject.toml`); avoid `Any` in domain logic and keep DTOs frozen.
- Event handlers must be idempotent, propagate `correlation_id`/`causation_id`, and tolerate replays.
- use `poetry run` for python commands, not system python. Example: `poetry run python -m the_alchemiser`.

## Architecture boundaries
- Five business modules live under `the_alchemiser/`: `strategy_v2`, `portfolio_v2`, `execution_v2`, `orchestration`, `shared`.
- Allowed imports: business modules → `shared`; orchestrators may import business APIs via their `__init__`. No cross business-module imports or deep paths.
- New shared utilities belong in `shared/` and must stay dependency-free on other modules.
- Event contracts and schemas sit in `shared/events` and `shared/schemas`; extend them rather than duplicating payloads.

## Event-driven workflow
- Strategy emits `SignalGenerated` after pulling market data via adapters; payload must include `schema_version`, correlation IDs, and DTO dumps.
- Portfolio consumes `SignalGenerated`, derives `RebalancePlan`, and publishes `RebalancePlanned` with allocation deltas and plan metadata.
- Execution consumes `RebalancePlanned`, executes via Alpaca adapters, and publishes `TradeExecuted` plus `WorkflowCompleted`/`WorkflowFailed`.
- Orchestrators (`orchestration/event_driven_orchestrator.py`) wire handlers through the `EventBus`; prefer registry/event wiring over direct imports.

## Typing & DTO policy
- DTOs live in `shared/dto/` with `ConfigDict(strict=True, frozen=True)` and explicit field types.
- Convert external SDK objects to DTOs at adapter boundaries (e.g., Alpaca managers); never leak raw dicts into business logic.
- When serializing events, call `.model_dump()` and add deterministic hashes for dedupe if workflows require repeat safety.

## Developer workflows
- Install: `poetry install` (or `make dev` for optional groups).
- Format & lint & type-check: `make format && make type-check`.
- Type-check: `make type-check`.
- Import boundaries: `poetry run importlinter --config pyproject.toml`.
- Run trading locally: `poetry run python -m the_alchemiser` (paper vs live controlled by config).
- Deploy via AWS Lambda: `make deploy` → `scripts/deploy.sh`.

## Implementation tips
- Prefer structured logging via `shared.logging`; include `module`, `event_id`, and correlation metadata.
- Use typed exceptions from `shared.errors`; avoid broad `except Exception` without re-raising as module-specific error.
- Keep handlers stateless; persistent state belongs in module-owned stores (see `shared/persistence`).
- Follow module READMEs (`strategy_v2/README.md`, `portfolio_v2/README.md`, etc.) for migration status before moving code.
- When unsure where code belongs, map the responsibility to the business units above before editing.
