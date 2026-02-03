# Migration Guide: Almgren-Chriss Optimal Execution

## Overview

This guide covers deploying the Almgren-Chriss optimal execution strategy to production. The implementation is backward compatible and can be deployed incrementally.

## Pre-Deployment Checklist

- [ ] Review [Almgren-Chriss documentation](ALMGREN_CHRISS_EXECUTION.md)
- [ ] Understand parameter tuning (λ, σ, η, N, T)
- [ ] Prepare environment variables for dev environment
- [ ] Plan rollback strategy (revert urgency routing if needed)

## Deployment Steps

### 1. Deploy to Development Environment

```bash
# Configure Almgren-Chriss parameters for dev
export AC_RISK_AVERSION=0.5       # Balanced risk aversion
export AC_VOLATILITY=0.02         # Medium volatility assumption
export AC_TEMP_IMPACT=0.001       # Mid cap liquidity
export AC_NUM_SLICES=5            # 5 slices (default)
export AC_TOTAL_TIME_SECONDS=300  # 5 minutes
export AC_SLICE_WAIT_SECONDS=30   # 30 seconds per slice
export AC_MARKET_FALLBACK=true    # Enable fallback

# Deploy to dev
make deploy-dev
```

### 2. Test with Small Orders

Test the new strategy with small, non-critical orders:

```python
# In your test script
intent = OrderIntent(
    side=OrderSide.BUY,
    symbol="AAPL",
    quantity=Decimal("10"),  # Small test order
    urgency=Urgency.MEDIUM,  # ← Uses Almgren-Chriss
    correlation_id="test-ac-001",
)
```

**What to monitor:**
- Execution strategy in logs: `"execution_strategy": "almgren_chriss"`
- Number of slices used: `"slices_used": 5`
- Fill rate: `"fill_percentage": "100.0%"`
- Average fill price compared to market price
- Total execution time

### 3. Monitor and Tune Parameters

After testing with small orders, analyze the results:

**If fill rates are low (<70%):**
- Increase `AC_RISK_AVERSION` (e.g., 0.5 → 0.8) for more aggressive execution
- Reduce `AC_NUM_SLICES` (e.g., 5 → 3) for larger slices
- Ensure `AC_MARKET_FALLBACK=true` is enabled

**If market impact is high:**
- Decrease `AC_RISK_AVERSION` (e.g., 0.5 → 0.3) for more patient execution
- Increase `AC_NUM_SLICES` (e.g., 5 → 7) for smaller slices
- Increase `AC_TOTAL_TIME_SECONDS` (e.g., 300 → 450) for longer execution

**If execution is too slow:**
- Increase `AC_RISK_AVERSION` for faster execution
- Reduce `AC_TOTAL_TIME_SECONDS` for shorter window
- Reduce `AC_SLICE_WAIT_SECONDS` for less waiting per slice

### 4. Gradual Rollout to Production

Once satisfied with dev testing:

```bash
# Configure production parameters (may differ from dev)
export AC_RISK_AVERSION=0.5
export AC_VOLATILITY=0.02
export AC_TEMP_IMPACT=0.001
export AC_NUM_SLICES=5
export AC_TOTAL_TIME_SECONDS=300
export AC_SLICE_WAIT_SECONDS=30
export AC_MARKET_FALLBACK=true

# Deploy to production
make deploy
```

**Rollout Strategy:**
1. **Week 1**: Monitor MEDIUM urgency orders (now using Almgren-Chriss)
2. **Week 2**: If metrics are good, continue monitoring
3. **Week 3**: Tune parameters based on observed market conditions
4. **Week 4**: Consider making Almgren-Chriss the default for LOW urgency too

### 5. Monitor Production Metrics

Key metrics to track:

| Metric | Target | How to Check |
|--------|--------|--------------|
| Fill Rate | >95% | CloudWatch logs: `fill_percentage` |
| Avg Execution Time | 5-10 min | CloudWatch logs: `execution_time_seconds` |
| Price Improvement | Positive | Compare `avg_fill_price` to market midpoint |
| Market Fallback Rate | <10% | Count logs with `"Market order fallback"` |
| Strategy Usage | MEDIUM → AC | CloudWatch logs: `"execution_strategy": "almgren_chriss"` |

**CloudWatch Insights Query Example:**
```
fields @timestamp, symbol, execution_strategy, total_filled, avg_fill_price, fill_percentage, execution_time_seconds
| filter execution_strategy = "almgren_chriss"
| stats count() as executions, avg(fill_percentage) as avg_fill_rate, avg(execution_time_seconds) as avg_time by symbol
| sort avg_fill_rate desc
```

## Rollback Plan

If Almgren-Chriss is not performing as expected:

### Option 1: Revert MEDIUM Urgency to Walk-the-Book

Edit `placement_service.py`:

```python
# Change routing back to walk-the-book for MEDIUM
elif intent.urgency == Urgency.MEDIUM:
    # MEDIUM urgency: walk-the-book (temporary rollback)
    result = await self._execute_walk_the_book(
        intent, quote_result, initial_position, start_time
    )
```

Redeploy:
```bash
make deploy
```

### Option 2: Adjust Parameters Dramatically

If the strategy is close but needs significant tuning:

```bash
# Much more aggressive (faster execution)
export AC_RISK_AVERSION=1.5
export AC_NUM_SLICES=3
export AC_TOTAL_TIME_SECONDS=180

# Or much more patient (lower impact)
export AC_RISK_AVERSION=0.2
export AC_NUM_SLICES=10
export AC_TOTAL_TIME_SECONDS=600
```

### Option 3: Disable for Specific Symbols

If certain symbols perform poorly with Almgren-Chriss, add symbol-specific routing:

```python
# In placement_service.py
if intent.urgency == Urgency.MEDIUM:
    # Use walk-the-book for low-liquidity symbols
    if intent.symbol in ["LOWLIQ1", "LOWLIQ2"]:
        result = await self._execute_walk_the_book(...)
    else:
        result = await self._execute_almgren_chriss(...)
```

## Parameter Tuning by Asset Class

Different asset classes may require different parameters:

### Large Cap (High Liquidity)
```bash
AC_RISK_AVERSION=0.5      # Balanced
AC_TEMP_IMPACT=0.0001     # Low impact
AC_NUM_SLICES=5
AC_TOTAL_TIME_SECONDS=300
```

### Mid Cap (Medium Liquidity)
```bash
AC_RISK_AVERSION=0.5      # Balanced (default)
AC_TEMP_IMPACT=0.001      # Medium impact
AC_NUM_SLICES=5
AC_TOTAL_TIME_SECONDS=300
```

### Small Cap (Low Liquidity)
```bash
AC_RISK_AVERSION=0.3      # Patient
AC_TEMP_IMPACT=0.01       # High impact
AC_NUM_SLICES=7           # More slices
AC_TOTAL_TIME_SECONDS=450 # Longer execution
```

## Success Criteria

After 30 days of production use, the strategy should demonstrate:

- ✅ Fill rate >95% for MEDIUM urgency orders
- ✅ Average execution time 5-10 minutes
- ✅ Market fallback rate <10%
- ✅ Price improvement vs. walk-the-book (lower avg slippage)
- ✅ No increase in failed trades or timeout errors

## Troubleshooting

### Issue: Low Fill Rates

**Symptoms**: `fill_percentage < 70%`, frequent market fallbacks

**Solutions**:
1. Increase `AC_RISK_AVERSION` to 0.8-1.0 (more aggressive)
2. Reduce `AC_NUM_SLICES` to 3-4 (larger slices)
3. Verify `AC_MARKET_FALLBACK=true` is enabled

### Issue: High Market Impact

**Symptoms**: Large difference between expected and realized prices

**Solutions**:
1. Decrease `AC_RISK_AVERSION` to 0.2-0.3 (more patient)
2. Increase `AC_NUM_SLICES` to 7-10 (smaller slices)
3. Increase `AC_TOTAL_TIME_SECONDS` to 450-600 (longer execution)

### Issue: Execution Too Slow

**Symptoms**: Orders taking >10 minutes to complete

**Solutions**:
1. Increase `AC_RISK_AVERSION` to 0.8-1.0 (faster)
2. Reduce `AC_TOTAL_TIME_SECONDS` to 180-240 (shorter window)
3. Reduce `AC_SLICE_WAIT_SECONDS` to 15-20 (less waiting)

### Issue: Orders Timing Out

**Symptoms**: DynamoDB errors, SQS timeout errors

**Solutions**:
1. Verify Lambda timeout is sufficient (>10 minutes)
2. Reduce `AC_TOTAL_TIME_SECONDS` to fit within Lambda timeout
3. Check DynamoDB and Alpaca API connectivity

## Support and Feedback

For questions or issues:
1. Check logs in CloudWatch for error messages
2. Review [Almgren-Chriss documentation](ALMGREN_CHRISS_EXECUTION.md)
3. Consult original research paper (Almgren & Chriss, 2001)
4. Open GitHub issue with logs and metrics

## References

- [Almgren-Chriss Execution Documentation](ALMGREN_CHRISS_EXECUTION.md)
- Almgren, R., & Chriss, N. (2001). "Optimal execution of portfolio transactions." Journal of Risk, 3, 5-40.
- [Environment Variables Example](.env.almgren_chriss.example)
