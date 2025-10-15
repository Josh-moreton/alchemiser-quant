# EventBridge JSON Serialization Contract

## Overview

All events published to EventBridge must use JSON-serializable payloads. This document describes the serialization contract and utilities enforced across the codebase.

## Why This Matters

EventBridge requires the `Detail` field to be a JSON string. Python objects like `Decimal`, `datetime`, `Exception`, and Pydantic models with these types cannot be serialized directly by `json.dumps()`. This causes pipeline failures and obscures error logging.

## Serialization Utilities

All JSON serialization must use one of these utilities from `shared/utils/serialization.py`:

### For EventBridge Publishing

```python
from the_alchemiser.shared.utils.serialization import event_to_detail_str

# Convert event to EventBridge Detail string
detail_str = event_to_detail_str(event)
```

### For General JSON Serialization

```python
from the_alchemiser.shared.utils.serialization import safe_json_dumps

# Safely serialize any object to JSON string
json_str = safe_json_dumps(obj, indent=2)
```

### For Error Serialization

```python
from the_alchemiser.shared.utils.serialization import error_to_payload

# Convert exception to JSON-safe dict
error_dict = error_to_payload(exception)
# Returns: {"error_type": "ValueError", "error_message": "error text"}
```

### For Data Sanitization

```python
from the_alchemiser.shared.utils.serialization import json_sanitise

# Recursively convert object to JSON-safe primitives
clean_data = json_sanitise(obj)
```

## Type Conversion Rules

| Python Type | JSON Output | Notes |
|------------|------------|-------|
| `Decimal` | `"123.456"` | String to preserve precision |
| `datetime` | `"2025-10-15T08:13:16.741Z"` | RFC3339 with Z suffix (UTC) |
| `Exception` | `{"error_type": "ValueError", "error_message": "..."}` | Flattened to dict |
| `BaseModel` | `{...}` | Uses `model_dump(mode="json")` |
| `dict[str, Any]` | `{...}` | Keys converted to strings, values recursed |
| `list`, `tuple`, `set` | `[...]` | Converted to list, values recursed |
| `None` | `null` | Preserved |
| Primitives | Same | `str`, `int`, `float`, `bool` unchanged |

## Schema Type Annotations

For Pydantic models in event schemas, use these annotated types from `shared/schemas/types.py`:

```python
from the_alchemiser.shared.schemas.types import (
    DecimalStr,      # Generic Decimal serialized to string
    MoneyDecimal,    # 2 decimal places
    PriceDecimal,    # 2 decimal places  
    WeightDecimal,   # 4 decimal places
    UtcDatetime,     # datetime serialized to RFC3339Z
)

class MyEvent(BaseEvent):
    amount: MoneyDecimal = Field(...)
    timestamp: UtcDatetime = Field(...)
```

These types automatically handle:
- Serialization: `Decimal("100.50")` → `"100.50"`
- Deserialization: `"100.50"` → `Decimal("100.50")`
- Datetime: `datetime(2025, 10, 15, 8, 13, 16, tzinfo=UTC)` → `"2025-10-15T08:13:16Z"`

## Best Practices

### ✅ DO

```python
# Use safe_json_dumps for logging
logger.info("Event data", data=safe_json_dumps(event))

# Use event_to_detail_str for EventBridge
detail_str = event_to_detail_str(event)

# Convert exceptions before adding to events
error_dict = error_to_payload(exception)
event = WorkflowFailed(..., error_details=error_dict)

# Use annotated types in schemas
class MyEvent(BaseEvent):
    price: PriceDecimal = Field(...)
```

### ❌ DON'T

```python
# Don't use raw json.dumps on events or models
json.dumps(event.model_dump())  # ❌ May fail on Decimal/datetime

# Don't put exceptions in events
event = WorkflowFailed(..., error=exception)  # ❌ Not serializable

# Don't use dict[str, Any] with non-JSON types
event = MyEvent(data={"amount": Decimal("100")})  # ❌ Won't serialize correctly
```

## CI Enforcement

The CI pipeline includes a check script (`scripts/check_json_dumps.sh`) that fails if:

1. Raw `json.dumps()` is used in `the_alchemiser/**/*.py`
2. Files are not in the allowlist:
   - `shared/utils/serialization.py` (implementation)
   - `execution_v2/services/trade_ledger.py` (uses `model_dump_json()`)
   - `shared/schemas/strategy_allocation.py` (manual string conversion)

To bypass the check (rare cases), add the file to the allowlist in the script.

## Testing

All event types have JSON contract tests in `tests/shared/events/test_event_json_contract.py` that verify:

1. Events serialize to valid JSON strings
2. JSON strings parse back to valid dicts
3. `Decimal` fields become strings
4. `datetime` fields become RFC3339Z strings
5. Nested structures are correctly converted

Test your own events:

```python
from the_alchemiser.shared.utils.serialization import event_to_detail_str
import json

# Should not raise
detail_str = event_to_detail_str(my_event)
parsed = json.loads(detail_str)
```

## Migration Guide

### Updating Existing Code

1. **Replace direct `json.dumps` on events:**
   ```python
   # Before
   detail = json.dumps(event.model_dump())
   
   # After
   detail = event_to_detail_str(event)
   ```

2. **Replace `json.dumps` in logging:**
   ```python
   # Before
   logger.info("Data", data=json.dumps(some_dict))
   
   # After
   logger.info("Data", data=safe_json_dumps(some_dict))
   ```

3. **Convert exceptions before adding to events:**
   ```python
   # Before
   event = WorkflowFailed(..., error=exception)
   
   # After
   error_dict = error_to_payload(exception)
   event = WorkflowFailed(..., error_details=error_dict)
   ```

4. **Update schemas with annotated types:**
   ```python
   # Before
   class MyEvent(BaseEvent):
       amount: Decimal = Field(...)
   
   # After
   from the_alchemiser.shared.schemas.types import MoneyDecimal
   
   class MyEvent(BaseEvent):
       amount: MoneyDecimal = Field(...)
   ```

### Testing Your Changes

1. Run serialization tests:
   ```bash
   poetry run pytest tests/shared/utils/test_json_sanitise.py -v
   ```

2. Run event contract tests:
   ```bash
   poetry run pytest tests/shared/events/test_event_json_contract.py -v
   ```

3. Check for raw `json.dumps`:
   ```bash
   ./scripts/check_json_dumps.sh
   ```

## Precision Policy

- **Money values:** 2 decimal places (use `MoneyDecimal`)
- **Weights/allocations:** 4 decimal places (use `WeightDecimal`)
- **Prices:** 2 decimal places for USD (use `PriceDecimal`)
- **Generic decimals:** No rounding (use `DecimalStr`)

All serialization preserves the exact decimal representation as a string.

## Timestamp Format

All timestamps use RFC3339 with Z suffix:
- Format: `YYYY-MM-DDTHH:MM:SS.fffffffZ`
- Example: `2025-10-15T08:13:16.741Z`
- Always UTC (no timezone offsets like `+00:00`)

## Troubleshooting

### Error: "Object of type X is not JSON serializable"

**Cause:** Using `json.dumps()` directly on an object containing non-JSON types.

**Solution:** Use `safe_json_dumps()` or `event_to_detail_str()`.

### Error: "Field required" when deserializing event

**Cause:** Event schema changed or missing required fields.

**Solution:** Check event schema in `shared/events/schemas.py` and provide all required fields.

### Decimal precision loss

**Cause:** Converting `Decimal` to `float` before serialization.

**Solution:** Use `DecimalStr`, `MoneyDecimal`, or `PriceDecimal` annotations which serialize to strings.

## References

- Implementation: `the_alchemiser/shared/utils/serialization.py`
- Type annotations: `the_alchemiser/shared/schemas/types.py`
- Event schemas: `the_alchemiser/shared/events/schemas.py`
- Tests: `tests/shared/utils/test_json_sanitise.py`
- Contract tests: `tests/shared/events/test_event_json_contract.py`
- CI check: `scripts/check_json_dumps.sh`
