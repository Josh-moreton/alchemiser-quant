# Phase 4: Testing Gap Report

**Status:** Complete  
**Date:** 2025-12-15  

## Overview

This document identifies where error scenarios lack test coverage in the Strategy module. Each gap includes the error scenario, current coverage status, priority, and recommended test approach.

---

## Current Test Coverage Summary

### Well-Covered Areas ✅

| Component | Test File | Coverage Level | Notes |
|-----------|-----------|----------------|-------|
| Error hierarchy | `tests/strategy_v2/test_errors.py` | ✅ Comprehensive | Exception classes, serialization, context propagation |
| Feature pipeline math | `tests/strategy_v2/adapters/test_feature_pipeline.py` | ✅ Comprehensive | Includes Hypothesis property tests |
| Market data adapter | `tests/strategy_v2/adapters/test_market_data_adapter.py` | ✅ Good | Input validation, None returns, Decimal correctness |
| Error types | `tests/shared/errors/test_error_*.py` | ✅ Comprehensive | Error handler, types, utils, details |

### Test Gaps ❌

| ID | Error Scenario | Current Coverage | Priority | Recommended Approach |
|----|----------------|------------------|----------|---------------------|
| TG-001 | Technical indicator fallback to 0.0 | ❌ None | **Critical** | Unit + Integration |
| TG-002 | Feature pipeline exception swallowing | ⚠️ Partial | **Critical** | Unit (specific exceptions) |
| TG-003 | RSI neutral fallback (50.0) | ⚠️ Partial | **High** | Unit + Property-based |
| TG-004 | Quote one-sided fallback | ❌ None | **High** | Unit + Integration |
| TG-005 | DSL symbol exclusion cascade | ❌ None | **High** | Integration |
| TG-006 | Aggregation timeout detection | ❌ None | **Critical** | Integration |
| TG-007 | Multi-node partial worker failure | ❌ None | **Critical** | Integration |
| TG-008 | Volatility zero fallback propagation | ⚠️ Partial | **High** | Integration |
| TG-009 | End-to-end fallback value flow | ❌ None | **Critical** | E2E |
| TG-010 | Indicator service price fallback $100 | ❌ None | **High** | Unit |

---

## Detailed Gap Analysis

### TG-001: Technical Indicator Fallback to 0.0

**Location:** `signal_generation_handler.py:493-506`

**Current State:** No tests verify the 0.0 fallback behavior or its downstream effects.

**Scenario Not Tested:**
```python
# When indicator fetch fails, all indicators become 0.0
indicators[symbol] = {
    "rsi_10": 0.0,  # <- Triggers oversold signals
    "rsi_20": 0.0,
    "current_price": 0.0,  # <- Division by zero risk
    "ma_200": 0.0,
}
```

**Required Tests:**
1. Unit test: Verify fallback values when indicator service throws
2. Integration test: Verify email contains fallback indicator flag
3. E2E test: Verify trade decisions handle fallback appropriately

**Recommended Test:**
```python
@pytest.mark.unit
def test_indicator_fetch_failure_uses_zero_fallback():
    """Test that indicator fetch failures produce 0.0 fallbacks."""
    handler = SignalGenerationHandler(...)
    
    with patch.object(indicator_service, 'get_indicator', side_effect=RuntimeError):
        indicators = handler._fetch_technical_indicators(["AAPL"], "corr-123")
        
        assert indicators["AAPL"]["rsi_10"] == 0.0
        assert indicators["AAPL"]["current_price"] == 0.0
        # TODO: Add assertion for fallback_used flag when implemented
```

---

### TG-002: Feature Pipeline Exception Swallowing

**Location:** `feature_pipeline.py:300-310`

**Current State:** Tests cover math functions but not the blanket exception handler.

**Scenario Not Tested:**
```python
except Exception as e:
    logger.warning(f"Error extracting price features: {e}")
    # ALL exceptions swallowed, neutral defaults returned
    features = {
        "current_price": 0.0,
        "volatility": 0.0,
        "ma_ratio": 1.0,
        "price_position": 0.5,
        "volume_ratio": 1.0,
    }
```

**Required Tests:**
1. Unit test: Verify specific exception types produce defaults
2. Unit test: Verify unexpected exceptions are also caught (and logged)
3. Integration test: Verify neutral defaults propagate to strategy evaluation

**Recommended Test:**
```python
@pytest.mark.unit
def test_extract_features_catches_all_exceptions():
    """Test that extract_price_features catches all exceptions."""
    pipeline = FeaturePipeline()
    
    # Create bars that will cause computation error
    bars_with_bad_data = [MarketBar(..., close_price=Decimal("NaN"))]
    
    features = pipeline.extract_price_features(bars_with_bad_data)
    
    # Should return defaults, not raise
    assert features["volatility"] == 0.0
    assert features["ma_ratio"] == 1.0
```

---

### TG-003: RSI Neutral Fallback (50.0)

**Location:** `indicator_service.py:103`

**Current State:** Basic RSI tests exist but don't verify fallback behavior distinction.

**Scenario Not Tested:**
- RSI returns 50.0 on insufficient data
- RSI returns 50.0 on NaN in series
- Downstream cannot distinguish synthetic 50.0 from real 50.0

**Required Tests:**
1. Property-based test: RSI always in [0, 100] or explicit None
2. Unit test: Insufficient data returns fallback (should be None, not 50.0)
3. Unit test: NaN in series returns fallback

**Recommended Test:**
```python
@pytest.mark.unit
def test_rsi_insufficient_data_returns_fallback():
    """Test RSI with insufficient data returns neutral fallback."""
    service = IndicatorService(mock_market_data)
    
    # Only 3 bars when RSI-14 needs at least 14
    request = IndicatorRequest(indicator_type="rsi", window=14, ...)
    result = service.get_indicator(request)
    
    # Currently returns 50.0, should return None
    assert result.rsi_14 == 50.0  # Document current behavior
    # TODO: Change to assert result.rsi_14 is None after fix
```

---

### TG-004: Quote One-Sided Fallback

**Location:** `market_data_service.py:262-270`

**Current State:** No tests for bid-only or ask-only quote handling.

**Scenario Not Tested:**
```python
if bid_valid:
    # Bid-only fallback: use bid for both sides
    return self._create_quote_model(
        symbol, bid_price_raw, bid_price_raw, bid_size, 0, timestamp
    )
```

**Required Tests:**
1. Unit test: Bid-only quote creates zero-spread quote
2. Unit test: Ask-only quote creates zero-spread quote
3. Integration test: Zero-spread quote affects mid-price calculation

**Recommended Test:**
```python
@pytest.mark.unit
def test_bid_only_quote_creates_zero_spread():
    """Test that bid-only quote uses bid for both sides."""
    service = MarketDataService(...)
    
    mock_raw_quote = Mock(bid_price=100.0, ask_price=0.0, ...)
    quote = service._build_quote_model("AAPL", mock_raw_quote)
    
    assert quote.bid_price == Decimal("100.0")
    assert quote.ask_price == Decimal("100.0")  # Same as bid
    assert (quote.ask_price - quote.bid_price) == 0  # Zero spread
```

---

### TG-005: DSL Symbol Exclusion Cascade

**Location:** `dsl_evaluator.py:100-180`

**Current State:** No tests for partial symbol evaluation failures.

**Scenario Not Tested:**
- One symbol fails during scoring
- Symbol is silently excluded from portfolio
- Final portfolio has fewer symbols than expected

**Required Tests:**
1. Integration test: Symbol failure excludes from portfolio
2. Integration test: Exclusion logged with count
3. E2E test: Portfolio composition changes due to exclusions

**Recommended Test:**
```python
@pytest.mark.integration
def test_symbol_evaluation_failure_excludes_symbol():
    """Test that symbol eval failure silently excludes from portfolio."""
    evaluator = DslEvaluator(...)
    
    # Create AST with 5 symbols, one will fail
    ast = create_select_top_ast(symbols=["AAPL", "BAD_SYMBOL", "GOOGL", ...])
    
    with patch(..., side_effect=ValueError("for BAD_SYMBOL")):
        allocation, trace = evaluator.evaluate(ast, "corr-123")
        
        # BAD_SYMBOL should be excluded
        assert "BAD_SYMBOL" not in allocation.target_weights
        assert len(allocation.target_weights) == 4  # Not 5
```

---

### TG-006: Aggregation Timeout Detection

**Location:** `aggregator_v2/lambda_handler.py:115-124`

**Current State:** No tests for timeout scenario.

**Scenario Not Tested:**
- Strategy worker dies mid-execution
- Aggregator waits indefinitely in "waiting" state
- No WorkflowFailed event published
- No operator notification

**Required Tests:**
1. Integration test: Timeout after session_timeout exceeded
2. Integration test: WorkflowFailed published on timeout
3. E2E test: Operator receives timeout notification

**Recommended Test:**
```python
@pytest.mark.integration
def test_aggregation_timeout_publishes_workflow_failed():
    """Test that aggregation timeout publishes WorkflowFailed."""
    session_service = Mock()
    session_service.get_session.return_value = {
        "status": "PENDING",
        "created_at": datetime.now(UTC) - timedelta(minutes=15),  # Old session
        "total_strategies": 3,
        "completed_strategies": 1,  # Only 1 of 3 completed
    }
    
    # Timeout checker should detect and publish WorkflowFailed
    # TODO: Implement timeout checker functionality first
```

---

### TG-007: Multi-Node Partial Worker Failure

**Location:** Orchestrator → Workers → Aggregator flow

**Current State:** No integration tests for partial worker failures.

**Scenario Not Tested:**
- 3 strategy workers launched
- 1 worker times out / crashes
- 2 workers complete successfully
- System behavior unclear

**Required Tests:**
1. Integration test: Partial completion handling
2. Integration test: Aggregator behavior with missing partials
3. E2E test: Final signal quality with partial data

---

### TG-008: Volatility Zero Fallback Propagation

**Location:** `feature_pipeline.py` → Portfolio weighting

**Current State:** Volatility math tested, but propagation to portfolio not tested.

**Scenario Not Tested:**
- Asset has zero volatility (data issue)
- Inverse volatility weighting assigns infinite weight
- Portfolio becomes over-concentrated

**Required Tests:**
1. Integration test: Zero volatility handled in weighting
2. Property-based test: Portfolio weights always sum to ~1.0
3. E2E test: No infinite weights in final portfolio

---

### TG-009: End-to-End Fallback Value Flow

**Location:** Full pipeline

**Current State:** No E2E tests for fallback value propagation.

**Scenario Not Tested:**
- Market data fetch fails for symbol
- Indicator computed with fallback
- Strategy evaluates with fallback data
- Signal generated with potentially wrong allocation
- Trade executed based on bad data

**Required Tests:**
1. E2E test: Full workflow with injected data failures
2. E2E test: Verify final trade decisions match expectations with fallbacks
3. E2E test: Verify operator visibility into fallback usage

---

### TG-010: Indicator Service Price Fallback $100

**Location:** `indicator_service.py:123`

**Current State:** No tests for the $100.0 price fallback.

**Scenario Not Tested:**
```python
current_price=(Decimal(str(prices.iloc[-1])) if len(prices) > 0 else Decimal("100.0")),
```

**Required Tests:**
1. Unit test: Empty price series returns $100.0
2. Unit test: Verify downstream impact of synthetic $100 price
3. Integration test: Position sizing with synthetic price

---

## Test Coverage Priorities

### Immediate (Blocking Issues)

| Priority | Test Gap | Effort | Impact |
|----------|----------|--------|--------|
| P0 | TG-001: Indicator 0.0 fallback | 1 day | Prevents wrong trade signals |
| P0 | TG-006: Aggregation timeout | 2 days | Prevents silent workflow hangs |
| P0 | TG-009: E2E fallback flow | 2 days | Validates complete error handling |

### Short-Term (High Value)

| Priority | Test Gap | Effort | Impact |
|----------|----------|--------|--------|
| P1 | TG-002: Feature pipeline exceptions | 0.5 days | Documents behavior |
| P1 | TG-003: RSI 50.0 fallback | 0.5 days | Prevents signal confusion |
| P1 | TG-007: Partial worker failure | 1 day | Multi-node reliability |

### Medium-Term (Technical Debt)

| Priority | Test Gap | Effort | Impact |
|----------|----------|--------|--------|
| P2 | TG-004: One-sided quotes | 0.5 days | Edge case coverage |
| P2 | TG-005: Symbol exclusion | 1 day | Portfolio integrity |
| P2 | TG-008: Zero volatility | 0.5 days | Weighting correctness |
| P2 | TG-010: $100 price fallback | 0.5 days | Position sizing |

---

## Recommended Test File Structure

```
tests/
├── strategy_v2/
│   ├── handlers/
│   │   └── test_signal_generation_handler.py  # NEW: TG-001
│   ├── adapters/
│   │   ├── test_feature_pipeline.py           # EXTEND: TG-002
│   │   └── test_market_data_adapter.py        # EXTEND: TG-004
│   ├── indicators/
│   │   └── test_indicator_service.py          # NEW: TG-003, TG-010
│   └── engines/
│       └── test_dsl_evaluator.py              # EXTEND: TG-005
├── aggregator_v2/
│   └── test_timeout_detection.py              # NEW: TG-006
├── integration/
│   ├── test_multi_node_failures.py            # NEW: TG-007
│   └── test_fallback_propagation.py           # NEW: TG-008
└── e2e/
    └── test_error_handling_workflow.py        # NEW: TG-009
```

---

## Summary Statistics

| Category | Count |
|----------|-------|
| **Critical Gaps** | 4 (TG-001, TG-006, TG-007, TG-009) |
| **High Priority Gaps** | 4 (TG-002, TG-003, TG-005, TG-008) |
| **Medium Priority Gaps** | 2 (TG-004, TG-010) |
| **Total Estimated Effort** | ~10 days |

## Action Items

1. **Create test tracking issue** for each gap
2. **Prioritize P0 tests** before next production deployment
3. **Add Hypothesis tests** for property-based validation of indicator bounds
4. **Create integration test fixtures** for multi-node failure simulation
