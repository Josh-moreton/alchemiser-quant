# Dynamic Options Contract Selection

## Overview

This module replaces the rigid "15-delta at 90 DTE" approach with dynamic contract selection based on market conditions and effective convexity.

## Key Features

### 1. Dynamic Tenor Selection (`tenor_selector.py`)

Selects optimal DTE (days to expiry) based on:

- **VIX Level**: High VIX (>35) → longer tenors (120-180 DTE) for better theta efficiency
- **IV Percentile**: High IV percentile (>70%) → longer tenors
- **Tenor Ladder**: Splits allocation between 60-90 DTE and 120-180 DTE for diversification
- **Term Structure**: Adjusts based on contango/backwardation (when available)

**Usage:**
```python
from the_alchemiser.shared.options.tenor_selector import TenorSelector

selector = TenorSelector()
recommendation = selector.select_tenor(
    current_vix=Decimal("25"),
    iv_percentile=Decimal("0.75"),
    use_ladder=True,
)
# recommendation.primary_dte = 150
# recommendation.strategy = "ladder"
```

### 2. Convexity-Based Strike Selection (`convexity_selector.py`)

Selects strikes based on:

- **Effective Convexity per Premium**: Gamma / (mid_price * 100)
  - Higher gamma = better protection curve
  - Lower premium = better value
- **Scenario Payoff Contribution**: Intrinsic value at -20% move / premium
  - Filters out options that don't contribute meaningfully in crash scenarios
  - Minimum 3x payoff multiple required
- **Combined Score**: Weights both convexity and payoff equally

**Usage:**
```python
from the_alchemiser.shared.options.convexity_selector import ConvexitySelector

selector = ConvexitySelector(
    scenario_move=Decimal("-0.20"),  # -20% crash scenario
    min_payoff_contribution=Decimal("3.0"),  # Min 3x payoff
)

metrics = selector.calculate_convexity_metrics(contract, underlying_price)
# metrics.convexity_per_dollar = 0.000012
# metrics.scenario_payoff_pct = 3.62
# metrics.effective_score = 3.63

# Filter and rank
filtered = selector.filter_by_payoff_contribution(metrics_list)
ranked = selector.rank_by_convexity(filtered)
best_contract = ranked[0].contract
```

### 3. Enhanced Liquidity Filters

New filters added to `hedge_config.py`:

- **Absolute Spread Threshold**: Max $0.10 bid-ask spread
  - Percentage spreads can be misleading on cheap options
  - Example: 2¢ option with 5¢ spread = 150% spread but only $0.05
- **Minimum Mid Price**: Min $0.05 mid price
  - Avoids "penny options" where spreads dominate
  - Ensures meaningful liquidity
- **Minimum Volume**: Min 100 daily volume
  - Adds volume filter to complement open interest
  - Better reflects recent liquidity

**Before:**
```python
LiquidityFilters(
    min_open_interest=1000,
    max_spread_pct=Decimal("0.05"),  # 5% max
    min_dte=14,
    max_dte=120,
)
```

**After:**
```python
LiquidityFilters(
    min_open_interest=1000,
    max_spread_pct=Decimal("0.05"),  # 5% max
    max_spread_absolute=Decimal("0.10"),  # $0.10 max
    min_mid_price=Decimal("0.05"),  # $0.05 min
    min_volume=100,  # 100 contracts/day min
    min_dte=14,
    max_dte=120,
)
```

## Integration

### Option Selector Flow

```
select_hedge_contract(current_vix=25, iv_percentile=0.75)
    ↓
1. Dynamic Tenor Selection
   - TenorSelector.select_tenor() → primary_dte=150
   ↓
2. Query Option Chain
   - Fetch contracts in DTE range
   - Enrich with quotes
   ↓
3. Liquidity Filtering
   - Apply all filters (OI, volume, spreads, mid price)
   ↓
4. Convexity-Based Selection
   - Calculate convexity metrics for each contract
   - Filter by scenario payoff (≥3x)
   - Rank by effective score
   - Return best contract
   ↓
5. Fallback (if insufficient gamma data)
   - Traditional delta/expiry scoring
```

### Event Flow

```
HedgeEvaluator
  ├─ Gets current VIX
  ├─ Calculates hedge recommendation
  ├─ Publishes HedgeEvaluationCompleted
  │   └─ recommendations[{"current_vix": "25", ...}]
  └─ current_vix: Decimal("25")
      ↓
HedgeExecutor
  ├─ Extracts current_vix from recommendation
  ├─ Calls select_hedge_contract(current_vix=...)
  └─ Dynamic tenor + convexity selection applied
```

## Acceptance Criteria

✅ **Tenor selection considers term structure / IV percentile**
- High IV percentile (>70%) → longer tenors
- Rich VIX (>35) → longer tenors
- Ladder strategy available for diversification

✅ **Delta selection based on convexity per premium**
- Gamma / (mid_price * 100) calculated
- Effective score combines convexity + payoff

✅ **Strike filter anchored to scenario payoff contribution**
- Minimum 3x payoff at -20% scenario
- Filters out OTM strikes that won't contribute

✅ **Absolute spread threshold added (not just %)**
- Max $0.10 absolute spread enforced
- Prevents excessive spreads on cheap options

✅ **Minimum mid price filter added**
- Min $0.05 mid price enforced
- Avoids penny options

✅ **OI/volume gates tightened**
- Added minimum volume requirement (100)
- Existing OI requirement maintained (1000)

## Testing

Run the test script to validate:

```bash
cd /home/runner/work/alchemiser-quant/alchemiser-quant
PYTHONPATH=layers/shared:$PYTHONPATH python3 scripts/test_dynamic_contract_selection.py
```

## Future Enhancements

1. **IV Percentile Calculation**: Add real IV percentile calculation from historical data
2. **Term Structure Analysis**: Calculate and use term structure slope
3. **Tenor Ladder Execution**: Support split execution across multiple tenors
4. **Adaptive Payoff Threshold**: Adjust min payoff multiple based on market conditions
5. **Greeks-Based Delta**: Use actual Greeks data instead of strike-based delta estimation

## Migration Notes

- Existing hedge positions continue to work unchanged
- New dynamic selection applied to new hedge evaluations
- VIX must be available for dynamic tenor selection (falls back to target_dte if not)
- Convexity selection requires gamma data (falls back to delta/expiry scoring if unavailable)
