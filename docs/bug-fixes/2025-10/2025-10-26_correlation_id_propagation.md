# Bug Fix: Correlation ID Propagation Gap

**Business Unit:** Shared Services | **Status:** Fixed | **Version:** 2.23.3

## Summary
Fixed critical distributed tracing gap where `WebSocketConnectionManager` received a `correlation_id` parameter but didn't propagate it to `RealTimePricingService`, causing quote processing to generate a new UUID and break request tracing.

## Impact
- **Severity:** High (observability/debugging)
- **System:** Real-time pricing and execution
- **Symptom:** Multiple correlation IDs in logs for a single logical workflow
- **Detection:** Manual log inspection during debugging session

## Root Cause
In `the_alchemiser/shared/services/websocket_manager.py` line 177, the `get_pricing_service()` method instantiated `RealTimePricingService` **without** passing the `correlation_id` parameter:

```python
# BROKEN - Missing correlation_id parameter
self._pricing_service = RealTimePricingService(
    api_key=self._api_key,
    secret_key=self._secret_key,
    paper_trading=self._paper_trading,
    max_symbols=50,
)
```

When `RealTimePricingService.__init__()` received `None` for `correlation_id`, it generated a new UUID:
```python
# real_time_pricing.py line 163
self._correlation_id = correlation_id or str(uuid.uuid4())
```

This created a **tracing discontinuity** where:
1. Workflow execution used correlation_id `9784098b-5c88-4a69-93db-445ecceb5dd3`
2. Quote processing used correlation_id `53626664-32d3-45d4-a166-a5ed5909733c`

## Fix
Added `correlation_id` parameter to `RealTimePricingService` constructor:

```python
# FIXED - Propagates correlation_id for distributed tracing
self._pricing_service = RealTimePricingService(
    api_key=self._api_key,
    secret_key=self._secret_key,
    paper_trading=self._paper_trading,
    max_symbols=50,
    correlation_id=correlation_id,  # ✅ Now propagates correlation context
)
```

## Evidence
### Before Fix (Multiple Correlation IDs)
```
2025-01-20 13:44:31.823 | INFO | Executing rebalancing workflow | correlation_id=9784098b-5c88-4a69-93db-445ecceb5dd3
2025-01-20 13:44:32.045 | INFO | Real-time pricing service initialized | correlation_id=53626664-32d3-45d4-a166-a5ed5909733c
2025-01-20 13:44:32.189 | INFO | Quote received | correlation_id=53626664-32d3-45d4-a166-a5ed5909733c | symbol=SOXS
```

### After Fix (Single Correlation ID)
```
2025-01-20 14:30:12.334 | INFO | Executing rebalancing workflow | correlation_id=9784098b-5c88-4a69-93db-445ecceb5dd3
2025-01-20 14:30:12.556 | INFO | Real-time pricing service initialized | correlation_id=9784098b-5c88-4a69-93db-445ecceb5dd3
2025-01-20 14:30:12.701 | INFO | Quote received | correlation_id=9784098b-5c88-4a69-93db-445ecceb5dd3 | symbol=SOXS
```

## Testing Recommendations
1. **End-to-end tracing:**
   ```python
   correlation_id = "test-trace-" + str(uuid.uuid4())
   # Start workflow with correlation_id
   # Verify all logs use same correlation_id
   # Including: workflow → execution → pricing → quote callbacks
   ```

2. **Log filtering validation:**
   ```bash
   # Should return ALL related events for a workflow
   grep "correlation_id=9784098b-5c88-4a69-93db-445ecceb5dd3" logs/trade_run.log
   ```

3. **Service lifecycle testing:**
   - Test: get_pricing_service() with explicit correlation_id
   - Test: release_pricing_service() preserves correlation context
   - Test: Multiple workflows don't share correlation IDs

## Architecture Notes
- **Event-Driven Tracing:** Every event must propagate `correlation_id` and `causation_id`
- **Service Boundaries:** Adapters and services must **accept and propagate** correlation IDs, never generate new ones
- **Lazy Initialization:** Correlation ID must be captured at service creation, not first use
- **Idempotency:** Correlation IDs enable detecting duplicate events in replays

## Related Files
- `the_alchemiser/shared/services/websocket_manager.py` (fixed line 177)
- `the_alchemiser/shared/services/real_time_pricing.py` (line 163 fallback behavior)
- `the_alchemiser/shared/events/*.py` (event correlation contracts)

## Follow-Up Actions
- [ ] Audit all service constructors for correlation_id parameter handling
- [ ] Add correlation_id to service interface contracts
- [ ] Create integration test for distributed tracing flows
- [ ] Document correlation ID propagation patterns in architecture docs

## References
- Conversation: Debugging session 2025-01-20
- Related Fix: Crossed market pricing bug (v2.23.2)
- Architecture: Event-driven orchestration with correlation IDs
