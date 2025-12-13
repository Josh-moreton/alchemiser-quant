# Strategy Lambda Scaling Plan: Multi-Node Signal Aggregation

## Problem Statement

Current architecture runs **all DSL strategy files in a single Strategy Lambda invocation**. As the number of strategies grows, we need to:
1. **Scale horizontally** - run multiple Strategy Lambda nodes in parallel, each evaluating a subset of strategies
2. **Aggregate signals** - combine all signals from multiple nodes into ONE unified `ConsolidatedPortfolio`
3. **Preserve existing flow** - Portfolio Lambda should receive a single consolidated signal as it does today

---

## Current Architecture

```
EventBridge Schedule (9:35 AM ET)
        ↓
    Strategy Lambda (evaluates ALL DSL files)
        ├─ KLM.clj (weight: 0.3)
        ├─ momentum.clj (weight: 0.3)
        └─ mean_reversion.clj (weight: 0.4)
        ↓ publishes ONE SignalGenerated event
    Portfolio Lambda
        ↓ publishes RebalancePlanned
    Execution Lambda
```

**Issue**: Single Lambda execution has limits:
- **Memory**: 10GB max
- **Timeout**: 15 minutes max
- **CPU**: Limited by memory allocation
- **Complexity**: 100+ strategies would be too slow/resource-intensive

---

## Proposed Architecture: Fan-Out/Fan-In with Signal Aggregator

### High-Level Design

```
EventBridge Schedule (9:35 AM ET)
        ↓
    Strategy Coordinator Lambda (NEW)
        ├─ Reads strategy config
        ├─ Splits strategies into batches
        ├─ Writes aggregation state to DynamoDB
        └─ Publishes StrategyBatchRequested events (one per batch)

        ↓ (Fan-out to multiple Strategy Lambda invocations)

    ┌──────────────────────────────────────────────────┐
    │  Strategy Lambda (Batch 1)                       │
    │  ├─ KLM.clj (weight: 0.3)                       │
    │  └─ momentum.clj (weight: 0.2)                  │
    │  └─ Publishes PartialSignalGenerated             │
    └──────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────┐
    │  Strategy Lambda (Batch 2)                       │
    │  ├─ mean_reversion.clj (weight: 0.25)           │
    │  └─ breakout.clj (weight: 0.25)                 │
    │  └─ Publishes PartialSignalGenerated             │
    └──────────────────────────────────────────────────┘

        ↓ (All PartialSignalGenerated events)

    Signal Aggregator Lambda (NEW)
        ├─ Collects partial signals in DynamoDB
        ├─ Waits for all batches to complete
        ├─ Aggregates into consolidated portfolio
        └─ Publishes ONE SignalGenerated event

        ↓ (Existing flow continues unchanged)

    Portfolio Lambda
        ↓ RebalancePlanned
    Execution Lambda
        ↓ TradeExecuted
    Notifications Lambda
```

### Key Components

| Component | Type | Purpose | Trigger |
|-----------|------|---------|---------|
| **Strategy Coordinator** | Lambda (new) | Split strategies into batches, initiate parallel execution | EventBridge Schedule |
| **Strategy Worker** | Lambda (existing, modified) | Evaluate assigned strategy batch, emit partial signals | StrategyBatchRequested event |
| **Signal Aggregator** | Lambda (new) | Collect partial signals, aggregate, emit consolidated signal | PartialSignalGenerated event |
| **Aggregation State Table** | DynamoDB (new) | Track which batches completed, store partial signals | - |

---

## Detailed Design

### 1. Strategy Coordinator Lambda

**File**: `the_alchemiser/coordinator_v2/lambda_handler.py` (NEW)

**Responsibilities**:
1. Read all configured DSL strategies and their allocations
2. Split strategies into **configurable batches** (e.g., 10 strategies per batch)
3. Create **aggregation session** in DynamoDB with:
   - Session ID (correlation_id)
   - Expected batch count
   - Batch configurations
   - Timestamp, timeout
4. Publish **StrategyBatchRequested** events to EventBridge (one per batch)

**Configuration**:
```python
STRATEGY_BATCH_SIZE: int = 10          # Max strategies per batch
STRATEGY_MAX_PARALLEL_BATCHES: int = 5 # Max concurrent Lambda executions
AGGREGATION_TIMEOUT_SECONDS: int = 600 # 10 minutes max wait
```

**Batching Strategy**:
```python
# Example: 25 strategies with batch_size=10
# Batch 1: strategies[0:10]   - combined weight: 0.35
# Batch 2: strategies[10:20]  - combined weight: 0.40
# Batch 3: strategies[20:25]  - combined weight: 0.25
```

**Event Published**:
```python
class StrategyBatchRequested(BaseEvent):
    event_type: str = "StrategyBatchRequested"

    session_id: str                          # Aggregation session ID
    batch_id: str                            # e.g., "batch-1-of-3"
    batch_number: int                        # 1, 2, 3...
    total_batches: int                       # 3

    dsl_files: list[str]                     # ["KLM.clj", "momentum.clj"]
    dsl_allocations: dict[str, float]        # {"KLM.clj": 0.3, "momentum.clj": 0.2}

    timeout_at: datetime                     # Session expiry
```

**DynamoDB Schema** (`AggregationSessionsTable`):
```python
{
    "PK": "SESSION#<session_id>",
    "SK": "METADATA",
    "session_id": str,
    "correlation_id": str,
    "total_batches": int,
    "completed_batches": int,
    "status": "PENDING" | "AGGREGATING" | "COMPLETED" | "FAILED",
    "created_at": datetime,
    "timeout_at": datetime,
    "batch_configs": [
        {
            "batch_id": str,
            "dsl_files": list[str],
            "dsl_allocations": dict[str, float]
        }
    ]
}

# One item per batch completion:
{
    "PK": "SESSION#<session_id>",
    "SK": "BATCH#<batch_id>",
    "batch_id": str,
    "completed_at": datetime,
    "signal_count": int,
    "consolidated_portfolio": dict,  # Partial portfolio from this batch
    "signals_data": dict             # Partial signals data
}
```

---

### 2. Strategy Worker Lambda (Modified)

**File**: `the_alchemiser/strategy_v2/lambda_handler.py` (MODIFIED)

**Changes**:
1. **New trigger**: Listen for `StrategyBatchRequested` events (in addition to direct schedule)
2. **Batch mode**: When triggered by event, only evaluate strategies in `dsl_files` from event
3. **Emit PartialSignalGenerated** instead of `SignalGenerated` when in batch mode

**Event Published** (new):
```python
class PartialSignalGenerated(BaseEvent):
    event_type: str = "PartialSignalGenerated"
    schema_version: str

    session_id: str                          # Links to aggregation session
    batch_id: str                            # Which batch this came from
    batch_number: int
    total_batches: int

    # Same as SignalGenerated:
    signals_data: dict[str, Any]             # Strategy signals (subset)
    consolidated_portfolio: dict[str, Any]   # Partial portfolio (weights sum < 1.0)
    signal_count: int
    metadata: dict[str, Any]
```

**Logic Changes**:
```python
def lambda_handler(event, context):
    # Detect if triggered by StrategyBatchRequested event
    if "detail-type" in event and event["detail-type"] == "StrategyBatchRequested":
        # BATCH MODE
        batch_request = StrategyBatchRequested.from_json_dict(event["detail"])

        # Override DSL config with batch-specific files
        settings.dsl_files = batch_request.dsl_files
        settings.dsl_allocations = batch_request.dsl_allocations

        # Generate signals (existing logic)
        handler = SignalGenerationHandler(...)
        partial_signal_event = handler.handle_event(...)

        # Publish PartialSignalGenerated (not SignalGenerated)
        publish_to_eventbridge(partial_signal_event)

    else:
        # LEGACY MODE (single invocation, all strategies)
        # Existing logic unchanged - for backward compatibility
        ...
```

**Backward Compatibility**:
- Direct schedule invocations continue to work (single SignalGenerated)
- Batch mode only activated when triggered by StrategyBatchRequested event
- No breaking changes to existing deployments

---

### 3. Signal Aggregator Lambda

**File**: `the_alchemiser/aggregator_v2/lambda_handler.py` (NEW)

**Responsibilities**:
1. **Collect partial signals** from PartialSignalGenerated events
2. **Store in DynamoDB** under the session
3. **Check completion** - have all batches reported?
4. **Aggregate portfolios** - sum allocations across all batches
5. **Publish consolidated SignalGenerated** event (triggers Portfolio Lambda)

**Trigger**: EventBridge rule matching `PartialSignalGenerated` events

**Aggregation Logic**:
```python
def lambda_handler(event, context):
    partial_signal = PartialSignalGenerated.from_json_dict(event["detail"])

    # 1. Store partial signal in DynamoDB
    store_partial_signal(
        session_id=partial_signal.session_id,
        batch_id=partial_signal.batch_id,
        consolidated_portfolio=partial_signal.consolidated_portfolio,
        signals_data=partial_signal.signals_data
    )

    # 2. Check if all batches completed (atomic increment)
    session = get_aggregation_session(partial_signal.session_id)
    completed_count = increment_completed_batches(session_id)

    if completed_count < session.total_batches:
        logger.info(f"Waiting for more batches: {completed_count}/{session.total_batches}")
        return  # Not ready yet

    # 3. All batches complete - aggregate!
    all_partial_signals = get_all_partial_signals(session_id)

    # 4. Merge consolidated portfolios
    merged_portfolio = merge_portfolios(all_partial_signals)
    merged_signals_data = merge_signals_data(all_partial_signals)

    # 5. Validate aggregated portfolio
    validate_consolidated_portfolio(merged_portfolio)  # Sum ≈ 1.0

    # 6. Publish consolidated SignalGenerated event
    signal_generated = SignalGenerated(
        event_id=generate_request_id(),
        correlation_id=session.correlation_id,
        causation_id=session_id,
        timestamp=datetime.now(UTC),
        source_module="aggregator_v2",
        source_component="SignalAggregator",

        signals_data=merged_signals_data,
        consolidated_portfolio=merged_portfolio.to_dict(),
        signal_count=sum(s.signal_count for s in all_partial_signals),
        metadata={"aggregation_session_id": session_id}
    )

    publish_to_eventbridge(signal_generated)

    # 7. Mark session as completed
    update_session_status(session_id, "COMPLETED")
```

**Portfolio Merging**:
```python
def merge_portfolios(partial_signals: list[PartialSignalGenerated]) -> ConsolidatedPortfolio:
    """
    Merge multiple partial portfolios into one consolidated portfolio.

    Example:
        Batch 1: {"AAPL": 0.3, "SPY": 0.2}  (total: 0.5)
        Batch 2: {"TSLA": 0.25, "QQQ": 0.25} (total: 0.5)
        Merged:  {"AAPL": 0.3, "SPY": 0.2, "TSLA": 0.25, "QQQ": 0.25} (total: 1.0)
    """
    merged_allocations: dict[str, Decimal] = {}

    for partial in partial_signals:
        portfolio = ConsolidatedPortfolio.from_json_dict(
            partial.consolidated_portfolio
        )

        for symbol, weight in portfolio.target_allocations.items():
            if symbol in merged_allocations:
                # Symbol appears in multiple batches (shouldn't happen with proper batching)
                logger.warning(f"Symbol {symbol} in multiple batches, summing weights")
                merged_allocations[symbol] += weight
            else:
                merged_allocations[symbol] = weight

    # Validate total allocation
    total = sum(merged_allocations.values())
    if not (Decimal("0.99") <= total <= Decimal("1.01")):
        raise AggregationError(f"Invalid total allocation: {total}")

    return ConsolidatedPortfolio(
        target_allocations=merged_allocations,
        correlation_id=partial_signals[0].correlation_id,
        timestamp=datetime.now(UTC),
        strategy_count=sum(p.signal_count for p in partial_signals),
        source_strategies=list(merged_allocations.keys())
    )
```

**Error Handling**:
```python
# Timeout handling (DynamoDB TTL + CloudWatch rule)
if session.timeout_at < datetime.now(UTC):
    logger.error(f"Aggregation session {session_id} timed out")
    publish_to_eventbridge(WorkflowFailed(...))
    update_session_status(session_id, "FAILED")
    return

# Partial failure handling
if any(batch.status == "FAILED" for batch in session.batches):
    logger.error(f"One or more batches failed in session {session_id}")
    publish_to_eventbridge(WorkflowFailed(...))
    update_session_status(session_id, "FAILED")
    return
```

---

### 4. DynamoDB Aggregation State Table

**Table Name**: `AlchemiserAggregationSessions`

**Schema**:
```
PK (String, Partition Key): SESSION#<session_id>
SK (String, Sort Key): METADATA | BATCH#<batch_id>
TTL (Number): Expiration timestamp (auto-cleanup after 24h)

Attributes:
- session_id (String)
- correlation_id (String)
- total_batches (Number)
- completed_batches (Number) - atomic counter
- status (String): PENDING | AGGREGATING | COMPLETED | FAILED | TIMEOUT
- created_at (String, ISO datetime)
- timeout_at (String, ISO datetime)
- batch_configs (List)
- consolidated_portfolio (Map) - only in BATCH items
- signals_data (Map) - only in BATCH items
```

**Access Patterns**:
```python
# 1. Create session
put_item({
    "PK": "SESSION#abc123",
    "SK": "METADATA",
    "session_id": "abc123",
    ...
})

# 2. Store partial signal (atomic)
update_item(
    Key={"PK": "SESSION#abc123", "SK": "BATCH#batch-1"},
    UpdateExpression="SET consolidated_portfolio = :portfolio, ...",
    ConditionExpression="attribute_not_exists(SK)"  # Idempotency
)

# 3. Increment completed counter (atomic)
update_item(
    Key={"PK": "SESSION#abc123", "SK": "METADATA"},
    UpdateExpression="ADD completed_batches :one",
    ExpressionAttributeValues={":one": 1},
    ReturnValues="UPDATED_NEW"
)

# 4. Get all partial signals (single query)
query(
    KeyConditionExpression="PK = :session AND begins_with(SK, 'BATCH#')",
    ExpressionAttributeValues={":session": "SESSION#abc123"}
)
```

**Indexes**: None needed (using single-table design with composite key)

**TTL**: Set to `created_at + 24 hours` for automatic cleanup

---

## Event Schemas

### New Events

```python
# File: the_alchemiser/shared/events/schemas.py

@dataclass(frozen=True)
class StrategyBatchRequested(BaseEvent):
    """Request to execute a batch of strategies."""
    event_type: str = "StrategyBatchRequested"
    schema_version: str = "1.0.0"

    session_id: str
    batch_id: str
    batch_number: int
    total_batches: int
    dsl_files: list[str]
    dsl_allocations: dict[str, float]
    timeout_at: datetime


@dataclass(frozen=True)
class PartialSignalGenerated(BaseEvent):
    """Signals from a subset of strategies (one batch)."""
    event_type: str = "PartialSignalGenerated"
    schema_version: str = "1.0.0"

    session_id: str
    batch_id: str
    batch_number: int
    total_batches: int
    signals_data: dict[str, Any]
    consolidated_portfolio: dict[str, Any]  # Partial (sum < 1.0)
    signal_count: int
    metadata: dict[str, Any]


@dataclass(frozen=True)
class AggregationCompleted(BaseEvent):
    """All batches aggregated successfully."""
    event_type: str = "AggregationCompleted"
    schema_version: str = "1.0.0"

    session_id: str
    total_batches: int
    total_signals: int
    aggregated_signal_event_id: str  # The SignalGenerated event ID
```

---

## SAM Template Changes (template.yaml)

### New Resources

```yaml
  # ==================== COORDINATOR LAMBDA ====================
  StrategyCoordinatorFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: .
      Handler: the_alchemiser.coordinator_v2.lambda_handler.lambda_handler
      Runtime: python3.12
      Timeout: 60
      MemorySize: 512
      Environment:
        Variables:
          STRATEGY_BATCH_SIZE: 10
          STRATEGY_MAX_PARALLEL_BATCHES: 5
          AGGREGATION_TIMEOUT_SECONDS: 600
          AGGREGATION_SESSIONS_TABLE: !Ref AggregationSessionsTable
          EVENT_BUS_NAME: !Ref AlchemiserEventBus
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref AggregationSessionsTable
        - EventBridgePutEventsPolicy:
            EventBusName: !Ref AlchemiserEventBus
      Events:
        DailySchedule:
          Type: Schedule
          Properties:
            Schedule: "cron(35 13 ? * MON-FRI *)"  # 9:35 AM ET (UTC-4/5)
            Description: Daily strategy execution trigger
            Enabled: true

  # ==================== SIGNAL AGGREGATOR LAMBDA ====================
  SignalAggregatorFunction:
    Type: AWS::Serverless::Function
    Properties:
      CodeUri: .
      Handler: the_alchemiser.aggregator_v2.lambda_handler.lambda_handler
      Runtime: python3.12
      Timeout: 120
      MemorySize: 1024
      Environment:
        Variables:
          AGGREGATION_SESSIONS_TABLE: !Ref AggregationSessionsTable
          EVENT_BUS_NAME: !Ref AlchemiserEventBus
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref AggregationSessionsTable
        - EventBridgePutEventsPolicy:
            EventBusName: !Ref AlchemiserEventBus
      Events:
        PartialSignalEvent:
          Type: EventBridgeRule
          Properties:
            EventBusName: !Ref AlchemiserEventBus
            Pattern:
              detail-type:
                - PartialSignalGenerated
            RetryPolicy:
              MaximumRetryAttempts: 2

  # ==================== AGGREGATION STATE TABLE ====================
  AggregationSessionsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: !Sub "${AWS::StackName}-aggregation-sessions"
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: PK
          AttributeType: S
        - AttributeName: SK
          AttributeType: S
      KeySchema:
        - AttributeName: PK
          KeyType: HASH
        - AttributeName: SK
          KeyType: RANGE
      TimeToLiveSpecification:
        Enabled: true
        AttributeName: TTL
      PointInTimeRecoverySpecification:
        PointInTimeRecoveryEnabled: true
      Tags:
        - Key: Purpose
          Value: Strategy signal aggregation state

  # ==================== STRATEGY LAMBDA UPDATES ====================
  StrategyFunction:
    Type: AWS::Serverless::Function
    Properties:
      # ... existing properties ...
      Events:
        # REMOVE DailySchedule (moved to Coordinator)
        # DailySchedule: ...  ← DELETE THIS

        # ADD batch execution trigger
        BatchRequest:
          Type: EventBridgeRule
          Properties:
            EventBusName: !Ref AlchemiserEventBus
            Pattern:
              detail-type:
                - StrategyBatchRequested
            RetryPolicy:
              MaximumRetryAttempts: 2
```

---

## Migration Path

### Phase 1: Deploy Infrastructure (No Behavior Change)
1. Deploy new DynamoDB table (`AggregationSessionsTable`)
2. Deploy Coordinator Lambda (but don't attach schedule yet)
3. Deploy Aggregator Lambda
4. Add `StrategyBatchRequested` event handler to Strategy Lambda (but keep existing schedule)
5. **Result**: System works exactly as before, new components are deployed but inactive

### Phase 2: Dual Mode Testing
1. Manually invoke Coordinator Lambda with test config
2. Verify Strategy Lambda handles batch requests correctly
3. Verify Aggregator correctly merges signals
4. Verify Portfolio Lambda receives proper consolidated signal
5. **Result**: Can test new flow without disrupting production

### Phase 3: Cutover
1. Move EventBridge schedule from Strategy Lambda to Coordinator Lambda
2. Monitor aggregation sessions in DynamoDB
3. Verify end-to-end workflow completes successfully
4. **Result**: Production traffic flows through new architecture

### Phase 4: Cleanup (Optional)
1. Remove legacy single-invocation code path from Strategy Lambda
2. Clean up old EventBridge rules
3. Update documentation

---

## Configuration Example

### Current Config (Single Lambda)
```python
# Settings
dsl_files = ["KLM.clj", "momentum.clj", "mean_reversion.clj", "breakout.clj"]
dsl_allocations = {
    "KLM.clj": 0.25,
    "momentum.clj": 0.25,
    "mean_reversion.clj": 0.25,
    "breakout.clj": 0.25
}
```

### New Config (Multi-Node with Batching)
```python
# Settings (same as before)
dsl_files = ["KLM.clj", "momentum.clj", "mean_reversion.clj", "breakout.clj"]
dsl_allocations = {
    "KLM.clj": 0.25,
    "momentum.clj": 0.25,
    "mean_reversion.clj": 0.25,
    "breakout.clj": 0.25
}

# Coordinator will automatically batch:
STRATEGY_BATCH_SIZE = 2  # 2 strategies per batch

# Result: 2 parallel Strategy Lambda invocations:
# Batch 1: KLM.clj (0.25) + momentum.clj (0.25) = 0.5 total weight
# Batch 2: mean_reversion.clj (0.25) + breakout.clj (0.25) = 0.5 total weight
```

---

## Performance Characteristics

### Single Lambda (Current)
- **Execution time**: T_strategy * N_strategies (sequential) or T_strategy (parallel with max_workers)
- **Memory**: Proportional to N_strategies
- **Cost**: 1 Lambda invocation
- **Limit**: ~100 strategies max (memory/timeout constraints)

### Multi-Node (Proposed)
- **Execution time**: ~T_strategy (all batches run in parallel)
- **Memory per batch**: Proportional to batch_size
- **Cost**: N_batches + 1 (coordinator) + 1 (aggregator) Lambda invocations
- **Limit**: Virtually unlimited (1000s of strategies possible)

**Example**: 100 strategies with batch_size=10
- Current: 1 Lambda, 10GB memory, 5+ minutes
- Proposed: 10 parallel Lambdas, 1GB each, ~30 seconds + aggregation overhead

---

## Monitoring & Observability

### CloudWatch Metrics
```python
# Custom metrics to add:
- AggregationSessionsCreated (count)
- AggregationSessionsCompleted (count)
- AggregationSessionsFailed (count)
- AggregationSessionDuration (ms)
- PartialSignalsReceived (count per session)
- BatchExecutionDuration (ms per batch)
```

### CloudWatch Alarms
```yaml
# Aggregation timeout alarm
AggregationTimeoutAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    MetricName: AggregationSessionsFailed
    Threshold: 1
    ComparisonOperator: GreaterThanOrEqualToThreshold
    EvaluationPeriods: 1
    AlarmActions:
      - !Ref DLQAlertTopic

# Batch failure alarm
BatchFailureAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    MetricName: StrategyLambdaErrors
    Threshold: 2
    ComparisonOperator: GreaterThanOrEqualToThreshold
    EvaluationPeriods: 1
    AlarmActions:
      - !Ref DLQAlertTopic
```

### Logs Insights Queries
```sql
-- Aggregation session timeline
fields @timestamp, message, session_id, batch_id, completed_batches, total_batches
| filter source_module = "aggregator_v2"
| sort @timestamp asc

-- Failed batches
fields @timestamp, correlation_id, batch_id, error
| filter event_type = "WorkflowFailed" and source_module = "strategy_v2"
| stats count() by batch_id

-- Aggregation duration
fields @timestamp, session_id, duration_ms
| filter message = "Aggregation completed"
| stats avg(duration_ms), max(duration_ms), min(duration_ms)
```

---

## Error Scenarios & Recovery

### Scenario 1: One Batch Fails
**Detection**: PartialSignalGenerated event not received for batch N
**Recovery**:
1. Aggregator times out after 10 minutes
2. Publishes WorkflowFailed event
3. Notifications Lambda sends alert email
4. Operator investigates failed batch in CloudWatch Logs
5. Can manually replay batch or full session

### Scenario 2: Aggregator Lambda Fails
**Detection**: SignalGenerated event not published after all batches complete
**Recovery**:
1. EventBridge retries PartialSignalGenerated delivery (up to 2x)
2. If still failing, message goes to DLQ
3. DLQ alarm triggers SNS notification
4. Operator investigates DLQ, can manually trigger aggregator

### Scenario 3: Partial Signals Exceed Timeout
**Detection**: DynamoDB session shows TIMEOUT status
**Recovery**:
1. CloudWatch alarm fires on AggregationSessionsFailed metric
2. Operator reviews which batches didn't complete
3. Can manually invoke missing batches
4. Or re-run entire session via Coordinator

### Scenario 4: DynamoDB Throttling
**Detection**: DynamoDB write throttles during batch storage
**Recovery**:
1. Lambda automatic retries with exponential backoff
2. DynamoDB on-demand scaling handles burst
3. If persistent, increase provisioned capacity or switch to on-demand

---

## Testing Strategy

### Unit Tests
```python
# Test batch splitting logic
def test_coordinator_splits_strategies_into_batches():
    strategies = ["A", "B", "C", "D", "E"]
    allocations = {"A": 0.2, "B": 0.2, "C": 0.2, "D": 0.2, "E": 0.2}

    batches = create_batches(strategies, allocations, batch_size=2)

    assert len(batches) == 3  # [AB, CD, E]
    assert sum(b.total_weight for b in batches) == 1.0

# Test portfolio merging
def test_aggregator_merges_partial_portfolios():
    partial1 = {"AAPL": Decimal("0.3"), "SPY": Decimal("0.2")}
    partial2 = {"TSLA": Decimal("0.25"), "QQQ": Decimal("0.25")}

    merged = merge_portfolios([partial1, partial2])

    assert merged == {"AAPL": 0.3, "SPY": 0.2, "TSLA": 0.25, "QQQ": 0.25}
    assert sum(merged.values()) == 1.0

# Test idempotency (duplicate partial signals)
def test_aggregator_handles_duplicate_partial_signals():
    # Simulate EventBridge retry
    signal = create_partial_signal(session_id="abc", batch_id="batch-1")

    store_partial_signal(signal)  # First delivery
    store_partial_signal(signal)  # Retry (duplicate)

    session = get_session("abc")
    assert session.completed_batches == 1  # Not double-counted
```

### Integration Tests
```python
# Test end-to-end flow with 2 batches
@pytest.mark.integration
def test_multi_batch_signal_aggregation():
    # 1. Invoke Coordinator
    coordinator_response = invoke_coordinator_lambda({
        "strategies": 4,
        "batch_size": 2
    })
    session_id = coordinator_response["session_id"]

    # 2. Verify 2 StrategyBatchRequested events published
    batch_events = get_eventbridge_events("StrategyBatchRequested")
    assert len(batch_events) == 2

    # 3. Wait for all batches to complete
    wait_for_condition(
        lambda: get_session_status(session_id) == "COMPLETED",
        timeout=120
    )

    # 4. Verify SignalGenerated event published
    signal_events = get_eventbridge_events("SignalGenerated")
    assert len(signal_events) == 1
    assert signal_events[0].correlation_id == session_id

    # 5. Verify portfolio allocations sum to 1.0
    portfolio = signal_events[0].consolidated_portfolio
    assert sum(portfolio.values()) == Decimal("1.0")
```

### Load Tests
```python
# Test 100 strategies across 10 batches
@pytest.mark.load
def test_large_scale_batching():
    strategies = [f"strategy_{i}.clj" for i in range(100)]
    allocations = {s: 0.01 for s in strategies}  # Equal weight

    start_time = time.time()

    session_id = invoke_coordinator({
        "dsl_files": strategies,
        "dsl_allocations": allocations,
        "batch_size": 10
    })

    wait_for_completion(session_id, timeout=300)

    duration = time.time() - start_time
    assert duration < 120  # Should complete in under 2 minutes

    # Verify no data loss
    final_signal = get_final_signal_event(session_id)
    assert len(final_signal.consolidated_portfolio) == 100
```

---

## Rollback Plan

If issues arise after deployment:

### Quick Rollback (5 minutes)
1. Update EventBridge rule: move schedule from Coordinator back to Strategy Lambda
2. Strategy Lambda still has legacy code path, will work immediately
3. Monitor for successful SignalGenerated events

### Full Rollback (via CloudFormation)
```bash
# Revert to previous stack version
aws cloudformation deploy \
  --template-file previous-template.yaml \
  --stack-name alchemiser-prod \
  --no-fail-on-empty-changeset
```

---

## Cost Analysis

### Current (Single Lambda)
- **Strategy Lambda**: 1 invocation/day × 256MB × 5min = ~$0.01/day
- **Total**: ~$3/month

### Proposed (Multi-Node)
Assuming 50 strategies, batch_size=10 (5 batches):
- **Coordinator Lambda**: 1 invocation/day × 512MB × 10s = ~$0.001/day
- **Strategy Lambda**: 5 invocations/day × 256MB × 1min = ~$0.02/day
- **Aggregator Lambda**: 1 invocation/day × 1GB × 5s = ~$0.001/day
- **DynamoDB**: Minimal (5 writes + 1 query per day)
- **Total**: ~$6/month

**Cost increase**: 2x (but handles 5x-10x more strategies)

### At Scale (500 strategies, 50 batches)
- **Strategy Lambda**: 50 invocations/day × 256MB × 1min = ~$0.20/day
- **Total**: ~$60/month (handles 100x more strategies than single Lambda)

---

## Timeline Estimate

### Week 1: Infrastructure Setup
- [ ] Create DynamoDB table (Aggregation Sessions)
- [ ] Implement Coordinator Lambda skeleton
- [ ] Implement Aggregator Lambda skeleton
- [ ] Update template.yaml with new resources
- [ ] Deploy to dev environment

### Week 2: Core Logic Implementation
- [ ] Implement batch splitting logic in Coordinator
- [ ] Implement signal aggregation in Aggregator
- [ ] Add PartialSignalGenerated event handling to Strategy Lambda
- [ ] Write unit tests for batching and aggregation

### Week 3: Integration & Testing
- [ ] End-to-end integration tests
- [ ] Load testing with 100+ strategies
- [ ] Monitor DynamoDB performance
- [ ] Fix bugs and edge cases

### Week 4: Production Deployment
- [ ] Deploy to production (dual mode)
- [ ] Run parallel tests (old vs new flow)
- [ ] Cutover to new architecture
- [ ] Monitor for 1 week
- [ ] Document and close

---

## Alternative Approaches Considered

### ❌ Option 2: DynamoDB Streams + Aggregator
**Pros**: Native event triggering, automatic retries
**Cons**: More complex error handling, harder to debug, stream lag issues
**Verdict**: Rejected - EventBridge provides better visibility and control

### ❌ Option 3: Step Functions State Machine
**Pros**: Built-in orchestration, visual workflow, automatic retries
**Cons**: More expensive, slower (state machine overhead), harder to test
**Verdict**: Rejected - Over-engineered for this use case

### ❌ Option 4: SQS FIFO + Batch Window
**Pros**: Built-in batching, ordered delivery
**Cons**: Fixed batch window (max 5 min), less flexible, harder timeout handling
**Verdict**: Rejected - Batch window not ideal for variable strategy counts

### ✅ Option 1: EventBridge + Aggregator Lambda (SELECTED)
**Pros**:
- Fits existing architecture
- Clear event flow
- Flexible batching
- Easy monitoring
- Low cost
**Cons**:
- Requires custom aggregation logic
- DynamoDB state management
**Verdict**: Best balance of simplicity, cost, and flexibility

---

## Summary

This scaling plan enables **horizontal scaling of strategy execution** while maintaining **backward compatibility** and **minimal changes to existing components**.

### Key Benefits
✅ **Scalable**: Handle 1000s of strategies across parallel Lambda nodes
✅ **Reliable**: Atomic aggregation with DynamoDB, built-in retries
✅ **Observable**: Full event traceability, CloudWatch metrics and alarms
✅ **Cost-effective**: Pay only for what you use, linear cost scaling
✅ **Maintainable**: Clear separation of concerns, single-responsibility Lambdas
✅ **Backward compatible**: Existing flow still works during migration

### Next Steps
1. Review and approve this plan
2. Create feature branch: `feature/multi-node-strategy-scaling`
3. Implement Phase 1 (infrastructure)
4. Deploy to dev environment for testing
5. Iterate based on findings
6. Production rollout

---

**Questions or feedback?** This is a living document - please provide input before implementation begins.
