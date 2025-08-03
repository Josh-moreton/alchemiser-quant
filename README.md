# The Alchemiser

Internal notes on how the trading bot is put together and how the pieces interact.

## System Architecture

### Configuration and Settings
- `the_alchemiser.core.config` uses Pydantic settings models to load configuration from environment variables and `.env` files.

### Data Layer
- `the_alchemiser.core.data.UnifiedDataProvider` unifies Alpaca REST and WebSocket access to provide account details, quotes and historical data.

### Strategy Layer
- Strategy engines live in `the_alchemiser.core.trading`.
- `MultiStrategyManager` instantiates enabled strategies and keeps per‑strategy position tracking and allocation.

### Execution Layer
- `TradingEngine` orchestrates the full trading cycle: it gathers strategy signals, invokes `PortfolioRebalancer` to compute target allocations and delegates order placement to `SmartExecution`.
- `ExecutionManager` drives multi‑strategy execution; `AccountService` exposes account and position data.

### Tracking and Reporting
- `the_alchemiser.tracking` stores fills, positions and P&L history, while reporting helpers summarise runs for the CLI and email output.

### Command Line Interface
- `the_alchemiser.cli` is built with Typer and provides the `alchemiser` command (`bot`, `trade`, `status`, `deploy`, etc.).

## Execution Flow

1. `load_settings()` builds a typed `Settings` object.
2. `UnifiedDataProvider` connects to Alpaca using those settings.
3. `MultiStrategyManager` runs each strategy and merges their desired portfolios.
4. `TradingEngine` uses `PortfolioRebalancer` to derive required trades.
5. `SmartExecution` submits orders and monitors fills via WebSockets.
6. Results and attribution are persisted by the tracking layer.

## 2025 Python Practices

- Project managed with Poetry and a single `pyproject.toml`.
- Strict typing checked by `mypy` with `disallow_untyped_defs`.
- Configuration and domain models defined with Pydantic.
- Code style enforced by `black` (line length 100) and linted by `flake8`.
- Tests run with `pytest`; `make test` executes the suite.
- Protocols and dataclasses enable clean dependency injection.
- Rich and Typer keep command‑line interfaces concise and user friendly.

## Quick Commands

```
make dev        # install with dev dependencies
make format     # run black
make lint       # run flake8
make test       # run pytest
alchemiser bot  # show current strategy signals
alchemiser trade --live  # live trading
```

---

This README is for personal reference and intentionally omits marketing material.
