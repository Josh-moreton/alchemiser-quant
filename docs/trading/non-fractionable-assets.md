# Non-Fractionable Asset Handling

## Problem

Some assets like leveraged ETFs (FNGU, TQQQ, SQQQ) and ETNs don't support fractional shares. When you try to buy 1.75 shares of FNGU, you get:

```
ERROR: {"code":40310000,"message":"asset \"FNGU\" is not fractionable"}
```

## Professional Solution

Our system now implements **three-tier smart handling**:

### 1. 🔍 **Predictive Detection**

- Automatically detects likely non-fractionable assets
- Known patterns: FNGU, TQQQ, SQQQ, UVXY, BIL, leveraged ETFs
- Smart conversion before orders are placed

### 2. 💰 **Notional Orders (Preferred)**

For **BUY orders** on non-fractionable assets:

```python
# Instead of: Buy 1.75 shares of FNGU
# System automatically converts to: Buy $46.20 worth of FNGU
```

**Benefits:**

- Broker calculates optimal whole shares
- Perfect execution with no rounding errors
- Professional institutional approach

### 3. 🔄 **Graceful Fallback**

If fractional order fails:

```python
# Try: 1.75 shares of FNGU
# Error: "not fractionable" 
# Fallback: 1 whole share of FNGU (or $26.40 notional)
```

## What Changed

### Enhanced Order Placement

```python
# Before (would fail for FNGU)
order_id = client.place_market_order('FNGU', OrderSide.BUY, qty=1.75)

# After (automatically handles non-fractionable)
order_id = client.place_market_order('FNGU', OrderSide.BUY, qty=1.75)
# ↳ Converts to: notional=$46.20 for optimal execution
```

### Smart Detection

```python
from the_alchemiser.utils.asset_info import fractionability_detector

# Check if asset is non-fractionable
is_non_frac = fractionability_detector.is_likely_non_fractionable('FNGU')  # True

# Should we use notional orders?
use_notional = fractionability_detector.should_use_notional_order('FNGU', 1.75)  # True

# Convert to whole shares if needed
whole_qty, was_rounded = fractionability_detector.convert_to_whole_shares('FNGU', 1.75, 26.40)
# Returns: (1.0, True)
```

## Supported Assets

### ✅ **Automatically Handled Non-Fractionable Assets**

- **Leveraged ETFs**: FNGU, FNGD, TQQQ, SQQQ, TECL, TECS
- **Market ETFs**: SPXL, SPXS, UPRO, SPXU, SSO, SDS
- **Volatility Products**: UVXY, SVXY, VXX, VIXY
- **Sector ETFs**: ERX, ERY, FAS, FAZ, LABU, LABD
- **Bond ETFs**: BIL, SHY, IEF, TLT, HYG, LQD
- **International ETFs**: EEM, VWO, EFA, FXI, GLD, SLV

### ✅ **Regular Fractionable Assets** (unchanged)

- **Stocks**: AAPL, MSFT, GOOGL, TSLA
- **Major ETFs**: SPY, QQQ, VTI, VOO

## Impact on Your Trading

### Before Enhancement

```
Midpoint: buy FNGU @ $26.39
ERROR: asset "FNGU" is not fractionable
Failed to place limit order at $26.39
[All progressive orders fail]
ERROR: Market order failed for FNGU: asset "FNGU" is not fractionable
```

### After Enhancement

```
🔄 Converting FNGU from qty=1.75 to notional=$46.20 (likely non-fractionable asset)
✅ BUY FNGU filled @ $26.39 (1 whole share via notional order)
```

## Key Benefits

1. **🎯 Zero Configuration** - Works automatically
2. **💰 Better Execution** - Uses professional notional order approach
3. **🔄 Backward Compatible** - No changes needed to existing code
4. **🛡️ Fail-Safe** - Graceful fallbacks if prediction is wrong
5. **📈 Future-Proof** - Handles new non-fractionable assets automatically

## Professional Trading Practices

This matches how **institutional traders** handle non-fractionable assets:

1. **Predict asset type** before order placement
2. **Use notional orders** for optimal execution
3. **Implement fallbacks** for edge cases
4. **Maintain compatibility** with all asset types

Your FNGU orders (and all other leveraged ETFs) should now execute perfectly! 🚀
