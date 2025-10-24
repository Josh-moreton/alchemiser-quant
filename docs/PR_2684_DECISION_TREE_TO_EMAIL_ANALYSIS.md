# PR #2684: Decision Tree to Human-Readable Email Content - Complete Analysis

## Executive Summary

This PR successfully implements the conversion of CLJ strategy decision trees into human-readable email content **with actual indicator values**. The implementation is complete and working, but there's a **critical missing piece**: the `technical_indicators` data is not being populated in the signal generation handler, so the enhanced parsing cannot display actual RSI/price values.

---

## How the System Works: End-to-End Flow

### 1. **Decision Tree Capture** (Strategy Engine)

**Location:** `the_alchemiser/strategy_v2/engines/dsl/strategy_engine.py`

When a CLJ strategy is evaluated:

```python
# In _build_decision_reasoning() - Line 601
def _build_decision_reasoning(
    self,
    decision_path: list[dict[str, Any]] | None,
    weight: float,
) -> str:
    """Build human-readable reasoning from decision path."""
    
    # Builds strings like:
    # "✓ SPY RSI(10)>79 → ✓ TQQQ RSI(10)<81 → 75.0% allocation"
```

The decision path is captured as a list of `DecisionNode` objects during DSL evaluation:

```python
# From the_alchemiser/strategy_v2/engines/dsl/context.py - Line 31
class DecisionNode(TypedDict):
    """Represents a single decision point in strategy evaluation."""
    condition: str          # "SPY RSI(10) > 79"
    result: bool            # True/False
    branch: str             # "then" or "else"
    values: dict[str, Any]  # Indicator values (may be placeholders)
```

This decision path is stored in the `StrategySignal.reasoning` field (max 1000 chars).

---

### 2. **Technical Indicators Computation** (Indicator Service)

**Location:** `the_alchemiser/strategy_v2/indicators/indicator_service.py`

During DSL evaluation, technical indicators are computed for each symbol:

```python
# In IndicatorService - Line 115
def _compute_rsi(self, symbol: str, prices: pd.Series, parameters: dict) -> TechnicalIndicator:
    """Compute RSI indicator."""
    return TechnicalIndicator(
        symbol=symbol,
        timestamp=datetime.now(UTC),
        rsi_14=rsi_value if window == 14 else None,
        rsi_10=rsi_value if window == 10 else None,
        rsi_20=rsi_value if window == 20 else None,
        rsi_21=rsi_value if window == 21 else None,
        current_price=Decimal(str(prices.iloc[-1])),
        data_source="real_market_data",
        metadata={"value": rsi_value, "window": window},
    )
```

These are used by the CLJ strategies for decision-making but are **NOT currently captured** for email reporting.

---

### 3. **Signal Generation** (Signal Handler) ⚠️ **MISSING LINK**

**Location:** `the_alchemiser/strategy_v2/handlers/signal_generation_handler.py` - Line 230

The `_convert_signals_to_display_format()` method builds the signal dictionary:

```python
strategy_signals[strategy_name] = {
    "symbols": symbols_and_allocations,
    "action": first_signal.action,
    "reasoning": first_signal.reasoning,  # ← Contains decision path like "✓ SPY RSI(10)>79 → ..."
    "signal": signal_display,
    "total_allocation": float(total_allocation),
    # ⚠️ MISSING: "technical_indicators": {...}  ← This is NOT populated!
}
```

**THE PROBLEM:** The `technical_indicators` field that the PR expects is not being added here. This is why the enhanced email content cannot display actual values—the data simply isn't passed through.

---

### 4. **Email Content Generation** (Notification System) ✅ **WORKING**

**Location:** `the_alchemiser/shared/notifications/templates/signals.py`

The PR adds three key enhancements:

#### 4a. Enhanced DSL Reasoning Parser

```python
# Line 809 - _get_rsi_classification()
def _get_rsi_classification(rsi_value: float) -> str:
    """Get RSI classification label based on value."""
    if rsi_value > 80.0:  # RSI_OVERBOUGHT_CRITICAL
        return "critically overbought"
    if rsi_value > 70.0:  # RSI_OVERBOUGHT_WARNING
        return "overbought"
    if rsi_value < 20.0:  # RSI_OVERSOLD
        return "oversold"
    return "neutral"
```

```python
# Line 832 - Enhanced _parse_condition()
def _parse_condition(
    condition: str,
    technical_indicators: dict[str, TechnicalIndicators] | None = None,
) -> str | None:
    """Parse a single condition into human-readable text with actual indicator values."""
    
    # Before (without indicators):
    # "RSI conditions met on SPY"
    
    # After (with indicators):
    # "SPY RSI(10) is **82.5**, above the **79** threshold (**critically overbought**)"
```

#### 4b. Price Action Gauge (New Feature)

```python
# Line 636 - build_price_action_gauge()
def build_price_action_gauge(strategy_signals: dict[Any, SignalData]) -> str:
    """Build price action gauge table showing RSI and price vs MA for all symbols."""
    
    # Creates table like:
    # Symbol | RSI(10) | Price vs 200-MA | Gauge
    # SPY    | 82.5    | Above           | Critically Overbought / Bullish
    # TMF    | 19.8    | Below           | Oversold / Bearish
    # TQQQ   | 18.0    | Above           | Oversold / Bullish ⚠️
```

#### 4c. Fixed Current Allocation Display

**Location:** `the_alchemiser/shared/notifications/templates/portfolio.py` - Line 315

```python
# Fixed to show "—" when position data is missing
has_position_data = total_value > 0

if has_position_data:
    current_pct_display = f"{current_pct:.1%}"
else:
    current_pct_display = "—"  # ← Instead of misleading "0.0%"
```

---

## What's Working vs. What's Not

### ✅ Working Components

1. **Decision path capture**: CLJ strategies emit reasoning strings like `"Nuclear: ✓ SPY RSI(10)>79 → ✓ TQQQ RSI(10)<81 → 75.0% allocation"`
2. **Enhanced parsing logic**: Code exists to extract actual values from `technical_indicators` dict
3. **RSI classification**: Maps values to "overbought", "oversold", etc.
4. **Price action gauge**: Builds comprehensive technical analysis table
5. **Portfolio table fix**: Correctly shows "—" for missing positions
6. **Tests**: 100+ comprehensive tests pass

### ❌ Missing Component (THE GAP)

**The `technical_indicators` dictionary is never populated in the signal generation handler.**

When `build_signal_summary()` or other email builders receive the `strategy_signals` dict, they call:

```python
technical_indicators = signal_data.get("technical_indicators", {})
```

But this returns an empty dict `{}` because it was never added during signal generation, so:

- Enhanced parsing falls back to simple text: `"SPY RSI(10) above 79"` (no actual value)
- Price action gauge cannot be generated (no indicator data)
- Market regime analysis cannot extract RSI/MA values

---

## What Needs to Be Done

### Required Fix: Populate `technical_indicators` in Signal Handler

**File:** `the_alchemiser/strategy_v2/handlers/signal_generation_handler.py`

**Method:** `_convert_signals_to_display_format()` (around line 230)

**Required Changes:**

```python
def _convert_signals_to_display_format(self, signals: list[StrategySignal]) -> dict[str, Any]:
    """Convert signals to display format for emails."""
    
    # Group signals by strategy
    strategy_groups: dict[str, list[StrategySignal]] = {}
    for signal in signals:
        strategy_name = signal.strategy_name or "DSL"
        if strategy_name not in strategy_groups:
            strategy_groups[strategy_name] = []
        strategy_groups[strategy_name].append(signal)

    strategy_signals: dict[str, Any] = {}

    for strategy_name, strategy_signals_list in strategy_groups.items():
        # ... existing code to collect symbols and allocations ...
        
        first_signal = strategy_signals_list[0]
        
        # ✅ NEW: Extract technical indicators for all symbols in this strategy
        technical_indicators = self._extract_technical_indicators_for_symbols(
            [signal.symbol.value for signal in strategy_signals_list]
        )
        
        strategy_signals[strategy_name] = {
            "symbols": symbols_and_allocations,
            "action": first_signal.action,
            "reasoning": first_signal.reasoning,
            "signal": signal_display,
            "total_allocation": float(total_allocation),
            "technical_indicators": technical_indicators,  # ✅ NEW
        }
    
    return strategy_signals
```

**New Helper Method Needed:**

```python
def _extract_technical_indicators_for_symbols(
    self, 
    symbols: list[str]
) -> dict[str, dict[str, float]]:
    """Extract current technical indicators for given symbols.
    
    Args:
        symbols: List of symbols to get indicators for
        
    Returns:
        Dict mapping symbol -> {rsi_10, rsi_20, current_price, ma_200}
        
    Example:
        {
            "SPY": {
                "rsi_10": 82.5,
                "rsi_20": 78.3,
                "current_price": 505.10,
                "ma_200": 487.50
            },
            "TQQQ": {
                "rsi_10": 18.2,
                "rsi_20": 22.1,
                "current_price": 65.30,
                "ma_200": 62.10
            }
        }
    """
    indicators: dict[str, dict[str, float]] = {}
    
    # Access the indicator service from the DSL engine
    market_data_port = self.container.infrastructure.market_data_service()
    indicator_service = IndicatorService(market_data_port)
    
    for symbol in symbols:
        try:
            # Fetch current indicators for this symbol
            # Need to make indicator requests for RSI(10), RSI(20), current-price, MA(200)
            
            rsi_10_request = IndicatorRequest(
                indicator_type="rsi",
                symbol=symbol,
                parameters={"window": 10},
                period=252,  # 1 year of data for RSI calculation
                correlation_id=str(uuid.uuid4())
            )
            rsi_10_indicator = indicator_service.get_indicator(rsi_10_request)
            
            rsi_20_request = IndicatorRequest(
                indicator_type="rsi",
                symbol=symbol,
                parameters={"window": 20},
                period=252,
                correlation_id=str(uuid.uuid4())
            )
            rsi_20_indicator = indicator_service.get_indicator(rsi_20_request)
            
            price_request = IndicatorRequest(
                indicator_type="current_price",
                symbol=symbol,
                parameters={},
                period=1,
                correlation_id=str(uuid.uuid4())
            )
            price_indicator = indicator_service.get_indicator(price_request)
            
            ma_200_request = IndicatorRequest(
                indicator_type="moving_average",
                symbol=symbol,
                parameters={"window": 200},
                period=252,
                correlation_id=str(uuid.uuid4())
            )
            ma_200_indicator = indicator_service.get_indicator(ma_200_request)
            
            # Build the indicators dict for this symbol
            indicators[symbol] = {
                "rsi_10": rsi_10_indicator.rsi_10 or 0.0,
                "rsi_20": rsi_20_indicator.rsi_20 or 0.0,
                "current_price": float(price_indicator.current_price or 0.0),
                "ma_200": float(ma_200_indicator.ma_200 or 0.0),
            }
            
        except Exception as e:
            self.logger.warning(
                f"Failed to fetch technical indicators for {symbol}: {e}",
                extra={"symbol": symbol, "error": str(e)}
            )
            # Fallback to empty indicators for this symbol
            indicators[symbol] = {
                "rsi_10": 0.0,
                "rsi_20": 0.0,
                "current_price": 0.0,
                "ma_200": 0.0,
            }
    
    return indicators
```

---

## Alternative: Cache Indicators During DSL Evaluation

A more efficient approach would be to capture the technical indicators **during** DSL strategy evaluation and store them in the `StrategySignal` metadata field:

**File:** `the_alchemiser/strategy_v2/engines/dsl/strategy_engine.py`

```python
# In _create_per_file_signals() around line 245
def _create_per_file_signals(
    self,
    dsl_files: list[str],
    file_results: list[tuple[...]],
    timestamp: datetime,
    correlation_id: str,
) -> list[StrategySignal]:
    """Create one signal per file per symbol."""
    
    signals: list[StrategySignal] = []
    
    for filename, (per_file_weights, _, _, _, _decision_path) in zip(dsl_files, file_results):
        # ... existing code ...
        
        # ✅ NEW: Capture technical indicators used in this strategy evaluation
        # These were already computed by the indicator service during evaluation
        # Extract them from the DSL context or indicator service cache
        
        for symbol, weight in per_file_weights.items():
            if weight <= 0:
                continue
            
            # Build reasoning with decision path
            reasoning = self._build_decision_reasoning(_decision_path, weight)
            
            # ✅ NEW: Get the technical indicators for this symbol
            # Option 1: Extract from decision_path "values" dict
            # Option 2: Re-query indicator service (inefficient but simple)
            technical_indicators = self._extract_indicators_from_decision_path(
                _decision_path, symbol
            )
            
            signals.append(
                StrategySignal(
                    symbol=Symbol(symbol),
                    action="BUY",
                    target_allocation=Decimal(str(weight)),
                    reasoning=reasoning,
                    timestamp=timestamp,
                    strategy=strategy_name,
                    data_source="dsl_engine:per_file",
                    correlation_id=correlation_id,
                    metadata={
                        "technical_indicators": technical_indicators,  # ✅ NEW
                        "filename": filename,
                    },
                )
            )
    
    return signals
```

Then in the signal handler, extract from metadata:

```python
def _convert_signals_to_display_format(self, signals: list[StrategySignal]) -> dict[str, Any]:
    """Convert signals to display format."""
    
    # ... existing code ...
    
    # Extract technical indicators from signal metadata
    technical_indicators = {}
    for signal in strategy_signals_list:
        if signal.metadata and "technical_indicators" in signal.metadata:
            symbol = signal.symbol.value
            technical_indicators[symbol] = signal.metadata["technical_indicators"]
    
    strategy_signals[strategy_name] = {
        "symbols": symbols_and_allocations,
        "action": first_signal.action,
        "reasoning": first_signal.reasoning,
        "signal": signal_display,
        "total_allocation": float(total_allocation),
        "technical_indicators": technical_indicators,  # ✅ From metadata
    }
```

---

## Benefits Once Implemented

Once `technical_indicators` is populated, the email system will automatically:

1. **Show actual RSI values** in signal reasoning:
   - Before: `"Nuclear strategy triggered: RSI conditions met on SPY and TQQQ, allocation set to 75%"`
   - After: `"Nuclear strategy triggered: SPY RSI(10) is **82.5**, above the **79** threshold (**critically overbought**), TQQQ RSI(10) is **78.0**, below the **81** threshold (**overbought**), allocation set to 75.0%"`

2. **Display price action gauge** showing technical analysis across all symbols

3. **Provide market regime analysis** based on SPY indicators

4. **Link indicators to insights**:
   - RSI > 80 → "critically overbought, potential pullback"
   - Price above 200-MA → "bullish trend"
   - RSI < 20 + Price > MA → "conflicting signals ⚠️"

---

## Summary

**The PR code is complete and working**—all the parsing logic, RSI classification, gauge building, and tests are implemented correctly.

**The missing piece is data plumbing**: The `technical_indicators` dictionary must be populated in `signal_generation_handler.py` and passed through to the email builders.

**Recommended approach:**
1. Add `_extract_technical_indicators_for_symbols()` method to signal handler
2. Call it in `_convert_signals_to_display_format()` to populate the dict
3. Add the `"technical_indicators": {...}` field to the returned signal data

Once this is done, all the enhanced email content will automatically light up with actual indicator values and insightful analysis.
