# Alchemiser Copilot Instructions

## Overview
- Multi-strategy trading bot; core components:
  - `the_alchemiser.core.config` uses Pydantic settings for env-based configuration.
  - `UnifiedDataProvider` (in `core/data`) merges Alpaca REST and WebSocket feeds.
  - Strategy engines live in `core/trading`; `MultiStrategyManager` combines outputs.
  - `TradingEngine` and `SmartExecution` handle portfolio rebalancing and order placement.
  - Tracking lives under `tracking/` for P&L and fill history.
- CLI (`the_alchemiser.cli`) built with Typer exposes `alchemiser` commands (`bot`, `trade`, `status`, etc.).

## Project Conventions
- Python ≥3.11 with Poetry for deps.
- Strict typing enforced via mypy; every function must be type annotated.
- Format with Black and lint/fix with Ruff (line length 100).
- Prefer Protocols/dataclasses over bare dicts.
- Centralised error handling via `core/error_handler.TradingSystemErrorHandler` with categorized exceptions.

## Workflow
- Install dev deps: `pip install -e .[dev]` or `make dev`.
- Format & lint: `pre-commit run --files <files>` or `make format` / `make lint`.
- Run tests: `pytest tests/ -v` or `make test` (coverage enabled by default via pyproject).
- Common Make targets: `run-signals`, `run-trade`, `run-trade-live`, `status`, `deploy`.

## Testing Notes
- Tests organised under `tests/` with subdirs: `unit/`, `integration/`, `contract/`, `property/`, `simulation/`, `infrastructure/`, `utils/`, and `fixtures/`.
- Use pytest-mock fixtures; never call real external APIs in tests.
- Standard fixtures in `tests/conftest.py` provide mock Alpaca/AWS clients and market scenarios.

## Style Reminders
- Keep lines ≤100 chars; imports sorted automatically by Ruff.
- Avoid bare `except:`; raise project-specific exceptions from `core/exceptions.py`.
- Place new modules under appropriate package (`core/`, `execution/`, `tracking/`, `utils/`).

