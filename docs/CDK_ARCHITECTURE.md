# CDK Infrastructure Architecture

**Status:** Current (replaces `template.yaml` SAM template)
**IaC Framework:** AWS CDK v2 (Python)
**Resource prefix:** `alch-{stage}` (e.g. `alch-dev`, `alch-prod`)

---

## Stack Dependency Graph

```
                   Foundation
                  /    |    \     \
                 /     |     \     \
                v      v      v     v
             Data   Dashboard  Execution
              |        |       /     |
              |        |      /      |
              v        v     v       v
                  Strategy       Hedging
                      |
                      v
                 Notifications
```

All cross-stack wiring is via Python constructor params (no CloudFormation exports/imports).
Stacks are deployed in dependency order with `--concurrency 3`.

---

## Stacks Overview

### 1. Foundation (`alch-{stage}-foundation`)

Shared resources consumed by every other stack.

| Resource | Type | Details |
|----------|------|---------|
| AlchemiserEventBus | EventBridge Bus | Custom event bus for all domain events |
| SharedCodeLayer | Lambda Layer | `layers/shared/` -- `the_alchemiser.shared` module |
| NotificationsLayer | Lambda Layer | `layers/notifications/` -- pydantic, structlog, alpaca-py |
| PortfolioLayer | Lambda Layer | `layers/portfolio/` -- alpaca-py, pydantic |
| TradeLedgerTable | DynamoDB | PK/SK, 5 GSIs (Correlation, Symbol, Strategy, CorrelationSnapshot, StrategyLots), PITR enabled |
| DLQAlertTopic | SNS Topic | Email subscription for DLQ alerts |

### 2. Data (`alch-{stage}-data`)

Market data ingestion and caching.

| Resource | Type | Details |
|----------|------|---------|
| DataFunction | Lambda | `functions/data/`, 900s timeout, 1024 MB |
| DataLayer | Lambda Layer | awswrangler 3.10.0 + alpaca-py (built locally via `LocalShellBundling`) |
| MarketDataBucket | S3 | Versioned, 30-day noncurrent expiry, RETAIN |
| MarketDataFetchRequestsTable | DynamoDB | PK, TTL |
| BadDataMarkersTable | DynamoDB | PK/SK, TTL |
| DataRefreshSchedule | EventBridge Scheduler | `cron(0 0,12 ? * TUE-SAT *)` ET |
| MarketDataFetchRequestedRule | EventBridge Rule | `alchemiser.strategy` / `MarketDataFetchRequested` -> DataFunction |

### 3. Dashboard (`alch-{stage}-dashboard`)

Account data snapshots for the Streamlit dashboard.

| Resource | Type | Details |
|----------|------|---------|
| AccountDataFunction | Lambda | `functions/account_data/`, 300s timeout, 256 MB |
| AccountDataTable | DynamoDB | PK/SK, TTL (`ExpiresAt`), PITR enabled |
| AccountDataSchedule | EventBridge Scheduler | Every 6 hours (4 AM, 10 AM, 4 PM, 10 PM ET) |

### 4. Execution (`alch-{stage}-execution`)

Trade execution and aggregation.

| Resource | Type | Details |
|----------|------|---------|
| ExecutionFunction | Lambda | `functions/execution/`, 600s timeout, 1024 MB, **reserved concurrency=10** |
| TradeAggregatorFunction | Lambda | `functions/trade_aggregator/`, 60s timeout, 512 MB |
| ExecutionLayer | Lambda Layer | `layers/execution/` -- alpaca-py, pydantic |
| ExecutionQueue | SQS Standard | 900s visibility, 4-day retention, DLQ after 3 failures |
| ExecutionDLQ | SQS Standard | 14-day retention |
| ExecutionFifoQueue | SQS FIFO | Per-message-group dedup, 900s visibility, DLQ after 3 failures |
| ExecutionFifoDLQ | SQS FIFO | 14-day retention |
| ExecutionRunsTable | DynamoDB | PK/SK, TTL |
| RebalancePlanTable | DynamoDB | PK/SK, TTL, 1 GSI (CorrelationIndex), PITR enabled |
| DLQMessageAlarm | CloudWatch Alarm | Standard DLQ messages >= 1 |
| FifoDLQMessageAlarm | CloudWatch Alarm | FIFO DLQ messages >= 1 |
| StuckRunsAlarm | CloudWatch Alarm | Custom metric `Alchemiser/Execution:StuckRuns` >= 1 |
| TradeExecutedRule | EventBridge Rule | `alchemiser.execution` / `TradeExecuted` -> TradeAggregator |

### 5. Strategy (`alch-{stage}-strategy`)

Strategy orchestration, workers, scheduling, analytics, and reports.

| Resource | Type | Details |
|----------|------|---------|
| StrategyOrchestratorFunction | Lambda | `functions/strategy_orchestrator/`, 60s, 512 MB |
| StrategyFunction (Worker) | Lambda | `functions/strategy_worker/`, 900s, 1024 MB (async failure -> EventBridge) |
| ScheduleManagerFunction | Lambda | `functions/schedule_manager/`, 60s, 256 MB |
| StrategyAnalyticsFunction | Lambda | `functions/strategy_analytics/`, 120s, 1024 MB |
| StrategyReportsFunction | Lambda | `functions/strategy_reports/`, 300s, 2048 MB |
| StrategyLayer | Lambda Layer | awswrangler 3.10.0 + alpaca-py + dependency-injector + cachetools (built locally) |
| GroupHistoricalSelectionsTable | DynamoDB | PK (`group_id`) / SK (`record_date`), TTL |
| PerformanceReportsBucket | S3 | 30-day lifecycle, `alch-{stage}-reports` |
| ScheduleManagerSchedule | EventBridge Scheduler | 9:00 AM ET MON-FRI |
| StrategyAnalyticsSchedule | EventBridge Scheduler | 9:00 PM ET MON-FRI |
| StrategyReportsSchedule | EventBridge Scheduler | 9:15 PM ET MON-FRI |
| OrchestratorErrorsAlarm | CloudWatch Alarm | Orchestrator errors >= 1 |
| StrategyWorkerErrorsAlarm | CloudWatch Alarm | Worker errors >= 1 |

### 6. Hedging (`alch-{stage}-hedging`)

Options hedging: evaluation, execution, and roll management.

| Resource | Type | Details |
|----------|------|---------|
| HedgeEvaluatorFunction | Lambda | `functions/hedge_evaluator/`, 300s, 512 MB |
| HedgeExecutorFunction | Lambda | `functions/hedge_executor/`, 600s, 1024 MB, **reserved concurrency=3** |
| HedgeRollManagerFunction | Lambda | `functions/hedge_roll_manager/`, 300s, 512 MB |
| HedgePositionsTable | DynamoDB | PK/SK, TTL, 1 GSI (UnderlyingExpirationIndex) |
| HedgeHistoryTable | DynamoDB | PK (`account_id`) / SK (`timestamp_action`), TTL |
| HedgeKillSwitchTable | DynamoDB | PK (`switch_id`) |
| IVHistoryTable | DynamoDB | PK (`underlying_symbol`) / SK (`record_date`), TTL |
| HedgeExecutionQueue | SQS Standard | 900s visibility, DLQ after 3 failures |
| HedgeExecutionDLQ | SQS Standard | 14-day retention |
| AllTradesCompletedToHedgeRule | EventBridge Rule | `alchemiser.trade_aggregator` / `AllTradesCompleted` -> HedgeEvaluator |
| HedgeRollManagerDailyCheck | EventBridge Rule | Cron 7:45 PM UTC MON-FRI (~3:45 PM ET) |

### 7. Notifications (`alch-{stage}-notifications`)

Email notifications via SES triggered by domain events.

| Resource | Type | Details |
|----------|------|---------|
| NotificationsFunction | Lambda | `functions/notifications/`, 60s, 512 MB, SES email |
| NotificationsErrorsAlarm | CloudWatch Alarm | CRITICAL: notification failures >= 1 |

**EventBridge Rules (8 total):**

| Rule | Source | Detail Type |
|------|--------|-------------|
| AllStrategiesCompleted | `alchemiser.coordinator` | `AllStrategiesCompleted` |
| AllTradesCompleted | `alchemiser.trade_aggregator` | `AllTradesCompleted` |
| WorkflowFailed | `alchemiser.*` (prefix) | `WorkflowFailed` |
| HedgeEvaluationCompleted | `alchemiser.hedge` | `HedgeEvaluationCompleted` |
| DataLakeUpdateCompleted | `alchemiser.data` | `DataLakeUpdateCompleted` |
| ScheduleCreated | `alchemiser.coordinator` | `ScheduleCreated` |
| LambdaAsyncFailure | `lambda` | `Lambda Function Invocation Result - Failure` |
| CloudWatchAlarm | `aws.cloudwatch` (default bus) | `CloudWatch Alarm State Change` (prefix `alch-`) |

---

## Resource Totals

| Category | Count |
|----------|-------|
| Lambda Functions | 13 |
| Lambda Layers | 6 (SharedCode, Notifications, Portfolio, Data, Strategy, Execution) |
| DynamoDB Tables | 11 |
| SQS Queues | 6 (2 Standard + DLQ for execution, 1 FIFO + DLQ, 1 Standard + DLQ for hedging) |
| S3 Buckets | 2 (MarketData, PerformanceReports) |
| EventBridge Bus | 1 (custom) |
| EventBridge Rules | 11 |
| EventBridge Schedules | 6 |
| CloudWatch Alarms | 7 |
| SNS Topics | 1 (DLQ alerts) |

---

## Event-Driven Workflow

### Daily Trading Flow

```
9:00 AM ET
    |
    v
ScheduleManager ------> Creates dynamic EventBridge schedule
                         for ~15 min before market close
    |
    v (at scheduled time, e.g. 3:45 PM ET)
StrategyOrchestrator
    |
    |---> StrategyWorker 1 (async Lambda invoke)
    |---> StrategyWorker 2
    |---> StrategyWorker N
    |
    v (each worker emits trades to FIFO SQS)
ExecutionFunction (up to 10 concurrent)
    |
    v (TradeExecuted events)
TradeAggregator
    |
    |---> AllTradesCompleted
    |         |
    |         v
    |     HedgeEvaluator
    |         |
    |         v (hedge orders to SQS)
    |     HedgeExecutor (up to 3 concurrent)
    |
    v
NotificationsFunction ---> SES email
```

### Data Refresh Flow

```
Midnight & Noon ET (Tue-Sat)
    |
    v
DataFunction ---> Fetches from Alpaca API
    |              Stores in MarketDataBucket (S3)
    |
    v (on-demand)
StrategyWorker ---> MarketDataFetchRequested event
    |
    v
DataFunction (triggered by EventBridge rule)
```

### Analytics Flow (Post-Market)

```
9:00 PM ET (Mon-Fri)
    |
    v
StrategyAnalyticsFunction ---> Reads TradeLedger
    |                           Writes Parquet to S3
    v
9:15 PM ET
    |
    v
StrategyReportsFunction ---> Reads analytics from S3
                              Generates HTML tearsheets
```

---

## Lambda Layers Architecture

```
                      SharedCodeLayer
                     (the_alchemiser.shared)
                    /    |    |    |    |    \
                   v     v    v    v    v     v
              All 13 Lambda functions get this layer

   NotificationsLayer          PortfolioLayer           DataLayer              StrategyLayer         ExecutionLayer
   (pydantic, structlog,      (alpaca-py, pydantic)    (awswrangler,          (awswrangler,         (alpaca-py,
    alpaca-py)                                          alpaca-py,              alpaca-py,            pydantic)
   |                          |                         pydantic, structlog)    dependency-injector,
   |                          |                        |                        cachetools)
   v                          v                        v                       |
   Orchestrator               HedgeEvaluator           DataFunction            v
   ScheduleManager            HedgeRollManager                                StrategyWorker
   TradeAggregator            AccountData                                     StrategyAnalytics
   Notifications                                                              StrategyReports
```

---

## Configuration (`infra/config.py`)

All environment-specific configuration is centralised in `StageConfig`:

```python
StageConfig(
    stage="dev",                  # dev | staging | prod | ephemeral
    alpaca=AlpacaConfig(...),     # API credentials from environment
    log_level="DEBUG",            # ALCHEMISER_LOG_LEVEL
    notification_email="...",     # SES recipient
)
```

**Global Lambda env vars** (applied to all 13 functions):
- `APP__STAGE` -- `dev`, `staging`, or `prod`
- `ALCHEMISER_LOG_LEVEL` -- `DEBUG` or `INFO`
- `ALPACA__KEY`, `ALPACA__SECRET`, `ALPACA__ENDPOINT`
- `ALPACA__EQUITY_DEPLOYMENT_PCT`

**Resource naming:** `config.resource_name("suffix")` -> `alch-{stage}-suffix`

---

## Reusable Constructs (`infra/constructs.py`)

| Construct | Purpose |
|-----------|---------|
| `AlchemiserFunction` | Lambda with standard defaults (Python 3.12, x86_64, global env vars, tags) |
| `alchemiser_table` | DynamoDB table factory (PAY_PER_REQUEST, SSE, tags, optional GSIs) |
| `lambda_execution_role` | IAM role with `AWSLambdaBasicExecutionRole` + inline policy |
| `scheduler_role` | IAM role for EventBridge Scheduler -> Lambda invocation |
| `LocalShellBundling` | Docker-free local layer builds (resolves `pip` from venv) |

---

## Deployment

### Prerequisites

1. CDK bootstrapped: `npx cdk bootstrap aws://{account}/{region}`
2. Poetry dependencies installed: `poetry install --with dev`
3. `.env` with `ALPACA__KEY` and `ALPACA__SECRET`

### Commands

```bash
make cdk-synth              # Validate all stacks compile
make cdk-diff               # Preview changes vs deployed
make cdk-deploy-dev         # Deploy all stacks to dev

# Override stage:
make cdk-synth stage=prod
make cdk-diff stage=prod
```

### CI/CD

- **CI** (`ci.yml`): Runs `cdk synth -c stage=dev --quiet` to validate templates
- **CD** (`cd.yml`): Runs `scripts/cdk_deploy.sh {env}` on tag push

### Ephemeral Stacks

```bash
cdk synth -c stage=ephemeral -c stack_name=alch-ephem-feature123
```

---

## File Layout

```
infra/
  __init__.py
  app.py              # CDK app entry point, wires all stacks
  config.py           # StageConfig + AlpacaConfig (frozen dataclasses)
  constructs.py       # Reusable CDK constructs
  stacks/
    foundation.py     # EventBridge, layers, TradeLedger, SNS
    data.py           # Market data Lambda + S3 + DynamoDB
    dashboard.py      # Account data Lambda + DynamoDB
    execution.py      # Trade execution Lambdas + SQS + DynamoDB
    strategy.py       # Strategy Lambdas + S3 + DynamoDB + schedules
    hedging.py        # Hedge Lambdas + SQS + DynamoDB
    notifications.py  # Notifications Lambda + EventBridge rules
```
