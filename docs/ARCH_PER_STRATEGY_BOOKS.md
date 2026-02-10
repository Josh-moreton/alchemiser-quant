# Architecture Proposal: Per-Strategy Books

## Executive Summary

This document proposes removing the signal aggregation and rebalance planner steps from the trading workflow, and instead having each strategy run its own independent book. Each strategy will:
- Generate its own signals
- Calculate its own rebalance plans
- Trigger its own execution runners
- Record trades in its own ledger partition

This simplifies the architecture, removes complex partial entry/exit logic, and provides cleaner P&L attribution per strategy.

## Current Architecture

### Event Flow
```
Strategy Orchestrator (EventBridge Schedule)
    ↓ (async Lambda invocation per DSL file)
Strategy Workers (parallel, 1 per file)
    ↓ (PartialSignalGenerated via EventBridge)
Signal Aggregator
    ↓ (SignalGenerated via EventBridge)
Rebalance Planner (Portfolio Lambda)
    ↓ (RebalancePlanned via EventBridge → SQS)
Execution Lambda (parallel per trade)
    ↓ (TradeExecuted via EventBridge)
Notifications Lambda
```

### Key Components

**Strategy Workers**
- Execute single DSL strategy file
- Apply strategy weight allocation (0-1)
- Scale portfolio weights by allocation
- Publish PartialSignalGenerated event

**Signal Aggregator**
- Collects PartialSignalGenerated events per session
- Merges partial portfolios by summing allocations
- Validates total allocation ≈ 1.0 (±1%)
- Publishes SignalGenerated with consolidated portfolio
- Handles partial failures (some strategies can fail)

**Rebalance Planner (Portfolio Lambda)**
- Consumes SignalGenerated event
- Reads current portfolio state from Alpaca
- Calculates target dollar values vs current values
- Generates trade list (SELLs and BUYs)
- Publishes RebalancePlanned event
- Enqueues SELL trades to SQS (BUYs stored in DynamoDB)

**Execution Lambda**
- Consumes trades from SQS Standard queue (parallel)
- Executes trades via Alpaca API
- Records trades to TradeLedgerTable
- Uses strategy_weights field for attribution
- Two-phase ordering: SELLs first, then BUYs

### Current Data Structures

**TradeLedgerTable (DynamoDB)**
- **PK**: `TRADE#{order_id}`
- **SK**: `METADATA`
- **Fields**:
  - `strategy_names`: list of contributing strategies
  - `strategy_weights`: dict mapping strategy → weight for attribution
  - `symbol`, `direction`, `filled_qty`, `fill_price`
  - `slippage_bps`, `spread_at_order`
- **GSI3**: `STRATEGY#{name}` → `TRADE#{timestamp}#{order_id}` for per-strategy queries

**ConsolidatedPortfolio Schema**
```python
{
    "target_allocations": {"AAPL": Decimal("0.5"), "SPY": Decimal("0.5")},
    "strategy_contributions": {
        "momentum": {"AAPL": Decimal("0.3"), "SPY": Decimal("0.2")},
        "mean_rev": {"AAPL": Decimal("0.2"), "SPY": Decimal("0.3")}
    },
    "strategy_count": 2,
    "is_partial": False
}
```

### Problems with Current Architecture

1. **Complex Attribution Logic**: Trades must track strategy_weights for multi-strategy positions
2. **Partial Entry/Exit Complexity**: When one strategy exits but another holds, need fractional position handling
3. **Aggregation Overhead**: Extra Lambda and DynamoDB session tracking
4. **Coupling**: Strategies are coupled through shared consolidated portfolio
5. **P&L Tracking**: Requires complex attribution logic to separate strategy performance
6. **Risk Management**: Harder to apply per-strategy risk limits

## Proposed Architecture

### New Event Flow
```
Strategy Orchestrator (EventBridge Schedule)
    ↓ (async Lambda invocation per DSL file)
Strategy Workers (parallel, 1 per file)
    ↓ (StrategyExecutionRequested via EventBridge → SQS)
Execution Lambda (parallel per trade)
    ↓ (TradeExecuted via EventBridge)
Notifications Lambda
```

### Key Changes

**Strategy Workers (Enhanced)**
- Execute single DSL strategy file
- Apply strategy weight to determine strategy capital
- Read current strategy positions from DynamoDB (strategy-specific partition)
- Calculate rebalance plan for this strategy's book
- Generate trade messages (SELLs and BUYs)
- Publish StrategyExecutionRequested event per trade
- Each strategy operates independently

**Remove Components**
- Signal Aggregator Lambda (no longer needed)
- Rebalance Planner Lambda (moved into Strategy Workers)
- AggregationSessionsTable (no longer needed)

**Execution Lambda (Modified)**
- Unchanged execution logic
- Records trades to strategy-specific partition in TradeLedgerTable
- No strategy_weights attribution needed (single strategy per trade)

**Trade Ledger (Modified)**
- **PK Pattern Changes**:
  - Old: `TRADE#{order_id}`
  - New: `STRATEGY#{strategy_id}#TRADE#{order_id}`
- **Remove Fields**: `strategy_weights` (not needed for single-strategy trades)
- **Keep Fields**: `strategy_name` (single strategy, not list)
- **GSI Changes**: Update to match new PK pattern

### New Data Structures

**StrategyExecutionRequested Event**
```python
{
    "event_type": "StrategyExecutionRequested",
    "strategy_id": "momentum",
    "dsl_file": "1-momentum.clj",
    "allocation": Decimal("0.30"),  # Strategy's capital allocation
    "trade": {
        "symbol": "AAPL",
        "direction": "BUY",
        "target_qty": 10,
        "target_value": Decimal("1500.00")
    },
    "strategy_capital": Decimal("50000.00"),  # Total capital for this strategy
    "correlation_id": "...",
    "timestamp": "..."
}
```

**Trade Ledger Entry (Per-Strategy)**
```python
{
    "PK": "STRATEGY#momentum#TRADE#a1b2c3",
    "SK": "METADATA",
    "strategy_id": "momentum",
    "strategy_name": "Momentum Strategy",
    "order_id": "a1b2c3",
    "symbol": "AAPL",
    "direction": "BUY",
    "filled_qty": 10,
    "fill_price": Decimal("150.50"),
    # No strategy_weights needed
}
```

**Strategy Capital Allocation**
```python
# In Coordinator or configuration
strategy_allocations = {
    "momentum": Decimal("0.30"),      # 30% of total capital
    "mean_reversion": Decimal("0.30"), # 30% of total capital
    "breakout": Decimal("0.40")        # 40% of total capital
}
# Total = 1.0 (100% of capital)
```

## Implementation Plan

### Phase 1: Schema and Event Changes

**Tasks:**
1. Create `StrategyExecutionRequested` event schema
   - Add to `shared/events/schemas.py`
   - Include strategy_id, allocation, trade details
   - Add to EventBridge routing configuration

2. Update `TradeLedgerEntry` schema
   - Change PK pattern to include strategy_id
   - Remove `strategy_weights` field
   - Change `strategy_names` to `strategy_name` (single string)
   - Add `strategy_capital` field for context

3. Create `StrategyPosition` schema
   - Track current positions per strategy
   - Fields: strategy_id, symbol, qty, avg_cost, market_value

**Affected Files:**
- `layers/shared/the_alchemiser/shared/events/schemas.py`
- `layers/shared/the_alchemiser/shared/schemas/trade_ledger.py`
- `layers/shared/the_alchemiser/shared/schemas/` (new file: `strategy_position.py`)

### Phase 2: Strategy Worker Enhancement

**Tasks:**
1. Add rebalance planning logic to Strategy Workers
   - Import/adapt `RebalancePlanCalculator` from portfolio module
   - Calculate strategy-specific rebalance plan
   - Use strategy's allocated capital as portfolio value

2. Add position reading logic
   - Query TradeLedgerTable for current strategy positions
   - Build PortfolioSnapshot for this strategy only
   - Calculate current dollar values per symbol

3. Generate trade messages
   - Create StrategyExecutionRequested events for each trade
   - Apply two-phase ordering (SELLs before BUYs) at generation time
   - Publish to EventBridge (routed to SQS)

4. Remove PartialSignalGenerated publishing
   - No longer needed since no aggregation step

**Affected Files:**
- `functions/strategy_worker/lambda_handler.py`
- `functions/strategy_worker/handlers/single_file_signal_handler.py`
- New file: `functions/strategy_worker/core/strategy_rebalancer.py`

**New Dependencies:**
- Strategy workers need access to TradeLedgerTable (read)
- Strategy workers need access to Alpaca API (for account info, current prices)
- Move RebalancePlanCalculator to shared module

### Phase 3: Execution Lambda Updates

**Tasks:**
1. Update trade recording logic
   - Use new PK pattern: `STRATEGY#{strategy_id}#TRADE#{order_id}`
   - Extract strategy_id from StrategyExecutionRequested event
   - Remove strategy_weights attribution logic

2. Update event handling
   - Change from RebalancePlanned to StrategyExecutionRequested
   - Update message parsing logic

3. Update position tracking
   - Query by strategy_id for position checks
   - Maintain per-strategy P&L calculations

**Affected Files:**
- `functions/execution/lambda_handler.py`
- `functions/execution/handlers/single_trade_handler.py`
- `layers/shared/the_alchemiser/shared/repositories/dynamodb_trade_ledger_repository.py`

### Phase 4: Infrastructure Changes (template.yaml)

**Tasks:**
1. Remove StrategyAggregatorFunction
   - Remove Lambda function definition
   - Remove EventBridge permissions
   - Remove CloudWatch alarms

2. Remove RebalancePlannerFunction
   - Remove Lambda function definition
   - Remove SignalGenerated EventBridge rule
   - Remove EventBridge permissions
   - Remove CloudWatch alarms

3. Remove AggregationSessionsTable
   - Remove DynamoDB table definition

4. Update EventBridge routing
   - Remove PartialSignalGenerated rule
   - Remove SignalGenerated rule
   - Remove RebalancePlanned rule
   - Add StrategyExecutionRequested rule → SQS

5. Update IAM policies
   - Grant Strategy Workers read access to TradeLedgerTable
   - Grant Strategy Workers access to Alpaca API (if not already)
   - Update Execution Lambda policies for new event type

6. Update TradeLedgerTable GSI definitions
   - Update GSI3 to match new PK pattern
   - May need to recreate GSI or create new one

**Affected Files:**
- `template.yaml` (extensive changes)

### Phase 5: Code Cleanup

**Tasks:**
1. Remove aggregator_v2 module
   - Delete `functions/strategy_aggregator/` directory
   - Remove from build/deployment scripts

2. Remove portfolio_v2 module
   - Delete `functions/portfolio/` directory (if only used for rebalancing)
   - Keep if used for other features (hedge evaluation, etc.)
   - Remove from build/deployment scripts

3. Update shared schemas
   - Remove ConsolidatedPortfolio schema (no longer needed)
   - Remove SignalGenerated event (no longer needed)
   - Remove RebalancePlanned event (no longer needed)
   - Remove PartialSignalGenerated event (no longer needed)

4. Update documentation
   - Update architecture diagrams
   - Update CLAUDE.md with new flow
   - Update README.md

**Affected Files:**
- Delete: `functions/strategy_aggregator/`
- Delete: `functions/portfolio/` (conditional)
- Update: `layers/shared/the_alchemiser/shared/events/schemas.py`
- Update: `layers/shared/the_alchemiser/shared/schemas/consolidated_portfolio.py` (mark deprecated)
- Update: `docs/`, `CLAUDE.md`, `README.md`

### Phase 6: Testing and Validation

**Tasks:**
1. Unit testing
   - Test strategy rebalance calculation
   - Test trade message generation
   - Test ledger queries by strategy

2. Integration testing
   - Test full flow: Orchestrator → Strategy → Execution
   - Test multiple strategies running in parallel
   - Test position tracking per strategy

3. Manual validation
   - Run single strategy end-to-end
   - Verify trades recorded with correct strategy_id
   - Query ledger to confirm per-strategy P&L
   - Run multiple strategies simultaneously
   - Verify no cross-contamination

4. Deployment testing
   - Deploy to dev environment
   - Run paper trading for 1+ weeks
   - Monitor for errors, edge cases

**Testing Scope:**
- No existing unit tests (repo doesn't use pytest)
- Focus on type checking: `make type-check`
- Manual testing via deployed Lambdas
- Monitor CloudWatch logs for errors

## Migration Strategy

### Option A: Big Bang Migration
- Implement all changes at once
- Deploy new system completely
- High risk, fast delivery

**Pros:**
- Clean break, no dual-system maintenance
- Faster time to completion

**Cons:**
- High risk if issues found in production
- Difficult to rollback
- All-or-nothing testing

### Option B: Gradual Migration (Recommended)
- Deploy new system alongside old system
- Route small percentage of strategies to new flow
- Gradually increase percentage as confidence grows
- Keep aggregation flow as fallback

**Implementation Steps:**
1. Deploy new StrategyExecutionRequested handler (doesn't affect existing flow)
2. Add feature flag in Coordinator to select flow per strategy
3. Route 1 strategy to new flow, rest to old flow
4. Monitor for 1+ week
5. Gradually increase strategies on new flow
6. Once 100% on new flow for 2+ weeks, remove old flow

**Pros:**
- Lower risk
- Easy rollback
- Validate in production incrementally

**Cons:**
- Longer timeline
- Maintain two code paths temporarily
- More complex deployment

### Recommended Approach: Option B (Gradual Migration)

Add feature flag:
```python
# In Coordinator Lambda
STRATEGY_ROUTING = {
    "1-momentum.clj": "new",  # Uses StrategyExecutionRequested
    "2-mean_rev.clj": "old",  # Uses PartialSignalGenerated → Aggregator
    # ... rest default to "old"
}
```

## Risk Assessment

### Technical Risks

**1. Capital Allocation Overlap**
- **Risk**: Multiple strategies try to trade same symbol, causing over-allocation
- **Mitigation**: 
  - Strategy allocations must sum to ≤ 1.0 (validated in Coordinator)
  - Each strategy operates on independent capital slice
  - No overlap by design

**2. Position Tracking Accuracy**
- **Risk**: Strategy position state gets out of sync with actual broker positions
- **Mitigation**:
  - Reconcile strategy positions against Alpaca API periodically
  - Add position reconciliation Lambda (scheduled)
  - Log discrepancies for investigation

**3. Failed Execution Recovery**
- **Risk**: Trade fails, strategy ledger shows different state than reality
- **Mitigation**:
  - SQS retry mechanism (existing)
  - DLQ for failed trades (existing)
  - Manual reconciliation process for DLQ items
  - Add monitoring alerts for DLQ depth

**4. Data Migration**
- **Risk**: Existing trade ledger incompatible with new schema
- **Mitigation**:
  - New PK pattern doesn't conflict with old pattern
  - Keep old trades as-is
  - Only new trades use new pattern
  - Maintain backward-compatible queries

### Operational Risks

**1. Increased Lambda Costs**
- **Risk**: More Lambda invocations (no aggregation batch)
- **Impact**: Likely minimal (pay-per-invocation model)
- **Mitigation**: Monitor costs, optimize if needed

**2. EventBridge Message Volume**
- **Risk**: More events published (per-trade vs per-session)
- **Impact**: EventBridge scales automatically
- **Mitigation**: Monitor EventBridge metrics

**3. Learning Curve**
- **Risk**: Team needs to understand new architecture
- **Mitigation**: 
  - This document
  - Updated architecture diagrams
  - Code comments

## Benefits

### Simplified Architecture
- Remove 2 Lambda functions (Aggregator, Rebalance Planner)
- Remove 1 DynamoDB table (AggregationSessionsTable)
- Remove 3 event types (PartialSignalGenerated, SignalGenerated, RebalancePlanned)
- Fewer moving parts = easier to understand and maintain

### Cleaner P&L Attribution
- Each trade belongs to exactly one strategy
- No complex strategy_weights attribution
- Direct per-strategy P&L queries: `query GSI3 by strategy_id`
- Easier to analyze strategy performance

### Independent Strategy Execution
- Strategies don't affect each other (beyond capital allocation)
- One strategy failing doesn't block others
- Easier to add/remove strategies
- Per-strategy risk limits possible

### Removed Complexity
- No partial entry/exit logic needed
- No allocation merging and validation
- No aggregation session tracking
- Simpler event flow

### Better Testing
- Test each strategy in isolation
- Mock strategy positions easily
- Clearer failure modes

## Open Questions

### 1. Capital Rebalancing
**Question**: If Strategy A has great performance and grows to 45% of total capital, do we rebalance back to target allocations?

**Options**:
- A. Let strategies drift based on performance (compound winners)
- B. Periodic rebalancing to maintain target allocations (e.g., monthly)
- C. Rebalance when drift exceeds threshold (e.g., ±10%)

**Recommendation**: Option C - rebalance on drift threshold
- Maintains intended risk profile
- Allows some compounding of winners
- Add rebalancing Lambda (scheduled weekly)

### 2. Symbol Overlap Handling
**Question**: What if two strategies both want to hold AAPL, but with different target allocations?

**Current State**: Aggregation merges them (Strategy A: 20% AAPL, Strategy B: 10% AAPL → Total: 30% AAPL)

**New State**: No overlap by design
- Strategy A gets 30% of capital → can allocate 100% to AAPL → holds 30% * 1.0 = 30% of total capital
- Strategy B gets 30% of capital → cannot also hold AAPL

**Options**:
- A. Accept constraint: No symbol overlap allowed
- B. Add validation: Warn if multiple strategies select same symbol
- C. Special handling: Allow overlap, maintain separate positions per strategy

**Recommendation**: Option B - warn but allow
- Log warning if overlap detected
- Let each strategy proceed independently
- Monitor in practice if this causes issues
- Can add overlap resolution logic later if needed

### 3. Account Cash Management
**Question**: Each strategy needs cash for buying. How do we allocate available cash?

**Options**:
- A. Each strategy gets its proportional share of cash (30% strategy → 30% of cash)
- B. Strategies share from common cash pool (first-come-first-served)
- C. Reserve cash per strategy (tracked in DynamoDB)

**Recommendation**: Option A - proportional cash allocation
- Simple to implement
- Fair allocation
- Matches capital allocation model
- Calculate in Strategy Worker: `available_cash = total_cash * allocation`

### 4. Hedge Management
**Question**: How do hedges work in per-strategy model? Do hedges belong to specific strategies?

**Current State**: Hedge Evaluator Lambda consumes RebalancePlanned event

**Options**:
- A. Remove hedging (not compatible with per-strategy model)
- B. Hedges belong to specific strategies
- C. Hedges are system-level (apply to total portfolio, not per-strategy)

**Recommendation**: Option C - system-level hedging
- Keep HedgeEvaluator Lambda
- Trigger on total portfolio state change (after all strategies execute)
- Hedges recorded to special "system" strategy_id
- Hedge logic unchanged from current implementation

### 5. Performance Reporting
**Question**: How do we report total portfolio performance vs per-strategy?

**Options**:
- A. Sum all strategy P&L for total performance
- B. Maintain separate total portfolio tracking
- C. Both (redundant but useful for validation)

**Recommendation**: Option C - maintain both
- Sum strategy P&L for total (primary method)
- Keep existing performance reporting (validation)
- Alert if discrepancy detected

## Success Criteria

### Functional Requirements
- ✅ Each strategy executes independently
- ✅ Trades recorded to per-strategy ledger partition
- ✅ Per-strategy P&L queryable from ledger
- ✅ No aggregation or rebalance planner needed
- ✅ Strategy failures don't affect other strategies

### Performance Requirements
- ✅ End-to-end latency ≤ current system (+10% acceptable)
- ✅ Lambda costs ≤ 1.2x current (small increase acceptable)
- ✅ No new bottlenecks or scaling issues

### Operational Requirements
- ✅ Successful paper trading for 2+ weeks
- ✅ Zero data loss or corruption
- ✅ Rollback plan tested and ready
- ✅ Documentation updated
- ✅ Team trained on new architecture

## Timeline Estimate

Assuming 1 developer working full-time:

- **Phase 1** (Schema/Events): 2-3 days
- **Phase 2** (Strategy Workers): 5-7 days
- **Phase 3** (Execution Updates): 3-4 days
- **Phase 4** (Infrastructure): 2-3 days
- **Phase 5** (Cleanup): 2-3 days
- **Phase 6** (Testing): 5-7 days
- **Gradual Migration**: 2-3 weeks (monitoring period)

**Total**: 4-6 weeks for full migration

## Conclusion

This proposal significantly simplifies the architecture by removing aggregation and rebalance planning steps. Each strategy operates independently with its own book, making the system easier to understand, test, and maintain. Per-strategy P&L tracking becomes trivial, and strategy failures are isolated.

The gradual migration approach minimizes risk while allowing us to validate the new design in production before fully committing. The main trade-off is handling symbol overlap between strategies, but this can be managed with warnings and monitoring.

**Recommendation**: Proceed with implementation using gradual migration strategy (Option B).

## References

- Current architecture: `CLAUDE.md`, `README.md`
- Event schemas: `layers/shared/the_alchemiser/shared/events/schemas.py`
- Portfolio logic: `functions/portfolio/core/planner.py`
- Trade ledger: `layers/shared/the_alchemiser/shared/repositories/dynamodb_trade_ledger_repository.py`
- SAM template: `template.yaml`
