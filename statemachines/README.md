# Step Functions State Machines

This directory contains AWS Step Functions state machine definitions for the Alchemiser trading system.

## Execution Workflow

**File**: `execution_workflow.asl.json`

**Purpose**: Orchestrates two-phase trade execution (SELL → BUY) with circuit breakers and automatic error handling.

### Workflow Overview

```
┌─────────────────────┐
│  PrepareTrades      │  ← Entry point from Portfolio Lambda
│  (Split SELL/BUY)   │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  ExecuteSellPhase   │  ← Map state (max 10 concurrent)
│  (Parallel)         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ EvaluateSellGuard   │  ← Check SELL failure threshold
│ (Threshold: $500)   │
└──────────┬──────────┘
           │
    ┌──────┴──────┐
    │ BUY Phase   │
    │ Allowed?    │
    └──┬───────┬──┘
       │       │
    Yes│       │No
       │       │
       ▼       ▼
┌─────────┐ ┌──────────────┐
│ExecuteBuy│ │BuyPhaseBlocked│
│Phase    │ │(Notify)       │
│(Parallel)│ └──────────────┘
└─────┬───┘
      │
      ▼
┌─────────────────────┐
│ AggregateResults    │  ← Collect all trade results
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│ SendNotification    │  ← Email via SNS
└─────────────────────┘
```

### Key Features

1. **Two-Phase Execution**: SELLs complete before BUYs to ensure cash availability
2. **Guard Condition**: BUY phase blocked if SELL failures exceed $500
3. **Parallel Execution**: Up to 10 concurrent trades per phase
4. **Circuit Breaker**: Equity deployment limit for BUY trades
5. **Automatic Retries**: 3 retries with exponential backoff (2x multiplier)
6. **Error Handling**: Catch blocks route failures to notification Lambda

### Lambda Functions

| Function | Purpose |
|----------|---------|
| `prepare-trades` | Splits rebalance plan into SELL/BUY arrays |
| `evaluate-sell-guard` | Checks SELL failure threshold ($500) |
| `check-equity-limit` | Circuit breaker for BUY phase (equity limit) |
| `execute-trade-sfn` | Executes single trade via Alpaca API |
| `aggregate-results` | Collects and summarizes trade results |
| `notify-completion` | Sends success notification via SNS |
| `notify-failure` | Sends failure notification via SNS |

### Input Schema

State machine expects this input from Portfolio Lambda:

```json
{
  "rebalancePlan": {
    "tradeMessages": [
      {
        "tradeId": "trade-123",
        "symbol": "TQQQ",
        "action": "SELL",
        "quantity": 10,
        "targetValue": "1000.00"
      }
    ]
  },
  "correlationId": "workflow-abc123",
  "runId": "run-xyz789",
  "planId": "plan-456",
  "prepareTradesFunctionName": "alchemiser-dev-prepare-trades",
  "evaluateSellGuardFunctionName": "alchemiser-dev-evaluate-sell-guard",
  "checkEquityLimitFunctionName": "alchemiser-dev-check-equity-limit",
  "executeTradeFunctionName": "alchemiser-dev-execute-trade-sfn",
  "aggregateResultsFunctionName": "alchemiser-dev-aggregate-results",
  "notifyCompletionFunctionName": "alchemiser-dev-notify-completion",
  "notifyFailureFunctionName": "alchemiser-dev-notify-failure"
}
```

### Output Schema

State machine produces this output:

```json
{
  "aggregation": {
    "totalTrades": 15,
    "succeededTrades": 14,
    "failedTrades": 1,
    "skippedTrades": 0,
    "sellCount": 7,
    "buyCount": 8,
    "totalValue": "15000.00",
    "summary": "Execution completed: 14/15 trades succeeded. SELLs: 7, BUYs: 8. Total value: $15000.00",
    "correlationId": "workflow-abc123",
    "runId": "run-xyz789",
    "planId": "plan-456"
  }
}
```

### Testing

To test the state machine locally:

```bash
# Install SAM CLI
pip install aws-sam-cli

# Validate state machine definition
sam validate --lint

# Test with sample payload (requires AWS credentials)
sam local start-api

# Or test via AWS Console:
# 1. Go to Step Functions console
# 2. Select "alchemiser-dev-execution-workflow"
# 3. Click "Start execution"
# 4. Paste sample input JSON
```

### Monitoring

State machine execution logs are sent to CloudWatch:

- Log Group: `/aws/states/alchemiser-{stage}-execution-workflow`
- Retention: 30 days
- Log Level: ALL (includes execution data)

To query execution history:

```bash
# List recent executions
aws stepfunctions list-executions \
  --state-machine-arn arn:aws:states:REGION:ACCOUNT:stateMachine:alchemiser-dev-execution-workflow

# Get execution details
aws stepfunctions describe-execution \
  --execution-arn arn:aws:states:REGION:ACCOUNT:execution:alchemiser-dev-execution-workflow:execution-name
```

### Migration Status

**Phase 1** (Current): Infrastructure created, runs in parallel with existing SQS-based execution
**Phase 2** (Next): Portfolio Lambda dual-publishes to both old and new paths for validation
**Phase 3** (Future): Cutover to Step Functions exclusively, remove SQS infrastructure

### References

- [AWS Step Functions Developer Guide](https://docs.aws.amazon.com/step-functions/latest/dg/welcome.html)
- [Amazon States Language](https://states-language.net/spec.html)
- [Map State Documentation](https://docs.aws.amazon.com/step-functions/latest/dg/amazon-states-language-map-state.html)
- [Error Handling](https://docs.aws.amazon.com/step-functions/latest/dg/concepts-error-handling.html)
