# Calmar-Tilted Strategy Weighting

## Overview

This feature implements a slow-moving, long-horizon capital allocation system that adjusts strategy weights based on 12-month Calmar ratios. It addresses two key failure modes:

1. **Short-window metrics** punish strategies during normal 2-3 month drawdowns
2. **Static weights** allow genuinely degraded strategies to consume capital too long

## Architecture

### Components

- **DynamoDB Table**: `StrategyWeightsTable` - Stores live weights with version history
- **Schemas**: `CalmarMetrics`, `StrategyWeights`, `StrategyWeightsHistory`
- **Repository**: `DynamoDBStrategyWeightsRepository` - Persistence layer
- **Service**: `StrategyWeightService` - Business logic for Calmar-tilt calculation
- **CLI Script**: `scripts/strategy_weights.py` - Management interface

### Data Flow

```
strategy.prod.json (base weights)
    ↓
StrategyWeightService.initialize_weights()
    ↓
DynamoDB (live weights = base weights initially)
    ↓
Coordinator Lambda reads live weights
    ↓
Monthly rebalance updates live weights
    ↓
DynamoDB (new version with partial adjustment)
```

## Calmar-Tilt Formula

For each strategy i:

```
w_i = Normalise(
    w_base × clip(
        (Calmar_i / MedianCalmar)^α,
        f_min,
        f_max
    )
)
```

Where:
- `w_base` = 1/N (base equal weight, e.g., 0.10 for 10 strategies)
- `Calmar_i` = 12-month return / 12-month max drawdown
- `MedianCalmar` = median Calmar across all strategies (shrinkage anchor)
- `α = 0.5` (square-root dampening)
- `f_min = 0.5` (no strategy below 50% of base weight)
- `f_max = 2.0` (no strategy above 200% of base weight)

### Partial Adjustment

Target weights are NOT applied instantly. Instead, we use partial adjustment:

```
w_new = w_old + λ × (w_target − w_old)
```

Where `λ ≈ 0.1–0.25` per rebalance (default: 0.1)

This enforces slow capital migration and avoids whipsaw.

## Usage

### Initial Setup

1. **Initialize weights** (first time only):

```bash
# For dev environment
make weights-init

# For production
make weights-init stage=prod
```

This reads:
- Base weights from `strategy.prod.json` (or `strategy.dev.json`)
- Initial Calmar ratios from `starter_calmar.json`

### View Current Weights

```bash
# Show current live weights
make weights-show

# Show production weights
make weights-show stage=prod
```

Output example:
```
📊 Current Strategy Weights
Version: v1
Stage: prod
Last Rebalance: 2026-01-13T10:00:00+00:00
Next Rebalance: 2026-02-13T10:00:00+00:00

Strategy                       Base       Target     Realized   Calmar    
------------------------------ ---------- ---------- ---------- ----------
blatant_tech.clj               0.0750     0.0780     0.0753     1.3300
defence.clj                    0.1000     0.1050     0.1005     1.5000
...
```

### Monthly Rebalance

```bash
# Create updated Calmar metrics file (updated_calmar.json)
# Then run rebalance
make weights-rebalance calmar=updated_calmar.json stage=prod
```

The rebalance will:
1. Load current weights from DynamoDB
2. Compute new target weights using Calmar-tilt formula
3. Apply partial adjustment (λ=0.1 by default)
4. Save new version to DynamoDB
5. Schedule next rebalance in 30 days

### View History

```bash
# Show last 10 weight adjustments
make weights-history stage=prod

# Show last 5 versions
make weights-history stage=prod limit=5
```

## Calmar Metrics Format

The Calmar metrics JSON file should have this structure:

```json
{
  "strategy_name.clj": {
    "twelve_month_return": 0.20,
    "twelve_month_max_drawdown": 0.15,
    "calmar_ratio": 1.33,
    "months_of_data": 12
  },
  ...
}
```

Fields:
- `twelve_month_return`: Annualized 12-month return (0.20 = 20%)
- `twelve_month_max_drawdown`: Max drawdown over 12 months (0.15 = 15%)
- `calmar_ratio`: Return / Max Drawdown (1.33 = 20% / 15%)
- `months_of_data`: Number of months of actual data (1-12)

## Rolling Calmar Calculation

Since we have limited historical data initially, we use a **gradual buildup** approach:

### Month 1-11: Partial Data
```python
# Start with starter values (12 months assumed)
starter_calmar = {
    "twelve_month_return": 0.20,
    "twelve_month_max_drawdown": 0.15,
    "calmar_ratio": 1.33,
    "months_of_data": 12
}

# After 1 month of live data:
# Use weighted average: 11/12 * starter + 1/12 * live_month_1
updated_return = (11/12) * 0.20 + (1/12) * live_month_1_return
updated_mdd = max((11/12) * 0.15, live_month_1_mdd)  # MDD is max, not average
```

### Month 12+: Full Rolling Window
```python
# Use true 12-month rolling window
twelve_month_return = calculate_return(last_12_months)
twelve_month_mdd = calculate_max_drawdown(last_12_months)
calmar_ratio = twelve_month_return / twelve_month_mdd
```

## Expected Behavior

- **Strong, stable strategies**: Drift toward ~15-20% weights (1.5-2x base)
- **Weaker but valid strategies**: Stay around ~5-8% weights (0.5-0.8x base)
- **No strategy drops to near-zero** unless explicitly removed
- **Slow capital migration**: Takes ~10 rebalances (10 months) to fully move from current to target

## Integration with Coordinator

The Strategy Orchestrator Lambda (`functions/strategy_orchestrator/lambda_handler.py`) now:

1. Loads base weights from `strategy.prod.json`
2. Attempts to load live weights from DynamoDB
3. Falls back to base weights if DynamoDB unavailable
4. Passes live weights to Strategy Workers

This ensures:
- **Graceful degradation**: If weights service unavailable, use base weights
- **Zero downtime**: Weights can be updated without redeploying code
- **Audit trail**: All weight changes tracked in DynamoDB version history

## DynamoDB Schema

### Current Weights Item
```
PK: "WEIGHTS#CURRENT"
SK: "METADATA"
EntityType: "CURRENT_WEIGHTS"
version: "v1"
base_weights: { "strategy_a": "0.333", ... }
target_weights: { "strategy_a": "0.350", ... }
realized_weights: { "strategy_a": "0.335", ... }
calmar_metrics: { "strategy_a": { ... }, ... }
adjustment_lambda: "0.1"
rebalance_frequency_days: 30
last_rebalance: "2026-01-13T10:00:00Z"
next_rebalance: "2026-02-13T10:00:00Z"
created_at: "2026-01-01T00:00:00Z"
updated_at: "2026-01-13T10:00:00Z"
```

### Version History Item
```
PK: "WEIGHTS#CURRENT"
SK: "VERSION#2026-01-13T10:00:00Z"
EntityType: "VERSION_HISTORY"
GSI1PK: "HISTORY#ALL"
GSI1SK: "VERSION#2026-01-13T10:00:00Z"
version: "v1"
reason: "monthly_rebalance"
correlation_id: "rebalance-uuid"
weights: { ... }  # Full StrategyWeights object
created_at: "2026-01-13T10:00:00Z"
```

## Validation

Run validation tests to ensure Calmar calculations work correctly:

```bash
python3 scripts/validate_calmar_weights.py
```

This validates:
1. Calmar-tilt formula produces expected results
2. Partial adjustment moves weights correctly toward targets
3. Caps (f_max=2.0) and floors (f_min=0.5) are enforced

## Deployment

1. Deploy infrastructure (creates DynamoDB table):
   ```bash
   make deploy-dev
   ```

2. Initialize weights:
   ```bash
   make weights-init
   ```

3. Verify:
   ```bash
   make weights-show
   ```

4. For production:
   ```bash
   make deploy stage=prod
   make weights-init stage=prod
   ```

## Monitoring

- **CloudWatch Logs**: Check coordinator Lambda logs for weight loading
- **DynamoDB**: Query `StrategyWeightsTable` for current/historical weights
- **Weight History**: Use `make weights-history` to audit changes

## Future Enhancements

1. **Automated Rebalancing**: Lambda scheduled monthly to auto-rebalance
2. **Performance Tracking**: Compute Calmar from trade ledger automatically
3. **Alert on Extreme Weights**: SNS notification if any weight hits cap/floor
4. **Backtest Comparison**: Compare Calmar-tilted vs equal-weight performance

## References

- Design spec: Issue #XXX "Implement 12-Month Calmar-Tilted Strategy Weighting"
- Template changes: `template.yaml` (StrategyWeightsTable)
- Code: `layers/shared/the_alchemiser/shared/services/strategy_weight_service.py`
