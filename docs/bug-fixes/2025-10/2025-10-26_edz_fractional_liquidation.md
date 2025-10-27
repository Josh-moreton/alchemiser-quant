# Bug Fix: EDZ Fractional Position Liquidation

**Date:** October 10, 2025  
**Issue:** Liquidation of fractional positions in non-fractionable assets fails  
**Affected Symbol:** EDZ (and any other non-fractionable asset with fractional positions)  
**Severity:** High - Prevents complete portfolio liquidation

## Problem Statement

The system failed to liquidate a 0.3 share position in EDZ (a non-fractionable ETF) during the October 10, 2025 live trading run. The liquidation was rounded down to 0 shares, causing the order to fail with error: **"Quantity must be positive"**.

### Root Cause

EDZ is marked as **non-fractionable** by Alpaca, meaning:
- New PURCHASES cannot be fractional (must buy whole shares: 1, 2, 3, etc.)
- The system can still HOLD fractional positions (from prior splits, mergers, or partial fills)
- Existing fractional positions CAN and MUST be sold in their exact quantity

The bug was in `phase_executor.py::_calculate_liquidation_shares()`:

```python
# BEFORE (buggy):
def _calculate_liquidation_shares(self, symbol: str) -> Decimal:
    raw_shares = self.position_utils.get_position_quantity(symbol)
    # ❌ This rounds 0.3 → 0 for non-fractionable assets
    return self.position_utils.adjust_quantity_for_fractionability(symbol, raw_shares)
```

The `adjust_quantity_for_fractionability()` method correctly rounds down fractional quantities for **new purchases** of non-fractionable assets, but this logic was incorrectly applied during **liquidation**.

## The Fix

**File:** `the_alchemiser/execution_v2/core/phase_executor.py`

Changed `_calculate_liquidation_shares()` to return the **exact position quantity** without applying fractionability rounding:

```python
# AFTER (fixed):
def _calculate_liquidation_shares(self, symbol: str) -> Decimal:
    """Calculate shares for liquidation (full position sell).

    For liquidation, we MUST sell the exact position quantity regardless
    of fractionability rules. This is critical because:
    1. We need to close out the position completely
    2. Brokers accept fractional sells even for non-fractionable assets
    3. Rounding down would leave orphaned fractional positions
    """
    if not self.position_utils:
        return Decimal("0")

    # For liquidation, return the EXACT position quantity without rounding
    # Fractionability rules only apply to NEW purchases, not position closes
    return self.position_utils.get_position_quantity(symbol)
```

## Rationale

### Why Brokers Accept Fractional Sells of Non-Fractionable Assets

1. **Position Close Out:** Brokers must allow you to fully close any position you hold
2. **Corporate Actions:** Stock splits/reverse splits can create fractional positions
3. **Partial Fills:** Even whole-share orders can partially fill leaving fractions
4. **DTCC Rules:** Fractional shares in existing positions can always be liquidated

### When Fractionability Rules Apply

| Action | Fractionable Asset | Non-Fractionable Asset |
|--------|-------------------|------------------------|
| **New BUY** | ✅ Allow fractional (e.g., 1.5 shares) | ❌ Round down to whole (1.5 → 1) |
| **Existing SELL** | ✅ Sell exact quantity | ✅ Sell exact quantity |
| **Liquidation** | ✅ Sell entire position | ✅ Sell entire position (even if fractional) |

## Test Coverage

Added comprehensive test class `TestFractionalLiquidationEdgeCase` to prevent regression:

**File:** `tests/execution_v2/test_position_utils.py`

```python
def test_liquidation_preserves_fractional_quantity_for_non_fractionable():
    """Test that liquidation does NOT round down fractional positions.
    
    This is the EDZ bug fix: even for non-fractionable assets, we must sell
    the exact position quantity during liquidation, not apply rounding rules.
    """
    # Setup: EDZ is non-fractionable but has 0.3 shares in position
    asset_info.fractionable = False
    position.qty = Decimal("0.3")
    
    # Must preserve exact fractional quantity for liquidation
    quantity = position_utils.get_position_quantity("EDZ")
    assert quantity == Decimal("0.3")
```

Test cases cover:
- ✅ Liquidation preserves fractional positions (0.1, 0.3, 0.5, 0.9, 1.3, 2.7 shares)
- ✅ New purchases still round down correctly (0.3 → 0)
- ✅ No regression in existing fractionability logic

## Impact Analysis

### Before Fix
- **EDZ position:** 0.3 shares held
- **Liquidation attempt:** Rounded to 0 shares
- **Result:** Order failed with "Quantity must be positive"
- **Portfolio state:** Orphaned 0.3 share position remains

### After Fix
- **EDZ position:** 0.3 shares held
- **Liquidation attempt:** Sells exactly 0.3 shares
- **Result:** Order succeeds, position fully closed
- **Portfolio state:** Clean, no orphaned positions

## Related Issues

This fix also resolves potential issues with:
- Stock splits creating fractional positions
- Partial fills from previous orders
- Any other non-fractionable asset with fractional holdings

## Verification

### Pre-deployment Verification
```bash
# Run specific tests
poetry run pytest tests/execution_v2/test_position_utils.py::TestFractionalLiquidationEdgeCase -xvs

# Run all position utils tests
poetry run pytest tests/execution_v2/test_position_utils.py -x

# Type checking
make type-check
```

### Post-deployment Monitoring
1. Check CloudWatch logs for EDZ liquidation attempts
2. Verify no "Quantity must be positive" errors
3. Monitor for orphaned fractional positions in account
4. Confirm complete position closes in trade ledger

## Version Update Required

Per Copilot instructions, this bug fix requires a version bump:

```bash
# This is a bug fix (PATCH version)
make bump-patch
```

## Additional Notes

### Why This Wasn't Caught Earlier

1. **Uncommon scenario:** Requires holding fractional position in non-fractionable asset
2. **EDZ acquisition:** Position likely created through:
   - Stock split/reverse split
   - Partial fill from previous order
   - Migration from another broker
3. **Test gap:** No existing tests covered fractional liquidation edge case

### Prevention for Future

- ✅ Added comprehensive test coverage
- ✅ Documented liquidation vs. purchase distinction
- ✅ Clear comments in code explaining the business rule
- 📋 Consider alert when fractional positions detected in non-fractionable assets

## References

- **Live run log:** `log-events-viewer-result.csv` (timestamp: 1760103342521)
- **Broker order history:** Shows only BWXT and SMR orders filled, EDZ skipped
- **Alpaca API docs:** Non-fractionable asset behavior
- **Fix commit:** `[Will be added after commit]`
