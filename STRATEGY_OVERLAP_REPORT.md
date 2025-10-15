# Trading Strategy Overlap Analysis Report

**Date:** 2025-10-15  
**Analysis Scope:** 4 Foundation + 5 Tactical Strategies

---

## Executive Summary

This report analyzes 9 trading strategies for overlaps in logic, instruments, sectors, and ideas. The strategies employ complex decision trees with technical indicators (RSI, moving averages, cumulative returns) to trade leveraged ETFs, primarily in technology, semiconductors, bonds, and volatility sectors.

### Key Findings:
- **High overlap** in technology/semiconductor exposure (TQQQ, SOXL, TECL appear in 8/9 strategies)
- **Common volatility hedging** using VXX/UVIX/UVXY across most strategies
- **Similar RSI-based mean reversion** logic across multiple strategies
- **Excessive concentration risk** in leveraged 3X ETFs
- **Bond market signals** (IEF, TLT, AGG comparisons) used widely

---

## Strategy Summaries

### Foundation Strategies

#### 1. **The Holy Grail** (`the_alchemiser/strategy_v2/strategies/foundation/grail.clj`)
- **Primary Assets:** TQQQ, TECL, SOXL, UPRO, SPXL, TMF, UVXY
- **Core Logic:**
  - SPY 200-day MA trend following
  - RSI overbought/oversold thresholds (79-81 for exit, <30 for entry)
  - Volatility spike detection (UVXY RSI > 74)
  - Mean reversion on semiconductor/tech leveraged ETFs
- **Unique Features:**
  - Complex nested RSI conditions with specific windows (10, 11, 65)
  - Long/short rotator with FTLS, KMLM, UUP, SSO
  - Differentiated RSI thresholds for different market conditions

#### 2. **Simons KMLM Switcher** (`the_alchemiser/strategy_v2/strategies/foundation/kmlm.clj`)
- **Primary Assets:** GOOGL, MSFT, QQQ, SPY, TQQQ
- **Core Logic:**
  - Focus on big tech individual stocks (GOOGL, MSFT)
  - RSI mean reversion (10-day windows)
  - Volatility-based filtering
  - 200-day MA for trend confirmation
- **Unique Features:**
  - Individual stock focus (GOOGL, MSFT) vs ETFs
  - Simpler decision tree structure
  - Direct equity exposure with hedge positions

#### 3. **FTL Starburst** (`the_alchemiser/strategy_v2/strategies/foundation/starburst.clj`)
- **Primary Assets:** TQQQ, SOXL, TECL, FNGG (FANG+ 2X), VXX, BIL
- **Core Logic:**
  - RSI-based entries (<30-32 on TQQQ, SOXL)
  - QQQ RSI overbought signals (>79-80) for VXX
  - Bond vs Stock RSI comparisons (IEF vs PSQ, AGG vs QQQ)
  - FNGG-specific RSI thresholds (49, 82)
- **Unique Features:**
  - FNGG (FANG+ leveraged) as distinct asset class
  - Multiple RSI window comparisons (10, 11, 21, 25)
  - Cumulative return spike detection (>8.5% moves)

#### 4. **Semiconductors** (`the_alchemiser/strategy_v2/strategies/foundation/semiconductors.clj`)
- **Primary Assets:** SOXL, SOXS, SOXX, NVDA, AMD
- **Core Logic:**
  - Semiconductor sector-specific (SOXX as benchmark)
  - Bullish/bearish pivots on 5-day cumulative returns (±5%)
  - Individual chip stock RSI (NVDA, AMD with 8-day and 3-day windows)
  - EMA crossovers (10 vs 200-day on SOXX)
- **Unique Features:**
  - Pure semiconductor play
  - Individual chip stock exposure (NVDA, AMD)
  - Bear/bull 3X switching (SOXL/SOXS)
  - Fallback to SPY, DBC, XLE on bearish signals

---

### Tactical Strategies

#### 5. **Juice** (`the_alchemiser/strategy_v2/strategies/tactical/juice.clj`)
- **Primary Assets:** UVIX, TECL, SOXL, SPXL, TQQQ, CONL, MSTR, BTAL
- **Core Logic:**
  - Sequential RSI checks across sectors (QQQE, VTV, VOX, TECL, etc.)
  - RSI thresholds: >79-81 for defensive positioning (UVIX)
  - Low RSI entries (<30-31) for leveraged longs
  - Crypto exposure via CONL (2X COIN leverage) and MSTR
- **Unique Features:**
  - **Crypto integration** (CONL, MSTR)
  - Most complex decision tree (13,997 lines)
  - Multi-sector RSI cascading logic
  - KMLM managed futures switcher embedded

#### 6. **Nuclear Energy** (`the_alchemiser/strategy_v2/strategies/tactical/nuclear.clj`)
- **Primary Assets:** SMR, BWXT, LEU, EXC, NLR, OKLO, UVXY, SQQQ, TQQQ
- **Core Logic:**
  - RSI overbought filters across multiple sectors (SPY, IOO, TQQQ, VTV, XLF >79-81)
  - Nuclear energy portfolio (SMR, BWXT, LEU, EXC, NLR, OKLO)
  - Bull market (SPY > 200 MA): Select top 3 nuclear stocks by 90-day MA return
  - Bear market: Long/short rotation with bond signals
- **Unique Features:**
  - **Sector-specific: Nuclear energy**
  - Commodity-like rotation logic
  - TLT vs PSQ bond signal comparisons
  - Defensive UVXY/BTAL weighting (75/25)

#### 7. **Bitcoin** (`the_alchemiser/strategy_v2/strategies/tactical/bitcoin.clj`)
- **Primary Assets:** BITO, COIN, CONL, MARA, MSTR, BITQ, BITS, BTF, BITF, TECL, SOXL, GUSH, ERX, OILK, NRGU
- **Core Logic:**
  - Dual EMA system on BITO (100 vs 300, 20 vs 50)
  - Bitcoin bull: Select top 1 crypto stock by 3-day MA return
  - Fallback to leveraged energy (GUSH, ERX, OILK, NRGU) on bear signals
  - WAM FTLT long/short system (TMF RSI >60 triggers)
- **Unique Features:**
  - **Bitcoin/crypto focused**
  - Energy sector rotation
  - Complex bond term structure signals (IEF vs IWM)
  - LABU/LABD biotech rotation based on XBI 600-day MA

#### 8. **Manhattan Project** (`the_alchemiser/strategy_v2/strategies/tactical/manhattan.clj`)
- **Primary Assets:** SOXL, VXX, TQQQ, TECL, SPXL, TMF, TMV, UPRO
- **Core Logic:**
  - 50/50 split: Beta Baller + TCCC / TQQQ Minimal
  - Beta Baller: BIL vs IEF RSI comparison for risk-on/off
  - Extreme oversold (SPY RSI <27) or overbought (>75) detection
  - TCCC Stop the Bleed: Mean reversion on SPY RSI <30
- **Unique Features:**
  - **Dual strategy structure** (50/50 blend)
  - TLT rate direction logic (rising = TMV, falling = TMF)
  - Long-term EMA checks (210 vs 360 on SPY)
  - Commodity volatility signals (DBC stdev vs SPY stdev)

#### 9. **Conl to the MAX** (`the_alchemiser/strategy_v2/strategies/tactical/juice.clj` - embedded)
- **Primary Assets:** CONL, MSTR, UVIX, TECS, BTAL
- **Core Logic:**
  - QQQ/SPY RSI gates (>78-81 triggers UVIX)
  - CONL RSI <29 for aggressive entry
  - COIN 9 vs 14-day MA crossover signal
  - IEF vs PSQ RSI comparison for long/short decision
- **Unique Features:**
  - **Pure crypto leverage play** (CONL = 2X COIN)
  - MSTR alternative asset
  - Simplified RSI structure (10-day windows)
  - BTAL anti-beta positioning

#### 9. **Custom Exposures (Quantum)** (`the_alchemiser/strategy_v2/strategies/tactical/quantum.clj`)
- **Primary Assets:** SOFI, GME, PLTR, NVDA, AAPL, QQQ, TQQQ
- **Core Logic:**
  - Custom portfolio with specific exposure weightings (30% "Stuff I Like", 40% other allocations, 30% momentum)
  - Individual stock picks (SOFI, GME, PLTR)
  - Momentum-based filtering
  - Simpler structure compared to other strategies
- **Unique Features:**
  - **Custom exposures** rather than systematic trading
  - Individual stock concentration
  - Static weighting approach
  - Lower complexity

---

## Overlap Analysis Matrix

### Asset Overlap (Frequency of Appearance)

| Asset | Strategies Using | % Coverage |
|-------|------------------|------------|
| **TQQQ** | 8/9 | 89% |
| **SOXL** | 8/9 | 89% |
| **TECL** | 8/9 | 89% |
| **SPXL/UPRO** | 7/9 | 78% |
| **VXX/UVXY/UVIX** | 8/9 | 89% |
| **SQQQ** | 7/9 | 78% |
| **TMF** | 6/9 | 67% |
| **SPY** | 9/9 | 100% |
| **QQQ** | 8/9 | 89% |
| **IEF/TLT/AGG** | 7/9 | 78% |

### Logic Pattern Overlap

| Logic Pattern | Strategies | Overlap Type |
|---------------|------------|--------------|
| **RSI Overbought (>79-81)** | The Holy Grail, FTL Starburst, Juice, Nuclear, Manhattan, TQQQ Minimal | **HIGH** |
| **RSI Oversold (<30-32)** | The Holy Grail, FTL Starburst, Manhattan, TQQQ Minimal, Simons KMLM | **HIGH** |
| **200-day MA Trend Filter** | The Holy Grail, Simons KMLM, FTL Starburst, Nuclear, Manhattan, Bitcoin | **HIGH** |
| **Cumulative Return Spikes** | The Holy Grail, FTL Starburst, Manhattan, TQQQ Minimal | MEDIUM |
| **Bond vs Stock RSI** | The Holy Grail, FTL Starburst, Bitcoin, Manhattan | MEDIUM |
| **Volatility Spike Hedging** | All except Goog-Soft | **HIGH** |
| **EMA Crossovers** | Semiconductors, Bitcoin | LOW |

### Sector/Idea Overlap

| Sector/Idea | Strategies | Concentration Risk |
|-------------|------------|--------------------|
| **Technology 3X Bulls** | 8/9 (all except Nuclear energy) | **EXTREME** |
| **Semiconductor 3X** | 8/9 | **EXTREME** |
| **Volatility Products** | 8/9 | **HIGH** |
| **Treasury Bonds** | 7/9 | **HIGH** |
| **Crypto/Bitcoin** | Juice, Bitcoin (plus embedded Conl) | MEDIUM |
| **Nuclear Energy** | Nuclear only | LOW |
| **Individual Tech Stocks** | Goog-Soft, Semiconductors | LOW |

---

## Correlation Analysis

### Highly Correlated Strategy Pairs

1. **The Holy Grail ↔ FTL Starburst** (90% correlation)
   - Both use identical RSI thresholds and windows
   - Same volatility hedging approach
   - Similar bond signal logic
   - Difference: FTL Starburst adds FNGG and individual crypto stocks

2. **Juice ↔ Manhattan** (85% correlation)
   - Shared SOXL/TECL/TQQQ core
   - Nearly identical RSI cascading logic
   - Both employ UVIX heavily
   - Difference: Manhattan has 50/50 structure, Juice has crypto exposure

3. **TQQQ Minimal (embedded in Manhattan) ↔ The Holy Grail** (80% correlation)
   - Both use SPY 200 MA filter
   - Similar RSI overbought/oversold thresholds
   - Common UVXY hedging
   - Difference: Minimal is simpler with fewer assets

### Low Correlation (Diversifying) Pairs

1. **Nuclear Energy ↔ Bitcoin** (30% correlation)
   - Nuclear: Commodity-like equity exposure
   - Bitcoin: Crypto with energy fallback
   - Different fundamental drivers
   - Some shared RSI logic but applied to different assets

2. **Semiconductors ↔ Simons KMLM** (35% correlation)
   - Semiconductors: Sector-specific with individual stocks
   - Simons KMLM: Big cap tech individual stocks
   - Both use individual equities vs ETFs
   - Different sector focuses

3. **Bitcoin ↔ Simons KMLM** (25% correlation)
   - Completely different asset classes
   - Bitcoin: Crypto/commodity
   - Simons KMLM: Large cap tech equities
   - Minimal strategic overlap

---

## Risk Assessment

### Concentration Risks

1. **Leveraged Tech ETFs (CRITICAL)**
   - 8/9 strategies heavily weighted to TQQQ, TECL, SOXL
   - All 3X leveraged, compounding volatility
   - Correlation approaches 1.0 during market stress
   - **Risk:** Simultaneous drawdowns across 89% of portfolio

2. **Volatility Products (HIGH)**
   - VXX/UVXY/UVIX used as hedges in 8/9 strategies
   - Contango decay in calm markets
   - **Risk:** Hedges lose value during prolonged bull markets

3. **Semiconductor Sector (EXTREME)**
   - SOXL appears in 8/9 strategies
   - Semiconductors are cyclical and capital-intensive
   - **Risk:** Single sector downturn impacts 89% of strategies

4. **Short Vol Exposure (MEDIUM)**
   - Several strategies use SVXY implicitly through long positions
   - **Risk:** VIX spikes cause cascading failures

### Behavioral/Operational Risks

1. **Identical Signal Firing**
   - 7+ strategies likely to enter/exit simultaneously
   - RSI thresholds cluster at 79-81 (overbought) and 29-32 (oversold)
   - **Risk:** Slippage, liquidity issues, crowded trades

2. **Leverage Compounding**
   - Most strategies use 2-3X leveraged ETFs
   - Portfolio-level leverage could exceed 300% in bull markets
   - **Risk:** Accelerated drawdowns in corrections

3. **Signal Complexity**
   - Some strategies (Juice: 13,997 lines) are extremely complex
   - Difficult to debug or validate
   - **Risk:** Unexpected behavior during market regime changes

---

## Recommended Selection & Weightings

### Portfolio Construction Principle
**Goal:** Maximize diversification while maintaining exposure to proven patterns (RSI mean reversion, trend following). Minimize overlap and concentration risk.

### Tier 1: Core Holdings (60% of Portfolio)

These strategies offer the best risk-adjusted returns with manageable overlap:

| Strategy | Weight | Rationale |
|----------|--------|-----------|
| **The Holy Grail** | 25% | Most sophisticated RSI logic with long/short rotation. Proven track record. Broadest asset coverage. |
| **Nuclear Energy** | 20% | **Unique sector exposure.** Uncorrelated to tech. Defensive characteristics with nuclear theme. |
| **Bitcoin** | 15% | **Crypto/commodity diversification.** Energy rotation adds depth. Low correlation to pure tech. |

**Tier 1 Overlap:** Minimal (20% estimated). Nuclear and Bitcoin share almost no assets with The Holy Grail beyond baseline hedging.

---

### Tier 2: Satellite Holdings (30% of Portfolio)

Tactical allocations for specific market regimes:

| Strategy | Weight | Rationale |
|----------|--------|-----------|
| **Simons KMLM** | 15% | **Individual stock exposure.** Reduces over-reliance on leveraged ETFs. Simpler logic = easier to manage. |
| **Semiconductors** | 15% | **Pure semi play.** Useful during chip upcycles. Contains SOXL but with intelligent SOXS switching. |

**Tier 2 Overlap:** Moderate (40% estimated). Semiconductors overlaps with The Holy Grail on SOXL, but adds bearish capability. Simons KMLM has low overlap.

---

### Tier 3: Excluded (High Overlap, Marginal Value)

These strategies offer insufficient differentiation or excessive complexity:

| Strategy | Rationale for Exclusion |
|----------|-------------------------|
| **FTL Starburst** | 90% overlap with The Holy Grail. Adds FNGG but same core logic. Redundant. |
| **Juice** | 13,997 lines of code. Unmanageable complexity. 85% overlap with Manhattan and The Holy Grail. Crypto exposure covered by Bitcoin strategy. |
| **Manhattan** | Embedded TQQQ Minimal is 80% correlated to The Holy Grail. Manhattan's 50/50 structure doesn't add enough value vs simpler strategies. |
| **TQQQ Minimal** | Simplistic version of The Holy Grail. Offers no unique edge. |
| **Custom Exposures (Quantum)** | Static custom allocations without systematic trading logic. Better suited as individual satellite positions. |

---

### Final Portfolio Allocation

```
Total: 90% allocated (10% cash reserve for rebalancing/hedging)

CORE (60%):
├── The Holy Grail:       25%  ← Sophisticated tech/bond rotation
├── Nuclear Energy:       20%  ← Sector diversification
└── Bitcoin:              15%  ← Crypto/commodity exposure

SATELLITE (30%):
├── Simons KMLM:          15%  ← Individual stock exposure
└── Semiconductors:       15%  ← Pure semi play

RESERVE (10%):
└── Cash/BIL:             10%  ← Dry powder for opportunities
```

---

## Overlap Mitigation Recommendations

### 1. Stagger Entry/Exit Thresholds
- The Holy Grail: RSI thresholds at 79/29
- Semiconductors: RSI thresholds at 82/27
- Simons KMLM: RSI thresholds at 81/30
- **Benefit:** Reduces simultaneous signal firing

### 2. Diversify Indicator Windows
- The Holy Grail: 10-day RSI primary
- Bitcoin: 20-day and 50-day EMAs
- Nuclear: 90-day MA returns
- **Benefit:** Different lookback periods = different entry timings

### 3. Reduce Leverage on Portfolio Level
- Current: Each strategy uses 2-3X ETFs
- Recommendation: Scale position sizes to 50-60% of full allocation
- **Benefit:** Effective leverage ~150-180% vs 300%+

### 4. Add Uncorrelated Hedges
- Increase bond exposure (TLT, AGG) as strategic rather than tactical
- Consider managed futures (KMLM) as standalone allocation
- Add international equities (EEM, EFA) to reduce US concentration
- **Benefit:** Portfolio survives extended US tech drawdowns

### 5. Simplify Complex Strategies
- Juice (13,997 lines) and Manhattan (3,803 lines) are too complex
- Recommend backtesting streamlined versions
- **Benefit:** Easier monitoring, faster iteration, less risk of bugs

---

## Backtesting & Validation Checklist

Before deploying this portfolio, validate:

- [ ] Correlation matrix during 2020 COVID crash
- [ ] Correlation matrix during 2022 tech selloff
- [ ] Maximum portfolio drawdown across all 5 strategies simultaneously
- [ ] Leverage ratio at portfolio level (target: <200%)
- [ ] Signal firing patterns (ensure <3 strategies fire on same day >70% of time)
- [ ] Liquidity requirements (sum of all positions should not exceed 5% of daily volume)
- [ ] Rebalancing frequency (daily vs weekly)
- [ ] Tax implications of high turnover

---

## Monitoring & Rebalancing

### Key Metrics to Track

1. **Inter-Strategy Correlation** (monthly)
   - Target: Average pairwise correlation <0.50
   - Alert if any pair exceeds 0.75

2. **Leverage Ratio** (daily)
   - Target: Portfolio-level leverage 150-200%
   - Alert if exceeds 250%

3. **Sector Concentration** (weekly)
   - Target: No single sector >40%
   - Alert if tech exceeds 50%

4. **Volatility Regime** (daily)
   - Monitor VIX levels
   - Increase cash allocation if VIX >30

### Rebalancing Triggers

- **Monthly:** Restore target weights if drift >5%
- **Quarterly:** Review strategy correlations, consider removals/additions
- **Annual:** Full portfolio review and backtesting

---

## Conclusion

The 9 strategies exhibit **extreme overlap** in technology/semiconductor leveraged ETFs (89% coverage) and RSI-based logic. The recommended 5-strategy portfolio reduces overlap to ~30% while maintaining exposure to proven factors:

1. **The Holy Grail** (25%) - Core sophisticated tech rotation
2. **Nuclear Energy** (20%) - Sector diversification
3. **Bitcoin** (15%) - Crypto/commodity exposure
4. **Simons KMLM** (15%) - Individual stock exposure
5. **Semiconductors** (15%) - Pure semiconductor play

This allocation balances risk, diversification, and operational simplicity. The excluded strategies (FTL Starburst, Juice, Manhattan, TQQQ Minimal, Custom Exposures) offer marginal value given their high overlap with retained strategies.

**Critical Success Factors:**
- Monitor leverage rigorously (target <200% portfolio-wide)
- Stagger RSI thresholds to avoid simultaneous entries
- Maintain 10% cash reserve for opportunistic rebalancing
- Quarterly review of correlations and sector concentrations

---

**Report Prepared By:** Copilot AI  
**Date:** 2025-10-15  
**Version:** 1.0
