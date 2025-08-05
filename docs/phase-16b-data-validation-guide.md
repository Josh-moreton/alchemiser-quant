# Phase 16b: Data Structure Validation Guide

## Overview

Phase 16b validates that our TypedDict definitions match actual Alpaca API response structures. This ensures type safety when we migrate from `dict[str, Any]` to strict TypedDict types.

## Quick Start

### Step 1: Collect Sample Data

Run this to collect sample data from your Alpaca account:

```bash
python scripts/collect_alpaca_data.py
```

This will create JSON files in `data_validation_samples/` directory:

- `account_data_YYYYMMDD_HHMMSS.json`
- `positions_data_YYYYMMDD_HHMMSS.json`
- `orders_data_YYYYMMDD_HHMMSS.json`

### Step 2: Validate Data Structures

Run the validation script to compare actual data against our TypedDict definitions:

```bash
python scripts/validate_data_structures.py
```

## What We're Validating

### 1. Account Information (`AccountInfo` TypedDict)

Our definition:

```python
class AccountInfo(TypedDict):
    account_id: str
    equity: str | float
    cash: str | float
    buying_power: str | float
    day_trades_remaining: int
    portfolio_value: str | float
    last_equity: str | float
    daytrading_buying_power: str | float
    regt_buying_power: str | float
    status: Literal["ACTIVE", "INACTIVE"]
```

**Validation Checks:**

- ✅ All required fields present
- ✅ Field types match (str/float/int)
- ✅ Status values are valid literals
- 🔍 Identify any extra fields from Alpaca

### 2. Position Information (`PositionInfo` TypedDict)

Our definition:

```python
class PositionInfo(TypedDict):
    symbol: str
    qty: str | float
    side: Literal["long", "short"]
    market_value: str | float
    cost_basis: str | float
    unrealized_pl: str | float
    unrealized_plpc: str | float
    current_price: str | float
```

**Validation Checks:**

- ✅ All position fields present
- ✅ Numeric types match expectations
- ✅ Side values are "long" or "short"
- 🔍 Detect any additional position fields

### 3. Order Details (`OrderDetails` TypedDict)

Our definition:

```python
class OrderDetails(TypedDict):
    id: str
    symbol: str
    qty: str | float
    side: Literal["buy", "sell"]
    order_type: Literal["market", "limit", "stop", "stop_limit"]
    time_in_force: Literal["day", "gtc", "ioc", "fok"]
    status: Literal["new", "partially_filled", "filled", "canceled", "expired", "rejected"]
    filled_qty: str | float
    filled_avg_price: str | float | None
    created_at: str
    updated_at: str
```

**Validation Checks:**

- ✅ All order fields present
- ✅ Enum values match Alpaca API
- ✅ Nullable fields handled correctly
- ✅ Timestamp formats compatible
- 🔍 Find any missing order attributes

## Expected Outcomes

### ✅ Perfect Match

If validation passes completely:

- Our TypedDict definitions are accurate
- Safe to migrate from `dict[str, Any]` to TypedDict
- Can remove relevant TODO comments

### ⚠️ Field Mismatches

If validation finds issues:

- Update TypedDict definitions to match reality
- Adjust field types (str vs float vs int)
- Add missing required fields
- Handle optional/nullable fields

### 🔍 Extra Fields Found

If Alpaca provides additional fields:

- Evaluate if we need them for trading logic
- Add useful fields to our TypedDict definitions
- Document fields we're intentionally ignoring

## Manual Data Provision

If you prefer to provide data manually, create JSON files with this structure:

### Account Data (`account_sample.json`)

```json
{
  "account_id": "your_account_id",
  "equity": "50000.00",
  "cash": "25000.00", 
  "buying_power": "100000.00",
  "day_trades_remaining": 3,
  "portfolio_value": "50000.00",
  "last_equity": "49500.00",
  "daytrading_buying_power": "100000.00",
  "regt_buying_power": "50000.00",
  "status": "ACTIVE"
}
```

### Position Data (`positions_sample.json`)

```json
[
  {
    "symbol": "AAPL",
    "qty": "10",
    "side": "long",
    "market_value": "1500.00",
    "cost_basis": "1400.00",
    "unrealized_pl": "100.00",
    "unrealized_plpc": "0.07142857",
    "current_price": "150.00"
  }
]
```

### Orders Data (`orders_sample.json`)

```json
[
  {
    "id": "order_id_123",
    "symbol": "AAPL", 
    "qty": "10",
    "side": "buy",
    "order_type": "market",
    "time_in_force": "day",
    "status": "filled",
    "filled_qty": "10",
    "filled_avg_price": "149.50",
    "created_at": "2025-08-05T10:30:00Z",
    "updated_at": "2025-08-05T10:30:15Z"
  }
]
```

## Next Steps After Validation

### If Validation Passes ✅

1. Update TODO comments to reflect validated structures
2. Begin migrating specific functions from `dict[str, Any]` to TypedDict
3. Update function signatures to use strict types
4. Run mypy validation on updated functions

### If Validation Fails ❌  

1. Update TypedDict definitions based on findings
2. Re-run validation until all checks pass
3. Document any intentional deviations
4. Update related Protocol definitions

## Benefits of Phase 16b

- **Type Safety**: Catch type mismatches at development time
- **API Compatibility**: Ensure our types match Alpaca's actual responses  
- **Future-Proofing**: Detect API changes that might break our code
- **Documentation**: Accurate type definitions serve as API documentation
- **IDE Support**: Better autocomplete and error detection

Ready to validate? Run `python scripts/collect_alpaca_data.py` to get started!
