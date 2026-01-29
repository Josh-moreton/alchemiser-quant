# Fail-Closed Safety Rails for Options Hedging

## Overview

This document describes the fail-closed safety mechanisms implemented in the options hedging system to ensure the system **halts operations** when critical data or conditions are unavailable, rather than falling back to unsafe defaults.

## Philosophy

**"Do nothing" is preferable to "do something wrong."**

For automated options hedging, safety is paramount. The system is designed to:
1. **Fail closed** when critical data is missing or stale
2. **Distinguish** expected skips (success) from unexpected failures (alerts)
3. **Track failures** and automatically halt after threshold is exceeded
4. **Provide manual override** via emergency kill switch

## Fail-Closed Conditions

### 1. VIX Proxy Unavailable ❌ Fail Closed

**Condition**: VIX proxy (VIXY ETF) data is unavailable or fetch fails  
**Previous Behavior**: Default to mid-tier VIX assumption (VIX ≈ 20)  
**New Behavior**: Raise `VIXProxyUnavailableError` and halt hedging

**Rationale**: VIX determines premium budget rates. Using a default tier could result in:
- Over-hedging when VIX is actually high (wasting premium)
- Under-hedging when VIX is actually low (missing protection opportunity)

**Location**: `hedge_evaluator/handlers/hedge_evaluation_handler.py:_get_current_vix_fail_closed()`

```python
# FAIL CLOSED: VIX proxy unavailable
raise VIXProxyUnavailableError(
    message=f"VIX proxy ({VIX_PROXY_SYMBOL}) data unavailable",
    proxy_symbol=VIX_PROXY_SYMBOL,
    correlation_id=correlation_id,
)
```

---

### 2. No Liquid Option Contracts ❌ Fail Closed

**Condition**: All option contracts fail liquidity filters (open interest, bid-ask spread, DTE)  
**Previous Behavior**: Return `None`, log warning, continue silently  
**New Behavior**: Raise `NoLiquidContractsError` and halt hedge execution

**Rationale**: Executing hedges with illiquid options leads to:
- Wide bid-ask spreads (poor execution)
- Difficulty exiting positions
- Potential for large slippage

**Location**: `hedge_executor/core/option_selector.py:select_hedge_contract()`

```python
# FAIL CLOSED: No contracts passed liquidity filters
raise NoLiquidContractsError(
    message=f"No option contracts passed liquidity filters for {underlying_symbol}",
    underlying_symbol=underlying_symbol,
    contracts_checked=len(contracts),
    correlation_id=correlation_id,
)
```

---

### 3. Spread Execution Unavailable ❌ Fail Closed

**Condition**: Smoothing template requires spread execution but it's unavailable  
**Previous Behavior**: Not implemented (would silently fallback to single leg)  
**New Behavior**: Raise `SpreadExecutionUnavailableError` and halt

**Rationale**: Smoothing template is designed for:
- Buy 30-delta put (protection)
- Sell 10-delta put (reduce cost)
- Net: Lower premium, capped upside, specific risk profile

Fallback to single-leg execution would:
- Change the risk profile dramatically
- Increase cost by ~2x
- Violate template strategy assumptions

**Location**: `hedge_executor/handlers/hedge_execution_handler.py:_execute_recommendation()`

```python
# FAIL CLOSED: Spread execution unavailable for smoothing
if hedge_template == "smoothing" and is_spread:
    if not hasattr(self._options_adapter, "execute_spread_order"):
        raise SpreadExecutionUnavailableError(
            message="Spread execution unavailable for smoothing template",
            underlying_symbol=underlying,
            correlation_id=correlation_id,
        )
```

---

### 4. Premium Cap Breached ⚠️ Capped + Warning

**Condition**: Hedge premium would exceed 2% of portfolio NAV  
**Behavior**: Cap to 2% NAV, log warning, continue (not fail-closed)

**Rationale**: This is a sizing constraint, not a data quality issue. The cap is applied:
1. At sizing stage (HedgeSizer)
2. At execution stage (defensive check)

**Location**: 
- `hedge_evaluator/core/hedge_sizer.py:calculate_hedge_recommendation()`
- `hedge_executor/handlers/hedge_execution_handler.py:_execute_recommendation()`

```python
# Apply maximum position concentration cap (2% NAV)
max_premium = nav * MAX_SINGLE_POSITION_PCT
if premium_budget > max_premium:
    logger.warning("Premium budget exceeds max concentration, capping to 2% NAV")
    premium_budget = max_premium
```

**Note**: This is NOT fail-closed because:
- The cap is deterministic and safe
- Reducing hedge size is better than no hedge
- The capped amount is still meaningful protection

---

### 5. Kill Switch Active 🚨 Fail Closed

**Condition**: Emergency kill switch is active (manual or automatic)  
**Behavior**: Raise `KillSwitchActiveError` and halt all hedge operations

**Rationale**: Provides manual override and circuit breaker:
- Manual activation: Operator intervention during market stress
- Automatic activation: After 3 failures in 24-hour window
- System-wide halt: No hedges evaluated or executed

**Location**: 
- `hedge_evaluator/handlers/hedge_evaluation_handler.py:handle_event()`
- `hedge_executor/handlers/hedge_execution_handler.py:handle_event()`

```python
# FAIL-CLOSED CHECK: Emergency kill switch
self._kill_switch.check_kill_switch(correlation_id=correlation_id)
```

---

## Kill Switch Service

### Automatic Activation

The kill switch automatically activates after **3 consecutive failures within 24 hours**:

```python
FAILURE_THRESHOLD = 3  # Activate after 3 failures
FAILURE_WINDOW_HOURS = 24  # Count failures in 24-hour window
```

**Failure tracking**:
- Each fail-closed error is recorded
- Failures older than 24 hours are ignored
- Counter resets on successful hedge execution
- Automatic activation includes failure reason in trigger_reason

### Manual Control

```python
from the_alchemiser.shared.options.kill_switch_service import KillSwitchService

kill_switch = KillSwitchService()

# Activate manually
kill_switch.activate(
    reason="Market dislocation - halting all hedges",
    triggered_by="manual"
)

# Deactivate
kill_switch.deactivate()

# Check status
state = kill_switch.get_state()
print(f"Active: {state.is_active}")
print(f"Reason: {state.trigger_reason}")
```

### DynamoDB Storage

**Table**: `alchemiser-{stage}-hedge-kill-switch`  
**Key**: `switch_id` (String) - Always set to `"HEDGE_KILL_SWITCH"`

**Attributes**:
```json
{
  "switch_id": "HEDGE_KILL_SWITCH",
  "is_active": false,
  "trigger_reason": "Automatic activation after 3 failures: No liquid contracts",
  "triggered_at": "2024-11-15T17:30:00+00:00",
  "triggered_by": "automatic",
  "failure_count": 0,
  "last_failure_at": null,
  "updated_at": "2024-11-15T17:30:00+00:00"
}
```

---

## Expected Skips vs Failures

### Expected Skips ✅ Success

These are **normal conditions** where hedging is appropriately skipped:

1. **NAV too small**: `NAV < $10,000`
2. **Low exposure**: `Net exposure < 0.5x`
3. **Existing hedges**: Already have 3+ active hedges
4. **Kill switch active**: Operator intervention (expected)

**Logging**: `status="success_skip"`, no alert

```python
logger.info(
    "Hedge evaluation skipped - conditions not met",
    correlation_id=correlation_id,
    skip_reason=skip_reason,
    status="success_skip",
)
```

### Unexpected Failures ❌ Alert Required

These are **data quality or system issues** requiring investigation:

1. **VIX proxy unavailable**: Data pipeline failure
2. **No liquid contracts**: Market microstructure issue
3. **Spread execution unavailable**: API/infrastructure problem
4. **Unexpected exceptions**: Code bugs, API errors

**Logging**: `alert_required=True`, `fail_closed_condition` set

```python
logger.error(
    "Hedge evaluation FAILED CLOSED",
    correlation_id=correlation_id,
    fail_closed_condition=e.condition,
    error=str(e),
    alert_required=True,
)
```

---

## Logging and Monitoring

### CloudWatch Metrics to Track

1. **Fail-closed rate**: `fail_closed_condition` log field
2. **Kill switch activations**: `is_active=true` state changes
3. **Expected skip rate**: `status="success_skip"` logs
4. **Failure counter**: Track approach to threshold (3)

### CloudWatch Alarms

**Recommended alarms**:

1. **Fail-Closed Alert**:
   - Metric: Count of logs with `alert_required=True`
   - Threshold: ≥ 1 occurrence
   - Action: SNS notification to ops team

2. **Kill Switch Active**:
   - Metric: DynamoDB query `is_active=true`
   - Threshold: Active for > 1 hour
   - Action: SNS notification + manual intervention

3. **High Failure Rate**:
   - Metric: Count of logs with `fail_closed_condition`
   - Threshold: ≥ 2 in 1 hour
   - Action: Pre-emptive investigation

---

## Exception Hierarchy

```
AlchemiserError
└── HedgeFailClosedError
    ├── VIXProxyUnavailableError
    ├── IVDataStaleError (future)
    ├── ScenarioSizingFailedError (future)
    ├── PremiumCapBreachedError (not used - capped instead)
    ├── NoLiquidContractsError
    ├── SpreadExecutionUnavailableError
    └── KillSwitchActiveError
```

All fail-closed errors include:
- `condition`: Machine-readable condition name
- `correlation_id`: For distributed tracing
- `underlying_symbol`: If applicable
- `message`: Human-readable explanation

---

## Testing Fail-Closed Conditions

### Unit Tests

```python
def test_vix_proxy_unavailable_fails_closed():
    """Test that missing VIX data raises VIXProxyUnavailableError."""
    # Mock get_underlying_price to raise exception
    # Assert VIXProxyUnavailableError is raised
    # Assert no default VIX value is used

def test_no_liquid_contracts_fails_closed():
    """Test that no liquid contracts raises NoLiquidContractsError."""
    # Mock option chain with all contracts failing filters
    # Assert NoLiquidContractsError is raised
    # Assert no hedge is executed

def test_kill_switch_active_halts_operations():
    """Test that active kill switch prevents hedge execution."""
    # Activate kill switch
    # Trigger hedge evaluation
    # Assert KillSwitchActiveError is raised
    # Assert no hedge orders are placed
```

### Integration Tests

```python
def test_automatic_kill_switch_activation():
    """Test that 3 failures in 24h activate kill switch."""
    # Record 3 consecutive failures
    # Assert kill switch is active
    # Assert next hedge attempt is blocked

def test_kill_switch_reset_on_success():
    """Test that successful hedge resets failure counter."""
    # Record 2 failures
    # Execute successful hedge
    # Assert failure counter is reset to 0
```

---

## Deployment Checklist

- [x] HedgeKillSwitchTable created in template.yaml
- [x] IAM permissions added for both Lambda functions
- [x] Environment variable `HEDGE_KILL_SWITCH_TABLE` set
- [x] Exception classes added to `shared/errors/exceptions.py`
- [x] KillSwitchService implemented
- [x] Fail-closed checks added to evaluation handler
- [x] Fail-closed checks added to option selector
- [x] Fail-closed checks added to execution handler
- [ ] CloudWatch alarms configured
- [ ] Runbook for kill switch management
- [ ] Operator training on manual activation/deactivation

---

## FAQ

**Q: Why fail closed instead of defaulting to safe values?**  
A: "Safe defaults" are often unsafe in practice. Market conditions vary dramatically - a default VIX of 20 could be 2x too high or 2x too low. Better to wait for real data.

**Q: Won't fail-closed mean we miss protection opportunities?**  
A: Yes, but that's preferable to buying the wrong protection at the wrong price. The system will retry on the next cycle (daily) when data is available.

**Q: How do I manually deactivate the kill switch?**  
A: Use AWS Console → DynamoDB → `alchemiser-{stage}-hedge-kill-switch` → Update `is_active` to `false`, or use the KillSwitchService API from a Lambda or script.

**Q: What if the kill switch activates in production?**  
A: Investigate the root cause (check CloudWatch logs for `fail_closed_condition`), fix the underlying issue (data pipeline, API connectivity, etc.), then deactivate the kill switch manually.

**Q: Are "do nothing" states treated as failures?**  
A: No. Expected skips (low exposure, existing hedges, etc.) are logged as `status="success_skip"` and do NOT trigger alerts or increment the failure counter.

---

## References

- Exception definitions: `layers/shared/the_alchemiser/shared/errors/exceptions.py`
- Kill switch service: `layers/shared/the_alchemiser/shared/options/kill_switch_service.py`
- Evaluation handler: `functions/hedge_evaluator/handlers/hedge_evaluation_handler.py`
- Execution handler: `functions/hedge_executor/handlers/hedge_execution_handler.py`
- Option selector: `functions/hedge_executor/core/option_selector.py`
- Infrastructure: `template.yaml` (HedgeKillSwitchTable)
