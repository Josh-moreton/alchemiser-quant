# Indicator Partial-Bar Classification Report

Generated: 2026-01-15
Evaluation Timestamp: 15:45 ET (Eastern Time)

## Summary

This report classifies all 9 technical indicators in the Alchemiser system by their suitability for partial-bar evaluation (using today's incomplete bar with close-so-far as the latest price).

**Design Principle:** All indicators use the same 15:45 ET synthetic close (T-0 data). If we accept a synthetic close for SMA, there's no mathematical reason to exclude EMA, cumulative return, or any other deterministic function of price history. Consistency beats cleverness.

### Classification Legend

| Eligibility | Description | Live Bar Used |
|-------------|-------------|---------------|
| ✅ YES | Indicator works correctly with partial bar close-so-far | Yes |
| ⚠️ CONDITIONAL | Indicator works but with caveats (increased variance) | **Yes** (caveats noted) |
| ❌ NO | Indicator requires completed bars only | No |

### Input Requirements Legend

| Requirement | Description |
|-------------|-------------|
| CLOSE_ONLY | Only close prices required |
| OHLC | Open, High, Low, Close required |
| OHLCV | Open, High, Low, Close, Volume required |

---

## Full Indicator Classification

| # | Indicator Name | DSL Operator | Inputs Required | Eligible for Partial Bar | Uses Live Bar | Current Behavior |
|---|----------------|--------------|-----------------|--------------------------|---------------|------------------|
| 1 | Current Price | `current-price` | CLOSE_ONLY | ✅ YES | ✅ Yes | Returns latest close price from bar series |
| 2 | Cumulative Return | `cumulative-return` | CLOSE_ONLY | ✅ YES | ✅ Yes | Computes (current/past - 1) * 100 over window |
| 3 | Max Drawdown | `max-drawdown` | CLOSE_ONLY | ✅ YES | ✅ Yes | Rolling max peak-to-trough using cummax() |
| 4 | Moving Average | `moving-average-price` | CLOSE_ONLY | ✅ YES | ✅ Yes | Simple moving average via rolling().mean() |
| 5 | RSI | `rsi` | CLOSE_ONLY | ⚠️ CONDITIONAL | ✅ Yes | Wilder's RSI using ewm() for smoothing |
| 6 | EMA | `exponential-moving-average-price` | CLOSE_ONLY | ⚠️ CONDITIONAL | ✅ Yes | Exponential moving average via ewm(span) |
| 7 | Moving Average Return | `moving-average-return` | CLOSE_ONLY | ⚠️ CONDITIONAL | ✅ Yes | Rolling mean of pct_change() * 100 |
| 8 | Stdev Return | `stdev-return` | CLOSE_ONLY | ⚠️ CONDITIONAL | ✅ Yes | Rolling std of pct_change() * 100 |
| 9 | Stdev Price | `stdev-price` | CLOSE_ONLY | ⚠️ CONDITIONAL | ✅ Yes | Rolling std of raw close prices |

---

## Detailed Analysis by Indicator

### 1. Current Price (`current-price`)

**Eligibility:** ✅ YES

**Module:** `functions.strategy_worker.indicators.indicator_service`

**Current Behavior:** Returns the latest close price from the bar series. When live bar is appended, returns today's close-so-far.

**Modifications Needed:** None. Already works with partial bars because it simply returns the latest close value regardless of completeness.

**Edge Cases:**
- Stale price if market closed and cache not updated
- Pre-market/after-hours price may differ from regular session

---

### 2. Cumulative Return (`cumulative-return`)

**Eligibility:** ✅ YES

**Module:** `functions.strategy_worker.indicators.indicators.TechnicalIndicators.cumulative_return`

**Current Behavior:** Computes ((current_price / price_N_days_ago) - 1) * 100. Uses shift(window) to get historical reference price.

**Modifications Needed:** None. Compares today's close-so-far to the close from N days ago. This is the intended behavior for momentum signals.

**Edge Cases:**
- Reference price (N days ago) must be from a completed bar
- For window=60, comparing to price from ~3 months ago is stable

---

### 3. Max Drawdown (`max-drawdown`)

**Eligibility:** ✅ YES

**Module:** `functions.strategy_worker.indicators.indicators.TechnicalIndicators.max_drawdown`

**Current Behavior:** Computes rolling max drawdown using cummax(). Today's close-so-far extends the price series for peak-to-trough calculation.

**Modifications Needed:** None. If today's close-so-far is below the rolling high, drawdown increases. If it sets a new high, drawdown may decrease. This reflects real-time risk exposure.

**Edge Cases:**
- Intraday drawdown may exceed EOD drawdown if price recovers later
- New all-time high intraday resets drawdown to 0 even if price falls later

---

### 4. Moving Average (`moving-average-price`)

**Eligibility:** ✅ YES

**Module:** `functions.strategy_worker.indicators.indicators.TechnicalIndicators.moving_average`

**Current Behavior:** Computes simple moving average over close prices using rolling().mean(). Requires min_periods=window to produce non-NaN values.

**Modifications Needed:** None. The partial close contributes 1/N weight to the average. Effect is minimal for large windows (e.g., 200-day).

**Edge Cases:**
- For short windows (5-20 days), partial bar has higher relative impact
- Gap up/down at open creates larger deviation from yesterday's close-based MA

---

### 5. RSI (`rsi`)

**Eligibility:** ⚠️ CONDITIONAL

**Module:** `functions.strategy_worker.indicators.indicators.TechnicalIndicators.rsi`

**Current Behavior:** Computes RSI using Wilder's smoothing over close prices. Uses ewm() which processes all bars including the latest.

**Modifications Needed:** Works with partial bar but RSI will be more volatile intraday. The partial bar's close-so-far contributes to the gain/loss calculation. Consider adding metadata flag to indicate partial bar was used.

**Edge Cases:**
- RSI may jump significantly near market open when close-so-far equals open
- Intraday RSI variance higher than end-of-day due to price swings
- Early in session (first 30 min), high/low may not yet be established

---

### 6. Exponential Moving Average (`exponential-moving-average-price`)

**Eligibility:** ⚠️ CONDITIONAL

**Module:** `functions.strategy_worker.indicators.indicators.TechnicalIndicators.exponential_moving_average`

**Current Behavior:** Computes EMA using ewm(span=window). More weight on recent prices means partial bar has higher influence than in SMA.

**Modifications Needed:** Works but partial bar has higher weight due to exponential decay. Short-term EMAs (8, 12) will show more intraday variance than long-term (50, 200).

**Edge Cases:**
- EMA crossover signals may flip intraday then revert by close
- For EMA-8 vs SMA-10 comparisons, timing of evaluation matters significantly

---

### 7. Moving Average Return (`moving-average-return`)

**Eligibility:** ⚠️ CONDITIONAL

**Module:** `functions.strategy_worker.indicators.indicators.TechnicalIndicators.moving_average_return`

**Current Behavior:** Computes rolling mean of pct_change(). The partial bar's return (close-so-far vs yesterday's close) is included in the average.

**Modifications Needed:** Works but today's return is incomplete. Early in session, today's return is (close-so-far / yesterday_close - 1) which may not reflect final daily return. Impact depends on window size.

**Edge Cases:**
- Morning volatility causes today's return to swing significantly
- Rolling average may differ from EOD value if session ends differently

---

### 8. Standard Deviation of Returns (`stdev-return`)

**Eligibility:** ⚠️ CONDITIONAL

**Module:** `functions.strategy_worker.indicators.indicators.TechnicalIndicators.stdev_return`

**Current Behavior:** Computes rolling std of pct_change(). Today's return (close-so-far vs yesterday) is included in the volatility calculation.

**Modifications Needed:** Works but today's incomplete return may skew volatility. If today has unusually high intraday range, stdev will spike. For short windows (6 days), this effect is pronounced.

**Edge Cases:**
- Flash crash or spike intraday inflates volatility reading
- Near market open, return is small (close-so-far ≈ open)
- Volatility reading changes significantly throughout the day

---

### 9. Standard Deviation of Price (`stdev-price`)

**Eligibility:** ⚠️ CONDITIONAL

**Module:** `functions.strategy_worker.indicators.indicators.TechnicalIndicators.stdev_price`

**Current Behavior:** Computes rolling std of raw close prices. Today's close-so-far is included in the standard deviation calculation.

**Modifications Needed:** Works but today's price may increase variance reading. Unlike stdev_return, this uses absolute prices so gap effects are included.

**Edge Cases:**
- Large gap up/down increases price stdev immediately at open
- Trending price action may show lower stdev than mean-reverting action

---

## Evaluation Timestamp Mechanism

### Standard Evaluation Time: 15:45 ET

The system uses a consistent evaluation timestamp of **15:45 ET (Eastern Time)** for both backtests and live trading. This time was chosen because:

1. **15 minutes before market close** - captures most of daily price action
2. **After majority of volume traded** - more representative price
3. **Before closing auction volatility** - avoids last-minute noise
4. **Consistent across environments** - backtest and live use same time

### Implementation

```python
from the_alchemiser.shared.utils.evaluation_timestamp import (
    EvaluationTimestampProvider,
    get_evaluation_timestamp,
)

# Get today's evaluation timestamp
eval_time = get_evaluation_timestamp()  # Returns 15:45 ET today

# Custom evaluation time
provider = EvaluationTimestampProvider(
    evaluation_hour=14,
    evaluation_minute=30,
)
custom_time = provider.get_evaluation_timestamp()  # Returns 14:30 ET
```

### Helper Methods

- `is_before_evaluation_time()` - Check if current time is before evaluation
- `is_market_hours()` - Check if during regular market session
- `get_session_progress()` - Get fraction of session completed (0.0 to 1.0)

---

## Partial Bar Data Flow

```
S3 Cache (Historical Bars)
         │
         ▼
CachedMarketDataAdapter.get_bars()
         │
         ├── append_live_bar=True
         │
         ▼
LiveBarProvider.get_todays_bar()  ◄── Alpaca Snapshot API
         │
         └── BarModel(is_incomplete=True)  ◄── Flag set!
                    │
                    ▼
         IndicatorService.get_indicator()
                    │
                    ├── should_use_live_bar(indicator_type)?
                    │   │
                    │   ├── YES: Keep all bars (current_price, moving_average, etc.)
                    │   │
                    │   └── NO: Strip last bar if is_incomplete=True (rsi, ema, stdev_*)
                    │
                    └── prices = pd.Series([bar.close for bar in bars])
                              │
                              ▼
                  TechnicalIndicator (computed without partial bar for volatile indicators)
```

---

## Per-Indicator Live Bar Configuration

The `should_use_live_bar()` function controls whether each indicator uses today's partial bar.

**Design Decision (2026-01-15):** All indicators now use live bars. If we accept a 15:45 synthetic close for any indicator, there's no mathematical reason to exclude others. The only distinction is eligibility (YES vs CONDITIONAL), which affects documentation, not behavior.

```python
from the_alchemiser.shared.indicators.partial_bar_config import should_use_live_bar

# ALL indicators now use live bars for consistency:
should_use_live_bar("current_price")                    # True
should_use_live_bar("moving_average")                   # True
should_use_live_bar("cumulative_return")                # True
should_use_live_bar("max_drawdown")                     # True
should_use_live_bar("rsi")                              # True (CONDITIONAL - more volatile intraday)
should_use_live_bar("exponential_moving_average_price") # True (CONDITIONAL - recursive, naturally updated intraday)
should_use_live_bar("moving_average_return")            # True (CONDITIONAL - today's return incomplete)
should_use_live_bar("stdev_return")                     # True (CONDITIONAL - may spike intraday)
should_use_live_bar("stdev_price")                      # True (CONDITIONAL - gap effects included)
```

To change an indicator's behavior, update `use_live_bar` in `partial_bar_config.py`.

---

## Key Fields Added

### BarModel

```python
@dataclass(frozen=True)
class BarModel:
    ...
    is_incomplete: bool = False  # Marks partial/live bars
```

### PartialBarIndicatorConfig

```python
@dataclass(frozen=True)
class PartialBarIndicatorConfig:
    ...
    use_live_bar: bool = True  # Whether to include live bar in computation
```

---

## Recommendations

### For Strategies Using CONDITIONAL Indicators

1. **RSI threshold buffer**: If using RSI > 70 as overbought, consider RSI > 72 to account for intraday variance
2. **EMA crossover confirmation**: Wait for consecutive evaluation periods to confirm crossover signals
3. **Volatility smoothing**: For stdev indicators, use longer windows to reduce partial bar impact

### For Backtesting

1. Use evaluation timestamp provider to construct partial bars at 15:45 ET
2. Fetch intraday data and aggregate to evaluation time (requires intraday bar source)
3. Mark synthetic partial bars with `is_incomplete=True` for consistency

### For Monitoring

1. Log `includes_partial_bar` in indicator computation events
2. Track indicator value variance between evaluation time and EOD
3. Alert on significant divergence for debugging
