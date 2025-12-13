# Order Attribution Model - Executive Summary

**Quick Reference**: See [ORDER_ATTRIBUTION_ANALYSIS.md](ORDER_ATTRIBUTION_ANALYSIS.md) for detailed analysis.

---

## TL;DR

**Question**: Is the system intent-aggregated with order-level attribution, or rebalance-plan-driven?

**Answer**: **Rebalance-plan-driven** (ephemeral coordination object) with **single-strategy consolidation**.

---

## System Architecture (Current Reality)

```
┌─────────────────────────────────────────────────────────────────┐
│                     STRATEGY LAMBDA                              │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                      │
│  │ DSL File │  │ DSL File │  │ DSL File │  (Multiple files,    │
│  │    A     │  │    B     │  │    C     │   single strategy)   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘                      │
│       │            │             │                               │
│       └────────────┼─────────────┘                               │
│                    │                                              │
│            ┌───────▼────────┐                                    │
│            │  CONSOLIDATION │  ← Per-symbol SUM                 │
│            │  (Lines 523-524)│                                   │
│            └───────┬────────┘                                    │
│                    │                                              │
│            ┌───────▼────────────┐                                │
│            │ ConsolidatedPortfolio│                              │
│            │  {AAPL: 0.6, ...}  │  (No strategy breakdown!)     │
│            └───────┬────────────┘                                │
└────────────────────┼───────────────────────────────────────────┘
                     │
                     │ SignalGenerated Event
                     │
┌────────────────────▼───────────────────────────────────────────┐
│                   PORTFOLIO LAMBDA                              │
│                                                                  │
│  ┌────────────────────────────────────┐                         │
│  │    RebalancePlanCalculator         │                         │
│  │                                    │                         │
│  │  • Validate target weights         │                         │
│  │  • Calculate dollar values         │                         │
│  │  • Check capital constraints       │                         │
│  │  • Suppress micro-trades (< $5)    │ ← EPHEMERAL DECISION!  │
│  │                                    │                         │
│  └───────────────┬────────────────────┘                         │
│                  │                                               │
│         ┌────────▼────────┐                                     │
│         │  RebalancePlan  │  ← NOT PERSISTED!                  │
│         │                 │    (24h EventBridge retention only) │
│         │ Items:          │                                     │
│         │  - AAPL: BUY    │                                     │
│         │  - MSFT: SELL   │                                     │
│         │  - TSLA: HOLD   │ ← Why HOLD? Info lost after 24h!   │
│         └────────┬────────┘                                     │
└──────────────────┼─────────────────────────────────────────────┘
                   │
                   │ RebalancePlanned Event
                   │
┌──────────────────▼─────────────────────────────────────────────┐
│                  EXECUTION LAMBDA                               │
│                                                                  │
│  For each RebalancePlanItem (BUY/SELL):                         │
│                                                                  │
│  ┌──────────────────────────────────────┐                       │
│  │  OrderIntent Construction            │                       │
│  │                                      │                       │
│  │  symbol: item.symbol                 │                       │
│  │  quantity: calculate_quantity(...)   │                       │
│  │  client_order_id: generate_client_   │                       │
│  │      order_id(symbol)                │ ← NO STRATEGY ID!    │
│  │                                      │                       │
│  │  Format: "alch-AAPL-20231201T093000- │                       │
│  │           a1b2c3d4"                  │                       │
│  └───────────────┬──────────────────────┘                       │
│                  │                                               │
│         ┌────────▼────────┐                                     │
│         │  Alpaca Order   │                                     │
│         │                 │                                     │
│         │ • Order ID      │                                     │
│         │ • Filled qty    │                                     │
│         │ • Fill price    │                                     │
│         │ • client_order_id│                                    │
│         └────────┬────────┘                                     │
└──────────────────┼─────────────────────────────────────────────┘
                   │
                   │ TradeExecuted Event
                   │
                   ▼
         ┌──────────────────┐
         │  Trade Ledger    │
         │  (DynamoDB)      │
         │                  │
         │ • trade_id       │
         │ • symbol         │
         │ • quantity       │
         │ • price          │
         │ • correlation_id │
         └──────────────────┘
```

---

## Critical Gap Visualization

### What We Have:

```
Signal → ConsolidatedPortfolio → RebalancePlan → Orders → Fills
  ↓           ↓                      ↓              ↓       ↓
Logs    EventBridge(24h)     EventBridge(24h)   Alpaca   Alpaca
                                                 (perm)   (perm)
```

### What We Can Reconstruct:

| Time After Event | Reconstructable Data |
|------------------|----------------------|
| **< 24 hours** | ✅ Full reconstruction (events available) |
| **> 24 hours** | ⚠️ Partial reconstruction (missing plan decisions) |
| **Any time** | ✅ Final positions (Alpaca API) |
| **Any time** | ❌ Per-strategy P&L (no strategy ID) |
| **Any time** | ❌ Suppressed trade reasons (plan lost) |

---

## The "HOLD" Problem

**Scenario**: Strategy signals +5% allocation to TSLA ($500 trade value)

**What Happens**:

1. Signal logged: `target_weight[TSLA] = 0.05`
2. Portfolio calculates: `trade_amount = $500`
3. Micro-trade suppression: `$500 < $1000 threshold`
4. Plan item marked: `action = HOLD` (was `BUY`)
5. Execution skips: No order submitted
6. After 24h: RebalancePlan lost from EventBridge

**Question**: "Why didn't we buy TSLA?"

**Answer**:
- **< 24h**: Check `RebalancePlan.items[TSLA].action == HOLD`
- **> 24h**: **UNKNOWABLE** (decision context lost)

---

## Multi-Strategy Attribution Gap

**Current System**:
```python
# Only ONE strategy runs per invocation
def lambda_handler(event, context):
    allocation = orchestrator.run_strategy(strategy_id="nuclear")
    # Result: {AAPL: 0.6, MSFT: 0.4}
```

**Hypothetical Multi-Strategy**:
```python
# This DOES NOT EXIST in current code
strategy_a = run_strategy("momentum")  # {AAPL: 0.6}
strategy_b = run_strategy("mean_rev")  # {AAPL: -0.2}
consolidated = aggregate([strategy_a, strategy_b])  # {AAPL: 0.4}
```

**Problem**: Even if implemented, current attribution cannot track:
- Which strategy contributed what to final AAPL order
- How to split fill P&L between strategies
- Which strategy to "blame" for losses

---

## client_order_id Encoding

### Current Format:
```
alch-AAPL-20231201T093000-a1b2c3d4
 │    │          │            │
 │    │          │            └─ Uniqueness UUID
 │    │          └─ Timestamp
 │    └─ Symbol
 └─ Hardcoded "alch" (NOT strategy ID!)
```

### What's Missing:
- ❌ Strategy identifier
- ❌ Signal version
- ❌ Quantity hash
- ❌ Plan item priority

### Recommended Format:
```
nuclear-AAPL-20231201T093000-a1b2c3d4-v1
   │      │          │            │     │
   │      │          │            │     └─ Signal version
   │      │          │            └─ UUID
   │      │          └─ Timestamp
   │      └─ Symbol
   └─ Strategy ID
```

---

## Reconstruction Matrix

| Artefact Combination | Final Positions | Per-Strategy P&L | Suppressed Trades | Slippage |
|----------------------|-----------------|------------------|-------------------|----------|
| **Alpaca only** | ✅ YES | ❌ NO | ❌ NO | ⚠️ Approximate |
| **Alpaca + Logs** | ✅ YES | ❌ NO | ⚠️ If < 24h | ✅ YES |
| **Alpaca + Logs + EventBridge** | ✅ YES | ⚠️ Single strategy | ✅ YES | ✅ YES |
| **Alpaca + Logs + DynamoDB Plans** | ✅ YES | ⚠️ Single strategy | ✅ YES | ✅ YES |

**Legend**:
- ✅ Fully reconstructable
- ⚠️ Partially reconstructable / time-limited
- ❌ Not reconstructable

---

## Recommendations Priority

### P0 - Critical for Auditability:
1. **Persist RebalancePlan to DynamoDB** (90-day retention)
   - Enables reconstruction of "why no trade" decisions
   - Audit trail for regulatory compliance

### P1 - Required for Multi-Strategy:
2. **Encode strategy ID in client_order_id**
   - Format: `{strategy_id}-{symbol}-{timestamp}-{uuid}`
   - Enables per-strategy P&L tracking

3. **Add strategy_contributions to ConsolidatedPortfolio**
   ```python
   strategy_contributions: dict[str, dict[str, Decimal]]
   # {"momentum": {"AAPL": 0.4}, "mean_rev": {"AAPL": 0.2}}
   ```

### P2 - Nice to Have:
4. **Log suppression decisions to Trade Ledger**
   - Record `action=SUPPRESSED` with reasoning
   - Queryable long-term

5. **Add plan_id to Trade Ledger entries**
   - Link fills back to originating plan
   - Enable plan-level P&L rollup

---

## Questions Answered

| Question | Answer | Location in Analysis |
|----------|--------|---------------------|
| Where are signals aggregated? | `signal_generation_handler.py:523` | Task 1 |
| Are constraints per-symbol or per-strategy? | **Per-symbol** (aggregated) | Task 2 |
| What does client_order_id encode? | Symbol + timestamp (NOT strategy) | Task 4 |
| Is plan persisted? | **No** (ephemeral in events) | Task 5 |
| Can we reconstruct P&L? | **Single-strategy yes, multi-strategy no** | Task 7 |
| Is broker data sufficient? | **No** (missing suppression context) | Conclusion |

---

## Next Actions

For issue closure, recommend:

1. ✅ **Accept analysis** - System is rebalance-plan-driven
2. 📝 **Document gaps** - Create tech debt tickets for:
   - Plan persistence to DynamoDB
   - Strategy ID in client_order_id
   - Multi-strategy attribution tracking
3. 🎯 **Define SLA** - Decide acceptable reconstruction time window (24h? 90d? Forever?)
4. 🔍 **Plan implementation** - Prioritize P0 recommendations if auditability is critical

---

**Document Version**: 1.0  
**Companion Document**: [ORDER_ATTRIBUTION_ANALYSIS.md](ORDER_ATTRIBUTION_ANALYSIS.md)  
**Last Updated**: 2025-12-13
