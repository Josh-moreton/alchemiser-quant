# Strategy Weighting Lambda

## Purpose

Dynamically adjusts strategy allocation weights based on recent Sharpe ratio performance. Runs weekly to tilt capital toward strategies with better risk-adjusted returns.

## Architecture

- **Trigger**: EventBridge Schedule (Sundays 6 PM ET)
- **Input**: Trade history from DynamoDB Trade Ledger
- **Output**: Dynamic weights stored in DynamoDB Strategy Weights Table
- **Dependencies**: Trade Ledger Table (read), Strategy Weights Table (write)

## Algorithm

1. **Load Baseline**: Read baseline allocations from JSON config (strategy.prod.json or strategy.dev.json)
2. **Calculate Sharpe Ratios**: For each strategy, compute annualized Sharpe ratio from recent trade history (default 90 days)
3. **Rank Strategies**: Sort strategies by Sharpe ratio (descending)
4. **Apply Multipliers**: Map normalized Sharpe to weight multiplier (0.5x to 2.0x baseline)
5. **Renormalize**: Scale adjusted weights to sum to 1.0
6. **Store Dynamic Weights**: Write to DynamoDB with metadata (Sharpe ratios, baseline allocations, timestamp)

## Weight Constraints

- **Minimum**: 0.5x baseline allocation (50% of original weight)
- **Maximum**: 2.0x baseline allocation (200% of original weight)
- **Rationale**: Prevents extreme tilts while allowing meaningful capital reallocation

## Sharpe Ratio Calculation

```
Sharpe Ratio = (Annualized Return - Risk Free Rate) / Annualized Volatility

Where:
- Annualized Return = Mean Daily Return × 252 trading days
- Annualized Volatility = Std Dev Daily Return × sqrt(252)
- Risk Free Rate = 4.5% (US 10-year Treasury approximation)
- Daily Returns = Realized P&L / Average Position Value
```

## Configuration

Environment variables:
- `TRADE_LEDGER__TABLE_NAME`: DynamoDB table for trade history
- `STRATEGY_WEIGHTS__TABLE_NAME`: DynamoDB table for dynamic weights
- `LOOKBACK_DAYS`: Number of days to look back for Sharpe calculation (default: 90)
- `APP__STAGE`: Deployment stage (dev/staging/prod) for loading baseline config

## Integration with Strategy Config

The `get_strategy_profile()` function in `strategy_profiles.py` automatically overlays dynamic weights on baseline allocations:

1. Load baseline allocations from JSON config
2. Query DynamoDB for most recent dynamic weights
3. Overlay dynamic weights on baseline (if available)
4. Return StrategyProfile with final allocations

If dynamic weights are unavailable or fail to load, the system falls back to baseline allocations.

## Monitoring

Check CloudWatch Logs for:
- Sharpe ratio calculations per strategy
- Weight multipliers applied
- Final dynamic allocations stored
- Errors loading trade history or calculating Sharpe ratios

## Manual Invocation

To manually trigger weight adjustment:

```bash
aws lambda invoke \
  --function-name alchemiser-dev-strategy-weighting \
  --payload '{"source": "manual"}' \
  response.json
```
