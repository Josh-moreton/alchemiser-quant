# Phase 1: Silent Fallback Audit

**Status:** Complete  
**Date:** 2025-12-15  

## Overview

This document catalogs every location in the Strategy module where errors are caught but execution continues with default/fallback values. Each entry includes the exact code location, the fallback behavior, impact assessment, and recommendation.

---

## Critical Severity (Direct Trading Impact)

### SF-001: Technical Indicators Fallback to 0.0

| Attribute | Value |
|-----------|-------|
| **Location** | `the_alchemiser/strategy_v2/handlers/signal_generation_handler.py:493-506` |
| **Error Type Caught** | `Exception` (broad catch) |
| **Fallback Behavior** | All indicators set to `0.0`: `rsi_10=0.0`, `rsi_20=0.0`, `current_price=0.0`, `ma_200=0.0` |
| **Impact** | **CRITICAL** - RSI=0.0 triggers extreme oversold signals (buy). Price=0.0 causes division errors. MA=0.0 causes incorrect trend signals. Email shows 0.0 values but trade decisions may use these. |
| **Recommendation** | **BLOCK** - Add `fallback_used=True` flag in email. Consider failing trade validation if fallback used for critical symbols. |

**Code:**
```python
except Exception as e:
    self.logger.warning(
        f"Failed to fetch technical indicators for {symbol}: {e}",
        extra={"symbol": symbol, "error": str(e)},
    )
    # Fallback to zero values so email generation doesn't break
    indicators[symbol] = {
        "rsi_10": 0.0,
        "rsi_20": 0.0,
        "current_price": 0.0,
        "ma_200": 0.0,
    }
```

---

### SF-002: Feature Pipeline Exception Swallowing

| Attribute | Value |
|-----------|-------|
| **Location** | `the_alchemiser/strategy_v2/adapters/feature_pipeline.py:300-310` |
| **Error Type Caught** | `Exception` (broad catch) |
| **Fallback Behavior** | Returns neutral defaults: `current_price=0.0`, `volatility=0.0`, `ma_ratio=1.0`, `price_position=0.5`, `volume_ratio=1.0` |
| **Impact** | **CRITICAL** - Creates artificially "stable" asset appearance. Zero volatility makes assets appear risk-free. Neutral ratios mask actual market conditions. |
| **Recommendation** | **BLOCK** - Remove blanket exception handler. Handle specific exceptions. Return explicit error indicator. |

**Code:**
```python
except Exception as e:
    logger.warning(f"Error extracting price features: {e}")
    # Return default features on error
    features = {
        "current_price": 0.0,
        "volatility": 0.0,
        "ma_ratio": 1.0,
        "price_position": 0.5,
        "volume_ratio": 1.0,
    }
```

---

### SF-003: RSI Neutral Fallback (50.0)

| Attribute | Value |
|-----------|-------|
| **Location** | `the_alchemiser/strategy_v2/indicators/indicator_service.py:103` |
| **Error Type Caught** | Missing/NaN data (not exception) |
| **Fallback Behavior** | Returns `50.0` (neutral RSI) when series is empty or contains NaN |
| **Impact** | **HIGH** - Neutral RSI=50.0 is indistinguishable from real neutral signal. Could mask missing data as "no signal" when data is actually unavailable. |
| **Recommendation** | **WARN** - Return explicit `None` instead of 50.0. Require strategy to handle missing indicator explicitly. |

**Code:**
```python
rsi_value = self._latest_value(rsi_series, 50.0)  # Neutral fallback
```

---

### SF-004: Quote One-Sided Fallback

| Attribute | Value |
|-----------|-------|
| **Location** | `the_alchemiser/shared/services/market_data_service.py:262-270` |
| **Error Type Caught** | Invalid price data (zero values) |
| **Fallback Behavior** | If only bid OR ask is valid, uses same price for both sides (creates artificial 0 spread) |
| **Impact** | **HIGH** - Zero spread affects pricing calculations. Mid-price equals the single valid price. Could cause unexpected slippage calculations. |
| **Recommendation** | **WARN** - Log warning with `one_sided_quote=True`. Fail trading validation if spread is zero for material positions. |

**Code:**
```python
if bid_valid:
    # Bid-only fallback: use bid for both sides
    return self._create_quote_model(
        symbol, bid_price_raw, bid_price_raw, bid_size, 0, timestamp
    )
if ask_valid:
    # Ask-only fallback: use ask for both sides
    return self._create_quote_model(
        symbol, ask_price_raw, ask_price_raw, 0, ask_size, timestamp
    )
```

---

### SF-005: Current Price Fallback to 100.0

| Attribute | Value |
|-----------|-------|
| **Location** | `the_alchemiser/strategy_v2/indicators/indicator_service.py:123` |
| **Error Type Caught** | Empty price series |
| **Fallback Behavior** | Returns `Decimal("100.0")` as current_price when price series is empty |
| **Impact** | **HIGH** - Arbitrary price of $100 used when no data. Could cause completely incorrect position sizing if used downstream. |
| **Recommendation** | **BLOCK** - Return `None` or raise exception. Never use synthetic price. |

**Code:**
```python
current_price=(Decimal(str(prices.iloc[-1])) if len(prices) > 0 else Decimal("100.0")),
```

---

## High Severity (Data Quality Issues)

### SF-006: Bar Fetch Failure Returns Empty List

| Attribute | Value |
|-----------|-------|
| **Location** | `the_alchemiser/strategy_v2/adapters/market_data_adapter.py:196-208` |
| **Error Type Caught** | `RuntimeError`, `ValueError` |
| **Fallback Behavior** | Returns `result[symbol] = []` (empty list) |
| **Impact** | **HIGH** - Empty bars list silently passed through pipeline. May cause downstream zero-division or incorrect calculations when indicators attempt computation on empty data. |
| **Recommendation** | **LOG** - Add `data_unavailable=True` flag. Track count of symbols with missing data. |

**Code:**
```python
except (RuntimeError, ValueError) as e:
    logger.warning(
        "Failed to fetch bars",
        extra={...}
    )
    result[symbol] = []
```

---

### SF-007: Current Price Returns None on Failure

| Attribute | Value |
|-----------|-------|
| **Location** | `the_alchemiser/strategy_v2/adapters/market_data_adapter.py:289-301` |
| **Error Type Caught** | `RuntimeError`, `ValueError`, `KeyError` |
| **Fallback Behavior** | Returns `result[symbol] = None` |
| **Impact** | **MEDIUM** - None price could propagate if not explicitly checked. Better than synthetic value, but requires downstream validation. |
| **Recommendation** | **MONITOR** - Ensure all downstream consumers explicitly handle None. Add metric for None price count. |

**Code:**
```python
except (RuntimeError, ValueError, KeyError) as e:
    logger.warning(
        "Failed to get current price",
        extra={...}
    )
    result[symbol] = None
```

---

### SF-008: Zero Volatility on Insufficient Returns

| Attribute | Value |
|-----------|-------|
| **Location** | `the_alchemiser/strategy_v2/adapters/feature_pipeline.py:53-65` (inferred) |
| **Error Type Caught** | Insufficient data |
| **Fallback Behavior** | Returns `volatility=0.0` when returns series is too short |
| **Impact** | **HIGH** - Zero volatility makes assets appear completely risk-free. Affects inverse-volatility weighting. Could over-allocate to assets with data issues. |
| **Recommendation** | **BLOCK** - Return explicit None. Exclude from inverse-vol weighting if volatility unavailable. |

---

### SF-009: Correlation Fallback to 0.0

| Attribute | Value |
|-----------|-------|
| **Location** | `the_alchemiser/strategy_v2/adapters/feature_pipeline.py` (correlation computation) |
| **Error Type Caught** | Any exception in correlation calculation |
| **Fallback Behavior** | Returns `0.0` correlation on any error |
| **Impact** | **MEDIUM** - False zero correlation between assets. Could affect portfolio optimization that relies on correlation matrix. |
| **Recommendation** | **LOG** - Track correlation calculation failures. Return None for failed correlations. |

---

## Medium Severity (Partial Functionality Loss)

### SF-010: Selection Limit Parse Failure

| Attribute | Value |
|-----------|-------|
| **Location** | `the_alchemiser/strategy_v2/engines/dsl/dsl_evaluator.py` (select-top parsing) |
| **Error Type Caught** | Parse failure for selection limit |
| **Fallback Behavior** | Sets `limit=None` (all assets selected) |
| **Impact** | **MEDIUM** - All assets selected instead of top N. Changes portfolio composition unexpectedly. |
| **Recommendation** | **WARN** - Log explicit warning. Consider failing evaluation if limit is core to strategy. |

---

### SF-011: Symbol Evaluation Failure Skipped

| Attribute | Value |
|-----------|-------|
| **Location** | `the_alchemiser/strategy_v2/engines/dsl/dsl_evaluator.py:100-180` |
| **Error Type Caught** | Per-symbol evaluation failure |
| **Fallback Behavior** | Symbol skipped with warning log, continues with remaining symbols |
| **Impact** | **MEDIUM** - Symbols silently excluded from portfolio. Portfolio may be incomplete without operator awareness. |
| **Recommendation** | **LOG** - Add `symbols_excluded` count to final output. Alert if exclusion rate > 10%. |

---

### SF-012: Volatility Calculation Returns None

| Attribute | Value |
|-----------|-------|
| **Location** | `the_alchemiser/strategy_v2/adapters/feature_pipeline.py` |
| **Error Type Caught** | Insufficient data for volatility |
| **Fallback Behavior** | Returns `None` for that asset |
| **Impact** | **MEDIUM** - Asset excluded from inverse volatility weighting. May cause over-concentration in remaining assets. |
| **Recommendation** | **MONITOR** - Track exclusion count. Add metric for "assets_excluded_no_volatility". |

---

### SF-013: Empty Target Weights Returns None

| Attribute | Value |
|-----------|-------|
| **Location** | `the_alchemiser/strategy_v2/handlers/signal_generation_handler.py` |
| **Error Type Caught** | Empty allocation from strategy |
| **Fallback Behavior** | Returns `None` (no signals generated) |
| **Impact** | **MEDIUM** - Strategy produces no signals. Logged as warning but may not reach operator attention. |
| **Recommendation** | **WARN** - Ensure WorkflowFailed event is published for zero-signal output. |

---

### SF-014: No Aggregation Timeout Detection

| Attribute | Value |
|-----------|-------|
| **Location** | `the_alchemiser/aggregator_v2/lambda_handler.py:115-124` |
| **Error Type Caught** | N/A - missing detection |
| **Fallback Behavior** | Session stays in "waiting" state indefinitely if worker dies |
| **Impact** | **HIGH** - If strategy worker Lambda times out or crashes, aggregator waits forever (until 600s timeout). No automatic detection or notification. |
| **Recommendation** | **BLOCK** - Add CloudWatch alarm on session age. Reduce timeout to 300s. Add dead letter queue monitoring. |

**Code:**
```python
if completed_count < total_strategies:
    return {
        "statusCode": 200,
        "body": {
            "status": "waiting",  # Stays here indefinitely if worker fails
            ...
        },
    }
```

---

## Low Severity (Acceptable with Monitoring)

### SF-015: Debug Log for Missing Quote Data

| Attribute | Value |
|-----------|-------|
| **Location** | `the_alchemiser/strategy_v2/adapters/market_data_adapter.py:275-283` |
| **Error Type Caught** | No quote data available |
| **Fallback Behavior** | Warning logged, returns `None` |
| **Impact** | **LOW** - Expected for some symbols (e.g., market hours). None is appropriate return. |
| **Recommendation** | **ACCEPT** - Current behavior is appropriate. Monitor warning frequency. |

---

### SF-016: Indicator Service Optional Market Data

| Attribute | Value |
|-----------|-------|
| **Location** | `the_alchemiser/strategy_v2/indicators/indicator_service.py:52-57` |
| **Error Type Caught** | None (design decision) |
| **Fallback Behavior** | `None` allowed for market_data_service in testing |
| **Impact** | **LOW** - Testing flexibility. Production code must provide service. |
| **Recommendation** | **ACCEPT** - Document clearly. Add runtime check if not testing. |

---

## Summary Statistics

| Severity | Count | Recommendation Breakdown |
|----------|-------|-------------------------|
| Critical | 5 | BLOCK: 3, WARN: 2 |
| High | 4 | BLOCK: 1, LOG: 2, MONITOR: 1 |
| Medium | 5 | LOG: 2, WARN: 2, MONITOR: 1 |
| Low | 2 | ACCEPT: 2 |
| **Total** | **16** | |

## Action Items from Audit

1. **Immediate (BLOCK):**
   - SF-001: Add fallback indicator flag
   - SF-002: Remove blanket exception handler in feature pipeline
   - SF-005: Remove $100 price fallback
   - SF-008: Return None for zero volatility
   - SF-014: Add aggregation timeout detection

2. **Short-term (WARN/LOG):**
   - SF-003: Change RSI fallback to None
   - SF-004: Log one-sided quotes
   - SF-006: Track missing bar data
   - SF-010: Log selection limit failures
   - SF-011: Track excluded symbol counts

3. **Monitoring (MONITOR):**
   - SF-007: Ensure None price handling
   - SF-009: Track correlation failures
   - SF-012: Track volatility exclusions
