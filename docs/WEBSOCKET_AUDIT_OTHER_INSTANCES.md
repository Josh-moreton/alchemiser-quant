# WebSocket Instances Audit - Lazy Connection Check

**Date:** 8 October 2025
**Related Fix:** `WEBSOCKET_LAZY_CONNECTION_FIX.md`

---

## Purpose

After fixing the lazy connection issue in `RealTimePricingService` (StockDataStream), this document audits all other WebSocket instances to verify they don't have the same problem.

---

## WebSocket Instances in Codebase

### 1. ✅ StockDataStream (RealTimePricingService) - FIXED

**Location:** `the_alchemiser/shared/services/real_time_pricing.py`

**Purpose:** Real-time market data (quotes, trades) for pricing

**Status:** ✅ **FIXED** - Lazy connection implemented

**How it works:**
```python
# Creation (no connection yet)
service = RealTimePricingService(...)

# Add subscriptions
service.subscribe_symbols_bulk(["SPY", "QQQ"])

# Auto-starts on first subscription
# → Checks is_connected() → False → Calls start() → Connects with symbols
```

**Why it needed fixing:**
- Requires symbols BEFORE connection
- Was connecting eagerly with no symbols → timeout

---

### 2. ✅ TradingStream (Order Updates) - NO ISSUE

**Location:** `the_alchemiser/shared/services/websocket_manager.py:236`

**Purpose:** Order execution updates, fill notifications

**Status:** ✅ **No fix needed**

**How it works:**
```python
# websocket_manager.py:261
self._trading_stream = TradingStream(api_key, secret_key, paper=True)

# Subscribe to ALL order updates (no specific symbols needed)
self._trading_stream.subscribe_trade_updates(callback)

# Start immediately in background thread (line 293)
self._trading_stream.run()
```

**Why it doesn't need fixing:**

1. **No symbols required:**
   - Subscribes to ALL order updates for the account
   - Not symbol-specific like StockDataStream
   - No "waiting for symbols" scenario

2. **Different subscription model:**
   ```python
   # TradingStream - account-wide
   subscribe_trade_updates(callback)  # No symbols parameter

   # StockDataStream - symbol-specific
   subscribe_quotes(callback, *symbols)  # Requires symbols list
   ```

3. **Starts in background thread:**
   - No blocking wait for connection in main thread
   - Non-blocking initialization (`daemon=True`)
   - Failures are logged but don't block execution

4. **Connection lifecycle:**
   ```
   TradingStream: Create → Subscribe (all orders) → Run (immediate) ✅
   StockDataStream: Create → Run (no symbols) → Wait → Timeout ❌ (WAS BROKEN)
   ```

**Code Evidence:**
```python
# Line 268: Subscribe to ALL orders (no symbols needed)
self._trading_stream.subscribe_trade_updates(callback)

# Line 293: Start immediately (safe because no symbols needed)
self._trading_stream_thread.start()  # Runs ts.run() in background

# No timeout waiting for symbols - it doesn't need them!
```

---

## Summary Table

| WebSocket Type | Purpose | Requires Symbols? | Connection Timing | Status |
|----------------|---------|-------------------|-------------------|--------|
| **StockDataStream** (Pricing) | Market quotes/trades | ✅ Yes | After subscriptions | ✅ FIXED |
| **TradingStream** (Orders) | Order updates | ❌ No (account-wide) | Immediate | ✅ No issue |

---

## Key Architectural Difference

### StockDataStream (Symbol-Specific)
```python
# REQUIRES symbols before connection
stream = StockDataStream(...)
stream.subscribe_quotes(callback, "SPY", "QQQ", "AAPL")  # Symbols needed
stream.run()  # Connects to symbols
```

**Problem if no symbols:** Waits indefinitely → timeout

---

### TradingStream (Account-Wide)
```python
# NO symbols required - account-level subscription
stream = TradingStream(...)
stream.subscribe_trade_updates(callback)  # No symbols parameter
stream.run()  # Connects to account order feed
```

**No problem:** Always has something to subscribe to (the account itself)

---

## Testing Verification

### Already Tested: TradingStream Works Fine

**Evidence from logs:**
```
2025-10-08T12:08:19.784227Z [info] Creating shared TradingStream service
started trading stream
starting trading websocket connection
2025-10-08T12:08:20.215137Z [info] connected to: BaseURL.TRADING_STREAM_PAPER
```

**Observations:**
1. ✅ Creates without issue
2. ✅ Connects immediately
3. ✅ No timeout errors
4. ✅ Orders process successfully

**Why it works:**
- Starts in background thread (non-blocking)
- No symbols needed (subscribes to account)
- Connection succeeds immediately

---

## Other Stream-Like Components

### Checked: No Other WebSocket Instances

**Search Results:**
```bash
grep -r "WebSocket\|\.run()" the_alchemiser/ --include="*.py"
```

**Found:**
1. ✅ `RealTimePricingService` (StockDataStream) - FIXED
2. ✅ `TradingStream` - No issue (account-wide)
3. ❌ No other WebSocket implementations

**Conclusion:** Only TWO WebSocket types in entire codebase, both reviewed.

---

## Risk Assessment

### StockDataStream (RealTimePricingService)
- **Before fix:** 🔴 HIGH RISK - Always timed out in smart execution
- **After fix:** 🟢 LOW RISK - Lazy connection implemented correctly

### TradingStream
- **Current:** 🟢 LOW RISK - Works as designed
- **Future:** 🟢 NO RISK - Architecture doesn't support symbol-specific subscriptions
- **Reason:** Account-wide subscription model prevents the "no symbols" scenario

---

## Recommendations

### 1. ✅ No Further Fixes Needed

**Rationale:**
- Only 2 WebSocket types exist
- StockDataStream: Fixed with lazy connection
- TradingStream: No issue (different subscription model)

### 2. 📝 Documentation Updates

**Recommended additions:**

#### A. WebSocket Architecture Doc
Add section explaining the two subscription models:

```markdown
## WebSocket Subscription Models

### Symbol-Specific (StockDataStream)
- Requires symbols before connection
- Use lazy connection pattern
- Subscribe → Connect

### Account-Wide (TradingStream)
- No symbols needed
- Can connect immediately
- Connect anytime
```

#### B. Developer Guidelines
```markdown
## Creating New WebSocket Services

If your service is **symbol-specific**:
- ✅ Use lazy connection (like RealTimePricingService)
- ✅ Auto-start on first subscription
- ❌ Don't call start() before adding symbols

If your service is **account-wide**:
- ✅ Can connect immediately (like TradingStream)
- ✅ Start in background thread
- ✅ Non-blocking initialization
```

### 3. 🧪 Add Integration Test

**Test both WebSocket types:**

```python
def test_stock_data_stream_lazy_connection():
    """Verify StockDataStream uses lazy connection."""
    service = RealTimePricingService(...)

    # Should NOT be connected yet
    assert not service.is_connected()

    # Add subscription
    service.subscribe_symbols_bulk(["SPY"])

    # Should auto-start and connect
    time.sleep(2)
    assert service.is_connected()

def test_trading_stream_immediate_connection():
    """Verify TradingStream connects immediately."""
    manager = WebSocketConnectionManager(...)

    # Subscribe to order updates
    result = manager.get_trading_service(callback)

    # Should connect immediately (no symbols needed)
    assert result is True
    time.sleep(2)
    assert manager._trading_ws_connected
```

---

## Conclusion

### ✅ Audit Complete

1. **StockDataStream (Pricing):** ✅ FIXED with lazy connection
2. **TradingStream (Orders):** ✅ No issue (account-wide subscription)
3. **Other WebSockets:** ✅ None exist

### No Further Action Required

The lazy connection fix for `RealTimePricingService` is **sufficient and complete**. No other WebSocket instances have the same problem due to their different subscription architecture.

---

## References

- `WEBSOCKET_LAZY_CONNECTION_FIX.md` - Full fix documentation
- `the_alchemiser/shared/services/websocket_manager.py` - TradingStream implementation
- `the_alchemiser/shared/services/real_time_pricing.py` - StockDataStream implementation

---

**Audit Status:** ✅ COMPLETE
**Action Items:** None - All WebSocket instances reviewed and addressed
