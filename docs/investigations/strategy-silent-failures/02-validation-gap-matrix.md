# Phase 2: Validation Gap Matrix

**Status:** Complete  
**Date:** 2025-12-15  

## Overview

This document identifies missing validations that could allow bad data to propagate through the strategy evaluation system. Each gap includes the data type affected, current validation status, recommended validation, and impact assessment.

---

## Validation Gap Matrix

| ID | Data Type | Location | Current Validation | Missing Validation | Impact if Invalid Data Passes | Recommendation |
|----|-----------|----------|-------------------|-------------------|------------------------------|----------------|
| VG-001 | **Bar Prices** | `market_data_adapter.py` | None | Price sanity bounds ($0.01 - $1M) | Extreme prices cause incorrect allocations | Add validation |
| VG-002 | **RSI Values** | `indicator_service.py` | None | RSI must be 0-100, flag synthetic 50.0 | Invalid RSI triggers wrong signals | Add validation |
| VG-003 | **Volatility** | `feature_pipeline.py` | None | Minimum volatility threshold (>0.001) | Zero volatility over-allocates "safe" assets | Add validation |
| VG-004 | **Bar Count** | `indicator_service.py` | None | Minimum bars for indicator (e.g., 30 for MA-20) | Indicator computed on insufficient data | Add validation |
| VG-005 | **Quote Timestamp** | `market_data_service.py` | None | Quote staleness check (< 5 min) | Stale quotes used for trading decisions | Add validation |
| VG-006 | **Allocation Sum** | `portfolio_merger.py` | Warns if ≠ 1.0 | Block if deviation > 5% from 1.0 | Under/over-invested portfolio | Enhance validation |
| VG-007 | **Spread Validity** | `market_data_service.py` | None | Spread must be positive (ask > bid) | Negative spread indicates bad data | Add validation |
| VG-008 | **OHLC Integrity** | `market_data_service.py` | ✅ Exists | - | - | Acceptable |
| VG-009 | **Symbol Format** | `market_data_adapter.py` | Basic check | Validate against known universe | Unknown symbols waste API calls | Enhance validation |
| VG-010 | **Decimal Precision** | Throughout | Implicit | Explicit precision limits (8 decimal places) | Rounding errors accumulate | Add validation |

---

## Detailed Gap Analysis

### VG-001: Price Sanity Bounds

**Current State:**
- No validation that prices are within reasonable bounds
- Prices accepted as-is from Alpaca API

**Missing Check:**
```python
# Should validate:
MIN_PRICE = Decimal("0.01")
MAX_PRICE = Decimal("1000000.00")  # $1M

if not MIN_PRICE <= price <= MAX_PRICE:
    raise DataValidationError(f"Price {price} outside valid range")
```

**Impact:** Extreme prices (e.g., $0.00001 or $999999999) could cause:
- Division by zero in returns calculations
- Incorrect percentage allocations
- Massive position sizing errors

**Recommendation:** Add bounds check in `market_data_adapter.py:get_bars()`

---

### VG-002: RSI Value Bounds

**Current State:**
- RSI computed via `technical_indicators.rsi()`
- Fallback to 50.0 on missing data (SF-003)
- No validation that computed RSI is 0-100

**Missing Check:**
```python
# Should validate:
if not 0 <= rsi_value <= 100:
    logger.error(f"Invalid RSI {rsi_value} for {symbol}")
    return None  # or raise

# Should flag synthetic values:
is_synthetic = (rsi_value == 50.0 and len(rsi_series) == 0)
```

**Impact:** Invalid RSI (e.g., -5 or 150) could:
- Trigger extreme buy/sell signals
- Bypass strategy logic expecting 0-100 range

**Recommendation:** Add bounds validation after RSI computation

---

### VG-003: Volatility Floor

**Current State:**
- Volatility computed from returns series
- Zero volatility returned on insufficient data
- No minimum threshold enforced

**Missing Check:**
```python
# Should validate:
MIN_VOLATILITY = 0.001  # 0.1% annualized

if volatility < MIN_VOLATILITY:
    logger.warning(f"Volatility {volatility} below minimum for {symbol}")
    return None  # Exclude from inverse-vol weighting
```

**Impact:** Zero volatility causes:
- Division by zero in inverse-volatility weighting
- Infinite weight assigned to "zero-risk" assets
- Over-concentration in assets with data issues

**Recommendation:** Add floor check in `feature_pipeline.py:compute_volatility()`

---

### VG-004: Minimum Bar Count for Indicators

**Current State:**
- Indicators computed regardless of input data length
- MA-200 computed even with 50 bars
- RSI-14 computed even with 5 bars

**Missing Check:**
```python
# Should validate:
MIN_BARS = {
    "ma_200": 200,
    "ma_50": 50,
    "rsi_14": 20,  # Need some buffer for RSI calculation
    "rsi_10": 15,
}

if len(bars) < MIN_BARS[indicator_type]:
    logger.warning(f"Insufficient bars ({len(bars)}) for {indicator_type}")
    return None
```

**Impact:** Indicators on insufficient data:
- MA-200 on 50 bars = MA-50 (wrong indicator)
- RSI on 5 bars = unstable/meaningless values
- Strategy logic assumes valid indicators

**Recommendation:** Add minimum bar check in `indicator_service.py:get_indicator()`

---

### VG-005: Quote Staleness

**Current State:**
- Quote timestamp captured but not validated
- `DataFreshnessValidator` exists but is non-blocking
- Old quotes used without warning

**Missing Check:**
```python
# Should validate:
MAX_QUOTE_AGE = timedelta(minutes=5)

quote_age = datetime.now(UTC) - quote.timestamp
if quote_age > MAX_QUOTE_AGE:
    logger.warning(f"Stale quote for {symbol}: {quote_age}")
    # Either block or flag as stale
```

**Impact:** Stale quotes used for:
- Current price calculations
- Mid-price for order sizing
- Could execute at significantly different prices

**Recommendation:** Add staleness check in `market_data_service.py:get_quote()`

---

### VG-006: Allocation Sum Validation

**Current State:**
- `portfolio_merger.py:136-151` validates total ≈ 1.0
- Logs warning if deviation detected
- Does not block execution

**Current Code:**
```python
total = sum(allocations.values())
if not math.isclose(total, 1.0, rel_tol=0.01):
    logger.warning(f"Allocation sum {total} deviates from 1.0")
```

**Missing Check:**
```python
# Should block on large deviations:
ALLOCATION_TOLERANCE = Decimal("0.05")  # 5%

total = sum(allocations.values())
if abs(total - Decimal("1.0")) > ALLOCATION_TOLERANCE:
    raise AllocationValidationError(f"Allocation sum {total} outside tolerance")
```

**Impact:** Invalid allocation sum causes:
- Under-invested: cash drag, missed returns
- Over-invested: leverage, margin calls

**Recommendation:** Block if deviation > 5% in `portfolio_merger.py`

---

### VG-007: Spread Validity

**Current State:**
- Spread calculated as ask - bid
- One-sided fallback creates zero spread (SF-004)
- Negative spread not checked

**Missing Check:**
```python
# Should validate:
spread = ask_price - bid_price
if spread < Decimal("0"):
    logger.error(f"Negative spread for {symbol}: bid={bid_price}, ask={ask_price}")
    return None  # Invalid quote
```

**Impact:** Negative spread indicates:
- Data error (bid/ask swapped)
- Stale quote (prices from different times)
- API error

**Recommendation:** Add spread validation in `market_data_service.py:_build_quote_model()`

---

### VG-008: OHLC Integrity ✅

**Current State:**
- Validation exists for: high >= low, high >= open/close, low <= open/close
- Located in `market_data_service.py`

**Status:** Adequate - no gap

---

### VG-009: Symbol Format Validation

**Current State:**
- Basic non-empty check
- No validation against known universe
- Unknown symbols cause API calls that return empty

**Missing Check:**
```python
# Should validate:
KNOWN_UNIVERSE = load_universe()  # From S3 or config

for symbol in symbols:
    if symbol not in KNOWN_UNIVERSE:
        logger.warning(f"Unknown symbol: {symbol}")
        # Consider excluding to save API calls
```

**Impact:** Unknown symbols cause:
- Wasted API rate limit
- Empty data returned silently
- Strategies may expect data for all symbols

**Recommendation:** Add universe validation in `market_data_adapter.py`

---

### VG-010: Decimal Precision Limits

**Current State:**
- Decimal used throughout for financial values
- No explicit precision limits
- Precision varies by source

**Missing Check:**
```python
# Should standardize:
PRICE_PRECISION = 8
ALLOCATION_PRECISION = 6

def standardize_decimal(value: Decimal, precision: int) -> Decimal:
    return value.quantize(Decimal(10) ** -precision, rounding=ROUND_HALF_UP)
```

**Impact:** Inconsistent precision causes:
- Rounding errors accumulate across operations
- Comparison failures due to precision mismatch
- Allocation sums not exactly 1.0

**Recommendation:** Add precision standardization utility

---

## Summary

| Priority | Gap Count | Action Required |
|----------|-----------|-----------------|
| **Critical** | 3 | VG-001, VG-003, VG-006 |
| **High** | 3 | VG-002, VG-004, VG-005 |
| **Medium** | 2 | VG-007, VG-009 |
| **Low** | 1 | VG-010 |
| **Adequate** | 1 | VG-008 (no action) |

## Implementation Priority

1. **Immediate:**
   - VG-003: Volatility floor (prevents infinite weights)
   - VG-006: Strict allocation sum validation (prevents leverage)

2. **Short-term:**
   - VG-001: Price bounds (prevents extreme values)
   - VG-002: RSI bounds (prevents invalid signals)
   - VG-004: Bar count minimums (prevents meaningless indicators)

3. **Medium-term:**
   - VG-005: Quote staleness (market hours dependent)
   - VG-007: Spread validation (rare edge case)
   - VG-009: Symbol universe validation (optimization)

4. **Long-term:**
   - VG-010: Decimal precision standardization (refactoring)
