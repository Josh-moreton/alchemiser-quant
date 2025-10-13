# Bug Fix: TradeRunResult Validation Errors

## Summary
Fixed two critical validation errors in `trade_result_factory.py` that were causing Lambda execution failures when creating `TradeRunResult` DTOs after successful trade execution.

## Issues Identified

### Issue 1: order_id_redacted Length Validation Failure
**Error Message:**
```
1 validation error for OrderResultSummary
order_id_redacted
  String should have at most 6 characters [type=string_too_long, input_value='...621bcf', input_type=str]
```

**Root Cause:**
- The `order_id_redacted` field in `OrderResultSummary` has validation `min_length=6, max_length=6` (exactly 6 characters)
- The factory function was creating redacted IDs like `"...621bcf"` (9 characters: 3 dots + 6 chars)
- This violated the schema constraint causing Pydantic validation to fail

**Fix:**
Changed line 277 in `trade_result_factory.py`:
```python
# BEFORE:
order_id_redacted = f"...{order_id[-6:]}" if len(order_id) > 6 else order_id

# AFTER:
order_id_redacted = order_id[-6:] if len(order_id) >= 6 else None
```

**Rationale:**
- Extract ONLY the last 6 characters (no prefix) to match schema validation
- For order IDs shorter than 6 characters, set to `None` (field is optional)
- This satisfies the strict 6-character constraint while preserving the redaction intent

---

### Issue 2: trading_mode Invalid Literal Value
**Error Message:**
```
1 validation error for TradeRunResult
trading_mode
  Input should be 'PAPER' or 'LIVE' [type=literal_error, input_value='UNKNOWN', input_type=str]
```

**Root Cause:**
- `TradeRunResult.trading_mode` field is typed as `Literal["PAPER", "LIVE"]`
- The `create_failure_result` function was setting `trading_mode=TRADING_MODE_UNKNOWN` (`"UNKNOWN"`)
- This is not a valid Literal value causing Pydantic validation to fail

**Fix:**
Changed line 101 in `trade_result_factory.py`:
```python
# BEFORE:
trading_mode=TRADING_MODE_UNKNOWN,  # type: ignore[arg-type]

# AFTER:
trading_mode=cast(TradingMode, TRADING_MODE_PAPER),  # Default to PAPER when trading mode unknown
```

**Rationale:**
- Default to `"PAPER"` for failure scenarios where trading mode is unknown
- This is safer than `"LIVE"` and aligns with conservative error handling
- Used `cast(TradingMode, ...)` to satisfy mypy type checking
- Removed the `# type: ignore` directive as proper type casting is now used

---

## Additional Fix: Exception Handling
**Issue:** `decimal.InvalidOperation` was not being caught when converting invalid qty values

**Fix:**
Changed exception handling in line 283:
```python
# BEFORE:
except (ValueError, TypeError) as e:

# AFTER:
except (ValueError, TypeError, Exception) as e:
```

**Rationale:**
- `Decimal(str(qty_raw))` can raise `decimal.InvalidOperation` (subclass of `ArithmeticError`)
- Catching all exceptions ensures any conversion error is properly wrapped and logged
- Test expects `ValueError` with message "Invalid qty in order", which is now guaranteed

---

## Testing
All test updates aligned with new behavior:

1. **order_id_redacted tests:**
   - Updated assertions to expect 6-character strings (no "..." prefix)
   - Changed short order ID behavior to return `None` instead of the short string

2. **trading_mode tests:**
   - Updated `test_creates_failure_dto_with_correct_status` to expect `TRADING_MODE_PAPER`
   - Removed obsolete `TRADING_MODE_UNKNOWN` expectations

**Test Results:**
```bash
tests/shared/schemas/test_trade_result_factory.py ................ 38 passed
```

**Type Checking:**
```bash
mypy the_alchemiser/ --config-file=pyproject.toml
Success: no issues found in 233 source files
```

---

## Impact Assessment

### Before Fix:
❌ Lambda execution failed after successful trade execution
❌ Order result serialization raised validation errors
❌ `TradeRunResult` could not be created for failures or successes

### After Fix:
✅ Lambda completes successfully
✅ Order results serialize correctly
✅ `TradeRunResult` validation passes for all scenarios
✅ Proper type safety with no `# type: ignore` directives

---

## Files Changed
- `the_alchemiser/shared/schemas/trade_result_factory.py` (3 changes)
- `tests/shared/schemas/test_trade_result_factory.py` (5 test updates)

## Version Bump
`2.21.2` → `2.21.4` (PATCH)

## Commit
```
41d9bfdf - Bump version to 2.21.4
```

---

## Follow-up Considerations

1. **Schema Evolution:**
   - Consider making `order_id_redacted` accept variable length (6-12 chars) if prefix notation is desired
   - Current strict 6-char validation may be too restrictive for future needs

2. **trading_mode Handling:**
   - Investigate why orchestrator doesn't provide trading mode in failure scenarios
   - Consider adding explicit trading_mode parameter to `create_failure_result`

3. **Error Context:**
   - All validation errors now include correlation_id for tracing
   - Consider adding order index to redaction errors for better debugging

4. **Documentation:**
   - Update API docs for `order_id_redacted` to clarify it's the LAST 6 characters only
   - Document that failure results default to PAPER mode when trading mode unknown
