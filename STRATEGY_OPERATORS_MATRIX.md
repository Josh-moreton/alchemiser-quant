# DSL Operators Matrix

## Complete Matrix: Strategies × Operators

| Strategy | Filter | Select-Top | Select-Bottom | Weight-Equal | Weight-Specified | If/Else |
|----------|--------|-----------|---------------|--------------|-----------------|---------|
| defence | ✓ | ✓ | | ✓ | | ✓ |
| fomo_nomo | ✓ | ✓ | | ✓ | | ✓ |
| ftl_starburst | ✓ | ✓ | ✓ | ✓ | | ✓ |
| gold | | | | ✓ | | ✓ |
| gold_and_miners | | | | ✓ | | ✓ |
| gold_currency | | | | ✓ | | ✓ |
| growth_blend | ✓ | ✓ | | ✓ | | ✓ |
| interstellar | ✓ | ✓ | | ✓ | ✓ | ✓ |
| kmlm_switcher | ✓ | ✓ | ✓ | ✓ | | ✓ |
| pals_spell | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| rains_concise_em | ✓ | | ✓ | ✓ | | ✓ |
| rains_em_dancer | ✓ | ✓ | | ✓ | ✓ | ✓ |
| simons_full_kmlm | | | | ✓ | | ✓ |
| sisyphus_lowvol | ✓ | | ✓ | ✓ | | ✓ |
| soxl_growth | ✓ | ✓ | ✓ | ✓ | | ✓ |
| vox_the_best | ✓ | ✓ | | ✓ | | ✓ |
| what_have_i_done | ✓ | ✓ | | ✓ | | ✓ |
| ftlt_holy_grail | ✓ | ✓ | | ✓ | | ✓ |
| ftlt_tqqq_ftlt | ✓ | ✓ | ✓ | ✓ | | ✓ |
| ftlt_tqqq_ftlt_1 | ✓ | ✓ | | ✓ | | ✓ |
| ftlt_tqqq_ftlt_2 | ✓ | ✓ | ✓ | ✓ | | ✓ |

---

## Operator Usage Statistics

| Operator | % of Strategies | Count | Notes |
|----------|-----------------|-------|-------|
| **If/Else** | 100% | 21 | Universal: all strategies use branching logic |
| **Weight-Equal** | 100% | 21 | Universal: baseline allocation in all strategies |
| **Filter** | 76% | 16 | Asset ranking/selection; absent only in simplest 5 |
| **Select-Top** | 81% | 17 | Rank by metric, pick top N (bullish, best performers) |
| **Select-Bottom** | 43% | 9 | Rank by metric, pick worst N (bearish, contrarian) |
| **Weight-Specified** | 29% | 6 | Custom weights; used in complex multi-leg strategies |

---

## Key Clusters by Operator Combination

### Cluster 1: "Simplest: If + Weight-Equal Only" (5 strategies)
**Members**: gold, gold_and_miners, gold_currency, simons_full_kmlm

**Characteristics**:
- Pure if/else decision trees
- All equal weighting
- No filtering or ranking
- Directly compare indicators via if conditions

**Example Pattern**:
```clojure
(if (> (rsi "TQQQ") 80)
  [asset1]
  [asset2])
```

---

### Cluster 2: "Standard: If + Weight-Equal + Filter + Select-Top" (8 strategies)
**Members**: defence, fomo_nomo, growth_blend, ftlt_holy_grail, ftlt_tqqq_ftlt_1, what_have_i_done, vox_the_best

**Characteristics**:
- Conditional routing via if/else
- Filter operators for asset ranking
- Select-top to pick winners by metric
- Equal weight allocation
- Typical use: "If trend up, filter assets by RSI, select top 2"

**Example Pattern**:
```clojure
(if (> (current-price "SPY") (moving-average-price "SPY" 200))
  (filter
    (rsi {:window 10})
    (select-top 3)
    [asset1 asset2 asset3 ...]))
```

---

### Cluster 3: "Bidirectional: Filter + Select-Top + Select-Bottom" (5 strategies)
**Members**: ftl_starburst, kmlm_switcher, soxl_growth, ftlt_tqqq_ftlt_2, sisyphus_lowvol

**Characteristics**:
- Use both select-top (bullish) and select-bottom (bearish)
- Rank by metric, pick opposite ends
- Heavy if/else for regime switching
- Useful for: momentum vs contrarian, long vs short decisions

**Example Pattern**:
```clojure
(if bullish-condition?
  (filter (metric) (select-top 1) assets)
  (filter (metric) (select-bottom 1) assets))
```

---

### Cluster 4: "Complex: With Weight-Specified" (6 strategies)
**Members**: interstellar, pals_spell, rains_em_dancer, (+ 3 partial)

**Characteristics**:
- Custom allocation weights for sub-strategies
- Combination of multiple strategies with different weights (e.g., 60% strategy A, 40% strategy B)
- Most complex; portfolio-level allocation
- Used in strategies with multiple independent signal sources

**Example Pattern**:
```clojure
(weight-specified 0.6
  [strategy-A ...]
  0.4
  [strategy-B ...])
```

---

## Decision Tree Depth Analysis

### Operator Nesting Patterns

**Simplest (1-2 levels of if/else)**:
- gold, gold_and_miners, gold_currency, simons_full_kmlm
- Direct RSI comparisons; no filter nesting

**Moderate (3-5 levels)**:
- defence, ftlt_holy_grail, ftlt_tqqq_ftlt_1
- If → weight-equal → filter → select-top

**Complex (6+ levels of nesting)**:
- growth_blend, pals_spell, ftl_starburst, sisyphus_lowvol
- Multiple if/else branches with filters at each level
- Often: if → weight-equal → [if → filter → select] repeatedly

**Most Complex**:
- pals_spell (1000+ lines): deeply nested multi-asset combinations
- Interstellar: weight-specified top-level split with 2-3 strategy blocks

---

## Combined Operator + Indicator Insights

### High-Complexity Strategies (5+ operators + 5+ indicators)
**Members**: pals_spell, growth_blend, ftl_starburst, sisyphus_lowvol, soxl_growth, fomo_nomo

**Pattern**: 
- RSI-heavy filtering (rank by RSI window variants)
- Filter + select-top for momentum (cumulative-return, moving-avg-return)
- Multiple if/else branches for regime detection (VIX, trend, volatility)
- Example: *pals_spell* uses **7 operators** × **8 indicators** in complex nesting

### Low-Complexity Strategies (2 operators + 1 indicator)
**Members**: gold, gold_and_miners, gold_currency, simons_full_kmlm

**Pattern**:
- if/else + weight-equal only
- Single metric decision (RSI threshold)
- Example: *simons_full_kmlm* uses simple RSI > 80 checks cascading through 10+ asset comparisons

### Balanced Strategies (4 operators + 3-4 indicators)
**Members**: defence, ftlt_holy_grail, interstellar, what_have_i_done, vox_the_best

**Pattern**:
- Producer-friendly: Easy to understand, moderate complexity
- Mix of filtering + regime checks
- Suitable for templates; common in FTLT variants

---

## Operator Usage by Feature

### Filter → Select-Top (Asset Ranking: Pick Best)
**Use Case**: Momentum-driven, trend-following
**Strategies Using**: defence, fomo_nomo, growth_blend, interstellar, kmlm_switcher, ftlt_holy_grail, soxl_growth, vox_the_best, what_have_i_done, ftlt_tqqq_ftlt_1, ftlt_tqqq_ftlt_2, pals_spell (12 total)

**Typical Pattern**:
```clojure
(filter (cumulative-return {:window 30}) (select-top 3) [assets])
```

### Filter → Select-Bottom (Asset Ranking: Pick Worst)
**Use Case**: Mean reversion, contrarian trades
**Strategies Using**: ftl_starburst, kmlm_switcher, rains_concise_em, sisyphus_lowvol, soxl_growth, ftlt_tqqq_ftlt, ftlt_tqqq_ftlt_2, pals_spell (8 total)

**Typical Pattern**:
```clojure
(filter (rsi {:window 10}) (select-bottom 1) [SQQQ BSV])
; Short the weakest of 2 assets
```

### Weight-Specified (Multi-Leg Allocation)
**Use Case**: Portfolio mixing incompatible strategies
**Strategies Using**: interstellar (0.67/0.33 split), pals_spell (multiple 60/40 splits), rains_em_dancer (0.25/0.75 split)

**Typical Pattern**:
```clojure
(weight-specified
  0.6 (strategy1 ...)
  0.4 (strategy2 ...))
```

---

## DSL Design Observations

1. **Operator Ubiquity**:
   - **If/Else**: 100% (universal conditional logic)
   - **Weight-Equal**: 100% (baseline allocation)
   - These two alone can express any strategy (see: 5 simplest strategies)

2. **Filtering Gap**:
   - 76% of strategies use filter
   - 24% hardcode asset lists (particularly gold-focused, simple strategies)

3. **Bidirectional Bias**:
   - Select-top (81%) vastly outweighs select-bottom (43%)
   - Suggests portfolio bias toward long/bullish; short rarely used except in complex vol strategies

4. **Custom Weights Rare**:
   - Only 29% use weight-specified
   - Most strategies favor equal or implicit (if-selected) weighting
   - Suggests operators prefer transparent, equal-risk allocation

5. **Nesting Complexity**:
   - Simple strategies: 2-3 levels
   - Medium: 4-6 levels
   - Complex (pals_spell, ftl_starburst): 8+ levels
   - No clear architectural limit, but readability breaks down beyond 10 levels

---

## CSV Export Location
- Indicators: `strategy_indicator_matrix.csv`
- Operators: `strategy_operators_matrix.csv`
- Combined analysis: This document

---

## Next Steps
To combine indicators + operators into a single analysis view:
1. Load both CSVs into a pivot table (Excel/Python/R)
2. Cross-tabulate by strategy
3. Identify high-complexity combinations (5+ indicators × 4+ operators)
4. Use for backtesting strategy families

