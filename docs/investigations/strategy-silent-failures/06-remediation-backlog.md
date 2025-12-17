# Phase 6: Prioritized Remediation Backlog

**Status:** Complete  
**Date:** 2025-12-15  

## Overview

This document provides a prioritized list of fixes for the silent failure issues identified in Phases 1-5. Each item includes severity, proposed solution, effort estimate, dependencies, and recommended timeline.

---

## Severity Categories

| Category | Definition | Response Time |
|----------|------------|---------------|
| **Critical** | Could produce incorrect trading signals or silent workflow hangs | Fix before next production deployment |
| **High** | Reduces signal quality or hides data issues | Fix within 2 weeks |
| **Medium** | Missing monitoring or test coverage | Fix within 1 month |
| **Low** | Technical debt or documentation | Fix as capacity allows |

---

## Critical Priority (Fix Now)

### REM-001: Add Aggregation Timeout Detection

| Attribute | Value |
|-----------|-------|
| **Issue ID** | SF-014, MC-007, TG-006 |
| **Description** | No detection when strategy workers fail/timeout. Aggregator waits indefinitely in "waiting" state with no notification to operators. |
| **Impact** | Complete workflow failure goes unnoticed. No trade signals generated. |
| **Proposed Solution** | 1. Add scheduled Lambda (every 5 min) to scan for stale sessions<br>2. Publish WorkflowFailed on timeout detection<br>3. Add CloudWatch Alarm on session age > 5 min |
| **Effort** | 2 days |
| **Dependencies** | None |
| **Timeline** | **Before next deployment** |
| **Files to Modify** | `template.yaml`, `aggregator_v2/services/timeout_checker.py` (new) |

**Implementation Notes:**
```python
# New timeout checker Lambda
def check_stale_sessions():
    sessions = session_service.get_sessions_by_status("PENDING")
    for session in sessions:
        age = datetime.now(UTC) - session["created_at"]
        if age > timedelta(minutes=5):
            publish_to_eventbridge(WorkflowFailed(
                workflow_type="aggregation_timeout",
                failure_reason=f"Session {session['id']} timed out after {age}",
                ...
            ))
            session_service.update_session_status(session["id"], "TIMEOUT")
```

---

### REM-002: Add Indicator Fallback Flag to Email

| Attribute | Value |
|-----------|-------|
| **Issue ID** | SF-001, MC-001, TG-001 |
| **Description** | Technical indicators fallback to 0.0 on fetch failure. Email shows 0.0 but operators cannot distinguish data errors from actual zero values. |
| **Impact** | RSI=0.0 could trigger incorrect buy signals. Current price=0.0 could cause division errors. |
| **Proposed Solution** | 1. Add `fallback_used: bool` to indicator response<br>2. Include fallback count in email metadata<br>3. Add CloudWatch metric for fallback events |
| **Effort** | 1 day |
| **Dependencies** | None |
| **Timeline** | **Before next deployment** |
| **Files to Modify** | `signal_generation_handler.py`, `notifications_v2/lambda_handler.py` |

**Implementation Notes:**
```python
# In signal_generation_handler.py
indicators[symbol] = {
    "rsi_10": 0.0,
    "fallback_used": True,  # NEW: Flag synthetic data
}

# In email template
if any(ind.get("fallback_used") for ind in indicators.values()):
    email_body += "\n⚠️ WARNING: Some indicators used fallback values due to data errors"
```

---

### REM-003: Remove Feature Pipeline Blanket Exception Handler

| Attribute | Value |
|-----------|-------|
| **Issue ID** | SF-002, MC-002, TG-002 |
| **Description** | Feature pipeline catches `Exception` and returns neutral defaults. Unexpected errors (bugs) hidden among expected errors (missing data). |
| **Impact** | Artificially "stable" asset appearance. Zero volatility makes assets appear risk-free. |
| **Proposed Solution** | 1. Replace blanket `except Exception` with specific exceptions<br>2. Let unexpected errors propagate<br>3. Return explicit error indicator for expected failures |
| **Effort** | 1 day |
| **Dependencies** | None |
| **Timeline** | **Before next deployment** |
| **Files to Modify** | `feature_pipeline.py` |

**Implementation Notes:**
```python
# BEFORE (BAD)
except Exception as e:
    logger.warning(f"Error extracting price features: {e}")
    return defaults

# AFTER (GOOD)
except (ValueError, ZeroDivisionError, IndexError) as e:
    # Expected errors from bad data
    logger.warning(f"Expected error extracting features: {e}", extra={"symbol": symbol})
    return {"error": str(e), **defaults}  # Explicit error indicator
# Let other exceptions propagate as bugs
```

---

### REM-004: Add Volatility Floor Validation

| Attribute | Value |
|-----------|-------|
| **Issue ID** | SF-008, VG-003, MC-012, TG-008 |
| **Description** | Zero volatility returned on insufficient data. Causes division by zero in inverse-volatility weighting. |
| **Impact** | Over-allocation to assets with data issues. Infinite weights possible. |
| **Proposed Solution** | 1. Add minimum volatility threshold (0.001)<br>2. Return None instead of 0.0 for invalid volatility<br>3. Exclude assets with None volatility from weighting |
| **Effort** | 0.5 days |
| **Dependencies** | None |
| **Timeline** | **Before next deployment** |
| **Files to Modify** | `feature_pipeline.py`, portfolio weighting code |

---

## High Priority (Fix Soon)

### REM-005: Change RSI Fallback from 50.0 to None

| Attribute | Value |
|-----------|-------|
| **Issue ID** | SF-003, VG-002, MC-003, TG-003 |
| **Description** | RSI returns 50.0 (neutral) when data is insufficient. Indistinguishable from real neutral signal. |
| **Impact** | Strategies may ignore assets that actually have missing data. |
| **Proposed Solution** | 1. Return `None` instead of 50.0 when fallback needed<br>2. Update strategies to handle `None` RSI<br>3. Add logging when fallback used |
| **Effort** | 1 day |
| **Dependencies** | Strategy code updates |
| **Timeline** | Within 2 weeks |
| **Files to Modify** | `indicator_service.py`, strategy DSL files |

---

### REM-006: Log One-Sided Quote Usage

| Attribute | Value |
|-----------|-------|
| **Issue ID** | SF-004, VG-007, MC-004, TG-004 |
| **Description** | Bid-only or ask-only quotes create artificial zero spread. Not logged or tracked. |
| **Impact** | Mid-price equals single valid price. Affects slippage calculations. |
| **Proposed Solution** | 1. Add Warning log when one-sided quote detected<br>2. Add `one_sided_quote: true` flag in response<br>3. Add CloudWatch metric |
| **Effort** | 0.5 days |
| **Dependencies** | None |
| **Timeline** | Within 2 weeks |
| **Files to Modify** | `market_data_service.py` |

---

### REM-007: Remove $100.0 Price Fallback

| Attribute | Value |
|-----------|-------|
| **Issue ID** | SF-005, TG-010 |
| **Description** | Indicator service returns $100.0 as current price when price series is empty. Arbitrary value could cause incorrect position sizing. |
| **Impact** | Position sizing could be completely wrong if $100 price used. |
| **Proposed Solution** | Return `None` instead of $100.0. Require callers to handle missing price. |
| **Effort** | 0.5 days |
| **Dependencies** | Caller updates |
| **Timeline** | Within 2 weeks |
| **Files to Modify** | `indicator_service.py` |

---

### REM-008: Track Symbol Exclusion Counts

| Attribute | Value |
|-----------|-------|
| **Issue ID** | SF-011, MC-006, TG-005 |
| **Description** | Symbols silently excluded from portfolio on evaluation failure. No count in final output. |
| **Impact** | Portfolio may have fewer assets than expected without operator awareness. |
| **Proposed Solution** | 1. Add `symbols_excluded_count` to final signal output<br>2. Add CloudWatch metric<br>3. Alert if exclusion rate > 10% |
| **Effort** | 1 day |
| **Dependencies** | None |
| **Timeline** | Within 2 weeks |
| **Files to Modify** | `dsl_evaluator.py`, `signal_generation_handler.py` |

---

### REM-009: Add Empty Bars Tracking

| Attribute | Value |
|-----------|-------|
| **Issue ID** | SF-006, MC-005 |
| **Description** | Bar fetch failures return empty list. Not tracked or aggregated. |
| **Impact** | Symbols with no data pass through silently. |
| **Proposed Solution** | 1. Add `symbols_with_no_data: list[str]` to workflow output<br>2. Add CloudWatch metric<br>3. Log percentage of symbols with missing data |
| **Effort** | 0.5 days |
| **Dependencies** | None |
| **Timeline** | Within 2 weeks |
| **Files to Modify** | `market_data_adapter.py`, `signal_generation_handler.py` |

---

## Medium Priority (Fix Within Month)

### REM-010: Add Price Sanity Validation

| Attribute | Value |
|-----------|-------|
| **Issue ID** | VG-001 |
| **Description** | No validation that prices are within reasonable bounds. |
| **Impact** | Extreme prices could cause incorrect allocations. |
| **Proposed Solution** | Add validation: $0.01 ≤ price ≤ $1,000,000 |
| **Effort** | 0.5 days |
| **Dependencies** | None |
| **Timeline** | Within 1 month |
| **Files to Modify** | `market_data_adapter.py` |

---

### REM-011: Add Minimum Bar Count Validation

| Attribute | Value |
|-----------|-------|
| **Issue ID** | VG-004 |
| **Description** | Indicators computed regardless of input data length. MA-200 computed with 50 bars. |
| **Impact** | Indicators meaningless with insufficient data. |
| **Proposed Solution** | Enforce minimum bars: MA-200 requires 200 bars, RSI-14 requires 20 bars |
| **Effort** | 1 day |
| **Dependencies** | None |
| **Timeline** | Within 1 month |
| **Files to Modify** | `indicator_service.py` |

---

### REM-012: Add Quote Staleness Validation

| Attribute | Value |
|-----------|-------|
| **Issue ID** | VG-005 |
| **Description** | Quote timestamps not validated for freshness. |
| **Impact** | Stale quotes used for trading decisions. |
| **Proposed Solution** | Add validation: quote_age < 5 minutes |
| **Effort** | 0.5 days |
| **Dependencies** | None |
| **Timeline** | Within 1 month |
| **Files to Modify** | `market_data_service.py` |

---

### REM-013: Enhance Allocation Sum Validation

| Attribute | Value |
|-----------|-------|
| **Issue ID** | VG-006 |
| **Description** | Allocation sum validation only warns, doesn't block. |
| **Impact** | Under/over-invested portfolio possible. |
| **Proposed Solution** | Block if allocation sum deviation > 5% from 1.0 |
| **Effort** | 0.5 days |
| **Dependencies** | None |
| **Timeline** | Within 1 month |
| **Files to Modify** | `portfolio_merger.py` |

---

### REM-014: Add Test Coverage for Critical Gaps

| Attribute | Value |
|-----------|-------|
| **Issue ID** | TG-001 through TG-010 |
| **Description** | Critical error scenarios lack test coverage. |
| **Impact** | Error handling not validated. Regressions possible. |
| **Proposed Solution** | Create tests per Phase 4 recommendations |
| **Effort** | 5 days |
| **Dependencies** | REM-001 through REM-009 |
| **Timeline** | Within 1 month |
| **Files to Modify** | `tests/strategy_v2/**`, `tests/aggregator_v2/**` |

---

### REM-015: Create CloudWatch Dashboard

| Attribute | Value |
|-----------|-------|
| **Issue ID** | MC-001 through MC-012 |
| **Description** | No centralized visibility into silent failures. |
| **Impact** | Operators unaware of data quality issues. |
| **Proposed Solution** | Create Strategy Health Dashboard per Phase 5 recommendations |
| **Effort** | 1 day |
| **Dependencies** | REM-001 through REM-009 (metrics) |
| **Timeline** | Within 1 month |
| **Files to Modify** | `template.yaml` (dashboard resource) |

---

## Low Priority (As Capacity Allows)

### REM-016: Add Decimal Precision Standardization

| Attribute | Value |
|-----------|-------|
| **Issue ID** | VG-010 |
| **Description** | No explicit precision limits for Decimal values. |
| **Impact** | Rounding errors could accumulate. |
| **Proposed Solution** | Add precision standardization utility |
| **Effort** | 1 day |
| **Dependencies** | None |
| **Timeline** | As capacity allows |

---

### REM-017: Add Symbol Universe Validation

| Attribute | Value |
|-----------|-------|
| **Issue ID** | VG-009 |
| **Description** | Unknown symbols cause API calls that return empty. |
| **Impact** | Wasted rate limit. |
| **Proposed Solution** | Validate symbols against known universe before API calls |
| **Effort** | 1 day |
| **Dependencies** | Universe configuration |
| **Timeline** | As capacity allows |

---

## Implementation Roadmap

### Week 1 (Critical)

| Day | Task | Owner |
|-----|------|-------|
| Mon | REM-001: Aggregation timeout detection | - |
| Tue | REM-002: Indicator fallback flag | - |
| Wed | REM-003: Feature pipeline exception handling | - |
| Thu | REM-004: Volatility floor validation | - |
| Fri | Testing & validation | - |

### Week 2 (High)

| Day | Task | Owner |
|-----|------|-------|
| Mon | REM-005: RSI fallback change | - |
| Tue | REM-006: One-sided quote logging | - |
| Wed | REM-007: Remove $100 price fallback | - |
| Thu | REM-008: Symbol exclusion tracking | - |
| Fri | REM-009: Empty bars tracking | - |

### Week 3-4 (Medium)

- REM-010 through REM-015
- Test coverage improvements
- Dashboard creation

---

## Effort Summary

| Priority | Items | Total Effort |
|----------|-------|--------------|
| Critical | 4 | 4.5 days |
| High | 5 | 3.5 days |
| Medium | 6 | 8.5 days |
| Low | 2 | 2 days |
| **Total** | **17** | **18.5 days** |

---

## Success Criteria

Investigation remediation is complete when:

- [ ] **REM-001**: Aggregation timeout detected and alerted within 5 minutes
- [ ] **REM-002**: Emails indicate when fallback values used
- [ ] **REM-003**: Feature pipeline only catches expected exceptions
- [ ] **REM-004**: Zero volatility returns None, excluded from weighting
- [ ] **REM-005**: RSI=None distinguishes missing data from neutral signal
- [ ] **REM-006**: One-sided quotes logged and tracked
- [ ] **REM-007**: No synthetic $100 prices in system
- [ ] **REM-008**: Symbol exclusion counts visible to operators
- [ ] **REM-009**: Empty bars percentage tracked
- [ ] **REM-014**: Test coverage for all critical error scenarios
- [ ] **REM-015**: CloudWatch Dashboard operational

---

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Breaking strategy logic when changing fallbacks | Medium | High | Comprehensive testing before deployment |
| False positive alerts on new metrics | High | Low | Start with Warning, tune thresholds |
| Performance impact from additional logging | Low | Low | Use structured logging, sample if needed |
| Incomplete fix due to scope creep | Medium | Medium | Strict adherence to remediation scope |

---

## Appendix: Quick Reference

### Files Most Modified

1. `the_alchemiser/strategy_v2/handlers/signal_generation_handler.py` - REM-002, REM-008, REM-009
2. `the_alchemiser/strategy_v2/adapters/feature_pipeline.py` - REM-003, REM-004
3. `the_alchemiser/strategy_v2/indicators/indicator_service.py` - REM-005, REM-007, REM-011
4. `the_alchemiser/shared/services/market_data_service.py` - REM-006, REM-012
5. `the_alchemiser/aggregator_v2/lambda_handler.py` - REM-001
6. `template.yaml` - REM-001, REM-015

### New Files Created

1. `the_alchemiser/aggregator_v2/services/timeout_checker.py` - REM-001
2. `tests/strategy_v2/handlers/test_signal_generation_handler.py` - REM-014
3. `tests/aggregator_v2/test_timeout_detection.py` - REM-014
