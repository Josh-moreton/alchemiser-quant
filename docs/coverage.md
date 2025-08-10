# Coverage Plan for The Alchemiser CLI

## Mode to Module Map

### `alchemiser signal`
- Entry: `the_alchemiser.interface.cli.cli:signal`
- Core logic: `the_alchemiser.main.run_all_signals_display`
- Key modules involved:
  - `the_alchemiser.main` (signal orchestration)
  - `the_alchemiser.application.strategy_manager`
  - `the_alchemiser.services` signal generators (Nuclear, TECL, KLM)
  - `the_alchemiser.interface.cli.cli_formatter` (Rich output)

### `alchemiser trade` (paper)
- Entry: `the_alchemiser.interface.cli.cli:trade`
- Core logic: `the_alchemiser.main.run_multi_strategy_trading`
- Key modules involved:
  - `the_alchemiser.execution.trading_engine`
  - `the_alchemiser.application.strategy_manager`
  - `the_alchemiser.services` order sizing & risk controls
  - `the_alchemiser.infrastructure.logging` utilities

### `alchemiser trade --live`
- Entry: same `trade` command with `--live` flag
- Exercises live‑trading branches in `run_multi_strategy_trading`
- Additional modules:
  - `the_alchemiser.execution.trading_engine` live path
  - Broker adapters (`the_alchemiser.infrastructure.broker.*`)
  - Enhanced risk checks and confirmation prompts

## Reproducible Coverage Commands

```bash
# Clean prior data
find . -name '.coverage*' -delete

# Unit + integration coverage
pytest -q \
  --cov=the_alchemiser --cov-branch \
  --cov-report=term-missing --cov-report=xml --cov-report=html

# CLI-driven coverage (simulate each mode)
export DRY_RUN=1 PYTHONHASHSEED=0
coverage run -m the_alchemiser.interface.cli.cli signal --no-header || true
coverage run -a -m the_alchemiser.interface.cli.cli trade --force --ignore-market-hours || true
coverage run -a -m the_alchemiser.interface.cli.cli trade --live --force --ignore-market-hours || true

# Combine + report
coverage combine
coverage html
coverage xml
coverage report -m
```

## Targeted Test Recommendations
- Mock broker/network/time side effects to ensure dry runs.
- Exercise error paths: API timeouts, rejected orders, rate limits.
- Edge cases: zero or conflicting signals, stale cache, missing credentials.
- Risk controls: position limits, notional caps, duplicate-order guards.
- CLI UX: invalid flags, help text, version, dry-run behaviour.

## CI Integration
A GitHub Actions workflow (`.github/workflows/tests.yml`) runs tests with branch coverage,
exports `DRY_RUN=1`, uploads `htmlcov` artefacts and enforces `--cov-fail-under=85`.
