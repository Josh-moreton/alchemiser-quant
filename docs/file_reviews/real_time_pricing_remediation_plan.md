# Remediation Plan for real_time_pricing.py

**Based on audit dated**: 2025-01-05  
**Target file**: `the_alchemiser/shared/services/real_time_pricing.py`  
**Current version**: 2.16.2  
**Overall grade**: B- (78/100)

---

## Executive Summary

The real_time_pricing.py module is a well-architected orchestrator for WebSocket-based market data streaming. It demonstrates good separation of concerns through delegation to specialized components. However, **critical security and correctness issues** must be addressed before production use.

**Key Strengths**:
- Clean separation of concerns via component delegation
- Proper async/await patterns for non-blocking I/O
- Comprehensive docstrings
- Good type hint coverage

**Key Weaknesses**:
- Secret exposure through public properties (SECURITY RISK)
- Generic exception handling (CORRECTNESS RISK)
- Decimal/float mixing (FINANCIAL PRECISION RISK)
- Missing observability metadata (TRACEABILITY RISK)

---

## Priority 1: Critical Fixes (MUST FIX - Security & Correctness)

### 1.1 Remove Secret Exposure (Lines 164-177)

**Risk**: API credentials could leak in logs, error messages, or debugging tools.

**Current code**:
```python
@property
def api_key(self) -> str:
    """Get API key."""
    return self._api_key  # ❌ CRITICAL: Exposes secret

@property
def secret_key(self) -> str:
    """Get secret key."""
    return self._secret_key  # ❌ CRITICAL: Exposes secret
```

**Solution**:
```python
# Option 1: Remove properties entirely (RECOMMENDED)
# Delete lines 164-177

# Option 2: If properties needed, redact values
@property
def api_key_redacted(self) -> str:
    """Get redacted API key for logging."""
    if not self._api_key:
        return "<not set>"
    return f"{self._api_key[:4]}...{self._api_key[-4:]}"
```

**Effort**: 30 minutes  
**Impact**: HIGH - Prevents credential leaks

---

### 1.2 Replace Generic Exception Handling (Lines 216, 236, 274, 304)

**Risk**: Broad exception catching masks real errors and violates guardrails.

**Current code**:
```python
except Exception as e:
    self.logger.error(f"Error starting real-time pricing service: {e}")
    return False
```

**Solution**:
```python
from the_alchemiser.shared.errors.exceptions import (
    StreamingError,
    WebSocketError,
    ConfigurationError,
)

# In start() method:
except (ConnectionError, OSError, WebSocketError) as e:
    self.logger.error(
        "Failed to start real-time pricing service",
        extra={"error_type": type(e).__name__, "error_details": str(e)},
    )
    raise StreamingError(f"Failed to start stream: {e}") from e
except ConfigurationError:
    # Re-raise config errors
    raise
except Exception as e:
    # Unknown error - log and raise
    self.logger.exception("Unexpected error in start()")
    raise StreamingError(f"Unexpected error: {e}") from e
```

**Apply to**: Lines 216-218, 236-237, 274-275, 304-310

**Effort**: 1-2 hours  
**Impact**: HIGH - Proper error classification and handling

---

## Priority 2: High Severity Fixes (SHOULD FIX - Precision & Traceability)

### 2.1 Fix Decimal/Float Mixing (Lines 353, 367)

**Risk**: Violates "never mix Decimal and float" guardrail for financial data.

**Current code**:
```python
def get_real_time_price(self, symbol: str) -> Decimal | float | None:
    """Get price - can be Decimal or float."""
    return self._price_store.get_real_time_price(symbol)

def get_bid_ask_spread(self, symbol: str) -> tuple[Decimal | float, Decimal | float] | None:
    """Get spread - can be Decimal or float."""
    return self._price_store.get_bid_ask_spread(symbol)
```

**Solution**:
```python
def get_real_time_price(self, symbol: str) -> Decimal | None:
    """Get price as Decimal for financial precision.
    
    Returns:
        Current price as Decimal or None if not available
        
    Note:
        Always returns Decimal to ensure consistent numerical precision
        for financial calculations.
    """
    price = self._price_store.get_real_time_price(symbol)
    if price is None:
        return None
    # Convert float to Decimal via string to avoid precision loss
    return Decimal(str(price)) if isinstance(price, float) else price

def get_bid_ask_spread(self, symbol: str) -> tuple[Decimal, Decimal] | None:
    """Get bid/ask spread as Decimal tuple.
    
    Returns:
        Tuple of (bid, ask) as Decimal, or None if not available
    """
    spread = self._price_store.get_bid_ask_spread(symbol)
    if spread is None:
        return None
    bid, ask = spread
    # Ensure both are Decimal
    bid_decimal = Decimal(str(bid)) if isinstance(bid, float) else bid
    ask_decimal = Decimal(str(ask)) if isinstance(ask, float) else ask
    return (bid_decimal, ask_decimal)
```

**Effort**: 1 hour  
**Impact**: HIGH - Ensures financial precision

---

### 2.2 Add Correlation ID Support (Throughout)

**Risk**: No traceability for debugging distributed systems.

**Solution**:
```python
import uuid

class RealTimePricingService:
    def __init__(
        self,
        api_key: str | None = None,
        secret_key: str | None = None,
        *,
        paper_trading: bool = True,
        max_symbols: int = 30,
        correlation_id: str | None = None,  # NEW
    ) -> None:
        """Initialize with optional correlation ID for traceability."""
        # ... existing code ...
        
        # Correlation ID for traceability
        self._correlation_id = correlation_id or str(uuid.uuid4())
        
        self.logger.info(
            "Real-time pricing service initialized",
            extra={
                "correlation_id": self._correlation_id,
                "mode": "paper" if paper_trading else "live",
            },
        )
    
    @property
    def correlation_id(self) -> str:
        """Get correlation ID for this service instance."""
        return self._correlation_id
    
    # Update all log calls to include correlation_id in extra dict
    def start(self) -> bool:
        try:
            # ... existing code ...
            self.logger.info(
                "Real-time pricing service started successfully",
                extra={"correlation_id": self._correlation_id},
            )
        except StreamingError as e:
            self.logger.error(
                "Failed to start service",
                extra={"correlation_id": self._correlation_id, "error": str(e)},
            )
```

**Effort**: 2 hours  
**Impact**: HIGH - Enables distributed tracing

---

### 2.3 Extract Magic Number (Line 507)

**Risk**: Hardcoded priority offset reduces maintainability.

**Solution**:
```python
# At module level (after imports, before class):
# Priority offset for high-priority subscriptions (e.g., order placement)
HIGH_PRIORITY_OFFSET = 1000

class RealTimePricingService:
    # ... existing code ...
    
    def subscribe_for_order_placement(self, symbol: str) -> None:
        """Subscribe with high priority for order placement.
        
        Uses HIGH_PRIORITY_OFFSET to ensure this subscription takes
        precedence over regular monitoring subscriptions.
        """
        self.subscribe_symbol(symbol, priority=time.time() + HIGH_PRIORITY_OFFSET)
        self.logger.info(
            f"Subscribed {symbol} for order placement",
            extra={"priority_offset": HIGH_PRIORITY_OFFSET},
        )
```

**Effort**: 15 minutes  
**Impact**: MEDIUM - Better maintainability

---

## Priority 3: Medium Severity Fixes (RECOMMENDED)

### 3.1 Move Inline Imports to Module Level (Lines 123-125, 409)

**Current**:
```python
def __init__(self, ...):
    if not api_key or not secret_key:
        import os  # ❌ Inline import
        from dotenv import load_dotenv  # ❌ Inline import
```

**Solution**:
```python
# At top of file with other imports:
import os
from dotenv import load_dotenv

# ... later in __init__:
def __init__(self, ...):
    if not api_key or not secret_key:
        load_dotenv()  # ✅ No inline import
        api_key = api_key or os.getenv("ALPACA_KEY")
```

**Effort**: 15 minutes  
**Impact**: MEDIUM - Code clarity

---

### 3.2 Add Thread Safety to Stats (Lines 272, 298)

**Risk**: Race conditions on concurrent stat updates.

**Solution**:
```python
class RealTimePricingService:
    def __init__(self, ...):
        # ... existing code ...
        
        # Statistics tracking with thread safety
        self._stats: dict[str, int] = {
            "quotes_received": 0,
            "trades_received": 0,
        }
        self._stats_lock = threading.Lock()  # NEW
        
    async def _on_quote(self, data: AlpacaQuoteData) -> None:
        try:
            # ... existing processing ...
            
            # Update stats with lock
            with self._stats_lock:
                self._stats["quotes_received"] += 1
        except Exception as e:
            await self._data_processor.handle_quote_error(e)
```

**Effort**: 30 minutes  
**Impact**: MEDIUM - Correctness under load

---

### 3.3 Improve Task Cancellation (Lines 228-232)

**Risk**: Tasks may not complete cleanup, causing resource leaks.

**Solution**:
```python
async def stop(self) -> None:
    """Stop the real-time pricing service."""
    try:
        if self._stream_manager:
            self._stream_manager.stop()
        
        self._price_store.stop_cleanup()
        
        # Cancel and await background tasks
        if self._background_tasks:
            for task in self._background_tasks:
                if not task.done():
                    task.cancel()
            
            # Wait for all tasks to complete with timeout
            await asyncio.wait_for(
                asyncio.gather(*self._background_tasks, return_exceptions=True),
                timeout=5.0,
            )
            self._background_tasks.clear()
        
        self.logger.info("Real-time pricing service stopped")
        
    except asyncio.TimeoutError:
        self.logger.warning("Some background tasks did not complete within timeout")
    except Exception as e:
        self.logger.error(f"Error stopping service: {e}")
```

**Effort**: 30 minutes  
**Impact**: MEDIUM - Resource cleanup

---

## Priority 4: Low Severity Improvements (OPTIONAL)

### 4.1 Add Deprecation Warning (Line 314)

```python
import warnings

def get_real_time_quote(self, symbol: str) -> RealTimeQuote | None:
    """Get real-time quote (DEPRECATED).
    
    Warning:
        This method is deprecated. Use get_quote_data() for new code.
    """
    warnings.warn(
        "get_real_time_quote() is deprecated, use get_quote_data()",
        DeprecationWarning,
        stacklevel=2,
    )
    return self._price_store.get_real_time_quote(symbol)
```

**Effort**: 10 minutes  
**Impact**: LOW - Better API migration

---

### 4.2 Extract Complex Lambdas (Lines 198-200, 206-208)

```python
class RealTimePricingService:
    # ... existing code ...
    
    def _get_subscribed_symbols_list(self) -> list[str]:
        """Get list of currently subscribed symbols."""
        return list(self._subscription_manager.get_subscribed_symbols())
    
    def _is_stream_connected(self) -> bool:
        """Check if stream manager is connected."""
        return self._stream_manager.is_connected() if self._stream_manager else False
    
    def start(self) -> bool:
        try:
            # ... existing code ...
            
            result = self._stream_manager.start(
                get_symbols_callback=self._get_subscribed_symbols_list  # ✅ Cleaner
            )
            
            if result:
                self._price_store.start_cleanup(
                    is_connected_callback=self._is_stream_connected  # ✅ Cleaner
                )
```

**Effort**: 20 minutes  
**Impact**: LOW - Readability

---

## Testing Requirements

After implementing fixes, ensure:

1. **Unit tests** for:
   - Error handling with typed exceptions
   - Decimal conversion logic
   - Thread-safe stats updates
   - Correlation ID propagation
   
2. **Integration tests** for:
   - WebSocket connection handling
   - Concurrent quote/trade processing
   - Service lifecycle (start/stop)
   
3. **Security tests** for:
   - Verify secrets don't leak in logs
   - Validate error messages don't expose credentials

---

## Implementation Timeline

| Priority | Tasks | Effort | Deadline |
|----------|-------|--------|----------|
| P1 Critical | 1.1 + 1.2 | 2-3 hours | Immediate (before next deploy) |
| P2 High | 2.1 + 2.2 + 2.3 | 4-5 hours | This sprint |
| P3 Medium | 3.1 + 3.2 + 3.3 | 1-2 hours | This sprint |
| P4 Low | 4.1 + 4.2 | 30 min | Next sprint |
| Testing | All priorities | 2-3 hours | With each priority |
| **TOTAL** | | **9-13 hours** | 1-2 sprints |

---

## Success Criteria

- [ ] All critical security issues resolved (no secret exposure)
- [ ] All exceptions are typed from shared.errors
- [ ] Return types consistently use Decimal for financial data
- [ ] Correlation ID present in all log statements
- [ ] Thread-safe operations verified under load
- [ ] Test coverage ≥ 85% for modified code
- [ ] Type checking passes: `poetry run mypy the_alchemiser/`
- [ ] All tests pass: `poetry run pytest`
- [ ] Security scan passes: `poetry run bandit -r the_alchemiser/`

---

## Next Steps

1. **Review this plan** with team lead
2. **Create tickets** for P1 and P2 items
3. **Implement fixes** iteratively with tests
4. **Update version**: 2.16.3 (PATCH after P1), 2.17.0 (MINOR after P2)
5. **Schedule follow-up audit** after P3 implementation

---

**Document version**: 1.0  
**Last updated**: 2025-01-05  
**Author**: GitHub Copilot Workspace Agent
