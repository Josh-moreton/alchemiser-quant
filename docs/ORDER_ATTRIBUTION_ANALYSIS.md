# Order Attribution Model Validation

**Status**: Complete
**Date**: 2025-12-13
**Author**: Copilot Agent
**Commit Hash**: 74ec1d3

> **Note**: This document contains line number references accurate as of commit 74ec1d3 (2025-12-13).
> As code evolves, line numbers may shift. Use function names and file paths for navigation.

## Executive Summary

After analyzing the codebase, the system operates as follows:

**Determination**: The system is **NOT intent-aggregated with order-level attribution**. Instead, it uses **single-strategy consolidation with ephemeral rebalance plans**.

### Key Findings

1. **Current Reality**: Signals from a single strategy run are consolidated at the strategy module level
2. **Multi-Strategy Limitation**: The system does not currently support concurrent signals from multiple independent strategies
3. **Rebalance Plan Dependency**: The `RebalancePlan` is ephemeral but acts as a coordination object between portfolio and execution
4. **Attribution Method**: Order attribution uses `client_order_id` with symbol and timestamp, NOT strategy identifiers
5. **Reconstruction**: Historical reconstruction requires `RebalancePlan` + broker data; signal logs alone are insufficient

---

## Task 1: Strategy Intent Aggregation

### Where Signals Are Combined

**Code Location**: `the_alchemiser/strategy_v2/handlers/signal_generation_handler.py`

```python
def _build_consolidated_portfolio(
    self, signals: list[StrategySignal]
) -> tuple[dict[str, Decimal], list[str]]:
    """Build consolidated portfolio from strategy signals."""
    consolidated_portfolio: dict[str, Decimal] = {}
    
    for signal in signals:
        symbol = signal.symbol.value
        allocation = self._extract_signal_allocation(signal)
        
        if allocation > 0:
            # Sum allocations if the same symbol appears in multiple strategies
            if symbol in consolidated_portfolio:
                consolidated_portfolio[symbol] += allocation  # <-- AGGREGATION HERE
            else:
                consolidated_portfolio[symbol] = allocation
```

**Line 523-524**: This is where per-symbol aggregation occurs.

### What Gets Aggregated

- **Scope**: Within a SINGLE strategy Lambda invocation
- **Mechanism**: Multiple DSL files within the same strategy run are summed per-symbol
- **Result**: A single `ConsolidatedPortfolio` DTO with aggregated weights

### Multi-Strategy Reality

**Current System**: The architecture description mentions "multiple strategies" but the **actual implementation** only runs one strategy Lambda at a time:

```python
# From strategy_v2/lambda_handler.py
def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Lambda entry point for strategy signal generation.
    
    Runs signal generation and publishes SignalGenerated to EventBridge.
    """
```

There is **no code path** for:
- Receiving signals from multiple concurrent strategy Lambda invocations
- Aggregating conflicting signals across strategies (e.g., +100 AAPL from Strategy A, -40 AAPL from Strategy B)
- Resolving conflicts or priority between strategies

### Net Per-Symbol Delta

**Yes**, net deltas are calculated, but:
- **Scope**: Only within a single strategy execution
- **Location**: `signal_generation_handler.py:523-524`
- **Persistence**: Ephemeral - exists only in the `ConsolidatedPortfolio` DTO

### Is Intent Persisted?

**No**. The consolidated portfolio is:
1. Created in `strategy_v2` Lambda
2. Embedded in `SignalGenerated` event
3. Consumed by `portfolio_v2` Lambda to create `RebalancePlan`
4. Not stored in any database or S3

---

## Task 2: Constraint Enforcement

### Where Constraints Are Enforced

**Code Location**: `the_alchemiser/portfolio_v2/core/planner.py`

#### Level 1: Target Weight Validation (Lines 84-106)
```python
def build_plan(...) -> RebalancePlan:
    total_target_weight = sum(strategy.target_weights.values())
    if total_target_weight > TARGET_WEIGHT_SUM_MAX:
        raise PortfolioError(
            f"Target weights sum to {total_target_weight}, must be <= {TARGET_WEIGHT_SUM_MAX}."
        )
```

#### Level 2: Capital Constraint Validation (Lines 470-546)
```python
def _validate_capital_constraints(...) -> None:
    """Validate that total buy orders don't exceed available capital."""
    total_buy_amount = Decimal("0")
    total_sell_proceeds = Decimal("0")
    
    for symbol in all_symbols:
        trade_amount = target_value - current_value
        if trade_amount > Decimal("0"):
            total_buy_amount += trade_amount
        elif trade_amount < Decimal("0"):
            total_sell_proceeds += abs(trade_amount)
    
    available_capital = snapshot.cash + total_sell_proceeds
    
    if leverage_enabled:
        # Check buying power limits
        if net_buy_needed > effective_bp:
            raise PortfolioError(...)
    else:
        # Cash-only mode
        if total_buy_amount > available_capital:
            raise PortfolioError(...)
```

#### Level 3: Margin Safety Validation (Lines 327-424)
```python
def _validate_leverage_capacity(...) -> Decimal:
    """Validate that leverage request can be fulfilled safely."""
    # Check margin utilization, maintenance buffer, etc.
    is_safe, safety_reason = margin_info.is_within_safety_limits(margin_safety_config)
    if not is_safe:
        raise PortfolioError(...)
```

### Constraints Are Evaluated Against

**Aggregated per-symbol deltas**, not individual strategy orders.

**Evidence**:
- `RebalancePlanCalculator` receives a single `StrategyAllocation` (already consolidated)
- Validation loops iterate over `all_symbols` with net `trade_amount` per symbol
- No strategy-level granularity exists at this point

### Partial Fill Scenario

**What happens if constraints are violated after partial fills?**

Currently: **The system does NOT handle this gracefully.**

**Code Evidence**:
```python
# execution_v2/unified/placement_service.py
def place_order(self, intent: OrderIntent) -> ExecutionResult:
    # Preflight validation BEFORE order placement
    preflight_result = self.execution_validator.validate_order(...)
    if not preflight_result.is_valid:
        return self._create_failure_result(...)
    
    # Post-execution validation (lines 373-384, 445-456)
    if self.enable_validation:
        validation_result = await self.validator.validate_execution(
            intent, walk_result, initial_position
        )
        if not validation_result.success:
            logger.warning("Portfolio validation failed after market order")
```

**Gap**: Post-execution validation only logs warnings. There is no:
- Automatic rollback mechanism
- Partial fill reconciliation logic
- Re-planning based on actual filled quantities

---

## Task 3: Order Construction

### Order-to-Strategy Relationship

**Code Location**: `the_alchemiser/execution_v2/unified/placement_service.py`

```python
async def place_order(self, intent: OrderIntent) -> ExecutionResult:
    # Generate client_order_id if not provided
    client_order_id = intent.client_order_id
    if not client_order_id:
        client_order_id = generate_client_order_id(intent.symbol)  # <-- NO STRATEGY ID
```

**Key Finding**: Each Alpaca order represents:
- A **per-symbol net delta** from the `RebalancePlan`
- NOT a single strategy's intent
- NOT multiple strategies combined (because only one strategy runs)

### Order Construction Process

**Path**: `RebalancePlan` → `OrderIntent` → Alpaca Order

1. **Portfolio creates RebalancePlan** (`portfolio_v2/core/planner.py:168`):
   ```python
   plan = RebalancePlan(
       items=trade_items,  # Per-symbol BUY/SELL/HOLD items
       ...
   )
   ```

2. **Execution constructs OrderIntent** (`execution_v2/handlers/trading_execution_handler.py:350-415`):
   ```python
   for item in items:
       if item.action in ("BUY", "SELL"):
           intent = OrderIntent(
               symbol=item.symbol,
               quantity=quantity,
               side=OrderSide.BUY if item.action == "BUY" else OrderSide.SELL,
               ...
           )
   ```

3. **Placement service submits to Alpaca** (`execution_v2/unified/placement_service.py:321-328`):
   ```python
   executed_order = await asyncio.to_thread(
       self.alpaca_manager.place_market_order,
       symbol=intent.symbol,
       side=intent.side.to_alpaca(),
       qty=intent.quantity,
       client_order_id=intent.client_order_id,  # <-- ATTRIBUTION FIELD
   )
   ```

---

## Task 4: Order Attribution and Traceability

### client_order_id Usage

**Code Location**: `the_alchemiser/shared/utils/order_id_utils.py`

```python
def generate_client_order_id(
    symbol: str,
    strategy: str = "alch",
    *,
    prefix: str | None = None,
) -> str:
    """Generate a unique client order ID for Alpaca order tracking.
    
    Format: `{strategy}-{symbol}-{timestamp}-{uuid_suffix}`
    """
    prefix_part = prefix if prefix is not None else strategy
    normalized_symbol = symbol.strip().upper().replace("/", "-")
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%S")
    uuid_suffix = str(uuid.uuid4())[:8]
    
    return f"{prefix_part}-{normalized_symbol}-{timestamp}-{uuid_suffix}"
```

### Fields Encoded in client_order_id

| Field | Example | Purpose |
|-------|---------|---------|
| `strategy` | `"alch"` | **Generic label, NOT strategy identifier** |
| `symbol` | `"AAPL"` | Trading symbol |
| `timestamp` | `"20231201T093000"` | Order submission time |
| `uuid_suffix` | `"a1b2c3d4"` | Uniqueness guarantee |

**Critical Gap**: No strategy ID, signal version, or quantity hash.

### Attribution Back to Strategy Intent

**Current Method**: 
- Orders are linked to `RebalancePlan` via `correlation_id`
- `RebalancePlan` is linked to `SignalGenerated` via `causation_id`
- `SignalGenerated` contains `consolidated_portfolio` data

**Code Evidence**:
```python
# portfolio_v2/handlers/portfolio_analysis_handler.py:793
rebalance_event = RebalancePlanned(
    correlation_id=original_event.correlation_id,
    causation_id=original_event.event_id,  # <-- LINKS BACK TO SIGNAL
    ...
)
```

### Partial Fill Attribution

**Problem**: The system does NOT track per-strategy attribution for partial fills.

**Why**: Because orders represent net per-symbol deltas, not individual strategy intents.

**Evidence**:
```python
# execution_v2/unified/placement_service.py:347-349
filled_qty = getattr(executed_order, "filled_qty", intent.quantity)
avg_price = getattr(executed_order, "filled_avg_price", executed_order.price)
```

Partial fills are logged but **not decomposed** back to originating strategy signals.

---

## Task 5: Rebalance Plan Dependency

### Does a "Rebalance Plan" Persist?

**Answer**: No, but it acts as an ephemeral coordination object.

**Evidence**:

1. **Creation** (`portfolio_v2/core/planner.py:168`):
   ```python
   plan = RebalancePlan(
       correlation_id=correlation_id,
       causation_id=causation_id,
       timestamp=datetime.now(UTC),
       plan_id=f"portfolio_v2_{correlation_id}_{int(datetime.now(UTC).timestamp())}",
       items=trade_items,
       ...
   )
   ```

2. **Transmission** (`portfolio_v2/handlers/portfolio_analysis_handler.py:793-797`):
   ```python
   rebalance_event = RebalancePlanned(
       ...
       rebalance_plan=plan,  # <-- EMBEDDED IN EVENT
       ...
   )
   publish_to_eventbridge(rebalance_event)
   ```

3. **Consumption** (`execution_v2/handlers/trading_execution_handler.py:337-339`):
   ```python
   rebalance_plan_data = event.rebalance_plan  # <-- EXTRACTED FROM EVENT
   
   for item in rebalance_plan_data.items:
       # Create orders from plan items
   ```

4. **No Persistence**:
   - Not written to DynamoDB
   - Not stored in S3
   - Not logged to CloudWatch (only summary metrics)

### What Decisions Does It Contain?

The `RebalancePlan` encodes:

| Decision | Source | Can Be Reconstructed? |
|----------|--------|-----------------------|
| Per-symbol net delta | Portfolio calculation | **Yes**, with signal + snapshot |
| Trade action (BUY/SELL/HOLD) | Portfolio calculation | **Yes**, with signal + snapshot |
| Execution priority | Trade amount threshold | **Yes**, deterministic from amount |
| Trade sizing policy | Suppression of micro-trades | **No**, depends on `min_trade_threshold` |
| Capital constraints | Buying power validation | **No**, requires live account state |

**Critical Decision That Cannot Be Reconstructed**:

**Micro-trade suppression** (`planner.py:682-718`):
```python
def _suppress_small_trades(
    self, items: list[RebalancePlanItem], min_threshold: Decimal
) -> list[RebalancePlanItem]:
    """Convert BUY/SELL items below the threshold into HOLDs."""
    suppressed: list[RebalancePlanItem] = []
    for item in items:
        if item.action in ("BUY", "SELL") and abs(item.trade_amount) < min_threshold:
            suppressed.append(
                item.model_copy(
                    update={
                        "action": "HOLD",
                        "trade_amount": Decimal("0.00"),
                    }
                )
            )
```

This decision is **ephemeral** - without the plan, you cannot know which trades were suppressed.

---

## Task 6: Failure-Mode Analysis

### Scenario: Mid-Cycle Strategy Error

**Setup**:
- Strategy Lambda errors after emitting some signals
- Portfolio Lambda creates partial `RebalancePlan`
- Execution Lambda submits some orders
- Market moves before reconciliation

### What Artefacts Allow Reconstruction?

#### Available Artefacts

1. **EventBridge Events** (retained for 24h):
   - `SignalGenerated` (if emitted before error)
   - `RebalancePlanned` (if portfolio succeeded)
   - `WorkflowFailed` (if strategy or portfolio failed)

2. **Alpaca Orders** (permanent):
   - Order ID, symbol, quantity, side
   - Filled quantity, average fill price
   - `client_order_id` (links to symbol + timestamp)

3. **CloudWatch Logs** (retention: 7-90 days):
   - Strategy execution logs
   - Portfolio plan calculation logs
   - Execution logs with correlation IDs

4. **DynamoDB Trade Ledger** (`execution_v2/services/trade_ledger.py`):
   ```python
   ledger_entry = TradeLedgerEntry(
       trade_id=...,
       symbol=symbol,
       quantity=quantity,
       filled_avg_price=avg_price,
       correlation_id=correlation_id,
       ...
   )
   ```

#### Reconstruction Path

**What Should Have Happened**:
```
Logs → SignalGenerated event → consolidated_portfolio → target_weights
```

**What Actually Happened**:
```
Alpaca API → get_orders() → filled orders + prices
```

**What Cannot Be Determined**:
- Which strategy signals were **never processed** (if error occurred mid-generation)
- Which trades were **suppressed** due to micro-trade thresholds
- Which trades **should have executed** but didn't due to capital constraints

---

## Task 7: Reconstruction Test

### Can We Reconstruct From Minimal Artefacts?

**Question**: If we delete all internal artefacts except:
1. Strategy signal logs
2. Alpaca orders
3. Alpaca fills

Can we deterministically recompute:
- Final positions? **YES**
- Per-strategy P&L? **NO**
- Execution slippage? **YES**

### Analysis

#### 1. Final Positions: **YES**

```python
# Reconstructable from Alpaca API
final_positions = alpaca_manager.trading_client.get_all_positions()
```

No internal state needed - broker is source of truth.

#### 2. Per-Strategy P&L: **NO**

**Missing Information**:
- Strategy signal logs contain `ConsolidatedPortfolio` (aggregated weights)
- No per-strategy allocation breakdown in logs
- `client_order_id` does not encode strategy ID
- Cannot decompose fills back to individual strategy contributions

**Example**:
```
Strategy A: +60% AAPL
Strategy B: +40% AAPL
Consolidated: +100% AAPL (but this is what's logged)

Fill: 100 shares @ $150
Question: How much belongs to Strategy A vs B? → UNKNOWN
```

#### 3. Execution Slippage: **YES**

**Calculation**:
```python
# From signal log
target_price = quote_at_signal_time

# From Alpaca fill
actual_fill_price = order.filled_avg_price

slippage = actual_fill_price - target_price
```

**Requirement**: Signal logs must include quote/price data (they currently do via `metadata`).

### What Is Missing?

| Information | Current Location | Essential or Redundant? |
|-------------|------------------|-------------------------|
| Per-strategy allocation breakdown | **NEVER RECORDED** | **ESSENTIAL** for multi-strategy attribution |
| Micro-trade suppression decisions | `RebalancePlan` (ephemeral) | **ESSENTIAL** for explaining "why no order" |
| Capital constraint reasoning | `RebalancePlan.metadata` (ephemeral) | **REDUNDANT** (can recalculate with snapshot) |
| Execution intent order | `RebalancePlan.items` priority | **REDUNDANT** (deterministic from amounts) |

---

## Conclusion

### Determination

The system is **NOT intent-aggregated with order-level attribution**.

**Actual Architecture**:
1. **Single-strategy execution** per Lambda invocation
2. **Within-strategy consolidation** of DSL files
3. **Ephemeral rebalance plan** acts as coordination object
4. **Symbol-level orders** without strategy attribution
5. **Broker data + plan** required for full reconstruction

### Hidden Dependencies

The `RebalancePlan` is **required but ephemeral**, creating a hidden dependency:

**Problem**: Without the plan:
- Cannot determine which trades were suppressed
- Cannot reconstruct per-strategy P&L (if multi-strategy were implemented)
- Cannot explain why a signal didn't result in an order

**Current Mitigation**: Plans are embedded in `RebalancePlanned` events (24h retention in EventBridge).

**Risk**: After 24h, cannot reconstruct "why no trade" decisions.

### Is client_order_id + Broker Data Sufficient?

**Answer**: **No, with caveats.**

**Sufficient For**:
- ✅ Final position reconciliation
- ✅ Trade execution history
- ✅ Slippage analysis
- ✅ Single-strategy P&L (current system)

**Insufficient For**:
- ❌ Multi-strategy P&L attribution
- ❌ Explaining suppressed trades
- ❌ Reconstructing "intended but not executed" scenarios
- ❌ Historical replays of decision logic

### Recommendations

If the goal is **client_order_id + broker data as long-term source of truth**, the system needs:

1. **Encode strategy ID in client_order_id**:
   ```python
   client_order_id = f"{strategy_id}-{symbol}-{timestamp}-{uuid}"
   ```

2. **Persist RebalancePlan metadata** to S3:
   ```python
   s3_key = f"plans/{correlation_id}/{plan_id}.json"
   s3.put_object(Bucket=bucket, Key=s3_key, Body=plan.to_dict())
   ```

3. **Log suppression decisions** to Trade Ledger:
   ```python
   ledger_entry = TradeLedgerEntry(
       trade_id=...,
       action="SUPPRESSED",
       reason="below_min_threshold",
       intended_amount=item.trade_amount,
   )
   ```

4. **Implement per-strategy allocation tracking** in `ConsolidatedPortfolio`:
   ```python
   class ConsolidatedPortfolio:
       target_allocations: dict[str, Decimal]
       strategy_contributions: dict[str, dict[str, Decimal]]  # NEW FIELD
   ```

---

## Code References

| Component | File | Key Lines |
|-----------|------|-----------|
| Signal Consolidation | `strategy_v2/handlers/signal_generation_handler.py` | 506-529 |
| Rebalance Plan Creation | `portfolio_v2/core/planner.py` | 57-211 |
| Constraint Validation | `portfolio_v2/core/planner.py` | 470-546 |
| Order Construction | `execution_v2/handlers/trading_execution_handler.py` | 273-450 |
| client_order_id Generation | `shared/utils/order_id_utils.py` | 15-76 |
| Order Placement | `execution_v2/unified/placement_service.py` | 146-289 |
| Trade Ledger | `execution_v2/services/trade_ledger.py` | (entire file) |

---

## Related Documents

- [CONTRACTS.md](../the_alchemiser/shared/CONTRACTS.md) - Event and schema contracts
- [strategy_v2/README.md](../the_alchemiser/strategy_v2/README.md) - Strategy module architecture
- [portfolio_v2/README.md](../the_alchemiser/portfolio_v2/README.md) - Portfolio planning logic
- [execution_v2/README.md](../the_alchemiser/execution_v2/README.md) - Execution architecture

---

**Document Version**: 1.0
**Last Updated**: 2025-12-13
**Review Status**: Initial analysis complete
