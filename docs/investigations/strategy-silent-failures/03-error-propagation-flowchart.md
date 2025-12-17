# Phase 3: Error Propagation Flowchart

**Status:** Complete  
**Date:** 2025-12-15  

## Overview

This document maps how errors flow through the strategy evaluation pipeline, identifying where errors are caught vs. re-raised, what notifications are triggered, and where errors are silently absorbed.

---

## Error Flow Diagram (ASCII)

```
┌─────────────────────────────────────────────────────────────────────────────────────────────┐
│                            STRATEGY SIGNAL GENERATION PIPELINE                               │
└─────────────────────────────────────────────────────────────────────────────────────────────┘

┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│  MARKET DATA     │    │  INDICATORS      │    │  DSL EVALUATOR   │    │  SIGNAL GEN      │
│  (Data Layer)    │───▶│  (Compute Layer) │───▶│  (Strategy Layer)│───▶│  (Output Layer)  │
└──────────────────┘    └──────────────────┘    └──────────────────┘    └──────────────────┘
        │                       │                       │                       │
        ▼                       ▼                       ▼                       ▼
┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│ ERRORS:          │    │ ERRORS:          │    │ ERRORS:          │    │ ERRORS:          │
│ • MarketDataError│    │ • IndicatorError │    │ • DslEvalError   │    │ • SignalGenError │
│ • DataProvider   │    │ • Fallback→0.0   │    │ • Empty Alloc    │    │ • WorkflowFailed │
│   Error          │    │ • Fallback→50.0  │    │ • Symbol Skip    │    │                  │
│ • Empty Bars []  │    │                  │    │                  │    │                  │
└──────────────────┘    └──────────────────┘    └──────────────────┘    └──────────────────┘
        │                       │                       │                       │
        │ CAUGHT               │ CAUGHT               │ CAUGHT/RAISED         │ RAISED
        │ Returns []           │ Returns fallback     │ Raises if empty       │ Publishes
        │ or None              │ (0.0, 50.0, 100.0)   │ Skips symbol if fail  │ WorkflowFailed
        │                       │                       │                       │
        ▼                       ▼                       ▼                       ▼
   ⚠️ WARNING LOG          ⚠️ WARNING LOG         ❌ ERROR LOG/RAISE     📧 SNS EMAIL
   No Event                No Event               DslEvaluationError     WorkflowFailed
   No Alert                No Alert               (if empty allocation)  Event Published

                                    │
                                    │ Multi-Node Mode Only
                                    ▼
                    ┌──────────────────────────────────────┐
                    │           AGGREGATOR                 │
                    │  (Partial Signal Collection)         │
                    └──────────────────────────────────────┘
                                    │
                    ┌───────────────┴───────────────┐
                    ▼                               ▼
            ┌──────────────┐              ┌──────────────────┐
            │ SUCCESS:     │              │ FAILURE:          │
            │ All partials │              │ • Timeout (600s)  │
            │ received     │              │ • Worker crash    │
            │              │              │ • Parse error     │
            └──────────────┘              └──────────────────┘
                    │                               │
                    ▼                               ▼
            SignalGenerated                ⚠️ "waiting" FOREVER
            Event Published                No automatic detection
                    │                      No WorkflowFailed
                    │                      No SNS Alert
                    ▼
            ┌──────────────────┐
            │   PORTFOLIO      │
            │   LAMBDA         │
            └──────────────────┘
                    │
                    ▼
            RebalancePlanned
            Event Published
                    │
                    ▼
            ┌──────────────────┐
            │   EXECUTION      │
            │   LAMBDA (SQS)   │
            └──────────────────┘
                    │
            ┌───────┴───────┐
            ▼               ▼
        SUCCESS         FAILURE
            │               │
            ▼               ▼
      TradeExecuted   WorkflowFailed
      + WorkflowCompleted  (📧 SNS Email)
```

---

## Error Handling Decision Points

### Layer 1: Market Data

| Error Type | Source | Handling | Propagation | Notification |
|------------|--------|----------|-------------|--------------|
| `MarketDataError` | API failure | Caught, re-raised as domain error | ✅ Re-raised | None until top-level |
| `DataProviderError` | Critical API failure | Caught, re-raised | ✅ Re-raised | None until top-level |
| Empty bars `[]` | Symbol not found | **Caught, returns `[]`** | ❌ Absorbed | ⚠️ Warning log only |
| Quote `None` | No quote available | **Caught, returns `None`** | ❌ Absorbed | ⚠️ Warning log only |
| Rate limit | API throttling | Retry with backoff | ✅ Re-raised after retries | None |

**Gap:** Empty bars and None quotes silently absorbed without aggregated tracking.

---

### Layer 2: Indicator Service

| Error Type | Source | Handling | Propagation | Notification |
|------------|--------|----------|-------------|--------------|
| Insufficient data | Short price series | **Returns fallback (50.0, 0.0)** | ❌ Absorbed | Debug log only |
| Computation error | Math exception | **Returns fallback** | ❌ Absorbed | ⚠️ Warning log only |
| Missing market data service | Initialization | Allowed (testing) | N/A | None |

**Gap:** Fallback values indistinguishable from real indicator values. No flag to indicate synthetic data.

---

### Layer 3: Feature Pipeline

| Error Type | Source | Handling | Propagation | Notification |
|------------|--------|----------|-------------|--------------|
| Any exception | Computation failure | **Catches `Exception`, returns defaults** | ❌ FULLY ABSORBED | ⚠️ Warning log only |
| Empty bars | No data to process | Returns `{}` | Passed through | None |

**Gap:** Blanket exception handler swallows ALL errors including unexpected ones. Returns neutral defaults that bias strategy decisions.

---

### Layer 4: DSL Evaluator

| Error Type | Source | Handling | Propagation | Notification |
|------------|--------|----------|-------------|--------------|
| `DslEvaluationError` | Empty allocation | ✅ Raised | ✅ Propagates | Error trace entry |
| Symbol eval failure | Per-symbol error | **Logged, symbol skipped** | ⚠️ Partial absorption | Warning log |
| Parse error | Invalid DSL syntax | ✅ Raised | ✅ Propagates | Error trace entry |
| Invalid result type | Wrong return type | ✅ Raised | ✅ Propagates | Error trace entry |

**Gap:** Per-symbol failures silently reduce portfolio without alerting. No count of excluded symbols in final output.

---

### Layer 5: Signal Generation Handler

| Error Type | Source | Handling | Propagation | Notification |
|------------|--------|----------|-------------|--------------|
| `StrategyExecutionError` | Strategy failure | ✅ Raised, publishes WorkflowFailed | ✅ Full propagation | 📧 SNS Email |
| Indicator fetch failure | Per-symbol | **Fallback to 0.0** | ❌ Absorbed | ⚠️ Warning log |
| Empty signals | No allocations | Returns None | Partial propagation | Warning log |

**Gap:** Indicator fallback to 0.0 not flagged in email. Operators cannot distinguish data error from actual zeros.

---

### Layer 6: Aggregator (Multi-Node)

| Error Type | Source | Handling | Propagation | Notification |
|------------|--------|----------|-------------|--------------|
| Session not found | Invalid session ID | ✅ Raised | ✅ Propagates | 📧 WorkflowFailed |
| Partial signal storage failure | DynamoDB error | ✅ Raised | ✅ Propagates | 📧 WorkflowFailed |
| Merge failure | Portfolio merger error | ✅ Raised | ✅ Propagates | 📧 WorkflowFailed |
| **Worker timeout** | Worker Lambda crash | **NO DETECTION** | ❌ NOT PROPAGATED | ❌ NO NOTIFICATION |

**Critical Gap:** If a Strategy Worker Lambda times out or crashes:
- Aggregator stays in "waiting" state
- Session eventually times out after 600s
- No automatic detection mechanism
- No WorkflowFailed event published
- No SNS email to operators

---

## Notification Coverage

### Events That Trigger SNS Email

| Event Type | Source | Trigger Condition | Email Sent |
|------------|--------|-------------------|------------|
| `WorkflowFailed` | Signal Gen | Strategy execution failure | ✅ Yes |
| `WorkflowFailed` | Aggregator | Aggregation error | ✅ Yes |
| `WorkflowFailed` | Portfolio | Rebalance failure | ✅ Yes |
| `WorkflowFailed` | Execution | Trade failure | ✅ Yes |
| `TradeExecuted` | Execution | Successful trades | ✅ Yes |
| `WorkflowCompleted` | Execution | Workflow success | ✅ Yes |

### Events That DON'T Trigger SNS Email

| Condition | Source | Current Behavior | Should Alert? |
|-----------|--------|------------------|---------------|
| Partial symbol failures | DSL Evaluator | Warning log only | ⚠️ If > 10% |
| Indicator fallback used | Signal Gen | Warning log only | ⚠️ If critical symbol |
| Empty bars for symbol | Market Data | Warning log only | ⚠️ If persistent |
| One-sided quote | Market Data | Debug log only | ⚠️ For large positions |
| Aggregation timeout | Aggregator | No detection | ✅ **CRITICAL** |
| Feature pipeline fallback | Feature Pipeline | Warning log only | ⚠️ If > 20% symbols |

---

## Error Correlation Tracking

### Current State

| Field | Usage | Coverage |
|-------|-------|----------|
| `correlation_id` | Passed through all layers | ✅ Good |
| `causation_id` | Links events to triggers | ✅ Good |
| `trace_id` | DSL evaluation tracing | ✅ Good |

### Missing Tracking

| Field | Purpose | Status |
|-------|---------|--------|
| `fallback_used` | Flag when synthetic data used | ❌ Missing |
| `symbols_excluded` | Count of skipped symbols | ❌ Missing |
| `data_quality_score` | Overall data quality metric | ❌ Missing |
| `partial_failure_count` | Multi-node failures | ❌ Missing |

---

## Recommendations

### Critical (Implement Immediately)

1. **Add aggregation timeout detection:**
   - CloudWatch alarm on session age > 5 minutes
   - Background checker Lambda to detect stale "waiting" sessions
   - Publish WorkflowFailed when timeout detected

2. **Add `fallback_used` flag to indicator output:**
   - Include in email metadata
   - Allow operators to identify data quality issues

### High Priority

3. **Track symbol exclusion counts:**
   - Add `symbols_requested` vs `symbols_included` to final output
   - Alert if exclusion rate > 10%

4. **Remove blanket exception handler in feature pipeline:**
   - Handle specific exceptions
   - Let unexpected errors propagate

### Medium Priority

5. **Add data quality metrics to CloudWatch:**
   - `FallbackUsedCount`
   - `EmptyBarsCount`
   - `OneSidedQuoteCount`

6. **Enhance logging with structured fields:**
   - `data_source: "fallback"` vs `data_source: "real"`
   - Enable CloudWatch Insights filtering
