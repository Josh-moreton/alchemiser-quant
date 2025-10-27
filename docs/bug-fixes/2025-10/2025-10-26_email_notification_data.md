# Bug Fix: Missing Data in Email Notifications

**Status:** ✅ Fixed
**Version:** 2.23.4
**Date:** 2025-10-15
**Severity:** Medium
**Category:** Notifications / User Experience

---

## Summary

Email notifications for trading execution were displaying incomplete information:
- **Order Execution Details** table showed only symbols, missing action, quantity, and status
- **Portfolio Rebalancing Plan** sometimes showed "No target portfolio data available"

## Root Causes

### Issue 1: Order Field Name Mismatch

**Problem:** The `OrderResult` model serialized orders with field names that didn't match what the email template expected.

- **OrderResult produces:** `action` (BUY/SELL), `shares` (Decimal), `success` (bool)
- **Template expected:** `side` (buy/sell), `qty` (float), `status` (filled/failed)

**Code Path:**
1. `TradingExecutionHandler._emit_trade_executed_event()` serializes orders via `order.model_dump()`
2. Data flows through `TradeExecuted` event → `EventDrivenOrchestrator` → `TradingNotificationRequested`
3. `NotificationService` creates `_ExecutionResultAdapter` and passes to template
4. Template `build_orders_table_neutral()` tries to access `order.get("side")`, `order.get("qty")`, etc.
5. All these lookups return `None` or defaults, resulting in empty cells

### Issue 2: Potential Data Flow Issue

The `consolidated_portfolio` data was being passed through the workflow but might not have been properly exposed by the adapter for template consumption.

## Solution

### Fix 1: Update Email Template to Use Correct Field Names

**File:** `the_alchemiser/shared/notifications/templates/portfolio.py`

Updated `build_orders_table_neutral()` to use the actual `OrderResult` field names:
- `action` instead of `side`
- `shares` instead of `qty`
- `success` instead of `status`

Added new helper method `_format_order_status_from_success()` to convert boolean `success` field to display string.

**Benefits:**
- No data transformation needed (cleaner, more efficient)
- Direct mapping from domain model to template
- Type-safe with proper field expectations

### Fix 2: Add Debug Logging

**File:** `the_alchemiser/notifications_v2/service.py`

Added debug logging in `_ExecutionResultAdapter.__init__()` to track:
- Whether `consolidated_portfolio` is present
- Whether `orders_executed` is present
- Available keys in `execution_data`

This will help diagnose any remaining data flow issues in production logs.

## Technical Details

### OrderResult Model Schema

```python
class OrderResult(BaseModel):
    symbol: str
    action: Literal["BUY", "SELL"]
    shares: Decimal
    price: Decimal | None
    success: bool
    order_id: str | None
    timestamp: datetime
    # ... other fields
```

### Template Field Mapping

| Model Field | Type | Template Usage |
|------------|------|----------------|
| `symbol` | str | Display as-is |
| `action` | "BUY"/"SELL" | Display with color coding |
| `shares` | Decimal | Format as float with decimals |
| `success` | bool | Convert to "filled"/"failed" |
| `price` | Decimal\|None | Format as currency if present |

## Testing

### Validation Steps

1. ✅ Type checking passes (`make type-check`)
2. ✅ Formatting passes (`make format`)
3. ✅ No new linting errors
4. ✅ Architecture boundaries respected

### Manual Testing Required

Deploy to staging/paper and verify:
1. Order Execution Details table shows all columns:
   - Action (BUY/SELL with color)
   - Symbol
   - Quantity (with decimal precision)
   - Status (filled/failed with color)
2. Portfolio Rebalancing Plan displays target allocations
3. Debug logs appear in CloudWatch showing data flow

## Impact

- **User Experience:** Email reports now show complete trade execution details
- **Operations:** Better visibility into what trades were executed
- **Debugging:** Added logging helps diagnose future data flow issues

## Files Modified

1. `the_alchemiser/shared/notifications/templates/portfolio.py`
   - Updated `build_orders_table_neutral()` to use correct field names
   - Added `_format_order_status_from_success()` helper
   - Added `_get_order_action_from_field()` helper

2. `the_alchemiser/notifications_v2/service.py`
   - Added debug logging in `_ExecutionResultAdapter.__init__()`

3. `the_alchemiser/execution_v2/handlers/trading_execution_handler.py`
   - Removed unnecessary data transformation (reverted to direct `model_dump()`)

## Lessons Learned

1. **Schema Alignment:** Templates should consume domain model fields directly when possible
2. **Type Safety:** Field name mismatches are easy to introduce; consider TypedDict protocols
3. **Logging:** Early debug logging at data flow boundaries helps catch issues
4. **Testing:** Need integration tests that verify end-to-end email rendering

## Follow-up Tasks

- [ ] Add integration test for email notification rendering
- [ ] Consider using TypedDict/Protocol for template data contracts
- [ ] Monitor CloudWatch logs for debug output after next deployment
- [ ] Verify consolidated_portfolio data flows correctly in production

## References

- Original issue: Email screenshots showing missing data
- CloudWatch logs: `log-events-viewer-result (5).csv`
- Copilot instructions: `.github/copilot-instructions.md` (version management)
