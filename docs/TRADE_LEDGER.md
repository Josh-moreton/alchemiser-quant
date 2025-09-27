# Trade Ledger: Design, APIs, and Usage

This document explains the trade ledger system in The Alchemiser. It covers data models (DTOs), the ledger protocol, implementations (local JSONL and S3), calculations (lots and performance), account value logging, configuration, file formats, integrity checks, and example usage patterns.

> Business Unit: shared | Status: current.

---

## Objectives and responsibilities

The trade ledger provides an append-only, idempotent record of all executions (fills) per strategy. It enables:

- Accurate performance attribution when multiple strategies trade the same symbol
- Querying and aggregations by strategy/symbol/time windows
- FIFO-aware lot calculation for open positions
- Realized/unrealized P&L and activity summaries
- Lightweight account value snapshots for portfolio-level P&L

It sits in the Shared layer and is consumed by portfolio/execution modules through the protocol interface.

---

## Key data models (DTOs)

Location: `the_alchemiser/shared/schemas/trade_ledger.py`

- TradeLedgerEntry
  - Atomic execution slice (fill), including strategy_name, symbol, side, quantity (Decimal), price (Decimal), fees (Decimal), timestamp (UTC), order references, and correlation/causation metadata.
  - Idempotency key: `(order_id, fill_id or ledger_id)` via `get_unique_key()`.
  - Helpers: `total_value`, `net_value`.
- TradeLedgerQuery
  - Filters by strategy, symbol, asset_type, side, account_id; plus date range, pagination, ordering.
- Lot
  - Represents an open position slice with quantity, cost_basis, opened_timestamp, opening_ledger_ids, and remaining_quantity.
- PerformanceSummary
  - Aggregates realized_pnl, realized_trades, open_quantity, open_lots_count, average_cost_basis, current_price (optional), unrealized_pnl, totals of buys/sells/fees.
- AccountValueEntry and AccountValueQuery
  - Daily (or ad hoc) portfolio snapshots: portfolio_value, cash, equity; with timestamp and source.

All DTOs are strict and frozen Pydantic models; timestamps are timezone-aware; symbols and strategy names are normalized.

---

## Protocol: persistence contract

Location: `the_alchemiser/shared/protocols/trade_ledger.py`

Core methods:
- upsert(entry), upsert_many(entries): idempotent append with index; respect `DISABLE_FULL_TRADE_LOGGING`.
- query(filters): retrieve entries matching filters and ordering/pagination.
- get_open_lots(strategy, symbol): compute open lots (FIFO-based).
- calculate_performance(strategy, symbol, current_prices): return `PerformanceSummary` objects at symbol and per-strategy (symbol=None) granularity.
- get_ledger_entries_by_order(order_id): retrieve all fills for an order.
- verify_integrity(): structural verification and index reconciliation.

Implementations MUST follow the protocol and ensure deterministic, idempotent behavior.

---

## Implementations

### Local JSONL: `the_alchemiser/shared/persistence/local_trade_ledger.py`

- Storage layout (default): `./data/trade_ledger/`
  - `ledger.jsonl`: append-only execution entries (one JSON line per fill)
  - `index.json`: idempotent key index mapping `(order_id||fill_id)` → `ledger_id`
  - `account_values.jsonl`: append-only account value snapshots
- Environment override: `TRADE_LEDGER_BASE_PATH`; on AWS Lambda defaults to `/tmp/alchemiser/trade_ledger`.
- Upsert rules: reject duplicates by unique key; warn on duplicate keys with different IDs.
- Query: streaming parse and filter, then sort and paginate in-memory (sufficient for volumes in paper mode).
- Performance and lots: delegates to `BaseTradeLedger` shared logic.
- Account value APIs: `log_account_value`, `query_account_values`, `get_latest_account_value`.

### S3-backed: `the_alchemiser/shared/persistence/s3_trade_ledger.py` (if present)

- Similar interfaces with S3 objects instead of local files; batching and eventual consistency considerations.
- Recommended for production/live trading; local JSONL for dev/paper mode.

---

## Shared calculations: `BaseTradeLedger`

Location: `the_alchemiser/shared/persistence/base_trade_ledger.py`

- `_matches_filters`: applies `TradeLedgerQuery` filter semantics.
- `_calculate_lots_from_entries(entries)`: FIFO match sells to buys to derive remaining open lots per (strategy, symbol).
- `_calculate_performance_from_entries(entries, current_prices)`: builds `PerformanceSummary` list by symbol and per-strategy (symbol=None). Includes:
  - Basic metrics: totals of buys/sells/fees, realized_trades
  - Realized P&L: `total_sell_value - total_buy_value` (fees included)
  - Open position and unrealized via open lots and optional `current_prices`

Note: lots are recomputed from entry history; for high throughput, consider indexing/caching in future.

---

## Account value logging service

Location: `the_alchemiser/shared/services/account_value_service.py`

- Wraps the trade ledger account value APIs with feature gating.
- `log_current_account_value(account)`: logs an `AccountValueEntry` (idempotent per date via ledger implementation).
- `get_account_value_history(account_id, start, end)`: returns sorted snapshots.
- `get_latest_account_value(account_id)`: fetch the last snapshot for an account.
- Config toggle: `is_account_value_logging_enabled()`; if disabled, methods are no-ops.

Usage:
- Enables portfolio-level P&L (e.g., monthly summary) even when full trade logging is disabled.

---

## Performance summaries and monthly reporting

- `calculate_performance(...)` produces symbol-level and per-strategy (symbol=None) `PerformanceSummary` objects.
- For monthly reporting:
  - Portfolio P&L ($ and %) computed from `AccountValueEntry` first vs last snapshot within the calendar month (UTC window).
  - Per-strategy realized P&L ($) presented without percentages to avoid capital base ambiguity.
- Implemented in `the_alchemiser/shared/services/monthly_summary_service.py`; rendered via `the_alchemiser/shared/notifications/templates/monthly.py` and sent through the email client.

---

## File formats (local JSONL)

- `ledger.jsonl`: one JSON object per line representing a `TradeLedgerEntry` (datetime ISO8601, Decimals serialized to strings).
- `index.json`: JSON object keyed by `"order_id||fill_id"` to `ledger_id`.
- `account_values.jsonl`: one JSON object per line representing an `AccountValueEntry` (datetime ISO8601, Decimals as strings).

Example ledger line (pretty-printed):
```json
{
  "ledger_id": "...",
  "event_id": "...",
  "correlation_id": "...",
  "causation_id": "...",
  "strategy_name": "Phoenix",
  "symbol": "AAPL",
  "asset_type": "STOCK",
  "side": "BUY",
  "quantity": "10.0",
  "price": "175.32",
  "fees": "0.00",
  "timestamp": "2025-08-29T14:31:05+00:00",
  "order_id": "...",
  "client_order_id": null,
  "fill_id": "...",
  "account_id": "acc-123",
  "venue": "ALPACA",
  "schema_version": 1,
  "source": "execution_v2.core",
  "notes": null
}
```

Example account value line:
```json
{
  "entry_id": "...",
  "account_id": "acc-123",
  "portfolio_value": "10000.00",
  "cash": "1000.00",
  "equity": "10000.00",
  "timestamp": "2025-08-31T23:59:59+00:00",
  "source": "account_value_service"
}
```

---

## Integrity and idempotency

- `verify_integrity()` scans and validates the ledger file and index consistency; rebuilds the index on mismatch.
- Upserts are idempotent by unique key `(order_id, fill_id)`, with warnings on duplicate keys with different `ledger_id`.
- When `DISABLE_FULL_TRADE_LOGGING=true`, trade upserts become no-ops while account value logging can continue.

---

## Configuration and environment

- Storage selection:
  - Local JSONL is the default for paper/dev; S3 for prod.
  - Lambda defaults local storage base path to `/tmp/alchemiser/trade_ledger` for writable ephemeral storage.
- Feature toggles (via `the_alchemiser/shared/persistence/trade_ledger_factory.py` and settings):
  - `is_account_value_logging_enabled()` → gate account value APIs.
  - `is_full_trade_logging_disabled()` → skip upserting trade entries.
- Paper vs Live detection is handled in orchestration; ledger selection is environment-driven.

---

## Typical usage patterns

- Record fills during execution:
  - Use the appropriate ledger (from `get_default_trade_ledger()`) and call `upsert`/`upsert_many`.
- Compute performance for a strategy:
  - Call `calculate_performance(strategy=..., current_prices=...)` and take the symbol=None rows for per-strategy totals.
- Query history for analysis:
  - Use `TradeLedgerQuery` with date filters to get entries for a period.
- Portfolio P&L for a month:
  - Use `AccountValueService.get_account_value_history(account_id, start, end)` and compare first vs last.

---

## Edge cases and cautions

- Decimals: all monetary/quantity fields are Decimal; avoid float equality and round appropriately when displaying.
- Timezones: all timestamps are UTC and validated; monthly windows use UTC calendar boundaries.
- Partial data: If only one account value snapshot exists in a month, we show the value and omit % unless start value is > 0.
- Performance scope: `calculate_performance` works on the implementation’s data; when you need a strict window, first query entries (with `TradeLedgerQuery`) and compute via `BaseTradeLedger` methods.

---

## Minimal code examples

Python snippets (illustrative):

```python
from datetime import UTC, datetime
from the_alchemiser.shared.persistence.trade_ledger_factory import get_default_trade_ledger
from the_alchemiser.shared.schemas.trade_ledger import TradeLedgerEntry, TradeLedgerQuery, TradeSide

ledger = get_default_trade_ledger()

# Upsert a fill
entry = TradeLedgerEntry(
    ledger_id="...", event_id="...", correlation_id="...", causation_id="...",
    strategy_name="Phoenix", symbol="AAPL", side=TradeSide.BUY,
    quantity=Decimal("10"), price=Decimal("175.32"), fees=Decimal("0"),
    timestamp=datetime.now(UTC), order_id="...", source="execution_v2.core"
)
ledger.upsert(entry)

# Query last week’s entries for Phoenix
q = TradeLedgerQuery(strategy_name="Phoenix", start_date=datetime(2025, 8, 24, tzinfo=UTC), end_date=datetime(2025, 8, 31, tzinfo=UTC))
rows = list(ledger.query(q))

# Strategy performance
summaries = ledger.calculate_performance(strategy="Phoenix", current_prices={"AAPL": 176.0})
strategy_total = [s for s in summaries if s.symbol is None][0]
print(strategy_total.realized_pnl)
```

```python
# Account value P&L for a month
from calendar import monthrange
from the_alchemiser.shared.services.account_value_service import AccountValueService

svc = AccountValueService(ledger)
year, month = 2025, 8
start = datetime(year, month, 1, tzinfo=UTC)
end = datetime(year, month, monthrange(year, month)[1], 23, 59, 59, tzinfo=UTC)
entries = svc.get_account_value_history("acc-123", start, end)
if entries:
    pnl_abs = entries[-1].portfolio_value - entries[0].portfolio_value
    pnl_pct = pnl_abs / entries[0].portfolio_value * Decimal("100") if entries[0].portfolio_value else None
```

---

## Where to go next

- Business logic: `the_alchemiser/shared/persistence/base_trade_ledger.py`
- Local ledger: `the_alchemiser/shared/persistence/local_trade_ledger.py`
- Protocol: `the_alchemiser/shared/protocols/trade_ledger.py`
- Account value service: `the_alchemiser/shared/services/account_value_service.py`
- Monthly summary service/template: `the_alchemiser/shared/services/monthly_summary_service.py`, `the_alchemiser/shared/notifications/templates/monthly.py`
