# EventBridge Decimal Serialization Bug Fix

**Date:** 2025-10-14
**Severity:** 🔴 CRITICAL - Blocks Trading Workflow
**Status:** 🔄 IN PROGRESS

## Problem Summary

Pydantic models with `Decimal` and `datetime` fields fail validation when deserialized from EventBridge JSON. EventBridge serializes these types to strings, but our schemas expect the original types.

## Root Cause

1. **Publishing**: Handler publishes event with `Decimal("0.2")` and `datetime` objects
2. **Serialization**: Pydantic's `.model_dump()` converts `Decimal` → `str` (to preserve precision)
3. **EventBridge**: Delivers JSON with string values: `"0.2"`, `"2025-10-14T15:47:36Z"`
4. **Receiving**: Lambda receives event and tries to validate
5. **Validation Error**: Pydantic expects `Decimal` and `datetime`, rejects `str`

## Example Error

```
ValidationError: 13 validation errors for ConsolidatedPortfolio
target_allocations.TLT
  Input should be an instance of Decimal [type=is_instance_of, input_value='0.2', input_type=str]
timestamp
  Input should be a valid datetime [type=datetime_type, input_value='2025-10-14T15:47:36.154041Z', input_type=str]
```

## Affected Schemas

### Event Schemas (in `shared/events/schemas.py`)

**Direct Decimal fields in events:**
1. `AllocationComparisonCompleted`:
   - `target_allocations: dict[str, Decimal]`
   - `current_allocations: dict[str, Decimal]`
   - `allocation_differences: dict[str, Decimal]`

2. `OrderSettlementCompleted`:
   - `settled_quantity: Decimal`
   - `settlement_price: Decimal`
   - `settled_value: Decimal`
   - `buying_power_released: Decimal`

3. `BulkSettlementCompleted`:
   - `total_buying_power_released: Decimal`

4. `TradingNotificationRequested`:
   - `total_trade_value: Decimal`

**Nested schemas with Decimal fields:**
5. `SignalGenerated`:
   - Contains `consolidated_portfolio: dict` with `ConsolidatedPortfolio` data ✅ **FIXED**

6. `RebalancePlanned`:
   - Contains `rebalance_plan: RebalancePlan` (has many Decimal fields)
   - Contains `allocation_comparison: AllocationComparison` (has Decimal dicts)

7. `TradeExecutionStarted`, `PortfolioStateChanged`:
   - Contains `portfolio_state_before/after: PortfolioState` (may have Decimals)

### DTO Schemas (nested in events)

1. **ConsolidatedPortfolio** (`shared/schemas/consolidated_portfolio.py`) ✅ **FIXED**
   - `target_allocations: dict[str, Decimal]`
   - `timestamp: datetime`

2. **RebalancePlan** (`shared/schemas/rebalance_plan.py`) ⚠️ **NEEDS FIX**
   - `total_portfolio_value: Decimal`
   - `total_trade_value: Decimal`
   - `max_drift_tolerance: Decimal`
   - `timestamp: datetime`

3. **RebalancePlanItem** (`shared/schemas/rebalance_plan.py`) ⚠️ **NEEDS FIX**
   - `current_weight: Decimal`
   - `target_weight: Decimal`
   - `weight_diff: Decimal`
   - `target_value: Decimal`
   - `current_value: Decimal`
   - `trade_amount: Decimal`

4. **AllocationComparison** (need to locate) ⚠️ **NEEDS FIX**

5. **PortfolioState** (need to locate) ⚠️ **NEEDS FIX**

## Solution Pattern

Add `mode="before"` validators to coerce strings back to proper types:

### For Decimal Fields

```python
@field_validator("field_name", mode="before")
@classmethod
def coerce_field_from_eventbridge(cls, v: Decimal | str) -> Decimal:
    """Coerce from EventBridge JSON string to Decimal."""
    if isinstance(v, str):
        return Decimal(v)
    elif isinstance(v, (int, float)):
        return Decimal(str(v))
    return v
```

### For dict[str, Decimal] Fields

```python
@field_validator("allocations", mode="before")
@classmethod
def coerce_allocations_from_eventbridge(
    cls, v: dict[str, Decimal] | dict[str, str]
) -> dict[str, Decimal]:
    """Coerce allocation dict from EventBridge JSON."""
    if not isinstance(v, dict):
        return v

    result = {}
    for symbol, weight in v.items():
        if isinstance(weight, str):
            result[symbol] = Decimal(weight)
        elif isinstance(weight, (int, float)):
            result[symbol] = Decimal(str(weight))
        else:
            result[symbol] = weight
    return result
```

### For datetime Fields

```python
@field_validator("timestamp", mode="before")
@classmethod
def coerce_timestamp_from_eventbridge(cls, v: datetime | str) -> datetime:
    """Coerce timestamp from EventBridge JSON string."""
    if isinstance(v, str):
        from datetime import datetime
        # Handle both 'Z' and '+00:00' formats
        v_normalized = v.replace("Z", "+00:00")
        return datetime.fromisoformat(v_normalized)
    return v
```

## Implementation Checklist

### Phase 1: Critical Path (Immediate) ✅
- [x] ConsolidatedPortfolio (used in SignalGenerated) ✅ **DONE**

### Phase 2: Next Most Likely (High Priority) 🔄
- [ ] RebalancePlan (used in RebalancePlanned)
- [ ] RebalancePlanItem (nested in RebalancePlan)
- [ ] AllocationComparison (used in RebalancePlanned)

### Phase 3: Less Common Events (Medium Priority)
- [ ] PortfolioState (used in PortfolioStateChanged, TradeExecutionStarted)
- [ ] OrderSettlementCompleted direct fields
- [ ] BulkSettlementCompleted direct fields
- [ ] AllocationComparisonCompleted direct fields

### Phase 4: Notification Events (Low Priority)
- [ ] TradingNotificationRequested direct fields

## Why This Happens

**JSON doesn't have a Decimal type.** To preserve precision for financial calculations:
- Pydantic serializes `Decimal` → `str` (avoids float precision errors)
- EventBridge delivers JSON with strings
- Receiving side must deserialize `str` → `Decimal`

**This is the correct, industry-standard approach** for financial data through JSON/EventBridge.

## Testing Strategy

1. **Unit tests**: Test validators with string inputs
   ```python
   # Should work after fix
   portfolio = ConsolidatedPortfolio.model_validate({
       "target_allocations": {"AAPL": "0.6"},  # String, not Decimal
       "timestamp": "2025-10-14T15:47:36Z",  # String, not datetime
       ...
   })
   ```

2. **Integration tests**: Publish event to EventBridge, verify receiving Lambda can deserialize

3. **End-to-end**: Run full workflow and verify no validation errors

## Related Issues

- WorkflowFailed events due to ConsolidatedPortfolio validation
- Portfolio handler can't process SignalGenerated events
- Rebalance plan will fail similarly when it reaches execution handler

## References

- Pydantic v2 validation modes: https://docs.pydantic.dev/latest/concepts/validators/#field-validators
- EventBridge event serialization: https://docs.aws.amazon.com/eventbridge/latest/userguide/eb-events.html
- Decimal precision in JSON: https://docs.python.org/3/library/decimal.html

## Next Steps

1. Add validators to RebalancePlan and RebalancePlanItem
2. Locate and fix AllocationComparison schema
3. Locate and fix PortfolioState schema
4. Add unit tests for all validators
5. Deploy and test end-to-end workflow
