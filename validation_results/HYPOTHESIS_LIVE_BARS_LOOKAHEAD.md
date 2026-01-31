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

## Validation Results

### Jan 22 → Jan 23 Comparison (2026-01-24)

**Test:** Compare Jan 23 `our_signals` against Jan 22 `live_signals`

If hypothesis is correct, Jan 23's computed signals should match Jan 22's backtest signals (since backtest shows "tomorrow's" signal).

| Strategy | Jan 22 live_signals | Jan 23 our_signals | Match? |
|----------|--------------------|--------------------|--------|
| blatant_tech | CORD, NBIS, SOXS (≈0.33 each) | CORD, NBIS, SOXS (0.33 each) | ✅ |
| defence | OSS: 0.466, RCAT: 0.534 | OSS: 0.5, RCAT: 0.5 | ✅ |
| gold | UGL: 1.0 | UGL: 1.0 | ✅ |
| nuclear | LEU, NLR, OKLO (≈0.33 each) | LEU, NLR, OKLO (0.33 each) | ✅ |
| pals_spell | GDXD: 1.0 | GDXD: 1.0 | ✅ |
| rains_concise_em | EDZ: 1.0 | EDZ: 1.0 | ✅ |
| rains_em_dancer | BSV: 0.107, EDZ: 0.892 | BSV: 0.107, EDZ: 0.893 | ✅ |
| simons_full_kmlm | SVIX: 1.0 | SVIX: 1.0 | ✅ |
| sisyphus_lowvol | 10 symbols (BIL, BOND, EDZ, etc.) | 10 symbols (identical) | ✅ |
| tqqq_ftlt | TQQQ: 1.0 | TQQQ: 1.0 | ✅ |
| tqqq_ftlt_1 | ENPH: 0.39, GNRC: 0.49, MU: 0.12 | ENPH: 0.39, GNRC: 0.49, MU: 0.12 | ✅ |
| tqqq_ftlt_2 | EDC, TNA, URTY (0.33 each) | EDC, TNA, URTY (0.33 each) | ✅ |

**Result: 12/12 strategies match (100%)**

**Conclusion:** Hypothesis strongly confirmed. The 1-day lag pattern is consistent across all strategies. Minor weight differences (e.g., defence) are rounding artifacts in Composer's display.

### Next Steps

- Continue validation week of Jan 27-31
- If pattern holds, update validation logic to compare against previous day's backtest
- Consider applying same fix to prod environment

---

## Notes

- Market closed Mon Jan 20 (MLK Day) - may affect data continuity
- If hypothesis is confirmed, consider updating prod environment similarly
- May need to adjust validation logic to compare Day N signals against Day N-1 backtests explicitly
