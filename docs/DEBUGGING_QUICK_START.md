# Debugging Stack - Quick Start

This debugging stack helps track how strategy signals change throughout the trading day when using live/partial bars. It runs every 5 minutes from 3:00-3:55 PM ET and records signal changes.

## Quick Start

### Deploy

```bash
make deploy-debug
```

### View Results

After the stack runs during market hours:

```bash
# Today's signal changes
make debug-report

# Specific date
make debug-report date=2026-01-18
```

### Clean Up

```bash
make destroy-debug
```

## What It Does

✅ Runs signal generation **every 5 minutes** from 3:00-3:55 PM ET
✅ Enables **live bars** for all indicators (RSI, EMA, stdev, etc.)
✅ Tracks **ticker changes** (added/removed positions)
✅ Tracks **weight changes** (rebalancing within existing positions)
✅ **No trading** - signal generation only (safe for debugging)

## Example Output

```
================================================================================
Signal Change Report for 2026-01-18
================================================================================

📊 Found 12 signal snapshots

┌─ Snapshot 1: 03:00:00 PM ET
│  Signals: 8 tickers
│  Top positions: TQQQ (45%), SOXL (25%), TECL (15%)
│  ✨ First snapshot of the day
└──────────────────────────────────────────────────────────────────────────────

┌─ Snapshot 2: 03:05:00 PM ET
│  Signals: 8 tickers
│  ⚖️  Weight changes:
│      TQQQ: 0.4500 → 0.4620 (+0.0120)
│      SOXL: 0.2500 → 0.2450 (-0.0050)
└──────────────────────────────────────────────────────────────────────────────

...

Summary:
  Total snapshots: 12
  Snapshots with changes: 8
  Total changes detected: 24
```

## Cost

**< $5 per month** when running for 20 trading days
- ~1,440 Lambda invocations
- ~240 DynamoDB writes
- 90-day automatic expiration (TTL)

## Documentation

📖 **Full Documentation:** [docs/DEBUGGING_STACK.md](./DEBUGGING_STACK.md)
📋 **Implementation Details:** [docs/IMPLEMENTATION_SUMMARY.md](./IMPLEMENTATION_SUMMARY.md)

## Architecture

```
EventBridge Schedule → Orchestrator → Workers (parallel) → Aggregator → Debugger → DynamoDB
```

**Stack components:**
- Strategy Orchestrator (fan-out)
- Strategy Workers (DSL execution with live bars)
- Signal Aggregator (merge signals)
- Signal Debugger (track changes)
- DynamoDB tables (sessions + history)
- 12 EventBridge schedules

## Troubleshooting

**No signals?**
- Check if market is open (Mon-Fri, 3:00-3:55 PM ET)
- View logs: `aws logs tail /aws/lambda/alchemiser-debug-strategy-orchestrator --follow`

**Debugger not storing data?**
- Check EventBridge routing
- View logs: `aws logs tail /aws/lambda/alchemiser-debug-signal-debugger --follow`

See [docs/DEBUGGING_STACK.md](./DEBUGGING_STACK.md) for detailed troubleshooting.

## Development

The stack reuses production Lambda code (orchestrator, workers, aggregator) but with:
- ✅ Live bars enabled for all indicators
- ✅ Separate EventBridge bus
- ✅ Dedicated DynamoDB tables
- ✅ Dev market data bucket (no production impact)
- ✅ Paper trading mode (no live orders)

## Next Steps

1. Deploy: `make deploy-debug`
2. Wait for market hours
3. View report: `make debug-report`
4. Analyze signal behavior
5. Update production config based on findings
6. Clean up: `make destroy-debug`
