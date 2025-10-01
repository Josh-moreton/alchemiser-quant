# Alpaca API Error Response Mapping

## Overview

This document describes how The Alchemiser handles Alpaca API error responses, particularly for order cancellation scenarios.

## Terminal State Detection

When attempting to cancel an order, Alpaca may return errors indicating the order is already in a terminal state. These are NOT actual errors - they indicate the order has already completed or been terminated.

### Alpaca Error Code 42210000

The primary error code for terminal states is `42210000`, which Alpaca returns when attempting to modify or cancel an order that has already reached a final state.

Example error message:
```json
{"code":42210000,"message":"order is already in \"filled\" state"}
```

### Terminal States

The following order states are considered terminal (order is complete and cannot be modified):

1. **filled** - Order successfully executed
2. **canceled/cancelled** - Order was cancelled (US/UK spelling supported)
3. **rejected** - Order was rejected by the broker
4. **expired** - Order expired before execution

## Implementation

### Error Detection

The `AlpacaErrorHandler.is_order_already_in_terminal_state()` method detects terminal state errors:

```python
from the_alchemiser.shared.utils.alpaca_error_handler import AlpacaErrorHandler

try:
    trading_client.cancel_order_by_id(order_id)
except Exception as e:
    is_terminal, state = AlpacaErrorHandler.is_order_already_in_terminal_state(e)
    if is_terminal:
        # Order is already complete - this is success, not failure
        print(f"Order already in terminal state: {state}")
```

### Structured Cancellation Results

The `cancel_order()` method returns `OrderCancellationResult`:

```python
result = alpaca_manager.cancel_order(order_id)

if result.success:
    if result.error and result.error.startswith("already_"):
        # Order was already in terminal state
        terminal_state = result.error.replace("already_", "")
        print(f"Order already {terminal_state}")
    else:
        # Order successfully cancelled
        print("Order cancelled")
else:
    # Genuine cancellation failure
    print(f"Cancellation failed: {result.error}")
```

## Use Cases

### Preventing Duplicate Orders

The primary use case is preventing duplicate order placement when:

1. System attempts to re-peg an unfilled limit order
2. Order fills while cancellation is in progress
3. System would previously attempt to place a duplicate order
4. With this fix, system detects the filled state and stops

### Log Example

**Before fix:**
```
2025-10-01 16:59:58,958 - ERROR - Failed to cancel order: {"code":42210000,"message":"order is already in \"filled\" state"}
2025-10-01 16:59:58,959 - WARNING - ⚠️ Failed to cancel order; attempting market order anyway
```

**After fix:**
```
2025-10-01 16:59:58,958 - INFO - Order already in terminal state 'filled' - treating as successful cancellation
2025-10-01 16:59:58,959 - INFO - ✅ Order already in terminal state 'filled' - no market escalation needed
```

## Testing

See test files:
- `tests/shared/test_alpaca_error_handler_terminal_states.py` - Error detection tests
- `tests/shared/test_order_cancellation_terminal_states.py` - Cancellation result tests

## Future Enhancements

Future Alpaca error responses should be mapped using similar patterns:

1. Add detection method to `AlpacaErrorHandler`
2. Update relevant service methods to check for specific error conditions
3. Return structured results with clear success/failure semantics
4. Add tests validating the error detection logic

## References

- Issue: "See this buy failure that we must handle better"
- Alpaca API Documentation: https://docs.alpaca.markets/
- Error Code 42210000: Order state modification errors
