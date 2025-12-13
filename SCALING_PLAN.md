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

## Proposed Architecture: Fan-Out/Fan-In Using Lambda Concurrency

### High-Level Design

```
EventBridge Schedule (9:35 AM ET)
        ↓
    Strategy Coordinator Lambda (NEW)
        ├─ Reads strategy config (all DSL files + allocations)
        ├─ Creates aggregation session in DynamoDB
        └─ Invokes Strategy Lambda ONCE PER STRATEGY FILE (parallel)

        ↓ (Fan-out: one Lambda invocation per strategy)

    ┌──────────────────────────────────────────────────┐
    │  Strategy Lambda Invocation 1                    │
    │  ├─ Evaluates: KLM.clj (weight: 0.25)           │
    │  └─ Publishes PartialSignalGenerated             │
    └──────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────┐
    │  Strategy Lambda Invocation 2                    │
    │  ├─ Evaluates: momentum.clj (weight: 0.25)      │
    │  └─ Publishes PartialSignalGenerated             │
    └──────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────┐
    │  Strategy Lambda Invocation 3                    │
    │  ├─ Evaluates: mean_reversion.clj (weight: 0.25)│
    │  └─ Publishes PartialSignalGenerated             │
    └──────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────┐
    │  Strategy Lambda Invocation 4                    │
    │  ├─ Evaluates: breakout.clj (weight: 0.25)      │
    │  └─ Publishes PartialSignalGenerated             │
    └──────────────────────────────────────────────────┘

        ↓ (All PartialSignalGenerated events arrive in parallel)

    Signal Aggregator Lambda (NEW)
        ├─ Collects partial signals in DynamoDB
        ├─ Waits for ALL strategy files to complete
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
| **Strategy Coordinator** | Lambda (new) | Read config, create session, invoke Strategy Lambda once per file | EventBridge Schedule |
| **Strategy Worker** | Lambda (existing, modified) | Evaluate SINGLE strategy file, emit partial signal | Direct Lambda invoke from Coordinator |
| **Signal Aggregator** | Lambda (new) | Collect partial signals, aggregate, emit consolidated signal | PartialSignalGenerated event |
| **Aggregation State Table** | DynamoDB (new) | Track which strategies completed, store partial signals | - |

---

## Detailed Design

### 1. Strategy Coordinator Lambda

**File**: `the_alchemiser/coordinator_v2/lambda_handler.py` (NEW)

**Responsibilities**:
1. Read all configured DSL strategies and their allocations
2. Create **aggregation session** in DynamoDB with:
   - Session ID (correlation_id)
   - Expected strategy count (number of files)
   - Strategy file configurations
   - Timestamp, timeout
3. **Directly invoke Strategy Lambda** once per strategy file (async invocation)
4. Lambda's natural concurrency handles parallelism

**Configuration**:
```python
AGGREGATION_TIMEOUT_SECONDS: int = 600      # 10 minutes max wait
STRATEGY_LAMBDA_FUNCTION_NAME: str          # ARN of Strategy Lambda
MAX_CONCURRENT_STRATEGIES: int = 1000       # Lambda account concurrency limit
```

**Invocation Logic**:
```python
def lambda_handler(event, context):
    correlation_id = generate_request_id()

    # Read all strategy files from settings
    dsl_files = settings.dsl_files  # ["KLM.clj", "momentum.clj", ...]
    dsl_allocations = settings.dsl_allocations  # {"KLM.clj": 0.25, ...}

    # Create aggregation session
    session_id = create_aggregation_session(
        correlation_id=correlation_id,
        total_strategies=len(dsl_files),
        strategy_configs=[(file, dsl_allocations[file]) for file in dsl_files]
    )

    # Invoke Strategy Lambda once per file (parallel async invocations)
    lambda_client = boto3.client('lambda')

    for dsl_file in dsl_files:
        payload = {
            "session_id": session_id,
            "correlation_id": correlation_id,
            "dsl_file": dsl_file,
            "allocation": float(dsl_allocations[dsl_file]),
            "total_strategies": len(dsl_files)
        }

        # Async invocation - returns immediately, Lambda runs in parallel
        lambda_client.invoke(
            FunctionName=STRATEGY_LAMBDA_FUNCTION_NAME,
            InvocationType='Event',  # Async
            Payload=json.dumps(payload)
        )

    return {
        "statusCode": 200,
        "body": {
            "session_id": session_id,
            "correlation_id": correlation_id,
            "strategies_invoked": len(dsl_files)
        }
    }
```

**DynamoDB Schema** (`AggregationSessionsTable`):
```python
# Session metadata
{
    "PK": "SESSION#<session_id>",
    "SK": "METADATA",
    "session_id": str,
    "correlation_id": str,
    "total_strategies": int,              # Total number of strategy files
    "completed_strategies": int,          # Counter (atomic increment)
    "status": "PENDING" | "AGGREGATING" | "COMPLETED" | "FAILED",
    "created_at": datetime,
    "timeout_at": datetime,
    "TTL": int,                           # Auto-cleanup after 24h
    "strategy_configs": [
        {
            "dsl_file": str,
            "allocation": float
        }
    ]
}

# One item per strategy completion
{
    "PK": "SESSION#<session_id>",
    "SK": "STRATEGY#<dsl_file>",
    "dsl_file": str,                      # "KLM.clj"
    "allocation": float,                  # 0.25
    "completed_at": datetime,
    "signal_count": int,
    "consolidated_portfolio": dict,       # Partial portfolio from this strategy
    "signals_data": dict                  # Signals from this strategy
}
```

---

### 2. Strategy Worker Lambda (Modified)

**File**: `the_alchemiser/strategy_v2/lambda_handler.py` (MODIFIED)

**Changes**:
1. **New trigger**: Direct Lambda invocation from Coordinator (async)
2. **Single-file mode**: Evaluate exactly ONE strategy file per invocation
3. **Emit PartialSignalGenerated** instead of `SignalGenerated` when in single-file mode

**Event Published** (new):
```python
class PartialSignalGenerated(BaseEvent):
    event_type: str = "PartialSignalGenerated"
    schema_version: str

    session_id: str                          # Links to aggregation session
    dsl_file: str                            # Which strategy file (e.g., "KLM.clj")
    allocation: Decimal                      # File weight (e.g., 0.25)
    strategy_number: int                     # 1, 2, 3... (for ordering)
    total_strategies: int                    # Total number of strategies in session

    # Same as SignalGenerated:
    signals_data: dict[str, Any]             # Strategy signals (single strategy)
    consolidated_portfolio: dict[str, Any]   # Partial portfolio (sum < 1.0)
    signal_count: int
    metadata: dict[str, Any]
```

**Logic Changes**:
```python
def lambda_handler(event, context):
    # Detect if triggered by Coordinator (single-file mode)
    if "session_id" in event and "dsl_file" in event:
        # SINGLE-FILE MODE (new)
        session_id = event["session_id"]
        correlation_id = event["correlation_id"]
        dsl_file = event["dsl_file"]
        allocation = Decimal(str(event["allocation"]))
        total_strategies = event["total_strategies"]

        # Override settings to evaluate ONLY this file
        temp_settings = Settings(
            dsl_files=[dsl_file],
            dsl_allocations={dsl_file: float(allocation)}
        )

        # Generate signals for this single file (existing DSL engine logic)
        handler = SignalGenerationHandler(...)
        signals = handler.generate_signals(temp_settings)

        # Build PartialSignalGenerated event
        partial_signal = PartialSignalGenerated(
            event_id=generate_request_id(),
            correlation_id=correlation_id,
            causation_id=session_id,
            timestamp=datetime.now(UTC),
            source_module="strategy_v2",
            source_component="StrategyWorker",

            session_id=session_id,
            dsl_file=dsl_file,
            allocation=allocation,
            strategy_number=event.get("strategy_number", 0),
            total_strategies=total_strategies,

            signals_data=signals.signals_data,
            consolidated_portfolio=signals.consolidated_portfolio.to_dict(),
            signal_count=signals.signal_count,
            metadata={"single_file_mode": True}
        )

        # Publish to EventBridge (triggers Aggregator)
        publish_to_eventbridge(partial_signal)

        return {"statusCode": 200, "session_id": session_id}

    else:
        # LEGACY MODE (all strategies in single invocation)
        # Existing logic unchanged - for backward compatibility
        # This path used when triggered by EventBridge schedule directly
        ...
```

**Backward Compatibility**:
- Direct EventBridge schedule invocations continue to work (single SignalGenerated)
- Single-file mode only activated when invoked by Coordinator with specific payload
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
        dsl_file=partial_signal.dsl_file,
        consolidated_portfolio=partial_signal.consolidated_portfolio,
        signals_data=partial_signal.signals_data,
        allocation=partial_signal.allocation
    )

    # 2. Check if all strategies completed (atomic increment)
    session = get_aggregation_session(partial_signal.session_id)
    completed_count = increment_completed_strategies(session_id)

    if completed_count < session.total_strategies:
        logger.info(
            f"Waiting for more strategies: {completed_count}/{session.total_strategies}",
            session_id=session_id,
            completed=completed_count,
            total=session.total_strategies
        )
        return  # Not ready yet

    # 3. All strategies complete - aggregate!
    logger.info(f"All strategies completed, starting aggregation", session_id=session_id)
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
        metadata={
            "aggregation_session_id": session_id,
            "strategies_aggregated": len(all_partial_signals)
        }
    )

    publish_to_eventbridge(signal_generated)

    # 7. Mark session as completed
    update_session_status(session_id, "COMPLETED")

    logger.info(
        f"Aggregation completed successfully",
        session_id=session_id,
        total_strategies=len(all_partial_signals),
        total_signals=signal_generated.signal_count
    )
```

**Portfolio Merging**:
```python
def merge_portfolios(partial_signals: list[PartialSignalGenerated]) -> ConsolidatedPortfolio:
    """
    Merge multiple partial portfolios (one per strategy file) into one consolidated portfolio.

    Example:
        Strategy 1 (KLM.clj, weight=0.5): {"AAPL": 1.0} → scaled: {"AAPL": 0.5}
        Strategy 2 (momentum.clj, weight=0.3): {"SPY": 1.0} → scaled: {"SPY": 0.3}
        Strategy 3 (mean_rev.clj, weight=0.2): {"TSLA": 1.0} → scaled: {"TSLA": 0.2}
        Merged: {"AAPL": 0.5, "SPY": 0.3, "TSLA": 0.2} (total: 1.0)

    Note: Each strategy already returns a scaled portfolio (allocation applied by DSL engine),
    so we just need to sum across all strategies.
    """
    merged_allocations: dict[str, Decimal] = {}

    for partial in partial_signals:
        portfolio = ConsolidatedPortfolio.from_json_dict(
            partial.consolidated_portfolio
        )

        for symbol, weight in portfolio.target_allocations.items():
            if symbol in merged_allocations:
                # Symbol appears in multiple strategies - sum their allocations
                logger.info(
                    f"Symbol {symbol} in multiple strategies, summing weights",
                    symbol=symbol,
                    previous_weight=merged_allocations[symbol],
                    adding_weight=weight,
                    strategy=partial.dsl_file
                )
                merged_allocations[symbol] += weight
            else:
                merged_allocations[symbol] = weight

    # Validate total allocation
    total = sum(merged_allocations.values())
    if not (Decimal("0.99") <= total <= Decimal("1.01")):
        raise AggregationError(
            f"Invalid total allocation: {total}. "
            f"Expected ~1.0. Allocations: {merged_allocations}"
        )

    # Collect source strategy names
    source_strategies = [p.dsl_file for p in partial_signals]

    return ConsolidatedPortfolio(
        target_allocations=merged_allocations,
        correlation_id=partial_signals[0].correlation_id,
        timestamp=datetime.now(UTC),
        strategy_count=len(partial_signals),
        source_strategies=source_strategies
    )
```

**Error Handling**:
```python
# Timeout handling (DynamoDB TTL + CloudWatch rule)
if session.timeout_at < datetime.now(UTC):
    logger.error(
        f"Aggregation session {session_id} timed out",
        session_id=session_id,
        completed=session.completed_strategies,
        total=session.total_strategies
    )
    publish_to_eventbridge(WorkflowFailed(
        correlation_id=session.correlation_id,
        error_message=f"Aggregation timeout after {AGGREGATION_TIMEOUT_SECONDS}s",
        error_type="AggregationTimeout"
    ))
    update_session_status(session_id, "FAILED")
    return

# Strategy failure handling
# Note: Individual strategy failures are handled by publishing WorkflowFailed from Strategy Lambda
# Aggregator will timeout if not all strategies report back
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
    "total_strategies": 4,
    "completed_strategies": 0,
    ...
})

# 2. Store partial signal (atomic, idempotent)
update_item(
    Key={"PK": "SESSION#abc123", "SK": "STRATEGY#KLM.clj"},
    UpdateExpression="SET consolidated_portfolio = :portfolio, signals_data = :signals, ...",
    ConditionExpression="attribute_not_exists(SK)"  # Prevents duplicate processing
)

# 3. Increment completed counter (atomic)
update_item(
    Key={"PK": "SESSION#abc123", "SK": "METADATA"},
    UpdateExpression="ADD completed_strategies :one",
    ExpressionAttributeValues={":one": 1},
    ReturnValues="UPDATED_NEW"
)

# 4. Get all partial signals (single query)
query(
    KeyConditionExpression="PK = :session AND begins_with(SK, 'STRATEGY#')",
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
class PartialSignalGenerated(BaseEvent):
    """Signals from a single strategy file."""
    event_type: str = "PartialSignalGenerated"
    schema_version: str = "1.0.0"

    session_id: str                          # Aggregation session ID
    dsl_file: str                            # Strategy file name (e.g., "KLM.clj")
    allocation: Decimal                      # File allocation weight (0-1)
    strategy_number: int                     # Order index (for debugging)
    total_strategies: int                    # Total strategies in session

    signals_data: dict[str, Any]             # Strategy signals (single file)
    consolidated_portfolio: dict[str, Any]   # Partial portfolio (sum < 1.0)
    signal_count: int
    metadata: dict[str, Any]


@dataclass(frozen=True)
class AggregationCompleted(BaseEvent):
    """All strategies aggregated successfully (internal event)."""
    event_type: str = "AggregationCompleted"
    schema_version: str = "1.0.0"

    session_id: str
    total_strategies: int
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
          AGGREGATION_TIMEOUT_SECONDS: 600
          AGGREGATION_SESSIONS_TABLE: !Ref AggregationSessionsTable
          STRATEGY_LAMBDA_FUNCTION_NAME: !Ref StrategyFunction
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref AggregationSessionsTable
        - LambdaInvokePolicy:
            FunctionName: !Ref StrategyFunction
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
      Environment:
        Variables:
          # Add any needed env vars for single-file mode
          SINGLE_FILE_MODE_ENABLED: "true"
      Events:
        # REMOVE DailySchedule (moved to Coordinator)
        # DailySchedule: ...  ← DELETE THIS

        # Strategy Lambda is now invoked directly by Coordinator (no EventBridge trigger needed)
        # It still listens for PartialSignalGenerated to publish to EventBridge
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

### New Config (Multi-Node, One Invocation Per File)
```python
# Settings (same as before)
dsl_files = ["KLM.clj", "momentum.clj", "mean_reversion.clj", "breakout.clj"]
dsl_allocations = {
    "KLM.clj": 0.25,
    "momentum.clj": 0.25,
    "mean_reversion.clj": 0.25,
    "breakout.clj": 0.25
}

# Coordinator automatically invokes Strategy Lambda once per file (4 parallel invocations):
# Invocation 1: KLM.clj (0.25)
# Invocation 2: momentum.clj (0.25)
# Invocation 3: mean_reversion.clj (0.25)
# Invocation 4: breakout.clj (0.25)

# All 4 run concurrently, results aggregated by Aggregator Lambda
```

---

## Performance Characteristics

### Single Lambda (Current)
- **Execution time**: T_strategy * N_strategies (sequential) or T_strategy (parallel with max_workers)
- **Memory**: Proportional to N_strategies
- **Cost**: 1 Lambda invocation
- **Limit**: ~100 strategies max (memory/timeout constraints)

### Multi-Node (Proposed)
- **Execution time**: ~T_strategy (all strategies run in parallel)
- **Memory per invocation**: Proportional to single strategy complexity
- **Cost**: N_strategies + 1 (coordinator) + 1 (aggregator) Lambda invocations
- **Limit**: Up to Lambda account concurrency limit (default 1000, can increase to 10,000+)

**Example**: 100 strategies
- Current: 1 Lambda, 10GB memory, 5+ minutes
- Proposed: 100 parallel Lambdas, 512MB each, ~30 seconds + aggregation overhead (~5s)

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
- StrategyExecutionDuration (ms per strategy file)
- ConcurrentStrategyInvocations (gauge)
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

# Strategy failure alarm
StrategyFailureAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    MetricName: StrategyLambdaErrors
    Threshold: 3
    ComparisonOperator: GreaterThanOrEqualToThreshold
    EvaluationPeriods: 1
    AlarmActions:
      - !Ref DLQAlertTopic
```

### Logs Insights Queries
```sql
-- Aggregation session timeline
fields @timestamp, message, session_id, dsl_file, completed_strategies, total_strategies
| filter source_module = "aggregator_v2"
| sort @timestamp asc

-- Failed strategies
fields @timestamp, correlation_id, dsl_file, error
| filter event_type = "WorkflowFailed" and source_module = "strategy_v2"
| stats count() by dsl_file

-- Aggregation duration
fields @timestamp, session_id, duration_ms, total_strategies
| filter message = "Aggregation completed"
| stats avg(duration_ms), max(duration_ms), min(duration_ms) by total_strategies

-- Strategy execution times
fields @timestamp, dsl_file, duration_ms
| filter source_module = "strategy_v2" and message = "Strategy completed"
| stats avg(duration_ms), max(duration_ms), min(duration_ms) by dsl_file
```

---

## Error Scenarios & Recovery

### Scenario 1: One Strategy Fails
**Detection**: PartialSignalGenerated event not received for strategy file
**Recovery**:
1. Aggregator times out after 10 minutes
2. Publishes WorkflowFailed event
3. Notifications Lambda sends alert email
4. Operator investigates failed strategy in CloudWatch Logs
5. Can manually re-invoke specific strategy Lambda or full session

### Scenario 2: Aggregator Lambda Fails
**Detection**: SignalGenerated event not published after all strategies complete
**Recovery**:
1. EventBridge retries PartialSignalGenerated delivery (up to 2x)
2. If still failing, message goes to DLQ
3. DLQ alarm triggers SNS notification
4. Operator investigates DLQ, can manually trigger aggregator

### Scenario 3: Partial Signals Exceed Timeout
**Detection**: DynamoDB session shows TIMEOUT status
**Recovery**:
1. CloudWatch alarm fires on AggregationSessionsFailed metric
2. Operator reviews which strategies didn't complete
3. Can manually invoke missing strategy Lambdas with same session_id
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
# Test coordinator invocation logic
def test_coordinator_invokes_lambda_per_strategy():
    strategies = ["A.clj", "B.clj", "C.clj"]
    allocations = {"A.clj": 0.33, "B.clj": 0.33, "C.clj": 0.34}

    with mock.patch('boto3.client') as mock_lambda:
        invoke_all_strategies(strategies, allocations, session_id="test-123")

        # Should invoke Lambda 3 times (once per strategy)
        assert mock_lambda.return_value.invoke.call_count == 3

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
# Test end-to-end flow with 4 strategies
@pytest.mark.integration
def test_multi_strategy_signal_aggregation():
    # 1. Invoke Coordinator
    coordinator_response = invoke_coordinator_lambda({
        "dsl_files": ["A.clj", "B.clj", "C.clj", "D.clj"],
        "dsl_allocations": {"A.clj": 0.25, "B.clj": 0.25, "C.clj": 0.25, "D.clj": 0.25}
    })
    session_id = coordinator_response["session_id"]

    # 2. Wait for all strategies to complete
    wait_for_condition(
        lambda: get_session_status(session_id) == "COMPLETED",
        timeout=120
    )

    # 3. Verify 4 PartialSignalGenerated events published
    partial_events = get_eventbridge_events("PartialSignalGenerated")
    assert len(partial_events) == 4
    assert all(e.session_id == session_id for e in partial_events)

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
# Test 100 strategies running in parallel
@pytest.mark.load
def test_large_scale_parallel_execution():
    strategies = [f"strategy_{i}.clj" for i in range(100)]
    allocations = {s: 0.01 for s in strategies}  # Equal weight

    start_time = time.time()

    session_id = invoke_coordinator({
        "dsl_files": strategies,
        "dsl_allocations": allocations
    })

    wait_for_completion(session_id, timeout=300)

    duration = time.time() - start_time
    assert duration < 60  # Should complete in under 1 minute (parallel execution)

    # Verify no data loss
    final_signal = get_final_signal_event(session_id)
    assert len(final_signal.consolidated_portfolio) <= 100  # May have duplicate symbols
    assert abs(sum(final_signal.consolidated_portfolio.values()) - 1.0) < 0.01
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
Assuming 50 strategies (50 parallel invocations):
- **Coordinator Lambda**: 1 invocation/day × 512MB × 10s = ~$0.001/day
- **Strategy Lambda**: 50 invocations/day × 512MB × 30s = ~$0.05/day
- **Aggregator Lambda**: 1 invocation/day × 1GB × 5s = ~$0.001/day
- **DynamoDB**: Minimal (50 writes + 1 query per day)
- **Total**: ~$15/month

**Cost increase**: 5x (but handles 50x more strategies)

### At Scale (500 strategies, 500 parallel invocations)
- **Strategy Lambda**: 500 invocations/day × 512MB × 30s = ~$0.50/day
- **Total**: ~$150/month (handles 500x more strategies than single Lambda)

**Note**: Lambda has a default account concurrency limit of 1000. For 500+ concurrent invocations, ensure:
- Reserve capacity for other Lambdas in your account
- Request limit increase if needed (up to 10,000+)

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

This scaling plan enables **horizontal scaling of strategy execution using AWS Lambda's natural concurrency** while maintaining **backward compatibility** and **minimal changes to existing components**.

### Key Benefits
✅ **Scalable**: Handle 1000s of strategies with parallel Lambda invocations (limited only by account concurrency)
✅ **Simple**: One Lambda invocation per strategy file - no complex batching logic
✅ **Reliable**: Atomic aggregation with DynamoDB, built-in retries, idempotent operations
✅ **Observable**: Full event traceability, CloudWatch metrics and alarms
✅ **Cost-effective**: Pay only for what you use, linear cost scaling
✅ **Maintainable**: Clear separation of concerns, single-responsibility Lambdas
✅ **Backward compatible**: Existing flow still works during migration
✅ **Natural AWS pattern**: Leverages Lambda's strengths (concurrency, auto-scaling)

### Next Steps
1. Review and approve this plan
2. Create feature branch: `feature/multi-node-strategy-scaling`
3. Implement Phase 1 (infrastructure)
4. Deploy to dev environment for testing
5. Iterate based on findings
6. Production rollout

---

**Questions or feedback?** This is a living document - please provide input before implementation begins.
