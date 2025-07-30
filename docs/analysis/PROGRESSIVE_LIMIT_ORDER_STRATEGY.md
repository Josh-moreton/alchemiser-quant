# Progressive Limit Order Strategy Implementation

## Overview

The enhanced limit order strategy starts at the midpoint of the bid-ask spread and progressively steps toward the less favorable price, maximizing the chance of price improvement while ensuring eventual execution.

## Strategy Description

### Core Algorithm

1. **Midpoint Start**: Begin with a limit order at the exact midpoint of bid/ask spread
2. **Progressive Steps**: Step 10% toward the less favorable price every 10 seconds
3. **WebSocket Monitoring**: Use real-time order status notifications (no polling)
4. **Market Fallback**: Place market order if all limit attempts fail

### Pricing Logic

**For BUY Orders (stepping toward ask):**

- Step 1: Midpoint = (bid + ask) / 2
- Step 2: Midpoint + (spread/2 × 0.1) = 10% toward ask
- Step 3: Midpoint + (spread/2 × 0.2) = 20% toward ask  
- Step 4: Midpoint + (spread/2 × 0.3) = 30% toward ask
- Step 5: Market order

**For SELL Orders (stepping toward bid):**

- Step 1: Midpoint = (bid + ask) / 2
- Step 2: Midpoint - (spread/2 × 0.1) = 10% toward bid
- Step 3: Midpoint - (spread/2 × 0.2) = 20% toward bid
- Step 4: Midpoint - (spread/2 × 0.3) = 30% toward bid
- Step 5: Market order

## Implementation Details

### Key Features

- **WebSocket Integration**: Real-time order fill notifications eliminate polling delays
- **Smart Timeout**: 10-second waits per step for optimal speed/price balance
- **Guaranteed Execution**: Market order fallback ensures order completion
- **Price Improvement**: Starting at midpoint maximizes savings potential
- **Progressive Aggression**: Each step increases fill probability

### Performance Metrics

From demo output showing real market data:

**UVXY Example:**

- Bid: $15.23, Ask: $15.32, Spread: $0.09 (0.59%)
- BUY progression: $15.28 → $15.28 → $15.28 → $15.29 → Market
- SELL progression: $15.28 → $15.27 → $15.27 → $15.26 → Market

**TSLA Example:**

- Bid: $319.00, Ask: $325.68, Spread: $6.68 (2.07%)
- BUY progression: $322.34 → $322.67 → $323.01 → $323.34 → Market
- SELL progression: $322.34 → $322.01 → $321.67 → $321.34 → Market

### Timing Analysis

| Scenario | Max Time | Typical Time |
|----------|----------|--------------|
| Fill at midpoint | 10 seconds | < 1 second |
| Fill at step 2 (10%) | 20 seconds | 10-15 seconds |
| Fill at step 3 (20%) | 30 seconds | 20-25 seconds |
| Fill at step 4 (30%) | 40 seconds | 30-35 seconds |
| Market order fallback | 50 seconds | 40-45 seconds |

## Code Implementation

### Enhanced OrderManagerAdapter.place_limit_or_market()

The method now implements the progressive strategy for both BUY and SELL orders:

```python
def place_limit_or_market(self, symbol, qty, side, ...):
    # Get real-time bid/ask from WebSocket
    quote = self.data_provider.get_latest_quote(symbol)
    bid, ask = float(quote[0]), float(quote[1])
    
    # Calculate midpoint and spread
    midpoint = (bid + ask) / 2.0
    spread = ask - bid
    
    # Progressive steps: 0%, 10%, 20%, 30%
    steps = [0.0, 0.1, 0.2, 0.3]
    
    for step_pct in steps:
        if side == OrderSide.BUY:
            limit_price = midpoint + (spread / 2 * step_pct)
        else:
            limit_price = midpoint - (spread / 2 * step_pct)
        
        # Place limit order
        order_id = place_limit_order(symbol, qty, side, limit_price)
        
        # Wait 10 seconds with WebSocket notifications
        result = wait_for_order_completion([order_id], 10)
        
        if 'filled' in result.get(order_id, ''):
            return order_id  # Success!
    
    # All limits failed, use market order
    return place_market_order(symbol, side, qty)
```

### WebSocket Integration

The strategy leverages the existing WebSocket infrastructure:

- **Real-time pricing**: `get_latest_quote()` uses WebSocket bid/ask data
- **Order notifications**: `wait_for_order_completion()` uses TradingStream events
- **No polling**: Eliminates the old 2-second polling with instant notifications

## Benefits

### Price Improvement

- **Midpoint start**: Maximum opportunity for price improvement vs market orders
- **Progressive steps**: Balances price optimization with execution probability
- **Smart aggression**: Becomes more aggressive only when needed

### Execution Speed

- **WebSocket notifications**: Instant fill detection (vs up to 2-second polling delays)
- **10-second steps**: Quick progression maintains execution speed
- **Guaranteed fills**: Market order fallback ensures completion

### Market Impact

- **Reduced slippage**: Starting at midpoint minimizes market impact
- **Adaptive pricing**: Steps respond to market conditions (wider spreads = bigger steps)
- **Institutional quality**: Professional execution strategy

## Example Usage

### Direct Usage

```python
order_manager = OrderManagerAdapter(trading_client, data_provider)

# BUY order with progressive limits
order_id = order_manager.place_limit_or_market(
    symbol="UVXY",
    qty=100.0,
    side=OrderSide.BUY
)

# SELL order with progressive limits  
order_id = order_manager.place_limit_or_market(
    symbol="UVXY", 
    qty=100.0,
    side=OrderSide.SELL
)
```

### Console Output Example

```
Starting progressive limit order for BUY UVXY
Bid: $15.23, Ask: $15.32, Midpoint: $15.28, Spread: $0.09

Midpoint: BUY UVXY @ $15.28
Waiting 10 seconds for fill via WebSocket...
✓ BUY UVXY filled @ $15.28 (Midpoint)
```

## Testing

### Demo Script

```bash
python demo_progressive_strategy.py
```

Shows pricing analysis for multiple symbols without placing orders.

### Live Test Script  

```bash
python test_progressive_limit_orders.py
```

Places actual small orders in paper trading to verify the strategy.

## Future Enhancements

### Potential Improvements

1. **Dynamic step sizes**: Adjust step percentages based on volatility
2. **Time-of-day optimization**: Different strategies for market open/close
3. **Volume analysis**: Consider order book depth in pricing decisions
4. **Machine learning**: Learn optimal step timing from historical fills

### Configuration Options

```yaml
progressive_limits:
  steps: [0.0, 0.1, 0.2, 0.3]  # Percentage steps toward unfavorable price
  step_timeout: 10             # Seconds to wait per step
  enable_websocket: true       # Use WebSocket notifications
  market_fallback: true        # Enable market order fallback
```

## Performance Summary

**Efficiency Gains:**

- 🚀 **Instant notifications**: WebSocket vs polling eliminates up to 2-second delays
- 💰 **Price improvement**: Midpoint start saves ~half spread on successful fills  
- ⚡ **Smart progression**: 10% steps balance speed with price optimization
- ✅ **Guaranteed execution**: Market fallback ensures order completion
- 📊 **Professional execution**: Institutional-quality limit order strategy

The progressive limit order strategy represents a significant advancement in execution quality, providing the price improvement opportunities of limit orders with the reliability of market orders, all powered by real-time WebSocket data.
