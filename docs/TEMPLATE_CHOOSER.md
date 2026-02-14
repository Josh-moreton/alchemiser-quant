# Template Chooser - Regime-Based Hedge Template Selection

## Overview

The `TemplateChooser` provides deterministic logic for selecting between `tail_first` and `smoothing` hedge templates based on market regime indicators (primarily VIX, with future support for IV percentile and skew).

## Problem Statement

Previously, the hedge template was fixed at initialization with no logic to switch based on market conditions. This resulted in:
- No adaptation to changing market regimes
- Potential overpaying for protection during high IV periods
- Missing opportunities to buy cheap tails during low IV periods
- No explanation of template selection decisions

## Solution

A deterministic regime-based template chooser that:
1. **Classifies market regimes** based on VIX levels (low/mid/high)
2. **Selects appropriate template** for each regime
3. **Prevents whipsaw** using hysteresis near regime boundaries
4. **Logs rationale** for each template selection decision

## Template Selection Logic

### Regime Classification

| VIX Range | Regime | Template | Rationale |
|-----------|--------|----------|-----------|
| < 18 | Low IV, Normal Skew | `tail_first` | Options are cheap - buy leveraged tail protection |
| 18-28 | Mid IV, Moderate Skew | `tail_first` | Moderate pricing - maintain protection bias |
| > 28 | High IV, Rich Skew | `smoothing` | Options expensive - use spreads for cost efficiency |

### Hysteresis (Whipsaw Prevention)

To prevent rapid switching near regime boundaries, a **10% hysteresis band** is applied around each threshold:

- **Low threshold (18)**: Hysteresis band = 16.2 to 19.8
- **High threshold (28)**: Hysteresis band = 25.2 to 30.8

If VIX is within a hysteresis band AND template selection would change, the previous template is retained.

### Decision Tree

```
VIX < 18
  → low_iv_normal_skew → tail_first (cheap tails)

18 <= VIX < 28
  → mid_iv_moderate_skew → tail_first (maintain protection)

VIX >= 28
  → high_iv_rich_skew → smoothing (spreads reduce cost)

Hysteresis Check:
  If near threshold AND template would change
    → Keep previous template (prevent whipsaw)
```

## Usage

### Basic Usage

```python
from the_alchemiser.shared.options import TemplateChooser

# Initialize chooser
chooser = TemplateChooser()

# Get template for current VIX
rationale = chooser.choose_template(vix=Decimal("22"))

# Access results
print(f"Template: {rationale.selected_template}")  # tail_first
print(f"Regime: {rationale.regime}")                # mid_iv_moderate_skew
print(f"Reason: {rationale.reason}")                # Human-readable explanation
```

### Custom Thresholds

```python
from the_alchemiser.shared.options import RegimeThresholds, TemplateChooser

# Define custom thresholds
thresholds = RegimeThresholds(
    vix_low_threshold=Decimal("15"),
    vix_high_threshold=Decimal("25"),
    hysteresis_pct=Decimal("0.05"),  # 5% hysteresis
)

chooser = TemplateChooser(thresholds=thresholds)
```

### Integration with HedgeEvaluationHandler

The template chooser is automatically integrated into `HedgeEvaluationHandler`:

```python
# Choose template based on current VIX
template_rationale = self._template_chooser.choose_template(
    vix=current_vix,
    vix_percentile=None,  # Future: from historical data
    skew=None,            # Future: from option chain
)

# Create HedgeSizer with selected template
self._hedge_sizer = HedgeSizer(template=template_rationale.selected_template)

# Template selection is logged automatically
logger.info(
    "Template selection rationale",
    selected_template=template_rationale.selected_template,
    regime=template_rationale.regime,
    reason=template_rationale.reason,
)
```

## Output Format

Each template selection produces structured logging:

```
Template selected: tail_first
Reason: VIX = 15 (low, cheap options); Low IV regime favors tail protection
```

Or with hysteresis:

```
Template selected: smoothing
Reason: VIX = 32 (high, expensive options); High IV regime favors spreads for cost efficiency; Hysteresis applied to prevent whipsaw; kept previous template 'smoothing' despite current regime conditions
```

## Historical Validation

The template chooser has been tested on three historical regimes:

### 2020 COVID Crash
- 9 rebalances
- 2 template switches (22.2% switch rate)
- Behavior: Switched from tail_first → smoothing when VIX spiked to 40+, stayed with smoothing through high volatility, returned to tail_first as VIX normalized

### 2022 Drawdown
- 8 rebalances
- 2 template switches (25.0% switch rate)
- Behavior: Hysteresis prevented one switch at VIX 25.9, demonstrating whipsaw prevention

### 2024 Calm Market
- 8 rebalances
- 0 template switches (0.0% switch rate)
- Behavior: Stayed with tail_first throughout low volatility period

All scenarios show **acceptable switch rates** (<50%), indicating no excessive whipsaw.

## Event Schema

Template selection metadata is included in `HedgeEvaluationCompleted` events:

```python
{
    "template_selected": "tail_first",
    "template_regime": "low_iv_normal_skew",
    "template_selection_reason": "VIX = 15 (low, cheap options); Low IV regime favors tail protection",
}
```

## Future Enhancements

### IV Percentile (Planned)
- Calculate VIX percentile from historical rolling window (e.g., 90 days)
- Use percentile instead of absolute VIX level for regime classification
- More robust to shifting volatility regimes

### Put/Call Skew (Planned)
- Fetch option chain data for underlying (SPY, QQQ)
- Calculate put/call skew metrics
- Incorporate skew richness into regime classification

### Blended Templates (Planned)
- Support for combining tail_first + smoothing in single allocation
- E.g., 60% tail_first + 40% smoothing for layered protection

## Testing

### Unit Tests

Run unit tests with pytest:

```bash
poetry run pytest shared_layer/python/the_alchemiser/shared/options/tests/test_template_chooser.py -v
```

**Coverage:**
- 19 tests covering all regime scenarios
- Edge cases (exact threshold values)
- Hysteresis behavior
- Deterministic selection
- Custom thresholds

### Integration Tests

Run regime switching validation:

```bash
poetry run python scripts/test_regime_template_chooser.py
```

**Coverage:**
- Deterministic behavior across multiple runs
- Hysteresis effectiveness
- Historical regime scenarios (2020, 2022, 2024)
- Switch rate validation

## Architecture

### Module Location
```
shared_layer/python/the_alchemiser/shared/options/
├── template_chooser.py          # Core implementation
├── tests/
│   └── test_template_chooser.py # Unit tests
└── __init__.py                  # Exports
```

### Integration Points

1. **HedgeEvaluationHandler** (`functions/hedge_evaluator/handlers/hedge_evaluation_handler.py`)
   - Instantiates `TemplateChooser` at initialization
   - Calls `choose_template()` before creating `HedgeSizer`
   - Logs rationale and publishes in event

2. **HedgeEvaluationCompleted Event** (`shared_layer/python/the_alchemiser/shared/events/schemas.py`)
   - Includes `template_selected`, `template_regime`, `template_selection_reason` fields

3. **HedgeSizer** (`functions/hedge_evaluator/core/hedge_sizer.py`)
   - Accepts `template` parameter at initialization
   - No changes required to existing logic

## Design Principles

1. **Deterministic**: Same VIX always produces same template (no randomness)
2. **Testable**: Pure functions with explicit inputs/outputs
3. **Traceable**: Structured logging of all decisions
4. **Backtestable**: Can replay historical VIX sequences
5. **Extensible**: Ready for IV percentile and skew metrics

## References

- Issue: [Options Hedging] Regime/template chooser - honest and testable
- Implementation: `shared_layer/python/the_alchemiser/shared/options/template_chooser.py`
- Tests: `shared_layer/python/the_alchemiser/shared/options/tests/test_template_chooser.py`
- Validation: `scripts/test_regime_template_chooser.py`
