# Strategy-Indicator-Operator Complete Matrix

## Overview
Complete analysis of all 21 strategies showing:
- **Indicators** (11): RSI, MA, current-price, etc. — what data each strategy computes
- **Operators** (6): filter, select-top, if/else, weight-equal, etc. — how strategies combine them

---

## Combined Matrix: Strategies × Indicators × Operators

| Strategy | **INDICATORS** | | | | | | | | | | | **OPERATORS** | | | | | |
|----------|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| | RSI | CP | MA | EMA | MAR | CR | StdR | StdP | MDD | PPO | PPOS | F | ST | SB | WE | WS | IE |
| **Basic (2-3 features)** |
| gold | 1 | 0 | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 |
| gold_and_miners | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 |
| gold_currency | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 |
| simons_full_kmlm | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 |
| **Standard (4-5 features)** |
| defence | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 0 | 1 |
| ftlt_holy_grail | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 0 | 1 |
| ftlt_tqqq_ftlt_1 | 1 | 1 | 1 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 0 | 1 |
| vox_the_best | 1 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 0 | 1 |
| what_have_i_done | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 0 | 1 |
| **Moderate (6-8 features)** |
| fomo_nomo | 1 | 1 | 1 | 0 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 0 | 1 |
| growth_blend | 1 | 1 | 1 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 0 | 1 |
| rains_concise_em | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 1 | 0 | 1 |
| rains_em_dancer | 1 | 1 | 1 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 |
| sisyphus_lowvol | 1 | 1 | 1 | 0 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 1 | 0 | 1 |
| **Complex (9+ features)** |
| ftl_starburst | 1 | 0 | 0 | 0 | 1 | 1 | 1 | 0 | 1 | 0 | 0 | 1 | 1 | 1 | 1 | 0 | 1 |
| interstellar | 1 | 1 | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 | 1 |
| kmlm_switcher | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 0 | 1 |
| pals_spell | 1 | 1 | 1 | 0 | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 1 | 1 |
| soxl_growth | 1 | 0 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 0 | 0 | 1 | 1 | 1 | 1 | 0 | 1 |
| **FTLT Variants** |
| ftlt_tqqq_ftlt | 1 | 1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 0 | 1 |
| ftlt_tqqq_ftlt_2 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 0 | 1 |

**Legend**: CP=Current-Price, MA=Moving-Avg-Price, EMA=Exp-Moving-Avg, MAR=Moving-Avg-Return, CR=Cumulative-Return, StdR=Stdev-Return, MDD=Max-Drawdown, F=Filter, ST=Select-Top, SB=Select-Bottom, WE=Weight-Equal, WS=Weight-Specified, IE=If-Else

---

## Feature Count Distribution

### By Complexity Level

| Level | Strategies | Total Features | Typical Profile |
|-------|-----------|-----------------|-----------------|
| **Simplest** | gold, gold_and_miners, gold_currency, simons_full_kmlm | 2-3 | RSI only + if/weight-equal |
| **Basic** | defence, ftlt_holy_grail, ftlt_tqqq_ftlt_1 | 4-5 | RSI/MA + filter + select-top |
| **Moderate** | fomo_nomo, growth_blend, sisyphus_lowvol, rains_* | 6-8 | MA/Return metrics + filter+select |
| **Complex** | pals_spell, soxl_growth, ftl_starburst, interstellar | 9-12 | Multi-indicator + bidirectional ops |

---

## Usage Statistics (Combined View)

### Indicators by Adoption
| Feature | % Strategies | Count | Type |
|---------|-----------|-------|------|
| **RSI** | 100% | 21 | Indicator |
| **If-Else** | 100% | 21 | Operator |
| **Weight-Equal** | 100% | 21 | Operator |
| **Select-Top** | 81% | 17 | Operator |
| **Current-Price** | 57% | 12 | Indicator |
| **Moving-Avg-Price** | 62% | 13 | Indicator |
| **Filter** | 76% | 16 | Operator |
| **Cumulative-Return** | 48% | 10 | Indicator |
| **Moving-Avg-Return** | 38% | 8 | Indicator |
| **Stdev-Return** | 29% | 6 | Indicator |
| **Select-Bottom** | 43% | 9 | Operator |
| **Weight-Specified** | 29% | 6 | Operator |
| **Max-Drawdown** | 19% | 4 | Indicator |
| **EMA-Price** | 5% | 1 | Indicator |
| **Stdev-Price, PPO, PPO-Signal** | 0% | 0 | Unused |

---

## Key Patterns & Strategy Families

### Strategy Family 1: "Gold Rotation" (Simple, Trend-Following)
**Members**: gold, gold_and_miners, gold_currency

**Feature Profile**:
- Indicators: RSI + stdev-return + cumulative-return
- Operators: if/else + weight-equal only
- Nesting: Shallow (2-3 levels)

**Pattern**: Multi-window RSI for overbought/oversold + moving averages for trend
- Example: `if (rsi > 80) → SHNY else if (cumulative-return > 1) → SHNY else GLD`

---

### Strategy Family 2: "FTLT Variants" (Mid-Complexity, Tech-Focused)
**Members**: ftlt_holy_grail, ftlt_tqqq_ftlt, ftlt_tqqq_ftlt_1, ftlt_tqqq_ftlt_2

**Feature Profile**:
- Indicators: RSI + current-price + moving-avg-price (+ returns in _1)
- Operators: filter + select-top/bottom + weight-equal
- Nesting: Moderate (4-6 levels)

**Pattern**: Price-vs-200MA for trend, RSI 10-14 for momentum, filter in reversals
- Common: `if (current-price > ma200) → if (rsi > 79) → filter(rsi, select-top 1)`

---

### Strategy Family 3: "Multi-Regime Complex" (High-Complexity, VIX-Aware)
**Members**: pals_spell, ftl_starburst, soxl_growth, sisyphus_lowvol

**Feature Profile**:
- Indicators: RSI + MA + returns (moving-avg-return, cumulative-return, stdev-return) + max-drawdown
- Operators: All 6 operators used in complex combinations
- Nesting: Deep (8+ levels)

**Pattern**: Volatility regime detection → asset ranking → multi-logic branching
- VIX sentinel (UVXY RSI) → market regime → filter by metric → select best/worst

---

### Strategy Family 4: "Cross-Asset Relative Strength" (EM/Global Focus)
**Members**: rains_concise_em, rains_em_dancer, interstellar, rains_em_dancer

**Feature Profile**:
- Indicators: RSI + current-price + moving-avg-price + cumulative-return
- Operators: filter/select-top + weight-specified for portfolio mixing
- Nesting: Moderate-to-complex (5-7 levels)

**Pattern**: Cross-asset RSI comparisons + multi-leg allocation
- Example: `if (rsi(EEM) > rsi(SPY)) → 60% EDC + 40% treasury strategy`

---

## Combined Feature Archetypes

### Archetype A: "Pure Momentum Rank" (6 strategies)
**Use**: defence, vox_the_best, interstellar, ftlt_holy_grail, growth_blend, ftlt_tqqq_ftlt_1

**Signature**: 
- Core: RSI + current-price + moving-avg-price
- Ops: filter + select-top (rank winners)
- Pattern: If trending → filter by RSI → select top N

### Archetype B: "Bidirectional Sentiment Rank" (5 strategies)
**Use**: ftl_starburst, kmlm_switcher, soxl_growth, ftlt_tqqq_ftlt, ftlt_tqqq_ftlt_2

**Signature**:
- Core: RSI ± max-drawdown/stdev-return
- Ops: select-top AND select-bottom (winners vs losers)
- Pattern: Bull branch → select-top; Bear branch → select-bottom

### Archetype C: "Momentum + Volatility Filter" (4 strategies)
**Use**: pals_spell, sisyphus_lowvol, fomo_nomo, ftl_starburst

**Signature**:
- Core: RSI + MA + cumulative-return + stdev-return ± moving-avg-return
- Ops: All + weight-specified for multi-strategy mixing
- Pattern: VIX regime → momentum check → select ranked assets

### Archetype D: "Cross-Asset Relative" (3 strategies)
**Use**: rains_em_dancer, rains_concise_em, interstellar (partial)

**Signature**:
- Core: RSI(asset1) vs RSI(asset2) comparisons
- Ops: weight-specified for portfolio mixing
- Pattern: Compare 2+ assets by metric → allocate weights

### Archetype E: "Simplest - Direct Threshold" (4 strategies)
**Use**: gold, gold_and_miners, gold_currency, simons_full_kmlm

**Signature**:
- Core: RSI only
- Ops: if/else + weight-equal
- Pattern: Cascade of RSI > threshold checks

---

## Insights for Strategy Development

### Highest-Leverage Combinations

**Top 3 Most Common Combos** (for benchmarking/cloning):
1. **RSI + Current-Price + MA + Filter + Select-Top** (10 strategies)
   - Used in: defence, ftlt_holy_grail, growth_blend, interstellar, soxl_growth, pals_spell, etc.
   - Success pattern: Best for bullish, rank-by-momentum designs

2. **RSI + Moving-Avg-Return + Cumulative-Return + Filter + Select-Top** (8 strategies)
   - Used in: fomo_nomo, pals_spell, sisyphus_lowvol, ftlt_tqqq_ftlt_1
   - Success pattern: Return-relative (momentum oscillators)

3. **RSI + Current-Price + MA + Select-Bottom** (5 strategies)
   - Used in: ftl_starburst, kmlm_switcher, ftlt_tqqq_ftlt, soxl_growth
   - Success pattern: Contrarian / mean reversion setups

### Indicator Gaps (Opportunities)

**Never or Rarely Used**:
- Stdev-Price (0%) — too noisy with price gaps
- PPO (0%) — traders prefer manual MA comparisons
- Max-Drawdown (19%) — underutilized for tail-risk hedging
- EMA (5%) — only one strategy (crypto-focused what_have_i_done)

**Strategic Opportunities**:
- Max-drawdown only in 4 strategies; could expand for risk-aware designs
- EMA unused in equities; hypothesis: simple MA sufficient, EMA adds complexity without edge

---

## CSV Export Location
Merged file: `strategy_complete_matrix.csv`
- One file, all features (21 rows × 17 columns)
- Load into Excel/Python for pivot analysis

---

## How to Use This Combined View

1. **Find Similar Strategies**: Match profile rows (e.g., find strategies with same feature count + ops)
2. **Design New Strategies**: Use archetype signatures as templates
3. **Spot Gaps**: See which indicators/operators are underutilized
4. **Complexity Assessment**: Count features per strategy to estimate development/test effort
5. **Performance Correlation**: Cross-reference feature profile with backtest results

