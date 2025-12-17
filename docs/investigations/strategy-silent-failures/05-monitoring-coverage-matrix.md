# Phase 5: Monitoring & Alerting Coverage Matrix

**Status:** Complete  
**Date:** 2025-12-15  

## Overview

This document assesses the current monitoring and alerting capabilities for silent failures in the Strategy module. It identifies what's being tracked, what's missing, and recommendations for improved operator visibility.

---

## Current Monitoring Infrastructure

### AWS Services in Use

| Service | Purpose | Configuration |
|---------|---------|---------------|
| **CloudWatch Logs** | Structured JSON logs from all Lambdas | Log groups per Lambda |
| **EventBridge** | Event routing and workflow orchestration | AlchemiserEventBus |
| **SNS** | Email notifications | TradingNotificationsTopic |
| **DynamoDB** | Session tracking (aggregation) | AggregationSessionsTable |
| **SQS** | Execution buffering | ExecutionQueue + DLQ |

### Notification Flow

```
Lambda Error → WorkflowFailed Event → EventBridge → Notifications Lambda → SNS → Email
```

---

## Monitoring Coverage Matrix

### Silent Failure Types

| ID | Silent Failure | CloudWatch Metric | CloudWatch Log | EventBridge Event | SNS Alert | Status |
|----|----------------|-------------------|----------------|-------------------|-----------|--------|
| MC-001 | Technical indicator fallback (0.0) | ❌ None | ⚠️ Warning only | ❌ None | ❌ None | **GAP** |
| MC-002 | Feature pipeline exception swallow | ❌ None | ⚠️ Warning only | ❌ None | ❌ None | **GAP** |
| MC-003 | RSI neutral fallback (50.0) | ❌ None | Debug only | ❌ None | ❌ None | **GAP** |
| MC-004 | Quote one-sided fallback | ❌ None | Debug only | ❌ None | ❌ None | **GAP** |
| MC-005 | Empty bars for symbol | ❌ None | ⚠️ Warning only | ❌ None | ❌ None | **GAP** |
| MC-006 | Symbol exclusion in DSL | ❌ None | ⚠️ Warning only | ❌ None | ❌ None | **GAP** |
| MC-007 | Aggregation timeout | ❌ None | ❌ None | ❌ None | ❌ None | **CRITICAL GAP** |
| MC-008 | Strategy execution failure | ❌ None | ✅ Error | ✅ WorkflowFailed | ✅ Email | ✅ Covered |
| MC-009 | Aggregator error | ❌ None | ✅ Error | ✅ WorkflowFailed | ✅ Email | ✅ Covered |
| MC-010 | Trade execution failure | ❌ None | ✅ Error | ✅ WorkflowFailed | ✅ Email | ✅ Covered |
| MC-011 | DLQ messages | ⚠️ Implicit | ✅ Error | N/A | ⚠️ DLQAlertTopic | ⚠️ Partial |
| MC-012 | Zero volatility | ❌ None | ❌ None | ❌ None | ❌ None | **GAP** |

### Coverage Summary

| Status | Count | Percentage |
|--------|-------|------------|
| ✅ Fully Covered | 3 | 25% |
| ⚠️ Partially Covered | 2 | 17% |
| ❌ Not Covered (Gap) | 7 | 58% |

---

## Detailed Gap Analysis

### MC-001: Technical Indicator Fallback (0.0)

**Current State:**
- Warning log: `"Failed to fetch technical indicators for {symbol}: {e}"`
- No metric emitted
- No event published
- No alert configured

**Impact:** Operators receive emails with indicator values of 0.0 but cannot distinguish data errors from actual zero values.

**Recommendation:**
1. Add CloudWatch metric: `Alchemiser/Strategy/IndicatorFallbackCount`
2. Add structured log field: `"fallback_used": true`
3. Add CloudWatch Alarm: Alert if > 0 fallbacks in any workflow

**Proposed Metric:**
```python
cloudwatch.put_metric_data(
    Namespace='Alchemiser/Strategy',
    MetricData=[{
        'MetricName': 'IndicatorFallbackCount',
        'Value': 1,
        'Unit': 'Count',
        'Dimensions': [
            {'Name': 'Symbol', 'Value': symbol},
            {'Name': 'CorrelationId', 'Value': correlation_id}
        ]
    }]
)
```

---

### MC-002: Feature Pipeline Exception Swallowing

**Current State:**
- Warning log: `"Error extracting price features: {e}"`
- Exception type not preserved in log
- No metric or alert

**Impact:** All exceptions treated equally. Unexpected errors (bugs) hidden among expected errors (missing data).

**Recommendation:**
1. Add CloudWatch metric: `Alchemiser/Strategy/FeaturePipelineError`
2. Dimension by exception type to distinguish expected vs unexpected
3. Alert on unexpected exception types

---

### MC-003: RSI Neutral Fallback (50.0)

**Current State:**
- Debug log only (not visible in standard monitoring)
- No indication that 50.0 is synthetic

**Impact:** Neutral RSI signals indistinguishable from data quality issues.

**Recommendation:**
1. Upgrade to Warning log when fallback used
2. Add structured field: `"rsi_source": "fallback"` vs `"rsi_source": "computed"`
3. Create CloudWatch Insights query for fallback detection

---

### MC-004: Quote One-Sided Fallback

**Current State:**
- Debug log only
- Not tracked or alerted

**Impact:** Zero-spread quotes used without operator awareness.

**Recommendation:**
1. Add CloudWatch metric: `Alchemiser/MarketData/OneSidedQuoteCount`
2. Add Warning log for one-sided quote detection
3. Alert if one-sided quotes exceed threshold for large positions

---

### MC-005: Empty Bars for Symbol

**Current State:**
- Warning log: `"Failed to fetch bars"`
- Returns empty list silently

**Impact:** Symbols with no data pass through pipeline, potentially excluded from portfolio without tracking.

**Recommendation:**
1. Add CloudWatch metric: `Alchemiser/MarketData/EmptyBarsCount`
2. Track percentage of symbols with missing data per workflow
3. Alert if > 10% symbols have empty bars

---

### MC-006: Symbol Exclusion in DSL

**Current State:**
- Warning log for per-symbol failures
- No aggregated count in final output

**Impact:** Portfolio may be unexpectedly reduced without operator awareness.

**Recommendation:**
1. Add metric: `Alchemiser/Strategy/SymbolExclusionCount`
2. Add to SignalGenerated event: `symbols_excluded_count`
3. Alert if exclusion rate > 10%

---

### MC-007: Aggregation Timeout (CRITICAL)

**Current State:**
- **NO MONITORING AT ALL**
- Session stays in "waiting" state indefinitely
- No CloudWatch Alarm
- No WorkflowFailed event
- No SNS notification

**Impact:** Strategy workers can die silently, aggregator waits forever, no trade signals generated, operator unaware.

**Recommendation (CRITICAL):**
1. Add CloudWatch Alarm on DynamoDB: Sessions with `status=PENDING` and `created_at` > 5 minutes ago
2. Add timeout checker Lambda (scheduled every 5 minutes)
3. Publish WorkflowFailed on timeout detection
4. Alert immediately on any aggregation timeout

**Proposed CloudWatch Alarm:**
```yaml
AggregationTimeoutAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: AggregationSessionTimeout
    MetricName: PendingSessionAge
    Namespace: Alchemiser/Aggregation
    Statistic: Maximum
    Period: 60
    EvaluationPeriods: 5
    Threshold: 300  # 5 minutes
    ComparisonOperator: GreaterThanThreshold
    AlarmActions:
      - !Ref DLQAlertTopic
```

---

### MC-011: DLQ Messages (Partial)

**Current State:**
- DLQAlertTopic configured
- Messages land in ExecutionDLQ after 3 retries
- Alert may be delayed or missed

**Impact:** Failed trade executions may not be noticed immediately.

**Recommendation:**
1. Add CloudWatch Alarm on DLQ message count > 0
2. Ensure DLQAlertTopic has active subscriptions
3. Add structured logging in DLQ consumer

---

### MC-012: Zero Volatility

**Current State:**
- No logging when zero volatility calculated
- No metric or alert

**Impact:** Assets with zero volatility could receive infinite weight in inverse-vol weighting.

**Recommendation:**
1. Add Warning log when volatility = 0.0
2. Add metric: `Alchemiser/Strategy/ZeroVolatilityCount`
3. Alert if any asset has zero volatility in production

---

## CloudWatch Insights Queries

### Recommended Queries for Monitoring Gaps

**1. Find Indicator Fallbacks:**
```
fields @timestamp, @message
| filter @message like /Failed to fetch technical indicators/
| stats count() by bin(1h)
```

**2. Find Feature Pipeline Errors:**
```
fields @timestamp, @message, exception_type
| filter @message like /Error extracting price features/
| stats count() by exception_type
```

**3. Find One-Sided Quotes:**
```
fields @timestamp, symbol, bid_price, ask_price
| filter bid_price = ask_price AND ask_price > 0
| stats count() by symbol
```

**4. Find Stale Aggregation Sessions:**
```
# Requires custom logging to be added
fields @timestamp, session_id, status, age_seconds
| filter status = "PENDING" AND age_seconds > 300
| sort @timestamp desc
```

---

## Proposed CloudWatch Dashboard

### Strategy Health Dashboard

| Panel | Metrics | Visualization |
|-------|---------|---------------|
| **Workflow Success Rate** | WorkflowCompleted / (WorkflowCompleted + WorkflowFailed) | Gauge |
| **Indicator Fallback Rate** | IndicatorFallbackCount / TotalIndicatorRequests | Line chart |
| **Empty Bars Rate** | EmptyBarsCount / TotalSymbolsRequested | Line chart |
| **Symbol Exclusion Rate** | SymbolExclusionCount / TotalSymbolsEvaluated | Line chart |
| **Aggregation Session Age** | Max(PendingSessionAge) | Number |
| **DLQ Message Count** | ExecutionDLQ ApproximateNumberOfMessages | Number |
| **One-Sided Quote Count** | OneSidedQuoteCount | Bar chart by symbol |

---

## Alerting Recommendations

### Critical Alerts (PagerDuty/Immediate)

| Alert | Condition | Action |
|-------|-----------|--------|
| **Aggregation Timeout** | Session pending > 5 min | Immediate page |
| **DLQ Non-Empty** | Messages > 0 | Immediate page |
| **Zero Workflow Output** | SignalCount = 0 | Immediate page |

### Warning Alerts (Email/Slack)

| Alert | Condition | Action |
|-------|-----------|--------|
| **High Indicator Fallback** | > 10% fallback rate | Daily email |
| **High Symbol Exclusion** | > 10% exclusion rate | Daily email |
| **One-Sided Quotes** | > 5 one-sided quotes | Daily email |

### Informational (Dashboard Only)

| Metric | Purpose |
|--------|---------|
| Workflow duration | Performance monitoring |
| Symbol coverage | Data quality tracking |
| Strategy contribution breakdown | Portfolio analysis |

---

## Implementation Priority

### Immediate (Before Next Deployment)

1. **MC-007: Aggregation Timeout Detection**
   - Add CloudWatch Alarm on session age
   - Add timeout checker logic
   - Add WorkflowFailed on timeout

### Short-Term (Within 2 Weeks)

2. **MC-001: Indicator Fallback Metric**
   - Add metric emission
   - Add structured log field
   - Create CloudWatch Alarm

3. **MC-011: DLQ Monitoring Enhancement**
   - Add CloudWatch Alarm on DLQ count
   - Verify SNS subscriptions

### Medium-Term (Within 1 Month)

4. **MC-002, MC-003, MC-004, MC-005, MC-006, MC-012**
   - Add metrics for all remaining gaps
   - Create comprehensive dashboard
   - Configure warning alerts

---

## Summary

| Category | Current | Target |
|----------|---------|--------|
| **Silent Failures Monitored** | 3/12 (25%) | 12/12 (100%) |
| **CloudWatch Metrics** | 0 custom | 7+ custom |
| **CloudWatch Alarms** | ~2 | 8+ |
| **Dashboard Panels** | 0 | 7 |
