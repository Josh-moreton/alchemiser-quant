# Debugging Stack

## Overview

The debugging stack is a lightweight CloudFormation deployment designed to track how strategy signals change throughout the trading day when using live bars (`use_live_bars=true`). This helps debug partial bar behavior and understand when and why signal outputs (tickers and weights) change during market hours.

## What It Does

The debugging stack:

1. **Runs signal generation every 5 minutes** from 3:00 PM to 3:55 PM ET (12 executions per day)
2. **Enables live bars** for all indicators (by modifying `partial_bar_config.py`)
3. **Tracks signal changes** by comparing each snapshot to the previous one
4. **Stores change history** in DynamoDB for later analysis
5. **Generates reports** showing when tickers were added/removed and when weights changed

## What It Does NOT Do

The debugging stack intentionally excludes:

- ❌ Portfolio management (no position tracking)
- ❌ Trade execution (no orders placed)
- ❌ Account integration (read-only market data access)
- ❌ Notifications (no email alerts)

This is purely for **signal debugging** with no trading capability.

## Architecture

```
EventBridge Schedule (every 5 min, 3:00-3:55 PM ET)
    ↓
Strategy Orchestrator Lambda
    ↓ (parallel async invocations)
Strategy Workers (1 per DSL file)
    ↓ (PartialSignalGenerated events)
Signal Aggregator Lambda
    ↓ (SignalGenerated event)
Signal Debugger Lambda
    ↓
DynamoDB (SignalHistoryTable)
```

### Resources Created

| Resource | Purpose |
|----------|---------|
| `alchemiser-debug-strategy-orchestrator` | Dispatches parallel strategy execution |
| `alchemiser-debug-strategy-worker` | Executes single DSL file with live bars |
| `alchemiser-debug-signal-aggregator` | Merges partial signals |
| `alchemiser-debug-signal-debugger` | Tracks signal changes over time |
| `alchemiser-debug-aggregation-sessions` | DynamoDB table for session tracking |
| `alchemiser-debug-signal-history` | DynamoDB table for signal snapshots |
| `alchemiser-debug-events` | EventBridge bus for event routing |
| 12 EventBridge Schedules | One for each 5-minute interval |

### Schedule Details

The stack creates 12 separate EventBridge schedules:

- 3:00 PM ET
- 3:05 PM ET
- 3:10 PM ET
- ...
- 3:55 PM ET

All schedules are timezone-aware (`America/New_York`) and only run Monday-Friday.

## Usage

### Deploy the Stack

```bash
make deploy-debug
```

This will:
1. Build the Lambda functions
2. Load Alpaca credentials from AWS SSM (dev environment)
3. Deploy the stack to AWS

### View Signal Changes

After the stack has run for a day, view the signal change report:

```bash
# View today's report
make debug-report

# View a specific date
make debug-report date=2026-01-18
```

Example output:

```
================================================================================
Signal Change Report for 2026-01-18
================================================================================

📊 Found 12 signal snapshots

┌─ Snapshot 1: 03:00:00 PM ET
│  Correlation ID: workflow-abc123
│  Signals: 8 tickers
│  Top positions:
│    TQQQ: 45.00%
│    SOXL: 25.00%
│    TECL: 15.00%
│  ✨ First snapshot of the day
└──────────────────────────────────────────────────────────────────────────────

┌─ Snapshot 2: 03:05:00 PM ET
│  Correlation ID: workflow-def456
│  Signals: 8 tickers
│  Top positions:
│    TQQQ: 46.20%
│    SOXL: 24.50%
│    TECL: 14.30%
│  ⚖️  Weight changes:
│      TQQQ: 0.4500 → 0.4620 (+0.0120)
│      SOXL: 0.2500 → 0.2450 (-0.0050)
│      TECL: 0.1500 → 0.1430 (-0.0070)
└──────────────────────────────────────────────────────────────────────────────

...

================================================================================
Summary
================================================================================
Total snapshots: 12
Snapshots with changes: 8
Total changes detected: 24
Average changes per snapshot: 3.0
```

### Monitor Logs

View Lambda logs in CloudWatch:

```bash
# View orchestrator logs
aws logs tail /aws/lambda/alchemiser-debug-strategy-orchestrator --follow --no-cli-pager

# View worker logs
aws logs tail /aws/lambda/alchemiser-debug-strategy-worker --follow --no-cli-pager

# View debugger logs
aws logs tail /aws/lambda/alchemiser-debug-signal-debugger --follow --no-cli-pager
```

### Destroy the Stack

When done debugging:

```bash
make destroy-debug
```

This will delete all resources (Lambdas, DynamoDB tables, EventBridge rules).

## Configuration

### Live Bars

The stack uses `use_live_bars=true` for all indicators. This is configured in:

```python
# layers/shared/the_alchemiser/shared/indicators/partial_bar_config.py
_INDICATOR_CONFIGS = {
    "rsi": PartialBarIndicatorConfig(..., use_live_bar=True),
    "moving_average": PartialBarIndicatorConfig(..., use_live_bar=True),
    # ... all indicators set to True for debugging
}
```

### Market Data

The debugging stack uses the **dev environment's market data bucket** (`alchemiser-dev-market-data`). This ensures:

1. No impact on production data
2. Access to the same historical data used for backtesting
3. Consistent baseline for comparison

### Credentials

Alpaca API credentials are loaded from **GitHub environment secrets** (dev environment) via CI/CD:

- `ALPACA_KEY` - Alpaca API key
- `ALPACA_SECRET` - Alpaca API secret

The deployment is triggered by `make deploy-debug`, which creates a git tag and triggers the GitHub Actions workflow. Credentials never leave GitHub - they are injected at deploy time.

The stack uses **paper trading** mode (`https://paper-api.alpaca.markets/v2`) to avoid any accidental live trading.

## Data Storage

### Signal History Table

Schema:

```
PK: "DATE#{YYYY-MM-DD}"
SK: "SNAPSHOT#{ISO8601_timestamp}"
Attributes:
  - correlation_id: Workflow correlation ID
  - timestamp: ISO8601 timestamp
  - signals_data: Dict of {ticker: weight}
  - signal_hash: Deterministic hash for change detection
  - changes_detected: Dict with change details
  - stage: "debug"
  - ttl: Expiration timestamp (90 days)
```

### Querying Manually

```python
import boto3
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('alchemiser-debug-signal-history')

# Get all snapshots for 2026-01-18
response = table.query(
    KeyConditionExpression=Key('PK').eq('DATE#2026-01-18')
)

for item in response['Items']:
    print(f"{item['timestamp']}: {len(item['signals_data'])} signals")
```

## Cost Estimation

Running the debugging stack for one month (20 trading days × 12 executions):

- **Lambda invocations**: 240 orchestrator + 720 workers + 240 aggregator + 240 debugger = ~1,440 invocations
- **DynamoDB writes**: ~240 per month (minimal)
- **EventBridge rules**: 12 schedules (negligible cost)

**Estimated monthly cost**: < $5 USD

The stack uses PAY_PER_REQUEST billing for DynamoDB and only runs during market hours, keeping costs minimal.

## Troubleshooting

### No Signals Generated

Check:
1. Market is open (not a holiday or weekend)
2. Strategy workers are executing successfully
3. DSL files are configured correctly

View logs:
```bash
aws logs tail /aws/lambda/alchemiser-debug-strategy-worker --since 1h --no-cli-pager
```

### Signal Debugger Not Storing Data

Check:
1. `SignalGenerated` events are being published (check EventBridge)
2. Lambda has permissions to write to DynamoDB
3. Table name environment variable is set correctly

View logs:
```bash
aws logs tail /aws/lambda/alchemiser-debug-signal-debugger --since 1h --no-cli-pager
```

### Schedule Not Triggering

Check:
1. EventBridge Scheduler rules are enabled
2. IAM role has permission to invoke Lambda
3. Current time is within 3:00-3:55 PM ET window

List schedules:
```bash
aws scheduler list-schedules --group-name default --query 'Schedules[?contains(Name, `alchemiser-debug`)]' --no-cli-pager
```

## Development

### Testing Locally

You can test the signal debugger logic locally:

```python
from functions.signal_debugger.lambda_handler import lambda_handler

event = {
    "detail": {
        "correlation_id": "test-123",
        "timestamp": "2026-01-18T20:00:00Z",
        "signals_data": {
            "TQQQ": 0.45,
            "SOXL": 0.25,
            "TECL": 0.15,
        }
    }
}

result = lambda_handler(event, None)
print(result)
```

### Modifying Indicator Settings

To change which indicators use live bars, edit:

```
layers/shared/the_alchemiser/shared/indicators/partial_bar_config.py
```

Then redeploy:

```bash
make deploy-debug
```

## See Also

- [Partial Bar Configuration](../layers/shared/the_alchemiser/shared/indicators/partial_bar_config.py)
- [Strategy Orchestrator](../functions/strategy_orchestrator/)
- [Signal Debugger](../functions/signal_debugger/)
- [Main Template](../template.yaml) (production stack)
