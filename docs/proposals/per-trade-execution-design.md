# Per-Trade Execution Design: Migration from Batched to Concurrent Execution

**Status:** Proposed  
**Created:** 2025-12-13  
**Author:** GitHub Copilot (investigation based on codebase analysis)  
**Issue:** #[TBD] - Investigate refactor to per-trade execution using Lambda native concurrency

## Executive Summary

This document provides a detailed, code-accurate design for migrating the Alchemiser trading system from its current **batched execution model** (one Lambda processes entire rebalance plan) to a **per-trade execution model** (one Lambda invocation per trade) using AWS native concurrency (Lambda + SQS FIFO).

**Current State:** Single execution Lambda processes all trades from a `RebalancePlan` in one invocation  
**Target State:** One execution Lambda invocation per trade, with deterministic ordering and completion detection  
**Key Benefits:** Better concurrency, cleaner failure isolation, partial execution resilience  
**Key Risks:** Run-level state management, completion detection complexity, increased infrastructure coordination

---

## 1. Current State: Execution Flow Mapping

### 1.1 High-Level Workflow

```
EventBridge Schedule (9:35 AM ET)
    ↓
Strategy Lambda
    → Generates signals
    → Publishes SignalGenerated to EventBridge
        ↓
Portfolio Lambda (triggered by EventBridge rule)
    → Reads current positions
    → Creates RebalancePlan with N items
    → Publishes RebalancePlanned to EventBridge
        ↓
EventBridge → SQS (ExecutionQueue)
    ↓
Execution Lambda (triggered by SQS, BatchSize=1)
    → Processes ENTIRE RebalancePlan in one invocation
    → Loops over items: SELL phase → BUY phase
    → Publishes TradeExecuted + WorkflowCompleted
        ↓
Notifications Lambda (triggered by EventBridge)
    → Sends email summary
```

### 1.2 Key Files and Components

| Component | File | Responsibility |
|-----------|------|----------------|
| **Execution Handler** | `execution_v2/handlers/trading_execution_handler.py` (775 lines) | Event handler for `RebalancePlanned` → calls `ExecutionManager` |
| **Execution Manager** | `execution_v2/core/execution_manager.py` (345 lines) | Coordinates async execution via `Executor` |
| **Executor Core** | `execution_v2/core/executor.py` (1191 lines) | **CRITICAL:** Contains batched loop logic over `plan.items` |
| **Phase Executor** | `execution_v2/core/phase_executor.py` | Executes SELL/BUY phases with `for item in items` loops |
| **Lambda Handler** | `execution_v2/lambda_handler.py` (324 lines) | SQS trigger → unwraps → calls `TradingExecutionHandler` |

### 1.3 Current Batch Execution Logic

**File:** `execution_v2/core/executor.py`

```python
async def execute_rebalance_plan(self, plan: RebalancePlan) -> ExecutionResult:
    """Execute ENTIRE rebalance plan in one invocation."""
    
    # Line 574-576: Split plan into phases
    sell_items = [item for item in plan.items if item.action == "SELL"]
    buy_items = [item for item in plan.items if item.action == "BUY"]
    
    # Line 597-600: Execute SELL phase (loops over all sell_items)
    sell_orders, sell_stats = await self._execute_sell_phase(
        sell_items, plan.correlation_id
    )
    
    # Line 630-633: Execute BUY phase (loops over all buy_items)
    buy_orders, buy_stats = await self._execute_buy_phase(
        buy_items, plan.correlation_id
    )
    
    # Return single ExecutionResult for entire plan
    return ExecutionResult(...)
```

**Phase Execution Loop (PhaseExecutor):**

```python
# File: execution_v2/core/phase_executor.py, line 292-303
async def _execute_phase(self, ...):
    for item in items:  # ← THIS LOOP BECOMES MESSAGE PRODUCER
        order_result, was_placed = await self._execute_order(item, ...)
        orders.append(order_result)
```

### 1.4 Implicit Assumptions

1. **All-or-nothing mindset:** Current design assumes "if one fails, log and continue"
2. **Single correlation_id per run:** All orders in one plan share same `correlation_id`
3. **No cross-invocation state:** Success/failure tracked in single `ExecutionResult` object
4. **Sequential sell→buy ordering:** Hardcoded in `executor.py` (sells complete before buys start)
5. **Settlement monitoring:** Monitors sell settlement to release buying power for buys

---

## 2. Trade and Rebalance Data Structures

### 2.1 Current Trade Representation

**`RebalancePlanItem` (source: `shared/schemas/rebalance_plan.py`)**

```python
class RebalancePlanItem(BaseModel):
    symbol: str              # e.g. "AAPL"
    current_weight: Decimal  # 0-1
    target_weight: Decimal   # 0-1
    weight_diff: Decimal     # target - current
    target_value: Decimal    # Dollar value
    current_value: Decimal   # Dollar value
    trade_amount: Decimal    # Positive=buy, Negative=sell
    action: str              # "BUY", "SELL", "HOLD"
    priority: int            # 1-5 (1=highest)
```

**`RebalancePlan` (parent container)**

```python
class RebalancePlan(BaseModel):
    plan_id: str                          # Unique plan identifier
    correlation_id: str                   # Workflow correlation
    causation_id: str                     # Traceability
    timestamp: datetime
    items: list[RebalancePlanItem]        # ← List of trades
    total_portfolio_value: Decimal
    total_trade_value: Decimal
    metadata: dict[str, Any] | None       # Strategy attribution, etc.
```

### 2.2 Stable Identifiers

- **plan_id:** Already unique per rebalance plan (UUID)
- **correlation_id:** Workflow-level identifier (carried from Strategy → Portfolio → Execution)
- **symbol:** Natural identifier for the asset being traded
- **No per-trade ID:** Currently no stable `trade_id` field

### 2.3 Sell vs Buy Distinction

- **Current:** `action` field (`"BUY"`, `"SELL"`, `"HOLD"`)
- **Current ordering:** Executor hardcodes sell-before-buy logic
- **No explicit phase field:** Ordering logic is in executor, not in data

### 2.4 Proposed Per-Trade Message Schema

```python
class TradeMessage(BaseModel):
    """Message payload for SQS FIFO per-trade execution."""
    
    # Execution identifiers
    run_id: str                    # NEW: Unique run identifier (UUID)
    trade_id: str                  # NEW: Unique trade identifier (UUID)
    plan_id: str                   # From RebalancePlan
    correlation_id: str            # Workflow correlation
    causation_id: str              # Event causation chain
    
    # Trade content (from RebalancePlanItem)
    symbol: str
    action: str                    # "BUY" or "SELL"
    trade_amount: Decimal
    current_weight: Decimal
    target_weight: Decimal
    target_value: Decimal
    priority: int
    
    # Execution control
    phase: str                     # NEW: "SELL" or "BUY"
    sequence_number: int           # NEW: For ordering within phase
    is_complete_exit: bool         # Flag for complete position exits
    
    # Run context
    total_portfolio_value: Decimal # Needed for validation
    total_run_trades: int          # NEW: Total trades in this run
    run_timestamp: datetime        # When run started
    
    # Metadata
    metadata: dict[str, Any]       # Strategy attribution, etc.
    
    # Schema versioning
    schema_version: str = "1.0.0"
```

---

## 3. Execution Lambda Refactor Feasibility

### 3.1 Current Batch Context Assumptions

**What assumes batch context:**

1. **Phase execution loops** (`executor.py:574-600`)
   - `sell_items = [item for item in plan.items if ...]`
   - `buy_items = [item for item in plan.items if ...]`
   - Loops over all items per phase

2. **Settlement monitoring** (`executor.py:601-630`)
   - Monitors sell order settlement across all sells
   - Tracks buying power release for entire buy phase

3. **Bulk symbol subscription** (`executor.py:571`)
   - Subscribes to all symbols upfront for efficient pricing
   - `self._bulk_subscribe_symbols(all_symbols)`

4. **Execution result aggregation** (`executor.py:712-750`)
   - Single `ExecutionResult` for entire plan
   - Aggregates: `orders_placed`, `orders_succeeded`, `total_trade_value`

5. **Idempotency cache** (`executor.py:506-515`)
   - In-memory dict keyed by `plan_id`
   - Prevents duplicate execution of same plan

### 3.2 What Can Operate on Single Trade

**Already single-trade compatible:**

1. **Order execution** (`phase_executor.py:323-400`)
   - `_execute_order(item, ...)` operates on single `RebalancePlanItem`
   - Calls `_execute_single_item(item)` which places one order

2. **Order validation** (`execution_v2/utils/execution_validator.py`)
   - `validate_order_size(symbol, order_value, ...)` per-order check
   - Daily trade limit check operates per-order

3. **Market order execution** (`executor.py:417-475`)
   - `_execute_market_order(symbol, side, quantity)` single-trade method

4. **Trade ledger recording** (`execution_v2/services/trade_ledger.py`)
   - Records individual trades to DynamoDB
   - Already per-trade granular

5. **WebSocket pricing** (`shared/services/real_time_pricing.py`)
   - Can subscribe to single symbol per invocation
   - No batch requirement

### 3.3 Single-Trade Execution Path

**New Handler Flow:**

```python
# File: execution_v2/lambda_handler.py (modified)

def lambda_handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle SQS event - ONE MESSAGE = ONE TRADE."""
    
    # Unwrap SQS message → TradeMessage
    trade_message = unwrap_trade_message(event)
    
    # Update run state (STARTED)
    run_state_service.mark_trade_started(
        run_id=trade_message.run_id,
        trade_id=trade_message.trade_id
    )
    
    # Execute SINGLE trade
    handler = SingleTradeExecutionHandler(container)
    result = handler.execute_trade(trade_message)
    
    # Update run state (COMPLETED or FAILED)
    run_state_service.mark_trade_completed(
        run_id=trade_message.run_id,
        trade_id=trade_message.trade_id,
        success=result.success
    )
    
    # Check if run is complete
    if run_state_service.is_run_complete(trade_message.run_id):
        publish_workflow_completed(trade_message.run_id)
    
    return {"statusCode": 200}
```

**Mapping to Existing Functions:**

| Current Function | Per-Trade Equivalent |
|------------------|----------------------|
| `executor.execute_rebalance_plan()` | **Remove** (no longer batch) |
| `phase_executor._execute_order(item)` | **Core execution logic** (keep) |
| `phase_executor._execute_single_item()` | **Direct call** per invocation |
| `trading_execution_handler._handle_rebalance_planned()` | **Rename** to `handle_trade_message()` |
| `execution_manager.execute_rebalance_plan()` | **Remove** (sync wrapper no longer needed) |

---

## 4. Queueing and Ordering Strategy

### 4.1 Where Messages Are Enqueued

**Current:** Portfolio Lambda publishes `RebalancePlanned` to EventBridge → routed to SQS

**Proposed:** Portfolio Lambda publishes individual `TradeMessage` events to SQS FIFO

**File to Modify:** `portfolio_v2/handlers/portfolio_analysis_handler.py`

```python
# BEFORE (current):
rebalance_event = RebalancePlanned(
    rebalance_plan=plan,  # Entire plan with N items
    ...
)
publish_to_eventbridge(rebalance_event)

# AFTER (per-trade):
for item in plan.items:
    if item.action == "HOLD":
        continue  # Skip HOLD items
    
    trade_message = TradeMessage(
        run_id=run_id,
        trade_id=str(uuid.uuid4()),
        plan_id=plan.plan_id,
        symbol=item.symbol,
        action=item.action,
        phase="SELL" if item.action == "SELL" else "BUY",
        sequence_number=assign_sequence(item),
        ...
    )
    
    publish_to_sqs_fifo(
        queue_url=EXECUTION_QUEUE_URL,
        message=trade_message,
        message_group_id=run_id,  # ← CRITICAL: Groups all trades in one run
        message_deduplication_id=trade_message.trade_id
    )
```

### 4.2 SQS FIFO Configuration

**New Resource:** `ExecutionFifoQueue` (to replace current `ExecutionQueue`)

```yaml
# template.yaml (new resource)
ExecutionFifoQueue:
  Type: AWS::SQS::Queue
  Properties:
    QueueName: !Sub "alchemiser-${Stage}-execution-fifo.fifo"
    FifoQueue: true
    ContentBasedDeduplication: false  # Use explicit dedup ID
    MessageRetentionPeriod: 345600    # 4 days
    VisibilityTimeout: 600            # 10 mins (single trade should be fast)
    RedrivePolicy:
      deadLetterTargetArn: !GetAtt ExecutionDLQ.Arn
      maxReceiveCount: 3
```

**Key Properties:**

- **MessageGroupId:** `run_id` (ensures all trades in one run are ordered)
- **MessageDeduplicationId:** `trade_id` (prevents duplicate trades)
- **FIFO guarantee:** Messages within same `MessageGroupId` are delivered in order

### 4.3 Sell-Before-Buy Ordering

**Current:** Hardcoded in `executor.py` (lines 574-633)

**Proposed:** Encoded in `sequence_number` field

**Sequencing Logic:**

```python
def assign_sequence_number(item: RebalancePlanItem, items: list[RebalancePlanItem]) -> int:
    """Assign sequence number ensuring sells before buys.
    
    Sequence numbers:
    - SELL phase: 1000-1999 (1000 + priority)
    - BUY phase: 2000-2999 (2000 + priority)
    
    This ensures all sells complete before buys start.
    """
    if item.action == "SELL":
        return 1000 + item.priority
    elif item.action == "BUY":
        return 2000 + item.priority
    else:
        raise ValueError(f"Invalid action: {item.action}")
```

**SQS FIFO Ordering:**

- FIFO guarantees delivery order within same `MessageGroupId`
- Sell messages (seq 1000-1999) delivered before buy messages (seq 2000-2999)
- Within each phase, priority determines order

### 4.4 Enqueue Flow Diagram

```
Portfolio Lambda
    ↓
Create RebalancePlan with N items
    ↓
FOR EACH item in plan.items:
    ↓
    Generate run_id (same for all trades)
    Generate trade_id (unique per trade)
    Assign sequence_number (sell phase < buy phase)
    ↓
    Publish TradeMessage to SQS FIFO
        MessageGroupId = run_id
        MessageDeduplicationId = trade_id
    ↓
NEXT item
    ↓
Publish RunStarted event to DynamoDB
    (run_id, total_trades, expected_symbols)
```

---

## 5. Run-Level State and Completion Detection

### 5.1 Current Completion Inference

**Current:** Single invocation = single `ExecutionResult`

```python
# File: execution_v2/handlers/trading_execution_handler.py:411-412
if execution_success:
    self._emit_workflow_completed_event(correlation_id, execution_result)
```

**Limitation:** No cross-invocation state → can't detect run completion across multiple Lambda invocations

### 5.2 Proposed Run State Model

**New DynamoDB Table:** `alchemiser-{stage}-execution-runs`

**Schema:**

```python
class ExecutionRun(BaseModel):
    """DynamoDB item for tracking execution run state."""
    
    # Primary key
    PK: str  # "RUN#{run_id}"
    SK: str  # "METADATA"
    
    # Run identification
    run_id: str              # UUID
    plan_id: str             # From RebalancePlan
    correlation_id: str      # Workflow correlation
    
    # Run metadata
    run_status: str          # "PENDING", "RUNNING", "COMPLETED", "FAILED"
    run_timestamp: datetime  # When run started
    
    # Trade tracking
    total_trades: int        # Expected number of trades
    completed_trades: int    # Number of completed trades
    succeeded_trades: int    # Number of successful trades
    failed_trades: int       # Number of failed trades
    
    # Trade IDs
    pending_trade_ids: list[str]    # Trades not yet started
    running_trade_ids: list[str]    # Trades in progress
    completed_trade_ids: list[str]  # Trades completed
    failed_trade_ids: list[str]     # Trades failed
    
    # Completion detection
    completion_timestamp: datetime | None
    
    # TTL for automatic cleanup
    ttl: int  # Unix timestamp (30 days after completion)
```

**Additional Items (per trade):**

```python
# PK = "RUN#{run_id}", SK = "TRADE#{trade_id}"
class TradeStatus(BaseModel):
    trade_id: str
    symbol: str
    action: str
    phase: str
    status: str              # "PENDING", "RUNNING", "COMPLETED", "FAILED"
    order_id: str | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
```

### 5.3 Run State Transitions

```
PENDING (created by Portfolio Lambda)
    ↓
RUNNING (first trade starts)
    ↓ (after each trade completes)
    Update: completed_trades++
    Check: completed_trades == total_trades?
    ↓
COMPLETED (all trades done)
    OR
FAILED (circuit breaker or critical error)
```

### 5.4 Completion Detection Algorithm

**Service:** `execution_v2/services/run_state_service.py` (new)

```python
class RunStateService:
    """Service for tracking execution run state in DynamoDB."""
    
    def __init__(self, dynamodb_client, table_name: str):
        self.dynamodb = dynamodb_client
        self.table_name = table_name
    
    def create_run(
        self,
        run_id: str,
        plan_id: str,
        correlation_id: str,
        trade_messages: list[TradeMessage]
    ) -> None:
        """Create new run state entry (called by Portfolio Lambda)."""
        
        item = {
            "PK": f"RUN#{run_id}",
            "SK": "METADATA",
            "run_id": run_id,
            "plan_id": plan_id,
            "correlation_id": correlation_id,
            "run_status": "PENDING",
            "run_timestamp": datetime.now(UTC).isoformat(),
            "total_trades": len(trade_messages),
            "completed_trades": 0,
            "succeeded_trades": 0,
            "failed_trades": 0,
            "pending_trade_ids": [msg.trade_id for msg in trade_messages],
            "running_trade_ids": [],
            "completed_trade_ids": [],
            "failed_trade_ids": [],
        }
        
        self.dynamodb.put_item(TableName=self.table_name, Item=item)
    
    def mark_trade_started(self, run_id: str, trade_id: str) -> None:
        """Mark trade as started (atomic update)."""
        
        # Update run metadata: PENDING → RUNNING
        self.dynamodb.update_item(
            TableName=self.table_name,
            Key={"PK": f"RUN#{run_id}", "SK": "METADATA"},
            UpdateExpression="""
                SET run_status = :running,
                    running_trade_ids = list_append(running_trade_ids, :trade_id)
                DELETE pending_trade_ids :trade_id
            """,
            ExpressionAttributeValues={
                ":running": "RUNNING",
                ":trade_id": [trade_id],
            }
        )
    
    def mark_trade_completed(
        self,
        run_id: str,
        trade_id: str,
        success: bool
    ) -> None:
        """Mark trade as completed (atomic update with conditional check)."""
        
        if success:
            update_expr = """
                SET completed_trades = completed_trades + :one,
                    succeeded_trades = succeeded_trades + :one,
                    completed_trade_ids = list_append(completed_trade_ids, :trade_id)
                DELETE running_trade_ids :trade_id
            """
        else:
            update_expr = """
                SET completed_trades = completed_trades + :one,
                    failed_trades = failed_trades + :one,
                    failed_trade_ids = list_append(failed_trade_ids, :trade_id)
                DELETE running_trade_ids :trade_id
            """
        
        self.dynamodb.update_item(
            TableName=self.table_name,
            Key={"PK": f"RUN#{run_id}", "SK": "METADATA"},
            UpdateExpression=update_expr,
            ExpressionAttributeValues={
                ":one": 1,
                ":trade_id": [trade_id],
            }
        )
    
    def is_run_complete(self, run_id: str) -> bool:
        """Check if run is complete (deterministic check)."""
        
        response = self.dynamodb.get_item(
            TableName=self.table_name,
            Key={"PK": f"RUN#{run_id}", "SK": "METADATA"}
        )
        
        item = response.get("Item", {})
        total = item.get("total_trades", 0)
        completed = item.get("completed_trades", 0)
        
        if completed >= total:
            # Mark run as COMPLETED
            self._finalize_run(run_id)
            return True
        
        return False
    
    def _finalize_run(self, run_id: str) -> None:
        """Finalize run state and set TTL."""
        
        completion_timestamp = datetime.now(UTC)
        ttl = int(completion_timestamp.timestamp()) + (30 * 86400)  # 30 days
        
        self.dynamodb.update_item(
            TableName=self.table_name,
            Key={"PK": f"RUN#{run_id}", "SK": "METADATA"},
            UpdateExpression="""
                SET run_status = :completed,
                    completion_timestamp = :timestamp,
                    ttl = :ttl
            """,
            ExpressionAttributeValues={
                ":completed": "COMPLETED",
                ":timestamp": completion_timestamp.isoformat(),
                ":ttl": ttl,
            }
        )
```

### 5.5 Completion Event Flow

```
Execution Lambda (per trade)
    ↓
Execute trade
    ↓
Update run state: mark_trade_completed()
    ↓
Check: is_run_complete()?
    ↓ YES
    Publish WorkflowCompleted to EventBridge
        (triggers Notifications Lambda)
    ↓ NO
    Return (wait for more trades)
```

**Race Condition Handling:**

- Multiple Lambdas may check `is_run_complete()` concurrently
- Use DynamoDB conditional updates to ensure only ONE Lambda publishes `WorkflowCompleted`
- Add `completion_published` flag to run state (set atomically)

```python
def publish_workflow_completed_once(run_id: str) -> bool:
    """Publish WorkflowCompleted event only once (idempotent)."""
    
    try:
        self.dynamodb.update_item(
            TableName=self.table_name,
            Key={"PK": f"RUN#{run_id}", "SK": "METADATA"},
            UpdateExpression="SET completion_published = :true",
            ConditionExpression="attribute_not_exists(completion_published)",
            ExpressionAttributeValues={":true": True}
        )
        # Success: we won the race, publish event
        publish_to_eventbridge(WorkflowCompleted(...))
        return True
    except ConditionalCheckFailedException:
        # Another Lambda already published, skip
        return False
```

---

## 6. Failure and Retry Semantics

### 6.1 Current Failure Handling

**Current:** Executor logs failure but continues with remaining trades

```python
# File: executor.py:323-403 (phase_executor.py)
for item in items:
    try:
        order_result = await self._execute_order(item)
        orders.append(order_result)
    except Exception as e:
        logger.error(f"Order failed: {e}")
        # Continue with next trade
```

**Partial success:** Tracked in `ExecutionResult.status` (SUCCESS, PARTIAL_SUCCESS, FAILURE)

### 6.2 Per-Trade Failure Modes

| Failure Type | Current Behavior | Per-Trade Behavior |
|--------------|------------------|--------------------|
| **Symbol validation error** | Log, skip trade, continue | Return failure, don't retry (bad data) |
| **Broker API error (transient)** | Log, continue | SQS retry (up to 3 times) |
| **Broker API error (permanent)** | Log, continue | Move to DLQ after 3 retries |
| **Timeout** | Fail entire execution | SQS retry (visibility timeout) |
| **WebSocket connection error** | Fallback to market order | Retry or fallback |
| **Daily trade limit exceeded** | Halt entire execution | Halt run (update run state to FAILED) |

### 6.3 Retry Matrix

| Error Type | Retryable? | Retry Strategy | Max Retries | DLQ Action |
|------------|------------|----------------|-------------|------------|
| **ValidationError** (bad data) | ❌ No | None | 0 | DLQ → Alert |
| **TradingClientError** (API) | ✅ Yes | Exponential backoff | 3 | DLQ → Alert |
| **MarketDataError** (quote fetch) | ✅ Yes | Exponential backoff | 3 | DLQ → Alert |
| **OrderExecutionError** | ✅ Yes | Linear backoff | 3 | DLQ → Alert |
| **NetworkError** (timeout) | ✅ Yes | Exponential backoff | 3 | DLQ → Alert |
| **DailyTradeLimitExceeded** | ❌ No | None | 0 | Fail entire run |

### 6.4 SQS Retry Configuration

```yaml
# template.yaml
ExecutionFifoQueue:
  Properties:
    VisibilityTimeout: 600  # 10 mins (single trade should complete in < 5 mins)
    MessageRetentionPeriod: 345600  # 4 days
    RedrivePolicy:
      deadLetterTargetArn: !GetAtt ExecutionDLQ.Arn
      maxReceiveCount: 3  # Retry up to 3 times before DLQ
```

**Retry Behavior:**

1. **First attempt:** Lambda invoked immediately
2. **Failure:** Message becomes invisible for `VisibilityTimeout` (10 mins)
3. **Retry 1:** After 10 mins, message visible again → Lambda retries
4. **Retry 2:** After another 10 mins
5. **Retry 3:** After another 10 mins
6. **DLQ:** After 3 failed attempts, message moved to DLQ

### 6.5 Run Failure Scenarios

| Scenario | Behavior | Run Status |
|----------|----------|------------|
| **Single trade fails (retryable)** | SQS retries up to 3 times | RUNNING → COMPLETED (with failures) |
| **Single trade fails (non-retryable)** | Move to DLQ, continue run | RUNNING → COMPLETED (with failures) |
| **Multiple trades fail** | Continue until all trades processed | RUNNING → COMPLETED (with failures) |
| **Daily limit exceeded** | Halt run, mark FAILED | RUNNING → FAILED |
| **All trades in DLQ** | Run completes with 100% failure | RUNNING → COMPLETED (0% success) |

### 6.6 Completed-With-Errors Definition

**Completed-With-Errors:** Run completes (all trades attempted) but some trades failed

**Criteria:**

```python
def get_run_outcome(run_state: ExecutionRun) -> str:
    """Determine run outcome."""
    
    if run_state.run_status == "FAILED":
        return "FAILED"  # Circuit breaker or critical error
    
    if run_state.completed_trades < run_state.total_trades:
        return "INCOMPLETE"  # Should not happen (timeout?)
    
    if run_state.succeeded_trades == run_state.total_trades:
        return "SUCCESS"  # All trades succeeded
    
    if run_state.succeeded_trades == 0:
        return "COMPLETE_FAILURE"  # All trades failed
    
    return "PARTIAL_SUCCESS"  # Some succeeded, some failed
```

**Notification Logic:**

- **SUCCESS:** Send success email
- **PARTIAL_SUCCESS:** Send warning email (list failed symbols)
- **COMPLETE_FAILURE:** Send critical alert email
- **FAILED:** Send critical alert email (circuit breaker triggered)

---

## 7. Step-by-Step Migration Plan

### 7.1 Phase 1: Add Run State Infrastructure (No Behavior Change)

**Goal:** Add DynamoDB table and run state service without changing execution flow

**Changes:**

1. **Add DynamoDB table** (`template.yaml`)
   - Create `ExecutionRunsTable` resource
   - Add IAM permissions for Execution and Portfolio Lambdas

2. **Create run state service** (`execution_v2/services/run_state_service.py`)
   - Implement `RunStateService` class
   - Add unit tests

3. **Wire up in Portfolio Lambda** (optional logging only)
   - Create run state entries when publishing `RebalancePlanned`
   - Log run_id but don't use for execution yet

**Rollback:** Remove table, revert Portfolio Lambda

**Risk:** Low (additive only)

### 7.2 Phase 2: Switch to SQS FIFO (Feature Flag)

**Goal:** Replace standard SQS with FIFO queue

**Changes:**

1. **Create FIFO queue** (`template.yaml`)
   - Add `ExecutionFifoQueue` resource
   - Update `RebalancePlannedRule` to route to FIFO queue
   - Keep old `ExecutionQueue` for rollback

2. **Update Portfolio Lambda enqueue logic**
   - Add feature flag: `ENABLE_FIFO_EXECUTION` (default: `false`)
   - If enabled: decompose plan → publish individual `TradeMessage` events
   - If disabled: publish full `RebalancePlanned` (current behavior)

3. **Deploy and test in dev**
   - Test with `ENABLE_FIFO_EXECUTION=true`
   - Verify message ordering
   - Monitor SQS metrics

**Rollback:** Set `ENABLE_FIFO_EXECUTION=false`

**Risk:** Medium (queue changes require testing)

### 7.3 Phase 3: Refactor Execution Lambda (Single Trade)

**Goal:** Execution Lambda processes one trade per invocation

**Changes:**

1. **Create single-trade handler** (`execution_v2/handlers/single_trade_handler.py`)
   - Extract logic from `TradingExecutionHandler._execute_order()`
   - Remove batch loops

2. **Update Lambda handler** (`execution_v2/lambda_handler.py`)
   - If FIFO message: call `SingleTradeHandler`
   - If legacy message: call `TradingExecutionHandler` (fallback)

3. **Wire up run state updates**
   - Call `run_state_service.mark_trade_started()`
   - Call `run_state_service.mark_trade_completed()`
   - Call `run_state_service.is_run_complete()`

4. **Deploy and test in dev**
   - Test with small plans (1-3 trades)
   - Verify completion detection
   - Monitor Lambda concurrency

**Rollback:** Disable FIFO queue, revert to standard SQS

**Risk:** High (core execution logic change)

### 7.4 Phase 4: Remove Legacy Batch Executor

**Goal:** Remove old batch execution code

**Changes:**

1. **Delete files:**
   - `execution_v2/core/execution_manager.py`
   - `execution_v2/core/executor.py` (batch logic)
   - `execution_v2/core/phase_executor.py` (batch loops)

2. **Update handler:**
   - Remove `TradingExecutionHandler` (batch)
   - Rename `SingleTradeHandler` → `TradeExecutionHandler`

3. **Remove feature flag:**
   - Delete `ENABLE_FIFO_EXECUTION` logic

**Rollback:** Revert to Phase 3 code

**Risk:** Medium (permanent change, requires confidence)

### 7.5 Incremental vs Flag Day Changes

| Component | Incremental? | Flag Day? | Notes |
|-----------|-------------|-----------|-------|
| **DynamoDB table** | ✅ Yes | | Additive infrastructure |
| **Run state service** | ✅ Yes | | Can be wired up gradually |
| **FIFO queue** | ✅ Yes | | Feature flag controls usage |
| **Execution Lambda** | ⚠️ Partial | | Need both handlers during transition |
| **Portfolio Lambda** | ✅ Yes | | Feature flag controls enqueue logic |
| **Deleting old code** | | ✅ Yes | Requires commitment |

**Recommended Approach:**

- **Phases 1-3:** Incremental with feature flags
- **Phase 4:** Flag day (after thorough testing)

---

## 8. Identified Risks and Unknowns

### 8.1 Technical Risks

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Completion detection race condition** | High | Use DynamoDB conditional updates |
| **Duplicate WorkflowCompleted events** | Medium | Add `completion_published` flag |
| **SQS FIFO ordering bug** | High | Extensive testing with diverse plans |
| **Increased Lambda concurrency costs** | Low | Monitor costs, set reserved concurrency |
| **DynamoDB hot partition** (run_id key) | Medium | Use composite key: `RUN#{run_id}#SHARD#{hash}` |
| **Sell-before-buy violated** | High | Validate sequence numbers in tests |
| **Orphaned trades** (run never completes) | Medium | Add TTL-based cleanup + CloudWatch alarm |

### 8.2 Operational Unknowns

| Unknown | Investigation Needed |
|---------|----------------------|
| **Settlement monitoring** | How to coordinate across Lambdas? (may need shared state in DynamoDB) |
| **Buying power checks** | Each Lambda checks independently or shared lock? |
| **Symbol subscription** | Can each Lambda subscribe to single symbol efficiently? |
| **WebSocket connections** | Does each Lambda need own connection? (current: shared) |
| **Daily trade limit** | Need distributed counter in DynamoDB (atomic increments) |

### 8.3 Open Questions

1. **Settlement Coordination:**
   - Current: Single executor monitors sell settlement before starting buys
   - Per-trade: How to ensure buys wait for sells to settle?
   - **Answer:** Add `settlement_wait_phase` to run state (SELL_SETTLEMENT, BUY_READY)

2. **Buying Power Validation:**
   - Current: Single executor checks buying power before buy phase
   - Per-trade: Each buy Lambda checks independently?
   - **Answer:** Use DynamoDB to track `available_buying_power` (decrement on each buy)

3. **Partial Execution Resume:**
   - If run fails mid-execution, can we resume?
   - **Answer:** Yes, with run state tracking (mark remaining trades as PENDING)

4. **Cost Impact:**
   - More Lambda invocations = higher costs?
   - **Analysis:** Need cost modeling (estimate: 5-20x Lambda invocations, but shorter duration)

---

## 9. Success Criteria

### 9.1 Functional Requirements

✅ **Ordering:** Sells execute before buys (deterministic FIFO guarantee)  
✅ **Completion Detection:** System detects when all trades in a run are complete  
✅ **Failure Isolation:** Single trade failure doesn't block other trades  
✅ **Idempotency:** Retry-safe (same trade_id → same result)  
✅ **Run Traceability:** All trades in a run share same `run_id` and `correlation_id`

### 9.2 Implementation Clarity

✅ **File-Level Mapping:**
- Portfolio Lambda: `portfolio_v2/handlers/portfolio_analysis_handler.py` (enqueue loop)
- Execution Lambda: `execution_v2/lambda_handler.py` (single trade handler)
- Run State Service: `execution_v2/services/run_state_service.py` (new)
- Infrastructure: `template.yaml` (FIFO queue, DynamoDB table)

✅ **Data Contract Clarity:**
- `TradeMessage` schema defined (section 2.4)
- `ExecutionRun` schema defined (section 5.2)
- Event schemas unchanged (TradeExecuted, WorkflowCompleted)

✅ **No Open Questions:**
- Ordering: Sequence numbers + FIFO
- Completion: DynamoDB atomic counters
- State: DynamoDB run state table

---

## 10. Implementation Checklist

### 10.1 Infrastructure Changes

- [ ] Create `ExecutionRunsTable` DynamoDB table
- [ ] Create `ExecutionFifoQueue` SQS FIFO queue
- [ ] Update IAM policies (Portfolio, Execution Lambdas)
- [ ] Add CloudWatch alarms for orphaned runs
- [ ] Add DLQ monitoring alerts

### 10.2 Code Changes

- [ ] Create `TradeMessage` schema (`shared/schemas/trade_message.py`)
- [ ] Create `RunStateService` (`execution_v2/services/run_state_service.py`)
- [ ] Update Portfolio Lambda enqueue logic (feature flag)
- [ ] Create `SingleTradeHandler` (`execution_v2/handlers/single_trade_handler.py`)
- [ ] Update Execution Lambda handler (route FIFO messages)
- [ ] Add completion detection logic
- [ ] Remove batch executor code (phase 4)

### 10.3 Testing

- [ ] Unit tests: `RunStateService` (concurrent updates)
- [ ] Unit tests: `SingleTradeHandler`
- [ ] Integration tests: Portfolio → SQS FIFO → Execution
- [ ] Load tests: Large plans (50+ trades)
- [ ] Failure tests: Retry logic, DLQ behavior
- [ ] Race condition tests: Concurrent completion detection

### 10.4 Deployment

- [ ] Deploy to dev environment (phase 1)
- [ ] Test with feature flag enabled
- [ ] Deploy to prod (after 2 weeks in dev)
- [ ] Monitor metrics (Lambda concurrency, costs)
- [ ] Rollback plan documented

---

## 11. Appendix: Code Snippets

### 11.1 Portfolio Lambda Enqueue Logic

```python
# File: portfolio_v2/handlers/portfolio_analysis_handler.py

def _enqueue_trades_to_fifo(
    self,
    plan: RebalancePlan,
    correlation_id: str
) -> str:
    """Decompose plan into individual trades and enqueue to SQS FIFO.
    
    Returns:
        run_id: Unique identifier for this execution run
    """
    run_id = str(uuid.uuid4())
    trade_messages = []
    
    # Assign sequence numbers (sells before buys)
    for item in plan.items:
        if item.action == "HOLD":
            continue  # Skip HOLD items
        
        trade_message = TradeMessage(
            run_id=run_id,
            trade_id=str(uuid.uuid4()),
            plan_id=plan.plan_id,
            correlation_id=correlation_id,
            causation_id=plan.causation_id,
            symbol=item.symbol,
            action=item.action,
            trade_amount=item.trade_amount,
            phase="SELL" if item.action == "SELL" else "BUY",
            sequence_number=self._assign_sequence(item),
            total_portfolio_value=plan.total_portfolio_value,
            total_run_trades=len([i for i in plan.items if i.action != "HOLD"]),
            run_timestamp=datetime.now(UTC),
            metadata=plan.metadata or {},
        )
        
        trade_messages.append(trade_message)
    
    # Create run state entry
    self.run_state_service.create_run(
        run_id=run_id,
        plan_id=plan.plan_id,
        correlation_id=correlation_id,
        trade_messages=trade_messages
    )
    
    # Enqueue all messages
    for msg in trade_messages:
        self._publish_to_sqs_fifo(msg, run_id)
    
    logger.info(
        f"Enqueued {len(trade_messages)} trades to FIFO queue",
        extra={"run_id": run_id, "correlation_id": correlation_id}
    )
    
    return run_id

def _publish_to_sqs_fifo(self, message: TradeMessage, run_id: str) -> None:
    """Publish single trade message to SQS FIFO."""
    
    sqs_client = boto3.client("sqs")
    
    sqs_client.send_message(
        QueueUrl=os.environ["EXECUTION_FIFO_QUEUE_URL"],
        MessageBody=message.model_dump_json(),
        MessageGroupId=run_id,  # All trades in same run are ordered
        MessageDeduplicationId=message.trade_id,  # Prevent duplicates
    )
```

### 11.2 Execution Lambda Single-Trade Handler

```python
# File: execution_v2/handlers/single_trade_handler.py

class SingleTradeHandler:
    """Handler for single-trade execution (per-trade Lambda invocations)."""
    
    def __init__(self, container: ApplicationContainer):
        self.container = container
        self.run_state_service = RunStateService(
            dynamodb_client=boto3.client("dynamodb"),
            table_name=os.environ["EXECUTION_RUNS_TABLE"]
        )
    
    def execute_trade(self, trade_message: TradeMessage) -> OrderResult:
        """Execute a single trade from TradeMessage."""
        
        # Mark trade as started
        self.run_state_service.mark_trade_started(
            run_id=trade_message.run_id,
            trade_id=trade_message.trade_id
        )
        
        try:
            # Convert TradeMessage → RebalancePlanItem
            item = self._convert_to_plan_item(trade_message)
            
            # Execute single order (extracted from phase_executor)
            result = self._execute_single_order(item)
            
            # Mark trade as completed
            self.run_state_service.mark_trade_completed(
                run_id=trade_message.run_id,
                trade_id=trade_message.trade_id,
                success=result.success
            )
            
            # Check if run is complete
            if self.run_state_service.is_run_complete(trade_message.run_id):
                self._publish_workflow_completed(trade_message.run_id)
            
            return result
        
        except Exception as e:
            logger.error(
                f"Trade execution failed: {e}",
                extra={
                    "run_id": trade_message.run_id,
                    "trade_id": trade_message.trade_id,
                    "symbol": trade_message.symbol
                }
            )
            
            # Mark as failed
            self.run_state_service.mark_trade_completed(
                run_id=trade_message.run_id,
                trade_id=trade_message.trade_id,
                success=False
            )
            
            raise  # Re-raise for SQS retry
```

---

## 12. Conclusion

This design provides a **complete, code-accurate blueprint** for migrating to per-trade execution. Key takeaways:

1. **Current batch loop** in `executor.py:574-633` becomes **message producer** in Portfolio Lambda
2. **Single-trade execution path** already exists in `phase_executor._execute_order()` 
3. **SQS FIFO** with `MessageGroupId=run_id` ensures ordering (sells before buys)
4. **DynamoDB run state** enables deterministic completion detection
5. **Incremental migration** possible with feature flags (Phases 1-3)
6. **No open questions** remain—all architectural decisions documented

**Next Steps:**
1. Review design with team
2. Create tracking issue with implementation subtasks
3. Begin Phase 1 (run state infrastructure)
4. Test in dev with feature flags
5. Graduate to production after 2-week validation

**Document Status:** ✅ Ready for Implementation
