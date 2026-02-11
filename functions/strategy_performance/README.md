# Strategy Performance Lambda

**Business Unit: strategy_performance | Status: current**

## Overview

The Strategy Performance Lambda consumes `TradeExecuted` events from EventBridge and writes per-strategy performance metrics to DynamoDB. These metrics power the Streamlit dashboard for strategy-level analytics (P&L, win rate, holdings).

## Architecture

```
EventBridge (alchemiser.execution / TradeExecuted)
    |
    v
StrategyPerformanceFunction
    |
    |--- READ ---> TradeLedgerTable (GSI3, GSI5, Scan)
    |                  |
    |                  +-- STRATEGY_METADATA items (GSI3-StrategyIndex)
    |                  +-- LOT items per strategy   (GSI5-StrategyLotsIndex)
    |
    |--- WRITE --> StrategyPerformanceTable
                       |
                       +-- STRATEGY#{name} / SNAPSHOT#{ts}  (time-series)
                       +-- LATEST / STRATEGY#{name}         (current pointer)
                       +-- CAPITAL_DEPLOYED / SNAPSHOT#{ts}  (capital metric)
                       +-- LATEST / CAPITAL_DEPLOYED         (current pointer)
```

## DynamoDB Tables

### TradeLedgerTable (Read Source)

| Access Pattern | Index | Key Condition |
|----------------|-------|---------------|
| List all strategy metadata | `GSI3-StrategyIndex` | `GSI3PK = "STRATEGIES"` |
| Query all lots for a strategy | `GSI5-StrategyLotsIndex` | `GSI5PK = "STRATEGY_LOTS#{name}"` |
| Discover strategies with open lots | Table scan | `begins_with(PK, "LOT#") AND is_open = true` |
| Discover strategies with closed lots | Table scan | `begins_with(PK, "LOT#") AND is_open = false` |

### StrategyPerformanceTable (Write Target)

Single-table design with per-strategy partitioning via composite keys (not separate physical tables per strategy).

| Item Type | PK | SK | Purpose |
|-----------|----|----|---------|
| Snapshot | `STRATEGY#{name}` | `SNAPSHOT#{iso_ts}` | Time-series history for charts |
| Latest Pointer | `LATEST` | `STRATEGY#{name}` | Fast current metrics lookup |
| Capital Deployed | `CAPITAL_DEPLOYED` | `SNAPSHOT#{iso_ts}` | Capital deployment history |
| Capital Latest | `LATEST` | `CAPITAL_DEPLOYED` | Current capital deployment |

All items include a 90-day TTL (`ExpiresAt`) for automatic cleanup.

### Snapshot Item Fields

| Field | Type | Description |
|-------|------|-------------|
| `strategy_name` | String | Strategy identifier (DSL filename stem) |
| `snapshot_timestamp` | String (ISO 8601) | When the snapshot was taken |
| `realized_pnl` | String (Decimal) | Sum of realized P&L from all closed trades |
| `current_holdings_value` | String (Decimal) | Cost basis of remaining open positions |
| `current_holdings` | Number | Count of lots with remaining position |
| `completed_trades` | Number | Total closed trades (exit records) |
| `winning_trades` | Number | Trades with positive P&L |
| `losing_trades` | Number | Trades with zero or negative P&L |
| `win_rate` | String (Decimal) | Percentage of winning trades (0-100) |
| `avg_profit_per_trade` | String (Decimal) | Mean realized P&L per closed trade |
| `correlation_id` | String (UUID) | Event tracing ID |
| `ExpiresAt` | Number (Unix epoch) | TTL for DynamoDB auto-deletion |

## Data Flow

### 1. Strategy Discovery (`get_all_strategy_summaries`)

The Lambda discovers strategies from three sources and unions them:

1. **STRATEGY_METADATA** items via `GSI3-StrategyIndex` - the canonical registry
2. **Closed LOT items** via table scan - fallback for strategies missing metadata
3. **Open LOT items** via table scan - ensures active strategies are included

### 2. Per-Strategy Aggregation (`get_strategy_summary`)

For each discovered strategy:

1. Queries `GSI5-StrategyLotsIndex` with `GSI5PK = "STRATEGY_LOTS#{name}"`
2. Iterates all LOT items:
   - Lots with `remaining_qty > 0` count toward current holdings
   - Each `exit_record` on a lot represents a completed trade
   - Sums realized P&L, win/loss counts from exit records
3. Computes derived metrics (win rate, avg profit per trade)

### 3. Snapshot Write (`write_strategy_metrics`)

Uses `batch_writer()` to atomically write two items per strategy:
- **Snapshot item** for time-series history
- **LATEST pointer** (overwrites previous) for fast current lookup

### 4. Capital Deployed (Optional)

If the `TradeExecuted` event contains `metadata.capital_deployed_pct`, writes an additional capital deployment metric item.

## IAM Permissions

```yaml
# Read from TradeLedger
- dynamodb:Query
- dynamodb:GetItem
- dynamodb:Scan
- dynamodb:*/index/*   # GSI access

# Write to StrategyPerformance
- dynamodb:PutItem
- dynamodb:BatchWriteItem
- dynamodb:GetItem
- dynamodb:Query
```

## Environment Variables

| Variable | Source | Description |
|----------|--------|-------------|
| `TRADE_LEDGER__TABLE_NAME` | `!Ref TradeLedgerTable` | Trade ledger table for reading lots/metadata |
| `STRATEGY_PERFORMANCE_TABLE` | `!Ref StrategyPerformanceTable` | Performance table for writing snapshots |
| `STAGE` | `!Ref Stage` | Deployment stage (dev/prod) |

## Lambda Configuration

| Setting | Value |
|---------|-------|
| Runtime | Python 3.12 |
| Memory | 512 MB |
| Timeout | 60 seconds |
| Trigger | EventBridge rule: `alchemiser.execution` / `TradeExecuted` |
| Layers | SharedCodeLayer, NotificationsLayer |

## Known Limitations

1. **Full table scans for strategy discovery**: `get_all_strategy_summaries()` performs two scans on the TradeLedger (open lots and closed lots) with `FilterExpression`. As lot count grows, these become increasingly expensive. The per-strategy GSI5 query itself is efficient.

2. **No pagination on `query_all_lots_by_strategy`**: The GSI5 query does not handle `LastEvaluatedKey`. If a strategy accumulates more than 1 MB of LOT items, results will be silently truncated, leading to incorrect metrics.

3. **Metrics computed on every trade**: Each `TradeExecuted` event triggers a full recomputation across all strategies, not just the strategy that traded. This is simple but redundant at scale.

## Key Files

| Component | Path |
|-----------|------|
| Lambda handler | `functions/strategy_performance/lambda_handler.py` |
| Metrics publisher | `layers/shared/the_alchemiser/shared/metrics/dynamodb_metrics_publisher.py` |
| Trade ledger repository | `layers/shared/the_alchemiser/shared/repositories/dynamodb_trade_ledger_repository.py` |
| Infrastructure | `template.yaml` (StrategyPerformanceTable, StrategyPerformanceFunction) |
| Backfill script | `scripts/backfill_strategy_performance.py` |
| Diagnosis script | `scripts/diagnose_strategy_performance.py` |

## Backfill and Diagnostics

**Backfill** (`scripts/backfill_strategy_performance.py`): Manually triggers `write_strategy_metrics()` to populate the StrategyPerformanceTable from existing TradeLedger data. Useful after initial deployment or migrations.

**Diagnose** (`scripts/diagnose_strategy_performance.py`): Checks LATEST items in StrategyPerformanceTable, validates strategy metadata and lots in TradeLedger, verifies Lambda deployment and env vars, and inspects CloudWatch logs for recent invocations.

## Module Boundaries

- **Imports from**: `shared/` only (events, logging, metrics, repositories)
- **No imports from**: `execution_v2/`, `strategy_v2/`, `portfolio_v2/`
- **Communication**: Event-driven only (EventBridge input, DynamoDB output)
