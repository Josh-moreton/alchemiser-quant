# Trade Ledger System

The Trade Ledger System provides persistent tracking of all trade executions with strategy attribution for accurate performance analysis when multiple strategies trade the same ticker.

## Overview

The system consists of several key components:

- **Trade Ledger DTOs**: Strongly typed data models for trade entries, queries, and performance summaries
- **Persistence Layer**: Pluggable backends for local (paper trading) and S3 (live trading) storage
- **Attribution Service**: FIFO-based lot tracking and cross-strategy attribution
- **Programmatic API**: Query and analyze trades via Python API

## Data Model

### TradeLedgerEntry

The atomic unit of trade recording, capturing each execution slice (fill):

```python
TradeLedgerEntry(
    ledger_id="uuid4",           # Unique entry identifier
    event_id="execution-...",    # Event identifier from execution
    correlation_id="uuid4",      # Workflow correlation identifier
    causation_id="uuid4",        # Causation identifier for chaining
    strategy_name="nuclear",     # Strategy that generated this trade
    symbol="AAPL",              # Trading symbol
    side=TradeSide.BUY,         # BUY or SELL
    quantity=Decimal("100"),     # Executed quantity
    price=Decimal("150.00"),     # Execution price per share
    fees=Decimal("1.00"),       # Total fees for this fill
    timestamp=datetime.now(UTC), # Execution timestamp
    order_id="broker-order-123", # Broker order identifier
    account_id="account-1",      # Trading account identifier
    venue="ALPACA",             # Execution venue
    schema_version=1,           # Schema version for migrations
    source="execution_v2.core"  # Source module
)
```

### Key Features

- **Idempotency**: Uses unique keys `(order_id, fill_id)` to prevent duplicates under at-least-once delivery
- **Strategy Attribution**: Every trade is tagged with the originating strategy
- **Correlation Tracking**: Full traceability through correlation and causation IDs
- **Decimal Precision**: All monetary values use Decimal to avoid floating-point errors

## Storage Backends

### Local Backend (Paper Trading)

Uses JSONL files with an index for efficient querying:

```text
./data/trade_ledger/
├── ledger.jsonl    # Append-only trade entries
└── index.json      # Index mapping (order_id, fill_id) -> ledger_id
```

On AWS Lambda, the local filesystem is read-only except for `/tmp`. The Local backend will automatically write to a safe, writable path when running in Lambda:

- Default path on Lambda: `/tmp/alchemiser/trade_ledger`
- Override with env var: set `TRADE_LEDGER_BASE_PATH` to a writable directory

Locally, the default remains `./data/trade_ledger`.

### S3 Backend (Live Trading)

Date-partitioned storage for scalability:

```text
s3://bucket/trade_ledger/
├── 2024/01/15/account.jsonl    # Trade entries for 2024-01-15
├── 2024/01/16/account.jsonl    # Trade entries for 2024-01-16
└── ...

s3://bucket/trade_ledger_index/
├── 2024/01/15/account.json     # Index for 2024-01-15
├── 2024/01/16/account.json     # Index for 2024-01-16
└── ...
```

## Attribution Example

When multiple strategies trade the same ticker:

```python
# Strategy A buys 60 AAPL @ $100
# Strategy B buys 40 AAPL @ $100
# Later, account sells 50 AAPL @ $110 (no strategy tag)

# Attribution uses FIFO across strategies:
# Strategy A: 30 shares sold @ $110 (50% of position) → Realized P&L: $300
# Strategy B: 20 shares sold @ $110 (50% of position) → Realized P&L: $200
```

## Usage

### Enable Trade Ledger in Execution

```python
from the_alchemiser.execution_v2.core.execution_manager import ExecutionManager

manager = ExecutionManager(
    alpaca_manager=alpaca_manager,
    enable_trade_ledger=True  # Enable ledger recording
)
```

### Query Trade History

```python
from the_alchemiser.shared.persistence.trade_ledger_factory import get_default_trade_ledger
from the_alchemiser.shared.schemas.trade_ledger import TradeLedgerQuery

ledger = get_default_trade_ledger()

# Query recent trades for a strategy
query = TradeLedgerQuery(
    strategy_name="nuclear",
    limit=100,
    order_by="timestamp",
    ascending=False
)

entries = list(ledger.query(query))
```

### Calculate Performance

```python
from the_alchemiser.shared.services.trade_performance_service import TradePerformanceService

service = TradePerformanceService(ledger)

# Get strategy performance
summaries = service.get_strategy_performance("nuclear")

# Get attribution report for a symbol
report = service.get_attribution_report("AAPL")
```

## Programmatic API

### List Trade Entries

```python
from the_alchemiser.shared.persistence.trade_ledger_factory import get_default_trade_ledger
from the_alchemiser.shared.schemas.trade_ledger import TradeLedgerQuery

ledger = get_default_trade_ledger()

# List recent trades
query = TradeLedgerQuery(limit=100, order_by="timestamp", ascending=False)
entries = list(ledger.query(query))

# Filter by strategy
query = TradeLedgerQuery(strategy_name="nuclear", limit=100)
entries = list(ledger.query(query))

# Filter by symbol and time range
from datetime import datetime, timedelta, UTC
start_date = datetime.now(UTC) - timedelta(days=7)
query = TradeLedgerQuery(symbol="AAPL", start_date=start_date)
entries = list(ledger.query(query))
```

### Performance Analysis

```python
from the_alchemiser.shared.services.trade_performance_service import TradePerformanceService

service = TradePerformanceService(ledger)

# Show performance summary
all_summaries = service.get_all_performance()

# Strategy-specific performance
nuclear_summaries = service.get_strategy_performance("nuclear")

# Symbol-specific performance across strategies
aapl_summaries = service.get_symbol_performance("AAPL")
```

### Attribution Analysis

```python
# Detailed attribution for a symbol
attribution_report = service.get_attribution_report("AAPL")
print(f"Attribution for AAPL: {attribution_report}")
```

## Configuration

The system automatically selects storage backend based on environment:

- **Paper Trading**: Uses local JSONL files
- **Live Trading**: Uses S3 storage (requires `S3_BUCKET_NAME` environment variable)

Detection is based on:

- `ALPACA_PAPER_TRADING=true`
- `ALPACA_ENDPOINT` containing "paper"

## Implementation Notes

### Execution Integration

Trade ledger recording is integrated at the execution manager level:

1. Orders are executed normally through the execution system
2. After successful execution, `ExecutionResult` is processed
3. Each successful order is converted to `TradeLedgerEntry` format
4. Entries are written to the ledger with strategy attribution

### Error Handling

- Trade ledger failures do not interrupt execution flow
- All operations are logged for debugging
- Idempotency ensures safe retries

### Performance Considerations

- Local backend: In-memory index for fast lookups
- S3 backend: Date partitioning limits scan scope
- Batch operations for multiple entries
- Lazy loading of indexes and data

## Future Enhancements

- **Real-time Price Integration**: Add current market prices for accurate unrealized P&L
- **Corporate Actions**: Handle stock splits and dividend adjustments
- **Advanced Attribution**: Support for tax lot optimization strategies
- **Data Export**: Export to CSV/Excel for external analysis
- **Reconciliation**: Cross-check with broker statements
