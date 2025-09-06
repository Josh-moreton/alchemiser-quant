# Phase 2 Migration - Batch 1 Report

**Execution Time**: Tue Sep  2 10:55:25 UTC 2025

## Summary
- ✅ **Successful migrations**: 3
- ❌ **Failed migrations**: 1
- 📝 **Total imports updated**: 108

## Successful Migrations
- `the_alchemiser/domain/types.py` → `the_alchemiser/shared/value_objects/core_types.py` (47 imports updated)
- `the_alchemiser/domain/trading/value_objects/symbol.py` → `the_alchemiser/shared/value_objects/symbol.py` (32 imports updated)
- `the_alchemiser/services/errors/exceptions.py` → `the_alchemiser/shared/utils/exceptions.py` (29 imports updated)

## Failed Migrations
- `the_alchemiser/interfaces/schemas/orders.py` → `the_alchemiser/execution/orders/order_schemas.py` (FAILED)