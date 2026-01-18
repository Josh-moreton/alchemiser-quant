# Live Bar Configuration Analysis

**Analysis Date:** 2026-01-17
**Related Investigation:** [SIGNAL_VALIDATION_2026-01-15_INVESTIGATION.md](./SIGNAL_VALIDATION_2026-01-15_INVESTIGATION.md)
**Status:** Consolidated findings

## Executive Summary

After multiple iterations of `use_live_bar` configuration changes and validation runs, we've identified a fundamental problem: **there is no single `use_live_bar` configuration that works for all strategies**. Some strategies match Composer with live bars ON, others only match with live bars OFF.

---

## Complete Timeline of `use_live_bar` Changes

### Jan 7, 2026 — Initial Creation (59f976ed)

File created with conservative defaults (most indicators OFF):

| Indicator | `use_live_bar` | Rationale |
|-----------|----------------|-----------|
| `current_price` | *(default True)* | - |
| `rsi` | **False** | "RSI too volatile with intraday data" |
| `moving_average` | **True** | "Use live bar for MA calculations" |
| `exponential_moving_average_price` | **False** | "EMA gives too much weight to partial bar" |
| `moving_average_return` | **False** | "Return-based indicator too volatile" |
| `cumulative_return` | **False** | "Bento testing: T-1 data required" |
| `stdev_return` | **False** | "Volatility too sensitive to incomplete returns" |
| `stdev_price` | **False** | "Price stdev too sensitive to partial bars" |
| `max_drawdown` | *(default True)* | - |

### Jan 14, 2026 — Validation Run

Validation against Composer's live signals showed **7 strategies failing**:

| Strategy | Our Signal | Composer Signal |
|----------|-----------|-----------------|
| defence | KTOS, RCAT | KTOS, SPAI |
| nuclear | LEU, OKLO, BWXT | LEU, OKLO, NLR |
| rains_concise_em | EDZ | XLF |
| rains_em_dancer | EDZ, YANG, TLT | EDZ, VBF |
| simons_full_kmlm | SVIX | UVXY |
| sisyphus_lowvol | Complex mix | Different weights/symbols |
| tqqq_ftlt_2 | EDC, RETL, TNA | VIXY |

### Jan 15, 2026 — T-0 Data Experiment (a0e7b74b)

Based on Jan 14 failures, turned ON live bars to "match Composer's live signals":

| Indicator | Change |
|-----------|--------|
| `rsi` | False → **True** |
| `moving_average_return` | False → **True** |
| `stdev_return` | False → **True** |

### Jan 15, 2026 — Re-validation Results

**Dev Environment (all live bars ON):**

| Strategy | Status | Change from Jan 14 |
|----------|--------|-------------------|
| defence | ✅ | **Fixed** |
| nuclear | ✅ | **Fixed** |
| rains_em_dancer | ✅ | **Fixed** |
| simons_full_kmlm | ✅ | **Fixed** |
| tqqq_ftlt_2 | ✅ | **Fixed** |
| blatant_tech | ❌ | Still failing |
| rains_concise_em | ❌ | Still failing |
| sisyphus_lowvol | ❌ | Still failing |

**Prod Environment (partial live bar config):**

| Strategy | Status | Notes |
|----------|--------|-------|
| rains_em_dancer | ❌ | **Passes in dev, fails in prod** |
| (others) | Same as dev | - |

### Jan 16, 2026 — Further Iterations

**12:07** — RSI reverted (cc68ed34):
| Indicator | Change | Reason |
|-----------|--------|--------|
| `rsi` | True → **False** | "RSI too volatile with partial bars" |

**12:19** — Cumulative return enabled (37de26e5):
| Indicator | Change |
|-----------|--------|
| `cumulative_return` | False → **True** |

**13:01** — All OFF except current_price (7231c853):

| Indicator | Change | New State |
|-----------|--------|-----------|
| `current_price` | Explicitly set | **True** |
| `moving_average` | True → False | **False** |
| `moving_average_return` | True → False | **False** |
| `cumulative_return` | True → False | **False** |
| `stdev_return` | True → False | **False** |
| `max_drawdown` | Explicitly set | **False** |

---

## Current State (as of Jan 17, 2026)

| Indicator | `use_live_bar` |
|-----------|----------------|
| `current_price` | **True** ✓ |
| `rsi` | False |
| `moving_average` | False |
| `exponential_moving_average_price` | False |
| `moving_average_return` | False |
| `cumulative_return` | False |
| `stdev_return` | False |
| `stdev_price` | False |
| `max_drawdown` | False |

---

## The Core Dilemma

### Strategy Compatibility Matrix

```
                        Live Bars ON              Live Bars OFF
                        ────────────              ─────────────
defence                 ✅ matches                ❌ fails
nuclear                 ✅ matches                ❌ fails
rains_em_dancer         ✅ matches                ❌ fails
simons_full_kmlm        ✅ matches                ❌ fails
tqqq_ftlt_2             ✅ matches                ❌ fails

blatant_tech            ❌ fails                  ❓ untested
rains_concise_em        ❌ fails                  ❓ untested
sisyphus_lowvol         ❌ fails                  ❓ untested
```

### Key Observations

1. **5 strategies require live bars ON** to match Composer (defence, nuclear, rains_em_dancer, simons_full_kmlm, tqqq_ftlt_2)

2. **3 strategies fail regardless** of live bar settings (blatant_tech, rains_concise_em, sisyphus_lowvol) — suggests deeper issues beyond live bar config

3. **rains_em_dancer is config-sensitive** — passes with all-live but fails with partial-live, indicating a specific indicator dependency

---

## Root Cause Hypotheses

### 1. Composer Timing Inconsistency

Composer may not use a consistent methodology across all strategies. Factors:
- Evaluation order affects which data is "live"
- Different strategies may be evaluated at different times
- Caching behavior may cause stale data for some indicators

### 2. Threshold Edge Cases

Many failures occur when indicator values are near decision thresholds:
- GDX RSI(7) = 80.27 vs threshold of 70 (blatant_tech)
- Small differences in calculation or data can flip TRUE/FALSE

### 3. Data Source Differences

Investigation revealed potential data discrepancies:
```
S3 Historical Data: GDX RSI(7) = 80.2733
T-1 Calculation:    GDX RSI(7) = 79.6965
Both >= 70, but Composer may see < 70
```

### 4. RSI Calculation Method

Different RSI implementations exist:
- Wilder's smoothing (our implementation)
- Simple moving average of gains/losses
- Exponential moving average variants

---

## Impact of Current "All OFF" Configuration

### Strategies That Will Diverge

With the current conservative config (all OFF except `current_price`):

| Strategy | Expected Outcome |
|----------|-----------------|
| defence | ❌ Will not match Composer |
| nuclear | ❌ Will not match Composer |
| rains_em_dancer | ❌ Will not match Composer |
| simons_full_kmlm | ❌ Will not match Composer |
| tqqq_ftlt_2 | ❌ Will not match Composer |

### Strategies With Deeper Issues

These fail regardless of config and need separate investigation:

| Strategy | Issue |
|----------|-------|
| blatant_tech | Data/RSI calculation difference |
| rains_concise_em | Missing symbol (XLF) in output |
| sisyphus_lowvol | Symbol universe mismatch (UVIX) |

---

## Potential Solutions

### Option 1: Per-Strategy Live Bar Overrides

Add strategy-level configuration to override global `use_live_bar` settings:

```python
STRATEGY_OVERRIDES = {
    "defence": {"rsi": True, "moving_average_return": True},
    "nuclear": {"rsi": True, "stdev_return": True},
    # ... etc
}
```

**Pros:** Maximum flexibility, can match each strategy individually
**Cons:** Complex to maintain, needs validation per strategy

### Option 2: Accept Divergence

Document which strategies will diverge and accept that our signals may differ from Composer's:

**Pros:** Simple, consistent behavior
**Cons:** ~5 strategies won't match live signals

### Option 3: Investigate Persistent Failures

Focus on the 3 strategies that fail regardless of config:
- blatant_tech: Compare RSI values with Composer directly
- rains_concise_em: Trace why XLF is excluded
- sisyphus_lowvol: Check if UVIX is in symbol universe

**Pros:** May reveal systematic issues
**Cons:** May be data source issues outside our control

### Option 4: Hybrid Approach

1. Keep current conservative config as default
2. Add per-strategy overrides for known-good configurations
3. Document expected divergences
4. Continue investigating persistent failures

---

## Recommended Next Steps

1. [ ] **Validate current config** — Run full validation with all-OFF config to establish baseline
2. [ ] **Test per-strategy overrides** — Prototype override system for defence/nuclear
3. [ ] **Deep dive blatant_tech** — Compare GDX RSI(7) directly with Composer's displayed value
4. [ ] **Check UVIX in sisyphus_lowvol** — Verify symbol is in strategy's universe
5. [ ] **Document expected divergences** — Update strategy docs with known differences

---

## References

- [partial_bar_config.py](../layers/shared/the_alchemiser/shared/indicators/partial_bar_config.py) — Live bar configuration
- [SIGNAL_VALIDATION_2026-01-15_INVESTIGATION.md](./SIGNAL_VALIDATION_2026-01-15_INVESTIGATION.md) — Detailed investigation notes
- [validation_results/signal_validation_2026-01-14.csv](../validation_results/signal_validation_2026-01-14.csv) — Jan 14 validation data
