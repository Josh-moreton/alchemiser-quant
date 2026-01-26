# Signal Validation Investigation - 2026-01-15

**Investigation Date:** 2026-01-16  
**Validation Date:** 2026-01-15  
**Status:** In Progress

## Executive Summary

Validation of dev and prod signals against Composer's live signals shows 4 strategies with divergences. This document tracks the root cause investigation.

---

## Validation Results Overview

### Dev Environment (all indicators using live bars)
| Strategy | Matches | Notes |
|----------|---------|-------|
| blatant_tech | ❌ | We have CORD SOX, live signal is CORD NBIS SOX |
| defence | ✅ | |
| gold | ✅ | |
| nuclear | ✅ | |
| pals_spell | ✅ | |
| rains_concise_em | ❌ | We have EDZ, live signal is EDZ XLF |
| rains_em_dancer | ✅ | |
| simons_full_kmlm | ✅ | |
| sisyphus_lowvol | ❌ | We have UVXY EDZ VIXY BOND BVIL UGL, live is VIXY UVIX EDZ UVXY UGL BOND BIL |
| tqqq_ftlt | ✅ | |
| tqqq_ftlt_1 | ✅ | |
| tqqq_ftlt_2 | ✅ | |

### Prod Environment (partial live bar config)
| Strategy | Matches | Notes |
|----------|---------|-------|
| blatant_tech | ❌ | Same as dev |
| defence | ✅ | |
| gold | ✅ | |
| nuclear | ✅ | |
| pals_spell | ✅ | |
| rains_concise_em | ❌ | Same as dev |
| rains_em_dancer | ❌ | Weights are way out, right symbols though, but way too much EDZ |
| simons_full_kmlm | ✅ | |
| sisyphus_lowvol | ❌ | Same as dev |
| tqqq_ftlt | ✅ | |
| tqqq_ftlt_1 | ✅ | |
| tqqq_ftlt_2 | ✅ | |

**Key Observation:** `rains_em_dancer` passes in dev (all-live) but fails in prod (partial-live), suggesting a live bar config issue for one of its indicators.

---

## Detailed Investigation

### 1. blatant_tech

**Discrepancy:**
- Our signal: `CORD, SOXS` (weights: 0.67, 0.33)
- Composer signal: `CORD, NBIS, SOX`

**Root Cause Analysis:**

The strategy has 3 top-level groups in a `weight-equal`:
1. First `if` branch: `(< (rsi "GDX" {:window 7}) 70)`
2. Second `if` branch: `(< (rsi "APLD" {:window 9}) 70)`
3. Third branch: SOXL/SOXS decision tree

**Debug Trace Results (2026-01-16 09:45 local):**

```
Decision Path:
1. GDX rsi :window(7) < 70 -> FALSE (branch: else)
   - GDX RSI(7) = 80.27, threshold = 70
   - Result: Takes ELSE branch -> CORD

2. APLD rsi :window(9) < 70 -> TRUE (branch: then)
   - APLD RSI(9) = 64.06
   - Result: Enters weight-equal -> filter select-bottom 1

Filter trace:
   - Candidates: NBIS, APLD, BE, CORD
   - RSI(10) scores: CORD=30.01, NBIS=61.75, APLD=63.75, BE=74.42
   - select-bottom 1 picks: CORD (lowest RSI)

3. SOXL decision tree -> SOXS
```

**Key Finding:**
- First `if` condition: `GDX RSI(7) = 80.27 >= 70` → FALSE → ELSE branch → CORD
- Composer must be seeing `GDX RSI(7) < 70` to enter the Metals group and pick NBIS

**Data Check:**
```
S3 Historical Data (last 5 bars):
  2026-01-09: 92.56
  2026-01-12: 95.72
  2026-01-13: 96.47
  2026-01-14: 96.86
  2026-01-15: 97.11

GDX RSI(7) with S3 data = 80.2733
GDX RSI(7) T-1 (without 01-15) = 79.6965

Both values >= 70, so condition is FALSE either way.
```

**Hypothesis:** 
- Data difference between S3 and Composer's data source
- OR RSI calculation method difference
- Need to compare our GDX RSI(7) value with what Composer shows

**Next Steps:**
- [ ] Check Composer's displayed RSI value for GDX
- [ ] Compare price data sources

---

### 2. rains_concise_em

**Discrepancy:**
- Our signal: `EDZ`
- Composer signal: `EDZ, XLF`

**Investigation Status:** Not yet started

**Next Steps:**
- [ ] Run trace_strategy_routes.py
- [ ] Identify which filter/condition excludes XLF

---

### 3. sisyphus_lowvol

**Discrepancy:**
- Our signal (validation): `UVXY, EDZ, VIXY, BOND, BIL, UGL` (BVIL was a typo)
- Composer signal: `VIXY, UVIX, EDZ, UVXY, UGL, BOND, BIL`

**Current Trace (2026-01-16):**
```json
{
  "BOND": 0.1,
  "UVXY": 0.3,
  "EDZ": 0.2,
  "VIXY": 0.2,
  "BIL": 0.1,
  "UGL": 0.1
}
```

**Key Differences:**
- Composer has `UVIX`, we don't
- Weight distribution differs
- Note: Current trace differs from yesterday's validation - data changed overnight

**Investigation Status:** Traced, needs deeper analysis

**Hypothesis:** 
- Volatility indicator (`stdev_return`) uses live bar, but `cumulative_return` does not (`use_live_bar=False`)
- Different indicator values near thresholds causing different filter rankings
- Need to check if UVIX is even in the strategy's symbol universe

**Next Steps:**
- [ ] Read sisyphus_lowvol.clj to understand symbol universe
- [ ] Check if UVIX vs UVXY is a filter/ranking issue
- [ ] Check partial_bar_config for indicators used in this strategy

---

### 4. rains_em_dancer (Prod only)

**Discrepancy:**
- Our signal: Right symbols but wrong weights ("way too much EDZ")
- Composer signal: Different weight distribution

**Key Observation:** 
- Passes in dev (all-live) but fails in prod (partial-live)
- This suggests a specific indicator with `use_live_bar=False` is affecting weight calculations

**Investigation Status:** Not yet started

**Next Steps:**
- [ ] Compare dev vs prod traces
- [ ] Identify which indicator's live bar setting affects weights
- [ ] Check weight-specified vs weight-equal handling

---

## Technical Context

### Partial Bar Configuration

Location: `layers/shared/python/the_alchemiser/shared/indicators/partial_bar_config.py`

Current settings (as of investigation):
| Indicator | use_live_bar | Notes |
|-----------|--------------|-------|
| rsi | True | |
| moving_average_price | True | |
| moving_average_return | True | |
| max_drawdown | True | |
| cumulative_return | **False** | "Bento testing: T-1 data required" |
| exponential_moving_average_price | **False** | |
| stdev_return | True | |
| stdev_price | **False** | |
| current_price | True | |

### Key Scripts Used

1. **trace_strategy_routes.py** - Main debugging tool
   ```bash
   poetry run python scripts/trace_strategy_routes.py <strategy> --policy composer
   poetry run python scripts/trace_strategy_routes.py <strategy> --policy all-live
   poetry run python scripts/trace_strategy_routes.py <strategy> --policy none-live
   ```

2. **debug_blatant_tech.py** - Custom script for this investigation
   ```bash
   poetry run python scripts/debug_blatant_tech.py
   ```

---

## Action Items

1. [ ] Compare GDX RSI(7) with Composer's displayed value
2. [ ] Trace rains_concise_em decision path
3. [ ] Trace sisyphus_lowvol filter rankings
4. [ ] Compare dev vs prod for rains_em_dancer
5. [ ] Consider if cumulative_return needs use_live_bar=True

---

## Change Log

| Date | Action | Result |
|------|--------|--------|
| 2026-01-15 | Moved more indicators to use live bars (prod) | Some strategies still failing |
| 2026-01-15 | Switched ALL indicators to live bars (dev) | blatant_tech, rains_concise_em, sisyphus_lowvol still fail |
| 2026-01-16 | Started investigation | Documented findings |
