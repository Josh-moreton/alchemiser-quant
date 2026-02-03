# Almgren-Chriss Optimal Execution

## Overview

The Almgren-Chriss optimal execution model is a quantitative framework for executing large orders that balances two competing costs:

1. **Market Impact Cost**: Price moves against you as you trade (larger trades have more impact)
2. **Timing Risk**: Volatility risk during the execution period (slow execution exposes you to price changes)

The model computes an optimal trading trajectory that minimizes:
```
E[Cost] + λ × Var[Cost]
```
where `λ` (lambda) is the risk aversion parameter.

## How It Works

### Mathematical Framework

The optimal trajectory is computed using:
```
x_k = Q × sinh(κ(N-k)Δt) / sinh(κNΔt)
```

Where:
- `x_k` = remaining quantity after slice k
- `Q` = total quantity to execute
- `N` = number of time slices
- `κ` (kappa) = sqrt(λσ²/η)
- `Δt` = time per slice (T/N)

**Key Parameters:**
- **λ (lambda)**: Risk aversion parameter (higher = more risk-averse, trades faster)
- **σ (sigma)**: Volatility per sqrt(Δt)
- **η (eta)**: Temporary market impact coefficient
- **N**: Number of time slices to split order into
- **T**: Total execution time horizon

### Execution Flow

1. **Compute Trajectory**: Calculate optimal quantity distribution across N slices
2. **Execute Slices**: Place limit orders for each slice with progressively more aggressive pricing
3. **Track Fills**: Monitor partial fills and adjust remaining trajectory
4. **Market Fallback**: Optional fallback to market order if execution stalls (<50% filled)

### Pricing Strategy

Each slice uses a limit price that becomes progressively more aggressive:
- **First slice (0)**: 60% toward aggressive side (patient)
- **Last slice (N-1)**: 90% toward aggressive side (aggressive)
- **BUY orders**: Limit price moves from bid toward ask
- **SELL orders**: Limit price moves from ask toward bid

## Configuration

### Environment Variables

The Almgren-Chriss strategy can be configured via environment variables:

| Variable | Description | Default | Typical Range |
|----------|-------------|---------|---------------|
| `AC_RISK_AVERSION` | Risk aversion parameter λ | `0.5` | 0.1 - 2.0 |
| `AC_VOLATILITY` | Volatility σ per sqrt(dt) | `0.02` | 0.01 - 0.05 |
| `AC_TEMP_IMPACT` | Temporary market impact η | `0.001` | 0.0001 - 0.01 |
| `AC_NUM_SLICES` | Number of time slices N | `5` | 3 - 10 |
| `AC_TOTAL_TIME_SECONDS` | Total execution time T | `300` (5 min) | 60 - 600 |
| `AC_SLICE_WAIT_SECONDS` | Wait time per slice | `30` | 10 - 60 |
| `AC_MARKET_FALLBACK` | Use market order fallback | `true` | true/false |

### Parameter Tuning Guidelines

**Risk Aversion (λ)**:
- **Low (0.1 - 0.3)**: Patient execution, tolerates timing risk, minimizes impact
- **Medium (0.4 - 0.7)**: Balanced approach (default)
- **High (0.8 - 2.0)**: Aggressive execution, minimizes timing risk, accepts more impact

**Volatility (σ)**:
- **Low volatility stocks**: 0.01 - 0.02
- **Medium volatility stocks**: 0.02 - 0.03 (default)
- **High volatility stocks**: 0.03 - 0.05

**Temporary Impact (η)**:
- **Large cap, liquid stocks**: 0.0001 - 0.001
- **Mid cap stocks**: 0.001 - 0.005 (default)
- **Small cap, illiquid stocks**: 0.005 - 0.01

**Number of Slices (N)**:
- **Small orders**: 3-5 slices (default: 5)
- **Medium orders**: 5-7 slices
- **Large orders**: 7-10 slices

**Total Time (T)**:
- **Quick execution**: 60-180 seconds (1-3 minutes)
- **Normal execution**: 180-300 seconds (3-5 minutes, default: 300)
- **Patient execution**: 300-600 seconds (5-10 minutes)

## Integration with Order Placement

The Almgren-Chriss strategy is integrated into the unified order placement service and automatically selected based on order urgency:

| Urgency | Strategy | Description |
|---------|----------|-------------|
| **HIGH** | Market Immediate | Immediate market order, guaranteed fill |
| **MEDIUM** | Almgren-Chriss | Optimal execution with risk-averse trajectory (default) |
| **LOW** | Walk-the-Book | Progressive pricing with 4 steps (50%, 75%, 95%, market) |

### Code Example

```python
from functions.execution.unified.order_intent import OrderIntent, OrderSide, Urgency
from functions.execution.unified.placement_service import UnifiedOrderPlacementService

# MEDIUM urgency → uses Almgren-Chriss automatically
intent = OrderIntent(
    side=OrderSide.BUY,
    symbol="AAPL",
    quantity=Decimal("1000"),
    urgency=Urgency.MEDIUM,  # ← Triggers Almgren-Chriss
    ...
)

service = UnifiedOrderPlacementService(alpaca_manager)
result = await service.place_order(intent)

print(f"Strategy: {result.execution_strategy}")  # "almgren_chriss"
print(f"Slices: {result.almgren_chriss_result.num_slices_used}")
print(f"Filled: {result.total_filled} @ ${result.avg_fill_price:.2f}")
```

## Advantages Over Walk-the-Book

The Almgren-Chriss model provides several improvements over the previous walk-the-book strategy:

1. **Theoretically Optimal**: Based on rigorous mathematical framework that provably minimizes cost + risk
2. **Risk-Aware**: Explicitly balances market impact vs. timing risk based on λ parameter
3. **Adaptive**: Trajectory shape adapts to market conditions (volatility, liquidity)
4. **Smooth Distribution**: Optimal quantity distribution across slices (not fixed steps)
5. **Better Pricing**: Progressive pricing strategy that's more patient early, aggressive late

### Comparison

| Feature | Walk-the-Book | Almgren-Chriss |
|---------|---------------|----------------|
| Pricing | Fixed steps (50%, 75%, 95%) | Optimal trajectory (60%-90%) |
| Quantity | Equal per step | Optimally distributed |
| Risk Model | None | Minimizes E[Cost] + λVar[Cost] |
| Adaptability | Fixed behavior | Adapts to λ, σ, η parameters |
| Market Fallback | Always after 3 steps | Optional, only if <50% filled |

## Monitoring and Logging

The Almgren-Chriss strategy provides detailed structured logging:

```json
{
  "message": "Starting Almgren-Chriss execution",
  "symbol": "AAPL",
  "quantity": "1000",
  "num_slices": 5,
  "risk_aversion": 0.5,
  "kappa": 2.236
}

{
  "message": "Slice 1/5",
  "target_quantity": "327.42",
  "actual_quantity": "327.42",
  "limit_price": "175.23",
  "aggression_factor": 0.60
}

{
  "message": "Almgren-Chriss execution complete",
  "success": true,
  "slices_used": 5,
  "total_filled": "1000",
  "avg_price": "175.48",
  "fill_percentage": "100.0%"
}
```

## Troubleshooting

### Low Fill Rates

If you're experiencing low fill rates (<50%):
- **Increase risk aversion (λ)**: More aggressive execution
- **Reduce number of slices (N)**: Larger slices may fill better
- **Enable market fallback**: `AC_MARKET_FALLBACK=true`

### Too Much Market Impact

If you're experiencing excessive market impact:
- **Decrease risk aversion (λ)**: More patient execution
- **Increase number of slices (N)**: Smaller slices have less impact
- **Increase total time (T)**: Spread execution over longer period

### Execution Too Slow

If execution is taking too long:
- **Increase risk aversion (λ)**: Faster execution
- **Reduce total time (T)**: Shorter execution window
- **Reduce number of slices (N)**: Fewer slices = faster completion

## References

- Almgren, R., & Chriss, N. (2001). "Optimal execution of portfolio transactions." Journal of Risk, 3, 5-40.
- [Dean Markwick's Blog: Solving the Almgren-Chris Model](https://dm13450.github.io/2024/06/06/Solving-the-Almgren-Chris-Model.html)
- [QuestDB: Optimal Execution Strategies](https://questdb.com/glossary/optimal-execution-strategies-almgren-chriss-model/)

## Implementation Files

- **Strategy**: `functions/execution/unified/almgren_chriss.py`
- **Integration**: `functions/execution/unified/placement_service.py`
- **Order Intent**: `functions/execution/unified/order_intent.py`
