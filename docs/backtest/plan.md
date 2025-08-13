# Backtest Engine Delivery Plan

## Objectives
- Provide a faithful, latency-aware backtest engine using quote/trade based fills.
- Maintain parity with the Alpaca SDK surface to allow seamless strategy reuse.

## Non-goals
- Full depth-of-book or venue level modelling.
- Smart order routing across multiple venues.

## Milestones

### M1 – Scaffolding
- **Acceptance**: Core module skeletons exist and import cleanly.
- **Tests**: `pytest tests/backtest -q` executes stubs.
- **DoD**: Modules under 400 lines, documented with TODOs.

### M2 – Market Data Replay
- **Acceptance**: Replayer merges multi-symbol events deterministically.
- **Tests**: `test_data_replayer_ordering.py`.
- **DoD**: Calendar gating implemented via `pandas_market_calendars`.

### M3 – Execution Engine & Broker
- **Acceptance**: Market and limit orders fill with basic queueing and slippage hooks.
- **Tests**: `test_execution_market_and_limit.py`.
- **DoD**: Deterministic fills given identical seeds.

### M4 – Accounting
- **Acceptance**: FIFO ledger with fees and corporate action hooks.
- **Tests**: `test_accounting_fifo.py`.
- **DoD**: Realised/unrealised P&L tracked for each symbol.

### M5 – Runner & CLI
- **Acceptance**: End-to-end run produces artefacts (`orders.csv`, `fills.csv`, `stats.json`).
- **Tests**: `test_cli_smoke.py`, `test_runner_determinism.py`.
- **DoD**: CLI exposed via `poetry run alchemiser backtest`.

### M6 – Metrics & Reporting
- **Acceptance**: Equity curve, drawdown and turnover metrics available.
- **Tests**: Future additions to `tests/backtest`.
- **DoD**: Artefacts extend to include `pnl.csv` and `stats.json`.

## Risk & Bias Controls
- No look-ahead: events processed strictly in timestamp order.
- Use of PIT universes to avoid survivorship bias.
- Deterministic seeds allow reproducible runs.
- Delisting and corporate action caveats documented.

## Calibration Path
- Optional live recorder for capturing live fills and quotes.
- Tune queue parameter `q` and `impact_coeff` by comparing live vs backtest logs.

## Performance Plan
- Parquet partitioning by symbol/day with lazy loading.
- Batch processing per symbol to bound memory usage.
- Progress bars via `tqdm` for long replays.

## Runbooks
- **Quickstart**: `poetry run alchemiser backtest --start 2024-06-03 --end 2024-06-07 --symbols AAPL,MSFT --config configs/backtest.example.yaml`
- **Reproduce**: Re-run with same seed to obtain identical artefacts.
- **Export**: Load `fills.csv`/`orders.csv` into Pandas for analysis.
