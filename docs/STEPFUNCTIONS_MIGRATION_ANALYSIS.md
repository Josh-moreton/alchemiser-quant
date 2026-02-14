# Step Functions Migration Analysis

## Executive Summary

After thorough analysis of the Alchemiser quantitative trading system, **I recommend against a wholesale migration to Step Functions**. The current event-driven architecture is well-designed for this use case, with sophisticated DynamoDB-based coordination patterns that would be partially redundant with Step Functions. However, **targeted hybrid adoption** for specific workflows would provide significant observability and debugging benefits.

**Final Recommendation: Hybrid approach - migrate Strategy Orchestration workflow only.**

---

## A) Workflow Inventory Table

| Workflow Name | Current Arch | Recommendation | Rationale | Risk | Effort | Key Changes |
|--------------|--------------|----------------|-----------|------|--------|-------------|
| **Strategy Orchestration** | Lambda async invoke + DynamoDB (AggregationSessionsTable) + EventBridge | **Step Functions (Standard)** | Classic fan-out/fan-in pattern; Map state ideal; 4 strategies ~10min runtime; execution-level debugging valuable | Low | Medium | Replace Orchestrator/Aggregator with SF; keep Strategy Worker as Lambda task |
| **Trade Execution (Two-Phase)** | SQS Standard + DynamoDB (ExecutionRunsTable) + EventBridge | **Keep Current** | Two-phase SELL→BUY ordering via enqueue timing works well; 10-concurrent execution cap matches Alpaca rate limits; SQS DLQ provides retry isolation | Medium | High | DynamoDB state machine more flexible than SF for circuit breakers |
| **Trade Aggregation** | EventBridge + DynamoDB atomic locking | **Keep Current** | Single-event emission (AllTradesCompleted) needs atomic lock pattern; SF doesn't help here | Low | Low | None - pattern is sound |
| **Signal→Portfolio Flow** | EventBridge (SignalGenerated→Portfolio) | **Keep Current** | Simple single-step event routing; SF overhead unjustified | Low | Low | None |
| **Portfolio→Execution Flow** | Direct SQS enqueue from Portfolio Lambda | **Keep Current** | Trade decomposition into TradeMessages is Lambda-native; batched SQS send is efficient | Low | Low | None |
| **Notifications** | EventBridge (AllTradesCompleted/WorkflowFailed→Notifications) | **Keep Current** | Simple event sink; no orchestration needed | Low | Low | None |
| **Data Refresh (Scheduled)** | EventBridge Schedule + Lambda | **Keep Current** | Single Lambda invocation; no workflow | Low | Low | None |
| **On-Demand Data Fetch** | EventBridge (MarketDataFetchRequested) + DynamoDB dedup | **Keep Current** | Deduplication table pattern works well; no multi-step orchestration | Low | Low | None |
| **Schedule Manager** | EventBridge Scheduler → Lambda | **Keep Current** | One-time schedule creation; no orchestration | Low | Low | None |

---

## B) Detailed State Machine Designs for Top Migration Candidates

### B.1) Strategy Orchestration Workflow (RECOMMENDED FOR MIGRATION)

#### Current Architecture

```
┌─────────────────────────┐
│  EventBridge Schedule   │  (9 AM ET via Schedule Manager)
│  or Direct Invoke       │
└───────────┬─────────────┘
            ▼
┌─────────────────────────┐
│  Strategy Orchestrator  │  Lambda (60s timeout)
│  - Creates session      │  - Reads DSL configs
│  - Async invokes N      │  - DynamoDB: create_session()
│    Strategy Workers     │  - Lambda: invoke_async() x N
└───────────┬─────────────┘
            │ async invoke (fire-and-forget)
            ▼
┌─────────────────────────┐
│  Strategy Worker (x N)  │  Lambda (900s timeout) - PARALLEL
│  - Fetches market data  │
│  - Runs DSL strategy    │
│  - Publishes event      │  → EventBridge: PartialSignalGenerated
└───────────┬─────────────┘
            │ EventBridge event
            ▼
┌─────────────────────────┐
│  Signal Aggregator      │  Lambda (60s timeout) - triggered N times
│  - Stores partial       │  - DynamoDB: store_partial_signal()
│  - Increments counter   │  - Atomic ADD completed_strategies
│  - When complete:       │
│    aggregate & emit     │  → EventBridge: SignalGenerated
└─────────────────────────┘
```

**Problems with current approach:**
1. No visual execution history - debugging requires CloudWatch Logs Insights across 3 Lambda functions
2. Timeout handling is implicit (TTL-based cleanup, no explicit alerts)
3. Error correlation requires manual log queries with correlation_id
4. Aggregator invoked N times, only last invocation does useful work

#### Proposed Step Functions State Machine (Standard)

```json
{
  "Comment": "Strategy Orchestration - Multi-Node Scaling",
  "StartAt": "ValidateConfiguration",
  "States": {
    "ValidateConfiguration": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:REGION:ACCOUNT:function:alchemiser-STAGE-config-validator",
      "Parameters": {
        "correlation_id.$": "$.correlation_id"
      },
      "ResultPath": "$.config",
      "Next": "ExecuteStrategiesInParallel",
      "Catch": [{
        "ErrorEquals": ["ConfigurationError"],
        "Next": "PublishWorkflowFailed"
      }]
    },

    "ExecuteStrategiesInParallel": {
      "Type": "Map",
      "ItemsPath": "$.config.strategy_configs",
      "MaxConcurrency": 4,
      "ItemProcessor": {
        "ProcessorConfig": {
          "Mode": "INLINE"
        },
        "StartAt": "ExecuteSingleStrategy",
        "States": {
          "ExecuteSingleStrategy": {
            "Type": "Task",
            "Resource": "arn:aws:lambda:REGION:ACCOUNT:function:alchemiser-STAGE-strategy-worker",
            "Parameters": {
              "dsl_file.$": "$.dsl_file",
              "allocation.$": "$.allocation",
              "correlation_id.$": "$$.Execution.Input.correlation_id",
              "session_id.$": "$$.Execution.Id"
            },
            "TimeoutSeconds": 900,
            "Retry": [{
              "ErrorEquals": ["Lambda.ServiceException", "Lambda.TooManyRequestsException"],
              "IntervalSeconds": 2,
              "MaxAttempts": 3,
              "BackoffRate": 2
            }],
            "End": true
          }
        }
      },
      "ResultPath": "$.partial_signals",
      "Next": "AggregateSignals",
      "Catch": [{
        "ErrorEquals": ["States.ALL"],
        "ResultPath": "$.error",
        "Next": "HandlePartialFailure"
      }]
    },

    "HandlePartialFailure": {
      "Type": "Choice",
      "Choices": [{
        "Variable": "$.partial_signals",
        "IsPresent": true,
        "Next": "AggregateSignals"
      }],
      "Default": "PublishWorkflowFailed"
    },

    "AggregateSignals": {
      "Type": "Task",
      "Resource": "arn:aws:lambda:REGION:ACCOUNT:function:alchemiser-STAGE-signal-aggregator-sf",
      "Parameters": {
        "partial_signals.$": "$.partial_signals",
        "correlation_id.$": "$.correlation_id",
        "execution_id.$": "$$.Execution.Id"
      },
      "ResultPath": "$.aggregated_signal",
      "Next": "PublishSignalGenerated",
      "Catch": [{
        "ErrorEquals": ["AggregationError"],
        "Next": "PublishWorkflowFailed"
      }]
    },

    "PublishSignalGenerated": {
      "Type": "Task",
      "Resource": "arn:aws:states:::events:putEvents",
      "Parameters": {
        "Entries": [{
          "Source": "alchemiser.strategy",
          "DetailType": "SignalGenerated",
          "Detail": {
            "correlation_id.$": "$.correlation_id",
            "causation_id.$": "$$.Execution.Id",
            "signals_data.$": "$.aggregated_signal.signals_data",
            "consolidated_portfolio.$": "$.aggregated_signal.consolidated_portfolio",
            "data_freshness.$": "$.aggregated_signal.data_freshness"
          },
          "EventBusName": "alchemiser-STAGE-events"
        }]
      },
      "End": true
    },

    "PublishWorkflowFailed": {
      "Type": "Task",
      "Resource": "arn:aws:states:::events:putEvents",
      "Parameters": {
        "Entries": [{
          "Source": "alchemiser.strategy",
          "DetailType": "WorkflowFailed",
          "Detail": {
            "correlation_id.$": "$.correlation_id",
            "workflow_type": "strategy_coordination",
            "failure_reason.$": "$.error.Cause",
            "execution_id.$": "$$.Execution.Id"
          },
          "EventBusName": "alchemiser-STAGE-events"
        }]
      },
      "Next": "FailExecution"
    },

    "FailExecution": {
      "Type": "Fail",
      "Error": "StrategyWorkflowFailed",
      "Cause": "One or more strategies failed to execute"
    }
  }
}
```

#### Migration Steps for Strategy Orchestration

**Phase 1: Parallel Run (Week 1-2)**
1. Deploy Step Functions state machine alongside existing Orchestrator
2. Modify Schedule Manager to invoke Step Functions instead of Orchestrator Lambda
3. Keep all existing Lambdas unchanged (Strategy Worker publishes to both SF callback and EventBridge)
4. Compare execution times and results

**Phase 2: Cutover (Week 3)**
1. Remove direct EventBridge trigger from Aggregator Lambda
2. Strategy Worker returns result to Step Functions (not via EventBridge)
3. Step Functions Map state collects all results
4. New Aggregator Lambda receives array input (not EventBridge event)

**Phase 3: Cleanup (Week 4)**
1. Delete AggregationSessionsTable (state now in Step Functions execution history)
2. Remove StrategyOrchestratorFunction Lambda
3. Update CloudWatch Dashboard queries

**Code Changes Required:**

```python
# Strategy Worker: Return result instead of publishing event
# functions/strategy_worker/lambda_handler.py

def lambda_handler(event: dict, context) -> dict:
    # ... existing strategy execution logic ...

    # BEFORE: Publish to EventBridge
    # publish_to_eventbridge(partial_signal_event)

    # AFTER: Return result for Step Functions Map state
    return {
        "dsl_file": event["dsl_file"],
        "allocation": str(event["allocation"]),
        "consolidated_portfolio": consolidated_portfolio,
        "signals_data": signals_data,
        "signal_count": len(signals),
        "data_freshness": data_freshness,
        "success": True
    }
```

```yaml
# template.yaml additions

StrategyStateMachine:
  Type: AWS::Serverless::StateMachine
  Properties:
    Name: !Sub "alchemiser-${Stage}-strategy-workflow"
    DefinitionUri: statemachines/strategy_workflow.asl.json
    DefinitionSubstitutions:
      StrategyWorkerArn: !GetAtt StrategyFunction.Arn
      SignalAggregatorArn: !GetAtt SignalAggregatorSFFunction.Arn
      EventBusName: !Ref AlchemiserEventBus
    Policies:
      - LambdaInvokePolicy:
          FunctionName: !Ref StrategyFunction
      - LambdaInvokePolicy:
          FunctionName: !Ref SignalAggregatorSFFunction
      - EventBridgePutEventsPolicy:
          EventBusName: !Ref AlchemiserEventBus
    Tracing:
      Enabled: true
```

---

### B.2) Trade Execution Workflow (NOT RECOMMENDED - Analysis Only)

#### Why NOT to Migrate

The two-phase trade execution workflow has sophisticated requirements that Step Functions would complicate:

1. **Dynamic concurrency control**: 10 concurrent Lambdas (Alpaca rate limit) is handled via SQS + Reserved Concurrency. Step Functions Map MaxConcurrency is static and doesn't support per-account limiting.

2. **Circuit breakers**:
   - Sell failure threshold (`sell_failed_amount > threshold`)
   - Equity deployment circuit breaker (`cumulative_buy_succeeded_value > max_equity_limit_usd`)

   These require DynamoDB atomic counters that update as each trade completes. Step Functions would need to pass state through Map iterations, which doesn't work for parallel execution.

3. **Deferred BUY enqueue**: The current pattern stores BUY trades in DynamoDB and enqueues them only after all SELLs complete. Step Functions would require either:
   - Sequential execution (SELLs then BUYs) - defeats parallelism
   - Complex Wait/Callback pattern with external SQS

4. **Cost**: At 4 trades/day average, ~50-100 state transitions/day is negligible. But adding Step Functions layer adds complexity without benefit.

#### Hypothetical Step Functions Design (For Reference)

If migration were required, here's how it would look:

```
                    ┌───────────────────────┐
                    │  Start Execution      │
                    │  (receives Plan)      │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Separate SELL/BUY    │
                    │  (Pass state)         │
                    └───────────┬───────────┘
                                │
              ┌─────────────────┴─────────────────┐
              │                                   │
    ┌─────────▼─────────┐               ┌─────────▼─────────┐
    │  Execute SELLs    │               │  Store BUYs       │
    │  (Map, MaxConc=10)│               │  (wait for SELLs) │
    └─────────┬─────────┘               └─────────┬─────────┘
              │                                   │
              └─────────────────┬─────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │  Check SELL Results   │
                    │  (circuit breaker)    │
                    └───────────┬───────────┘
                           ┌────┴────┐
                       Pass│         │Fail
                           ▼         ▼
              ┌───────────────┐ ┌────────────┐
              │ Execute BUYs  │ │ Block BUYs │
              │ (Map, MaxC=10)│ │ (Fail)     │
              └───────┬───────┘ └────────────┘
                      │
              ┌───────▼───────┐
              │  Aggregate    │
              │  & Publish    │
              └───────────────┘
```

**Challenges:**
- Map state callback pattern for rate limiting is complex
- Circuit breaker state must be passed externally (DynamoDB still needed)
- SQS DLQ for individual trade retries is lost

**Verdict: Keep current SQS + DynamoDB architecture.**

---

### B.3) Notification Workflow (NOT RECOMMENDED)

The notification workflow is a simple event sink:

```
EventBridge (AllTradesCompleted) → Notifications Lambda → SES/SNS
```

Step Functions would add unnecessary complexity. Keep as-is.

---

## C) Final Recommendation

### Recommendation: **Selective Migration - Strategy Orchestration Only**

| Decision | Recommendation | Reasoning |
|----------|---------------|-----------|
| **Wholesale Migration** | **NO** | Trade execution's DynamoDB-based state machine is more flexible than Step Functions for circuit breakers and dynamic concurrency |
| **Strategy Orchestration** | **YES - Migrate** | Classic fan-out/fan-in; Map state is ideal; debugging benefits significant; eliminates N-1 wasted Aggregator invocations |
| **Trade Execution** | **NO - Keep SQS** | Two-phase ordering, circuit breakers, 10-concurrent rate limiting all work well with current architecture |
| **All Other Workflows** | **NO - Keep EventBridge** | Simple single-step event routing; Step Functions overhead unjustified |

### Rationale

1. **Strategy Orchestration is the best candidate:**
   - Clear fan-out (4 strategies) / fan-in (aggregate) pattern
   - Current Aggregator Lambda invoked 4 times, only last invocation aggregates (wasteful)
   - Step Functions Map state handles fan-out/fan-in natively
   - Execution history provides debugging without CloudWatch Logs Insights
   - AggregationSessionsTable can be retired (state in SF execution history)

2. **Trade Execution should remain on SQS:**
   - 10-concurrent rate limiting via Reserved Concurrency works well
   - Circuit breakers need real-time DynamoDB counters
   - Two-phase SELL→BUY enqueue timing is elegant
   - SQS DLQ provides per-trade retry isolation
   - Step Functions would need external state for circuit breakers anyway

3. **Cost implications:**
   - Strategy workflow: ~4 state transitions × 4 strategies × 252 trading days = 4,032 transitions/year = **$0.10/year** (trivial)
   - Eliminated DynamoDB reads: Aggregator currently does 4 get_session() + 4 store_partial_signal() per run = significant reduction

### Constraints and Caveats

1. **Payload limits**: Step Functions has 256KB input/output limit per state. Strategy Worker outputs (consolidated_portfolio) must be monitored. If portfolios grow large, store in S3 and pass pointers.

2. **Express vs Standard**: Use **Standard** workflows (not Express) because:
   - Strategy execution can take 15 minutes
   - Need execution history for debugging
   - Cost difference is negligible at 1 execution/day

3. **Idempotency**: Step Functions provides built-in idempotency via execution ID. However, Strategy Worker should remain idempotent in case of retries.

4. **Rollback plan**: Keep existing Orchestrator/Aggregator code for 30 days post-migration. Schedule Manager can be toggled between SF and direct Lambda invocation via environment variable.

---

## D) Cost Analysis

### Current Architecture Costs (Monthly Estimate)

| Resource | Usage | Monthly Cost |
|----------|-------|--------------|
| Lambda (Strategy Workers) | 4 × 900s × 1024MB × 22 days | ~$2.00 |
| Lambda (Orchestrator) | 22 × 60s × 512MB | ~$0.01 |
| Lambda (Aggregator) | 88 × 60s × 512MB (4 invocations × 22 days) | ~$0.03 |
| DynamoDB (AggregationSessions) | ~100 WCU, ~400 RCU | ~$0.50 |
| EventBridge | 88 events + 22 rules | ~$0.01 |
| **Total** | | **~$2.55** |

### Proposed Architecture Costs (With Step Functions)

| Resource | Usage | Monthly Cost |
|----------|-------|--------------|
| Lambda (Strategy Workers) | Same | ~$2.00 |
| Step Functions (Standard) | 22 executions × 8 transitions | ~$0.01 |
| Lambda (Aggregator - SF version) | 22 × 60s × 512MB (1 invocation/day) | ~$0.01 |
| DynamoDB (AggregationSessions) | **ELIMINATED** | $0.00 |
| EventBridge | 22 events (SignalGenerated only) | ~$0.00 |
| **Total** | | **~$2.02** |

**Savings: ~$0.50/month** (from eliminating AggregationSessions table reads/writes and reducing Aggregator invocations)

---

## E) Migration Plan

### Phase 1: Preparation (1 week)

1. **Create Step Functions state machine definition**
   - Write ASL JSON in `statemachines/strategy_workflow.asl.json`
   - Add SAM resource definition to `template.yaml`
   - Create new Lambda `SignalAggregatorSFFunction` (takes array input instead of EventBridge event)

2. **Modify Strategy Worker for dual-mode operation**
   - Detect invocation source (Step Functions vs direct)
   - Return result object for SF, publish event for legacy

3. **Add feature flag to Schedule Manager**
   - `USE_STEP_FUNCTIONS` environment variable
   - Default: `false` (legacy mode)

### Phase 2: Shadow Mode (1 week)

1. **Deploy Step Functions alongside existing workflow**
   - Both paths execute on each trading day
   - Compare results (should be identical)
   - Monitor execution times, error rates

2. **Create CloudWatch Dashboard for Step Functions**
   - Execution success/failure rate
   - Duration metrics
   - Error breakdown by state

### Phase 3: Cutover (1 week)

1. **Switch Schedule Manager to invoke Step Functions**
   - Set `USE_STEP_FUNCTIONS=true`
   - Disable legacy Orchestrator schedule trigger

2. **Remove EventBridge rule for PartialSignalGenerated**
   - Aggregator no longer triggered by EventBridge
   - SF invokes Aggregator directly

3. **Monitor for 5 trading days**
   - Verify SignalGenerated events still flow to Portfolio
   - Check notification emails match expected format

### Phase 4: Cleanup (1 week)

1. **Delete deprecated resources**
   - `StrategyOrchestratorFunction` Lambda
   - `StrategyAggregatorFunction` Lambda (replaced by SF version)
   - `PartialSignalEvent` EventBridge rule
   - `AggregationSessionsTable` DynamoDB table

2. **Update documentation**
   - CLAUDE.md architecture diagram
   - README.md workflow description

3. **Archive rollback code**
   - Keep in branch for 90 days
   - Document restoration procedure

### Test Plan

| Test Type | Description | Pass Criteria |
|-----------|-------------|---------------|
| **Unit Tests** | Aggregator Lambda with array input | All existing tests pass with new input format |
| **Integration Test** | Manual SF execution with test payload | SignalGenerated event published to EventBridge |
| **Shadow Test** | Both workflows execute in parallel | Results match within tolerance (allocation sums, signal counts) |
| **Failure Test** | Kill one Strategy Worker mid-execution | SF retries, eventually succeeds or fails gracefully |
| **Timeout Test** | Strategy Worker exceeds 15 min timeout | SF times out, publishes WorkflowFailed event |
| **Load Test** | N/A - 1 execution/day is trivial load | - |

---

## Appendix: Implementation Checklist

### IaC Changes (template.yaml)

- [ ] Add `StrategyStateMachine` resource (AWS::Serverless::StateMachine)
- [ ] Add `SignalAggregatorSFFunction` Lambda (new handler for array input)
- [ ] Add IAM role for Step Functions (Lambda invoke, EventBridge put)
- [ ] Add `USE_STEP_FUNCTIONS` parameter for feature flag
- [ ] Conditional: invoke SF or legacy Orchestrator based on flag

### Code Changes

- [ ] `functions/strategy_worker/lambda_handler.py`: Return result for SF mode
- [ ] New `functions/signal_aggregator_sf/lambda_handler.py`: Accept array input
- [ ] `functions/schedule_manager/lambda_handler.py`: Invoke SF or Lambda based on flag
- [ ] Remove `functions/strategy_orchestrator/` (after cleanup phase)
- [ ] Remove `functions/strategy_aggregator/` (after cleanup phase)

### Shared Code Changes

- [ ] `shared_layer/python/the_alchemiser/shared/services/aggregation_session_service.py`: Mark as deprecated
- [ ] Update container/wiring to not instantiate AggregationSessionService in SF mode

### Tests

- [ ] Unit test: SignalAggregatorSFFunction with array input
- [ ] Integration test: Step Functions execution via AWS SDK
- [ ] E2E test: Schedule Manager → SF → Portfolio → Execution → Notification

### Monitoring

- [ ] CloudWatch Dashboard: Step Functions metrics widget
- [ ] CloudWatch Alarm: Step Functions execution failures
- [ ] Update Log Insights queries to include SF execution logs

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-12 | Claude | Initial analysis |
