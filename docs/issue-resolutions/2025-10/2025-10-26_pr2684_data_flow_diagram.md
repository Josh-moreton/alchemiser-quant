# PR #2684: Data Flow Diagram - Decision Trees to Email Content

## Current System (With Missing Link)

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. CLJ STRATEGY FILES (e.g., Nuclear.clj)                           │
│    DSL expressions with decision logic                              │
│    Example: (if (> (rsi "SPY" 10) 79) ...)                          │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. DSL STRATEGY ENGINE                                              │
│    File: strategy_v2/engines/dsl/strategy_engine.py                 │
│                                                                      │
│    • Evaluates CLJ conditions                                       │
│    • Builds decision_path: list[DecisionNode]                       │
│      [                                                               │
│        {                                                             │
│          condition: "SPY RSI(10) > 79",                             │
│          result: True,                                               │
│          branch: "then",                                             │
│          values: {"rsi_10": 82.5, ...}                              │
│        },                                                            │
│        {...}                                                         │
│      ]                                                               │
│    • Calls _build_decision_reasoning()                              │
│    • Creates StrategySignal with:                                   │
│      - reasoning: "✓ SPY RSI(10)>79 → ✓ TQQQ RSI(10)<81 → 75% allo" │
│      - metadata: {...}  (could contain indicators, but doesn't)     │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. INDICATOR SERVICE (Used during DSL evaluation)                   │
│    File: strategy_v2/indicators/indicator_service.py                │
│                                                                      │
│    ✅ Computes: TechnicalIndicator objects                          │
│       - rsi_10: 82.5                                                │
│       - rsi_20: 78.3                                                │
│       - current_price: 505.10                                       │
│       - ma_200: 487.50                                              │
│                                                                      │
│    ⚠️  BUT: These are used internally and NOT captured for email!    │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. SIGNAL GENERATION HANDLER                                        │
│    File: strategy_v2/handlers/signal_generation_handler.py          │
│                                                                      │
│    Method: _convert_signals_to_display_format()                     │
│                                                                      │
│    ✅ Creates:                                                       │
│       strategy_signals[strategy_name] = {                           │
│         "symbols": ["SPY", "TQQQ"],                                 │
│         "action": "BUY",                                             │
│         "reasoning": "✓ SPY RSI(10)>79 → ...",                      │
│         "signal": "BUY SPY, TQQQ",                                  │
│         "total_allocation": 0.75,                                   │
│       }                                                              │
│                                                                      │
│    ❌ MISSING:                                                       │
│         "technical_indicators": {                                   │
│           "SPY": {                                                  │
│             "rsi_10": 82.5,                                          │
│             "rsi_20": 78.3,                                          │
│             "current_price": 505.10,                                 │
│             "ma_200": 487.50                                         │
│           },                                                         │
│           "TQQQ": {...}                                             │
│         }                                                            │
│                                                                      │
│    ⚠️  THIS IS THE GAP! Indicators not added to signal data.         │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 5. EMAIL NOTIFICATION SYSTEM                                        │
│    File: shared/notifications/templates/signals.py                  │
│                                                                      │
│    Method: build_signal_summary()                                   │
│                                                                      │
│    ✅ PR #2684 ENHANCEMENTS (Code exists and works):                │
│       • _parse_dsl_reasoning_to_human_readable()                    │
│       • _parse_condition() - with technical_indicators param        │
│       • _get_rsi_classification()                                   │
│       • build_price_action_gauge()                                  │
│                                                                      │
│    BUT:                                                              │
│       technical_indicators = signal_data.get("technical_indicators") │
│       # Returns {} because it was never added! ❌                    │
│                                                                      │
│    RESULT:                                                           │
│       • Falls back to simple parsing:                               │
│         "RSI conditions met on SPY"                                 │
│       • Cannot show actual values:                                  │
│         "SPY RSI(10) is **82.5**, above **79** (**overbought**)"   │
│       • Price action gauge cannot be generated                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Desired System (With Fix)

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. CLJ STRATEGY FILES                                               │
│    (No changes needed)                                              │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 2. DSL STRATEGY ENGINE                                              │
│    (No changes needed - or optionally cache indicators in metadata) │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 3. INDICATOR SERVICE                                                │
│    ✅ Computes indicators (same as before)                          │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 4. SIGNAL GENERATION HANDLER ⬅️ FIX NEEDED HERE                     │
│    File: strategy_v2/handlers/signal_generation_handler.py          │
│                                                                      │
│    ✅ NEW METHOD:                                                    │
│       def _extract_technical_indicators_for_symbols(                │
│           self, symbols: list[str]                                  │
│       ) -> dict[str, dict[str, float]]:                             │
│           """Fetch current technical indicators for symbols."""     │
│           indicators = {}                                            │
│           indicator_service = IndicatorService(market_data_port)    │
│                                                                      │
│           for symbol in symbols:                                    │
│               # Request RSI(10), RSI(20), current_price, MA(200)    │
│               indicators[symbol] = {                                │
│                   "rsi_10": ...,                                    │
│                   "rsi_20": ...,                                    │
│                   "current_price": ...,                             │
│                   "ma_200": ...                                     │
│               }                                                      │
│           return indicators                                          │
│                                                                      │
│    ✅ UPDATED METHOD:                                                │
│       def _convert_signals_to_display_format(...):                  │
│           # Extract symbols from strategy                            │
│           symbols = [signal.symbol.value for signal in signals]     │
│                                                                      │
│           # ✅ NEW: Fetch technical indicators                       │
│           technical_indicators =                                    │
│               self._extract_technical_indicators_for_symbols(symbols)│
│                                                                      │
│           strategy_signals[strategy_name] = {                       │
│               "symbols": symbols_and_allocations,                   │
│               "action": first_signal.action,                        │
│               "reasoning": first_signal.reasoning,                  │
│               "signal": signal_display,                             │
│               "total_allocation": float(total_allocation),          │
│               "technical_indicators": technical_indicators, # ✅ NEW │
│           }                                                          │
└───────────────────────┬─────────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────┐
│ 5. EMAIL NOTIFICATION SYSTEM                                        │
│    File: shared/notifications/templates/signals.py                  │
│                                                                      │
│    ✅ NOW WORKS AS INTENDED:                                         │
│       technical_indicators = signal_data.get("technical_indicators") │
│       # Returns populated dict! ✅                                   │
│       # {                                                            │
│       #   "SPY": {"rsi_10": 82.5, "current_price": 505.10, ...},    │
│       #   "TQQQ": {...}                                             │
│       # }                                                            │
│                                                                      │
│    ✅ Enhanced parsing now works:                                    │
│       _parse_condition(                                             │
│           "SPY RSI(10)>79",                                         │
│           technical_indicators  # ✅ Has data now!                   │
│       )                                                              │
│       # Returns:                                                     │
│       # "SPY RSI(10) is **82.5**, above the **79** threshold        │
│       #  (**critically overbought**)"                               │
│                                                                      │
│    ✅ Price action gauge now generates:                              │
│       build_price_action_gauge(strategy_signals)                    │
│       # Returns HTML table showing:                                 │
│       # Symbol | RSI(10) | Price vs 200-MA | Gauge                  │
│       # SPY    | 82.5    | Above           | Critically Overbought  │
│                                                                      │
│    ✅ Market regime analysis works:                                  │
│       build_market_regime_analysis(strategy_signals)                │
│       # Extracts SPY indicators and analyzes market conditions       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Key Insight: Where the Break Occurs

```
┌──────────────────────┐
│ IndicatorService     │ ← Indicators ARE computed here
│ • Computes RSI       │
│ • Computes MA        │
│ • Returns            │
│   TechnicalIndicator │
└──────────┬───────────┘
           │
           ├─────────────────────────────────┐
           │                                 │
           ▼                                 ▼
    ┌─────────────┐                  ┌──────────────┐
    │ DSL Engine  │                  │ Email System │
    │ Uses them   │                  │ Needs them   │
    │ for logic   │                  │ for display  │
    └─────────────┘                  └──────────────┘
                                              ▲
                                              │
                                              │ ❌ Gap here!
                                              │
                                     ┌────────┴────────┐
                                     │ Signal Handler  │
                                     │ Doesn't pass    │
                                     │ them through    │
                                     └─────────────────┘
```

The indicators **exist** in the system—they're computed by `IndicatorService` and used by the `DSL Engine` to make trading decisions. But when the `Signal Handler` converts signals to the display format for emails, it doesn't include the indicator data.

The email system is **ready** to use this data (PR #2684 added all the parsing logic), but the data never arrives.

---

## Two Implementation Options

### Option 1: Fetch Indicators in Signal Handler (Simpler)

**Pros:**
- Cleaner separation of concerns
- Signal handler owns email data formatting
- Can fetch exactly what email system needs

**Cons:**
- Re-fetches indicators already computed during DSL evaluation
- Slight performance hit (additional API calls)

### Option 2: Cache Indicators in StrategySignal Metadata (More Efficient)

**Pros:**
- Reuses indicators already computed
- No duplicate API calls
- More efficient

**Cons:**
- Requires changes in DSL engine
- Indicators must be serializable for metadata dict
- Slightly more coupling between DSL and email systems

---

## Recommendation

**Start with Option 1** (fetch in signal handler) because:
1. It's simpler to implement
2. It's cleaner architecturally
3. Performance impact is negligible (only runs once per rebalance)
4. Can be optimized to Option 2 later if needed

The key is to add the `technical_indicators` field to the dict returned by `_convert_signals_to_display_format()`. Once that's done, all the email enhancements in PR #2684 will immediately work.
