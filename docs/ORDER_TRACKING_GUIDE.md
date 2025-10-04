# Order Tracking Feature - Quick Start Guide

## Overview

The order tracking feature provides a trade ledger that records all filled orders with comprehensive details including:
- Fill price, bid/ask spreads, quantity, direction
- Order type (MARKET, LIMIT, etc.)
- Timestamp of fill
- Strategy attribution (which strategies contributed to each order)

**Persistence**: Trade ledger entries are automatically saved to S3 after each execution run in JSON format for historical analysis and audit purposes.

## Basic Usage

### Automatic Recording

The trade ledger is automatically populated during execution. No manual intervention needed:

```python
from the_alchemiser.execution_v2.core.executor import Executor
from the_alchemiser.shared.brokers.alpaca_manager import AlpacaManager

# Initialize executor
alpaca_manager = AlpacaManager(...)
executor = Executor(alpaca_manager)

# Execute a rebalance plan
result = await executor.execute_rebalance_plan(plan)

# Access the ledger
ledger = executor.trade_ledger.get_ledger()
print(f"Total trades: {ledger.total_entries}")
print(f"Total buy value: ${ledger.total_buy_value}")
print(f"Total sell value: ${ledger.total_sell_value}")
```

### Query the Ledger

```python
# Get all trades for a specific symbol
aapl_trades = executor.trade_ledger.get_entries_for_symbol("AAPL")

for trade in aapl_trades:
    print(f"{trade.direction} {trade.filled_qty} @ ${trade.fill_price}")
    print(f"  Order ID: {trade.order_id}")
    print(f"  Strategies: {', '.join(trade.strategy_names)}")

# Get all trades attributed to a specific strategy
strategy_trades = executor.trade_ledger.get_entries_for_strategy("momentum_strategy")
```

### Access Individual Trade Details

```python
# Get complete ledger
ledger = executor.trade_ledger.get_ledger()

for entry in ledger.entries:
    print(f"""
    Order ID: {entry.order_id}
    Symbol: {entry.symbol}
    Direction: {entry.direction}
    Quantity: {entry.filled_qty}
    Fill Price: ${entry.fill_price}
    Bid/Ask: ${entry.bid_at_fill} / ${entry.ask_at_fill}
    Timestamp: {entry.fill_timestamp}
    Order Type: {entry.order_type}
    Strategies: {entry.strategy_names}
    """)
```

## Strategy Attribution

### Single Strategy

For a single strategy, no special setup needed. The ledger will record the order without strategy attribution:

```python
# No metadata needed
plan = RebalancePlan(
    correlation_id="corr-123",
    causation_id="cause-123",
    timestamp=datetime.now(UTC),
    plan_id="plan-123",
    items=[...],
    total_portfolio_value=Decimal("10000"),
    total_trade_value=Decimal("5000"),
)
```

### Multi-Strategy Attribution

When multiple strategies suggest the same symbol, include strategy attribution in the rebalance plan metadata:

```python
# Example: Two strategies both suggest AAPL with different weights
# Strategy A wants 30% AAPL, Strategy B wants 20% AAPL
# Combined: 50% AAPL (60% from A, 40% from B)

plan = RebalancePlan(
    correlation_id="corr-123",
    causation_id="cause-123",
    timestamp=datetime.now(UTC),
    plan_id="plan-123",
    items=[
        RebalancePlanItem(
            symbol="AAPL",
            current_weight=Decimal("0.0"),
            target_weight=Decimal("0.5"),
            weight_diff=Decimal("0.5"),
            target_value=Decimal("5000"),
            current_value=Decimal("0"),
            trade_amount=Decimal("5000"),
            action="BUY",
            priority=1,
        )
    ],
    total_portfolio_value=Decimal("10000"),
    total_trade_value=Decimal("5000"),
    metadata={
        "strategy_attribution": {
            "AAPL": {
                "momentum_strategy": 0.6,  # 60% contribution
                "mean_reversion_strategy": 0.4,  # 40% contribution
            }
        }
    }
)

# Execute and check attribution
result = await executor.execute_rebalance_plan(plan)
aapl_trades = executor.trade_ledger.get_entries_for_symbol("AAPL")

for trade in aapl_trades:
    print(f"Strategies: {trade.strategy_names}")
    # Output: ['momentum_strategy', 'mean_reversion_strategy']
    print(f"Weights: {trade.strategy_weights}")
    # Output: {'momentum_strategy': Decimal('0.6'), 'mean_reversion_strategy': Decimal('0.4')}
```

## Missing Data Handling

The trade ledger gracefully handles missing data:

- **No bid/ask data**: Fields set to `None`
- **No order type**: Defaults to "MARKET"
- **No strategy attribution**: Empty lists or `None`
- **Failed orders**: Not recorded (only successful fills)

Example:
```python
entry = executor.trade_ledger.get_entries_for_symbol("TEST")[0]

if entry.bid_at_fill is None:
    print("Bid/ask data not available at fill time")

if not entry.strategy_names:
    print("No strategy attribution available")
```

## Integration with Existing Code

The trade ledger is designed to work seamlessly with existing code:

1. **No breaking changes**: Existing execution code continues to work
2. **Automatic recording**: Filled orders are recorded without manual intervention
3. **Optional access**: Query the ledger only when needed
4. **Backward compatible**: Missing metadata fields are handled gracefully

## Performance Notes

- **Minimal overhead**: Recording happens after order execution
- **Memory efficient**: Only successful fills are stored in-memory during execution
- **S3 persistence**: Ledger is written to S3 once at the end of execution
- **No I/O blocking**: Recording doesn't block execution flow
- **Thread safe**: Service can be safely accessed from multiple contexts

## S3 Storage

Trade ledger entries are automatically persisted to S3 for long-term storage and analysis:

### Storage Structure

```
s3://the-alchemiser-v2-trade-ledger-{stage}/
  └── trade-ledgers/
      └── 2024/
          └── 01/
              └── 15/
                  └── 143052-{ledger-id}-{correlation-id}.json
```

### Retention

- Indefinite retention: Trade ledger data is stored permanently for audit purposes
- No automatic cleanup
- Manual deletion can be performed if needed via AWS console or CLI

### Configuration

Set via environment variables (automatically configured in Lambda):

```bash
TRADE_LEDGER__BUCKET_NAME=the-alchemiser-v2-trade-ledger-dev
TRADE_LEDGER__ENABLED=true  # Set to false to disable S3 persistence
```

### Accessing Historical Data

```python
# Ledgers are stored as JSON files in S3
# Example: Download and analyze past executions
import boto3
import json

s3 = boto3.client('s3')
bucket = 'the-alchemiser-v2-trade-ledger-prod'

# List all ledger files for a specific date
response = s3.list_objects_v2(
    Bucket=bucket,
    Prefix='trade-ledgers/2024/01/15/'
)

# Download and parse a specific ledger
obj = s3.get_object(Bucket=bucket, Key='trade-ledgers/2024/01/15/143052-abc123-xyz789.json')
ledger_data = json.loads(obj['Body'].read())
```

## Examples

See the test file for comprehensive examples:
- `tests/execution_v2/test_trade_ledger.py`

## API Reference

### TradeLedgerService

Main service for recording and querying trades.

**Methods:**
- `record_filled_order(order_result, correlation_id, rebalance_plan, quote_at_fill)` - Record a filled order
- `get_ledger()` - Get complete ledger
- `get_entries_for_symbol(symbol)` - Filter by symbol
- `get_entries_for_strategy(strategy_name)` - Filter by strategy
- `total_entries` - Property returning count of entries

### TradeLedgerEntry

Individual trade record with all execution details.

**Fields:**
- `order_id: str` - Broker order ID
- `symbol: str` - Trading symbol
- `direction: Literal["BUY", "SELL"]` - Trade direction
- `filled_qty: Decimal` - Quantity filled
- `fill_price: Decimal` - Average fill price
- `bid_at_fill: Decimal | None` - Bid at fill time
- `ask_at_fill: Decimal | None` - Ask at fill time
- `fill_timestamp: datetime` - Fill timestamp
- `order_type: str` - Order type (MARKET, LIMIT, etc.)
- `strategy_names: list[str]` - Contributing strategies
- `strategy_weights: dict[str, Decimal] | None` - Strategy weight allocation

### TradeLedger

Collection of trade entries with aggregate metrics.

**Fields:**
- `entries: list[TradeLedgerEntry]` - All ledger entries
- `ledger_id: str` - Unique ledger ID
- `created_at: datetime` - Ledger creation time

**Properties:**
- `total_entries: int` - Number of entries
- `total_buy_value: Decimal` - Total BUY trade value
- `total_sell_value: Decimal` - Total SELL trade value
