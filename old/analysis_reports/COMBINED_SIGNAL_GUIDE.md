# MACD + SMA Signal Combination Guide

## Executive Summary

This guide explains how to combine MACD momentum signals with SMA trend signals for optimal LQQ3 trading using TQQQ as the signal source. Our analysis shows that the **OR Logic combination** delivers superior returns (10,189% vs 5,405% buy-and-hold) by maximizing bull market participation while managing downside risk.

## Signal Overview

### MACD (Moving Average Convergence Divergence)

- **Parameters**: 12-day EMA, 26-day EMA, 9-day Signal Line
- **Signal**: Bullish when MACD line > Signal line
- **Characteristics**:
  - Fast-responding momentum indicator
  - Generates ~247 signals over 12 years
  - Good at catching momentum shifts
  - More prone to false signals in sideways markets

### SMA (Simple Moving Average)

- **Parameters**: 200-day Simple Moving Average
- **Signal**: Bullish when TQQQ price > 200-day SMA
- **Characteristics**:
  - Slow-responding trend indicator
  - Generates ~56 signals over 12 years
  - Excellent at identifying major trends
  - Less prone to whipsaws but slower to respond

## Current Signal Status (2025-06-18)

| Indicator | Status | Value | Signal |
|-----------|--------|-------|---------|
| **TQQQ Price** | $73.46 | - | - |
| **200-day SMA** | $71.59 | +2.6% above | 🟢 **BULLISH** |
| **MACD Line** | 2.8631 | Below signal | 🔴 **BEARISH** |
| **MACD Signal** | 3.3625 | - | - |
| **MACD Histogram** | -0.4994 | Negative | 🔴 **BEARISH** |

### Combined Signal: 🟢 **BUY** (Cautious Bullish)

**Recommendation**: HOLD/BUY LQQ3 with medium confidence

## Signal Combination Methods

### 1. OR Logic (Recommended Strategy)

**Rule**: BUY when either MACD OR SMA is bullish, SELL only when both are bearish

**Performance**: 10,189% total return, 4,784% excess return over buy-and-hold

**Advantages**:

- Maximum bull market participation (87.3% time in market)
- Reduces impact of individual signal noise
- Captures trends early via MACD, confirms via SMA

**Current Status**: 🟢 BUY (SMA bullish, MACD bearish)

### 2. AND Logic (Conservative Alternative)

**Rule**: BUY only when both MACD AND SMA are bullish

**Performance**: Lower returns but reduced volatility

**Advantages**:

- High confidence signals
- Reduced whipsaw trades
- Lower time in market (39.3%)

**Current Status**: 🔴 SELL (requires both signals)

### 3. Signal Strength Classification

| Strength Level | Criteria | Action | Confidence |
|----------------|----------|--------|------------|
| **Strong Bullish** | Both bullish + strong momentum | Strong Buy | High |
| **Bullish** | Both signals bullish | Buy | High |
| **Cautious Bullish** | One signal bullish | Cautious Buy | Medium |
| **Bearish** | Both signals bearish | Sell/Reduce | High |

**Current**: Cautious Bullish (SMA bullish, MACD bearish)

## How Signals Complement Each Other

### Signal Correlation

- **Agreement**: 52% of the time
- **MACD leads SMA**: Sometimes by 0.7 days on average
- **Complementary coverage**: When one signal misses a move, the other often catches it

### Market State Distribution (Last 12 Years)

- **Both Bullish**: 39.3% of days (strongest performance)
- **SMA Only**: 33.1% of days (steady trend)
- **MACD Only**: 14.9% of days (momentum plays)
- **Both Bearish**: 12.7% of days (avoid market)

### Performance by Signal State

| Signal State | Avg 1-Day Return | Avg 20-Day Return | Win Rate |
|--------------|------------------|-------------------|----------|
| Both Bullish | +0.298% | +3.109% | 55.2% |
| MACD Only | +0.314% | +5.660% | 53.7% |
| SMA Only | +0.133% | +3.462% | 52.7% |
| Both Bearish | -0.132% | +4.250% | 51.5% |

## Trading Implementation

### Position Sizing Rules

1. **Buy Signal** (OR Logic): Deploy 100% of available cash
2. **Sell Signal** (Both bearish): Sell 66% of position
3. **Hold Signal**: Maintain current position

### Signal Monitoring

- **Daily check**: Review both MACD and SMA status
- **Signal changes**: Pay attention to crossovers
- **Trend context**: Consider price distance from SMA
- **Momentum strength**: Monitor MACD histogram

### Risk Management

- **Maximum exposure**: 100% during bull signals
- **Reduced exposure**: 34% during bear signals
- **Volatility awareness**: TQQQ is 3x leveraged
- **Drawdown tolerance**: Strategy max drawdown -59.16%

## Current Market Context (June 2025)

### Recent Signal Activity

- **May 16**: SMA turned bullish (major trend shift)
- **Recent weeks**: MACD oscillating (momentum uncertainty)
- **Current state**: Trend positive, momentum weak

### Key Levels to Watch

- **TQQQ $71.59**: 200-day SMA support level
- **MACD convergence**: Watch for MACD to cross above signal line
- **Volume confirmation**: Higher volume on breakouts

## Implementation Checklist

### Daily Routine

1. ✅ Check TQQQ closing price vs 200-day SMA
2. ✅ Check MACD line vs Signal line
3. ✅ Determine combined signal (OR Logic)
4. ✅ Execute trades if signal changed
5. ✅ Update position tracking

### Weekly Review

1. 📊 Analyze signal strength and momentum
2. 📊 Review recent performance vs benchmark
3. 📊 Check for any strategy adjustments needed
4. 📊 Monitor correlation between TQQQ and LQQ3

### Monthly Analysis

1. 📈 Calculate returns vs buy-and-hold
2. 📈 Review drawdown and risk metrics
3. 📈 Analyze signal effectiveness
4. 📈 Document lessons learned

## Why This Combination Works

### Complementary Strengths

1. **MACD catches momentum**: Early entry/exit signals
2. **SMA confirms trends**: Filters out noise
3. **OR Logic maximizes participation**: Don't miss bull runs
4. **Reduced whipsaws**: Either signal can keep you invested

### Historical Evidence

- **12+ years of data**: Robust backtest period
- **Multiple market cycles**: 2013 recovery, 2018 correction, COVID crash/recovery
- **Consistent outperformance**: 4,784% excess return over buy-and-hold
- **Manageable risk**: Sharpe ratio of 1.0

### Current Recommendation

Given the current signal status (SMA bullish, MACD bearish), the strategy indicates:

**🟡 CAUTIOUS BUY**: Maintain or establish LQQ3 position with medium confidence. The uptrend is intact (price above 200 SMA) but momentum is currently weak (MACD bearish). This is exactly the type of situation where the OR Logic shines - keeping you invested during trend continuation even when momentum temporarily weakens.

**Monitor closely**: Watch for MACD to turn bullish for stronger conviction, or for price to break below $71.59 (200 SMA) which would turn the SMA bearish and trigger a sell signal.

---

*This analysis is based on historical data and should not be considered financial advice. Always consider your risk tolerance and investment objectives before trading.*
