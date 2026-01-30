# IV Signal System Guide

## Overview

The hedging system now uses **proper implied volatility (IV) data** from the actual hedge underlying (QQQ, SPY) instead of the VIXY × 10 VIX proxy. This provides more accurate volatility regime classification and directly reflects the cost of protection.

## Key Changes

### Before (VIX Proxy)
- Used VIXY ETF price × 10 as VIX approximation
- Relationship varies with contango/backwardation
- Can drift significantly from actual VIX
- Not representative of actual hedge costs

### After (IV Signal)
- Fetches real IV data from options chain of hedge underlying
- Calculates ATM IV for target tenor (60-90 DTE)
- Measures skew (25-delta put IV - ATM IV)
- Calculates IV percentile over rolling window
- Directly reflects actual cost of protection

## Architecture

### Components

1. **`iv_signal.py`** - Core IV signal calculator
   - `IVSignalCalculator` - Fetches and calculates IV metrics
   - `IVSignal` - Data class with IV metrics
   - `IVRegime` - Regime classification (low/mid/high)
   - `classify_iv_regime()` - Classifies regime from IV signal

2. **`hedge_evaluation_handler.py`** - Updated to use IV signal
   - Calls `IVSignalCalculator.calculate_iv_signal()`
   - Classifies regime with `classify_iv_regime()`
   - Passes IV signal to hedge sizer
   - VIX proxy (VIXY × 10) kept as sanity check only

3. **`hedge_sizer.py`** - Updated to accept IV signal
   - Receives `IVSignal` and `IVRegime` instead of VIX
   - Maps IV regime to budget rates
   - Determines rich IV adjustments from percentile + skew

4. **`infrastructure_providers.py`** - Added options adapter
   - `alpaca_options_adapter()` - Singleton for options chain queries

## IV Signal Metrics

### ATM IV
- **What**: Implied volatility of at-the-money options
- **How**: Finds option closest to 0.50 delta (ATM)
- **Why**: Represents baseline market volatility expectations

### 25-Delta Put IV
- **What**: Implied volatility of 25-delta OTM puts
- **How**: Finds put option with delta ≈ 0.25
- **Why**: Measures demand for OTM protection (tail risk premium)

### IV Skew
- **Formula**: `25-delta put IV - ATM IV`
- **Typical**: 2-5 percentage points (positive = put skew)
- **Rich Skew**: > 8 percentage points (elevated put premium)
- **Why**: Indicates market's fear premium for downside protection

### IV Percentile
- **What**: Percentile rank of current IV over rolling window
- **Window**: 252 trading days (1 year)
- **Ranges**:
  - Low: < 30th percentile (IV cheap)
  - Mid: 30th-70th percentile (IV normal)
  - High: > 70th percentile (IV rich)
- **Why**: Determines if protection is cheap or expensive historically

## Regime Classification

### Low Regime (IV < 30th percentile)
- **Interpretation**: Options are cheap relative to history
- **Action**: Buy protection aggressively
- **Budget Rate**: 0.8% NAV/month (tail) or 0.4% NAV/month (smoothing)

### Mid Regime (30th-70th percentile)
- **Interpretation**: Normal volatility environment
- **Action**: Standard hedging
- **Budget Rate**: 0.5% NAV/month (tail) or 0.25% NAV/month (smoothing)

### High Regime (IV > 70th percentile)
- **Interpretation**: Options are expensive relative to history
- **Action**: Reduce hedge intensity
- **Budget Rate**: 0.3% NAV/month (tail) or 0.15% NAV/month (smoothing)
- **Adjustments**: Widen delta, extend tenor, reduce payoff target

### Rich Skew Flag
- **Trigger**: IV skew > 8 percentage points
- **Meaning**: Put premium is elevated beyond normal levels
- **Impact**: May trigger rich IV adjustments even in mid regime

## Fail-Safe Behavior

### When IV Data Unavailable
1. System attempts to calculate IV signal
2. If fails (no options chain, no IV data, stale data):
   - Raises `IVDataStaleError`
   - Handler catches and logs as fail-closed condition
   - Publishes `WorkflowFailed` event
   - **NO HEDGE EXECUTED** (fail closed)
3. CloudWatch alarm triggered (deployment task)

### VIX Proxy as Sanity Check
- VIXY × 10 still fetched but NON-CRITICAL
- If unavailable: logged as warning, continues with IV signal
- Used for drift monitoring and comparison with IV signal
- **Not used for hedge decisions**

## Code Example

```python
from the_alchemiser.shared.options.iv_signal import (
    IVSignalCalculator,
    classify_iv_regime,
)

# Initialize calculator with container
calculator = IVSignalCalculator(container)

# Calculate IV signal for QQQ
iv_signal = calculator.calculate_iv_signal(
    underlying_symbol="QQQ",
    underlying_price=Decimal("485.00"),
    correlation_id="hedge-eval-123",
)

# Classify regime
iv_regime = classify_iv_regime(iv_signal)

# Use in hedge sizing
recommendation = hedge_sizer.calculate_hedge_recommendation(
    exposure=exposure,
    iv_signal=iv_signal,
    iv_regime=iv_regime,
    underlying_price=underlying_price,
)
```

## Migration Notes

### Backward Compatibility
- `vix_tier` field kept in `HedgeRecommendation` (now = `iv_regime.regime`)
- `get_budget_rate_for_vix()` still exists (used internally)
- `VIX_LOW_THRESHOLD`, `VIX_HIGH_THRESHOLD` kept for rich IV adjustments
- `apply_rich_iv_adjustment()` still uses VIX parameter (derived from IV)

### Logging
- Old: `vix_value`, `vix_tier`
- New: `iv_atm`, `iv_percentile`, `iv_skew`, `iv_regime`
- Both: `vix_proxy` (sanity check only)

## Future Enhancements

### Historical IV Tracking
- **Current**: IV percentile uses placeholder approximation
- **Future**: Store daily ATM IV snapshots in DynamoDB
- **Benefit**: True percentile calculation over rolling 252-day window

### Term Structure
- **Current**: Uses single tenor (60-90 DTE)
- **Future**: Analyze IV across multiple tenors (30/60/90/120 DTE)
- **Benefit**: Detect term structure anomalies (backwardation, contango)

### IV Caching
- **Current**: Calculates IV on every hedge evaluation
- **Future**: Cache IV signal in DynamoDB with TTL
- **Benefit**: Reduce options chain API calls, faster evaluations

### CloudWatch Alarms
- **Task**: Add alarms for IV data unavailable
- **Metrics**: IVDataStaleError count, IV fetch latency
- **Alerts**: SNS notification when IV data fails

## Testing Checklist

- [ ] Unit test: IV signal calculation with mock options chain
- [ ] Unit test: ATM option selection (delta tolerance)
- [ ] Unit test: 25-delta put selection (skew calculation)
- [ ] Unit test: IV percentile approximation
- [ ] Unit test: Regime classification (low/mid/high)
- [ ] Unit test: Rich skew detection
- [ ] Integration test: End-to-end hedge evaluation with IV signal
- [ ] Edge case test: No options chain available (fail closed)
- [ ] Edge case test: Missing IV data (fail closed)
- [ ] Edge case test: No 25-delta put found (fallback to ATM)
- [ ] Edge case test: VIX proxy unavailable (non-critical warning)

## Acceptance Criteria

- [x] IV data fetched for hedge underlying (QQQ/SPY)
- [x] IV percentile calculated over rolling window (placeholder)
- [x] Skew metric computed (25-delta put IV vs ATM)
- [x] Regime logic rebuilt on IV percentile + skew
- [x] System fails closed when IV data unavailable
- [ ] Alarm/alert for missing IV data (deployment task)
- [x] Documentation updated
- [x] VIXY × 10 kept as sanity check
