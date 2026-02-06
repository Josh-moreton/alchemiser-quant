Strategy-Indicator Matrix
==========================

## Complete Matrix: Strategies × Indicators

| Strategy | RSI | Current-Price | Moving-Avg-Price | Exp-Moving-Avg-Price | Moving-Avg-Return | Cumulative-Return | Stdev-Return | Stdev-Price | Max-Drawdown | PPO | PPO-Signal |
|----------|-----|----------------|-------------------|----------------------|-------------------|-------------------|--------------|------------|-------------|-----|-----------|
| defence | ✓ | | | | | | | | | | |
| fomo_nomo | ✓ | ✓ | ✓ | | ✓ | ✓ | ✓ | | | | |
| ftl_starburst | ✓ | | | | ✓ | ✓ | ✓ | | ✓ | | |
| gold | ✓ | | ✓ | | | | ✓ | | | | |
| gold_and_miners | ✓ | | | | | ✓ | | | | | |
| gold_currency | ✓ | | | | | ✓ | | | | | |
| growth_blend | ✓ | ✓ | ✓ | | ✓ | ✓ | | | | | |
| interstellar | ✓ | ✓ | ✓ | | ✓ | | | | | | |
| kmlm_switcher | ✓ | | | | | | ✓ | | | | |
| pals_spell | ✓ | ✓ | ✓ | | ✓ | ✓ | ✓ | | | | |
| rains_concise_em | ✓ | ✓ | ✓ | | | | | | | | |
| rains_em_dancer | ✓ | ✓ | ✓ | | | ✓ | | | | | |
| simons_full_kmlm | ✓ | | | | | | | | | | |
| sisyphus_lowvol | ✓ | ✓ | ✓ | | ✓ | ✓ | | | | | |
| soxl_growth | ✓ | | | | | ✓ | ✓ | | ✓ | | |
| vox_the_best | ✓ | ✓ | ✓ | | | ✓ | | | | | |
| what_have_i_done | ✓ | ✓ | ✓ | ✓ | ✓ | | | | | | |
| ftlt_holy_grail | ✓ | ✓ | ✓ | | | | | | | | |
| ftlt_tqqq_ftlt | ✓ | ✓ | ✓ | | | | | | | | |
| ftlt_tqqq_ftlt_1 | ✓ | ✓ | ✓ | | ✓ | ✓ | | | | | |
| ftlt_tqqq_ftlt_2 | ✓ | | | | | | | | | | |

---

## Key Patterns & Insights

### Indicator Usage Statistics
- **Total Strategies**: 21
- **Total Indicators Defined**: 11
- **Indicators Actually Used**: 9

| Indicator | % of Strategies | Count | Notes |
|-----------|-----------------|-------|-------|
| **RSI** | 100% | 21 | Used in ALL strategies (universal) |
| **Moving-Avg-Price** | 62% | 13 | Trend confirmation; second most common |
| **Current-Price** | 57% | 12 | Price-level thresholds; FTLT variants favor it |
| **Cumulative-Return** | 48% | 10 | Momentum & mean reversion |
| **Moving-Avg-Return** | 38% | 8 | Momentum filter; complex strategies |
| **Stdev-Return** | 29% | 6 | Volatility-aware; FTL, growth, complex |
| **Max-Drawdown** | 19% | 4 | Risk management; FTL Starburst, Soxl Growth |
| **Exponential-Moving-Avg-Price** | 5% | 1 | Only What-Have-I-Done uses it |
| **Stdev-Price** | 0% | 0 | Not used in any strategy |
| **PPO** | 0% | 0 | Not used in any strategy |
| **PPO-Signal** | 0% | 0 | Not used in any strategy |

### Key Clusters by Indicator Combination

#### Cluster 1: "RSI-Only" (Simplest - 5 strategies)
- **Members**: defence, gold_and_miners, gold_currency, simons_full_kmlm, ftlt_tqqq_ftlt_2
- **Pattern**: Single-metric decision making; minimal complexity
- **Use Case**: Overbought/oversold detection via RSI windows

#### Cluster 2: "RSI + Moving Averages" (Trend + Momentum - 8 strategies)
- **Members**: gold, rains_concise_em, rains_em_dancer, ftlt_holy_grail, ftlt_tqqq_ftlt, vox_the_best, interstellar, ftlt_tqqq_ftlt_1
- **Pattern**: Price-vs-MA for trend confirmation + RSI for timing
- **Window Convention**: MA typically 200-day (long) with RSI 10-20 (short)
- **Use Case**: Directional trades with momentum filters

#### Cluster 3: "RSI + Price + MA + Return Metrics" (Complex - 6 strategies)
- **Members**: fomo_nomo, growth_blend, sisyphus_lowvol, pals_spell, ftl_starburst, what_have_i_done
- **Pattern**: Multi-layered: trend (MA) + momentum (RSI) + volatility (stdev/cumulative-return)
- **Complexity**: Nested if/else with 5+ indicators per rule
- **Use Case**: Regime-aware strategies; VIX monitoring; multi-asset allocation

#### Cluster 4: "Risk Management Focus" (Drawdown-aware - 4 strategies)
- **Members**: ftl_starburst, soxl_growth, kmlm_switcher, (implicitly in growth_blend)
- **Pattern**: Max-drawdown + stdev-return for risk gating
- **Use Case**: Tail-risk hedging; volatility regime detection

### Notable Observations

1. **RSI Ubiquity**: RSI is the univers indicator across all 21 strategies
   - Window ranges: 2 to 90 periods (extreme ranges: RSI-2 for entry timing, RSI-90 for long-term regime)
   - Cross-asset comparisons common: `rsi(asset1) > rsi(asset2)`

2. **MA Not in PPO/EMA Derivatives**: While Moving-Average-Price is common (62%), PPO (price oscillator) is never used
   - Suggests traders prefer simple MA over PPO complexity

3. **FTLT Variant Consistency**:
   - 4 FTLT strategies cluster tightly: 3 use RSI+current-price+MA; 1 (tqqq_ftlt_2) is RSI-only
   - Suggests FTLT as a template family; tqqq_ftlt_2 is simplified variant

4. **Volatility (Stdev) Usage Concentrated**:
   - Only 6 strategies use stdev-return
   - Grouped in complex, regime-aware strategies (fomo_nomo, ftl_starburst, soxl_growth, kmlm_switcher, pals_spell)
   - Suggests specific use case: volatility filtering, not core to all strategies

5. **Cumulative-Return as Tie-Breaker**:
   - Appears in 10/21 strategies, usually as secondary filter
   - Common in asset-ranking filters: `select-top N by cumulative-return`

6. **What-Have-I-Done: Only User of EMA**:
   - Unique in using `exponential-moving-average-price`
   - Crypto-focused strategy (BITO, COIN, etc.); perhaps EMA better for volatile assets

7. **Unused Indicators**:
   - **Stdev-Price**: Never used; likely too noisy for price-level data with gaps
   - **PPO & PPO-Signal**: Never used; traders prefer raw MA over derived oscillators

### Strategy Complexity Ranking

| Complexity | Strategies | Indicator Count | Characteristics |
|-----------|-----------|-----------------|---|
| **Simple** | defence, gold_and_miners, gold_currency, simons_full_kmlm, ftlt_tqqq_ftlt_2 | 1 | RSI only |
| **Basic** | gold, kmlm_switcher, rains_concise_em | 2-3 | RSI + 1-2 others |
| **Intermediate** | fomo_nomo, ftlt_holy_grail, ftlt_tqqq_ftlt, vox_the_best, interstellar, ftlt_tqqq_ftlt_1, rains_em_dancer, sisyphus_lowvol | 4-5 | RSI + MA + Return metrics |
| **Complex** | growth_blend, pals_spell, ftl_starburst, what_have_i_done, soxl_growth | 5-8 | Multi-regime, risk-aware, nested logic |

---

## How to Use This Matrix

1. **Find Similar Strategies**: Look for rows with similar indicator patterns
2. **Spot Missing Indicators**: Columns with all zeros are unused (stdev-price, PPO)
3. **Identify Themes**: Cluster strategies by indicator profile for backtesting comparisons
4. **Design New Strategies**: Use high-performers' indicator combinations as templates

---

## CSV Export Location
Exported as: `strategy_indicator_matrix.csv` for import into Excel/Sheets/Python

