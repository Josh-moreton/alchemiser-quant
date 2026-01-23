# Hypothesis: Composer Backtest Lookahead Bias

**Created:** 2026-01-23
**Status:** Testing
**Fix Applied:** Live bars disabled in dev environment (commit 1fda9aa5)

---

## The Problem

Our signal validation was showing mismatches between `our_signals` and `live_signals` (captured from Composer backtests). Despite running the same strategies, results frequently diverged.

## The Hypothesis

**Composer backtests use the day's close price, but actual execution happens at 3:45pm ET before market close.**

This creates a lookahead bias in the backtest data:

| Data Point | What It Shows | Data Available |
|------------|---------------|----------------|
| Composer backtest for Day N | Signal using Day N's **close price** | Has Day N close |
| Actual execution at 3:45pm on Day N | Signal using Day N-1's close + intraday | Does **not** have Day N close |

Therefore: **Backtest for Day N ≈ Reality for Day N+1**

The backtest is effectively showing what signal would generate *tomorrow* (when Day N's close is actually available), not what would execute *today*.

## Evidence from Jan 20-22 Data

### gold strategy - Strong support

| Date | Our Signals | Live (Backtest) | Match |
|------|-------------|-----------------|-------|
| Jan 20 | UGL: 1.0 | BIL: 1.0 | ❌ |
| Jan 21 | BIL: 1.0 | BIL: 1.0 | ✅ |
| Jan 22 | UGL: 1.0 | UGL: 1.0 | ✅ |

**Key finding:** Our Jan 21 signal (BIL) matches the Jan 20 backtest (BIL) - a 1-day lag as predicted.

### rains_em_dancer - Partial support

| Date | Our Signals | Live (Backtest) | Match |
|------|-------------|-----------------|-------|
| Jan 20 | EDZ: 1.0 | EDZ: 0.892, TLT: 0.107 | ❌ |
| Jan 21 | EDZ: 1.0 | EDZ: 0.893, TLT: 0.107 | ❌ |
| Jan 22 | BSV: 0.107, EDZ: 0.892 | BSV: 0.107, EDZ: 0.892 | ✅ |

**Key finding:** Persistent lagging behavior - we were consistently behind the backtest's allocation split.

### pals_spell - Edge case

| Date | Our Signals | Live (Backtest) | Match |
|------|-------------|-----------------|-------|
| Jan 20 | GDXD: 1.0 | GDXD: 1.0 | ✅ |
| Jan 21 | SOXS, SQQQ, TECS | BABA: 1.0 | ❌ |
| Jan 22 | GDXD: 1.0 | GDXD: 1.0 | ✅ |

**Key finding:** Dramatic mismatch doesn't fit simple 1-day lag. May indicate additional data source differences or high sensitivity to intraday vs close prices.

---

## The Fix

**Disabled live bars in dev environment** (commit 1fda9aa5)

With live bars off, our dev signals should now:
1. Use only completed daily bars (previous day's close)
2. Match what Composer actually executes at 3:45pm
3. **Validate correctly against the PREVIOUS day's backtest**

## Expected Validation Pattern (Post-Fix)

```
Our signal on Day N (dev, no live bars)
    SHOULD MATCH
Composer backtest from Day N-1
```

Or equivalently:
```
Our signal on Day N
    SHOULD MATCH
Live signal captured on Day N (which shows Day N-1's "real" execution)
```

---

## Re-Test Protocol (Week of Jan 27-31)

### Data to Collect

For each trading day, capture:
1. `our_signals` from dev environment (live bars OFF)
2. `live_signals` from Composer backtest

### Validation Criteria

**Hypothesis CONFIRMED if:**
- Match rate improves significantly (target: >90%)
- Remaining mismatches are explainable (data source differences, etc.)

**Hypothesis REJECTED if:**
- Match rate does not improve
- Same lagging pattern persists despite live bars being disabled

### Specific Checks

1. **gold strategy**: Should show consistent matches (was our clearest 1-day lag case)
2. **rains_em_dancer**: Allocation splits should now align
3. **pals_spell**: Watch for continued dramatic mismatches (may indicate separate issue)

---

## Files for Comparison

**Pre-fix (live bars ON):**
- `signal_validation_2026-01-20.csv`
- `signal_validation_2026-01-21_dev.csv`
- `signal_validation_2026-01-22_dev.csv`

**Post-fix (live bars OFF):**
- `signal_validation_2026-01-27_dev.csv` (pending)
- `signal_validation_2026-01-28_dev.csv` (pending)
- `signal_validation_2026-01-29_dev.csv` (pending)
- `signal_validation_2026-01-30_dev.csv` (pending)
- `signal_validation_2026-01-31_dev.csv` (pending)

---

## Notes

- Market closed Mon Jan 20 (MLK Day) - may affect data continuity
- If hypothesis is confirmed, consider updating prod environment similarly
- May need to adjust validation logic to compare Day N signals against Day N-1 backtests explicitly
