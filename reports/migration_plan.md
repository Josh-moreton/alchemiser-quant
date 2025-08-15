# Migration Plan

## Overview
Transition to a hybrid approach where domain models are frozen, slotted, kw-only dataclasses and Pydantic v2 is used only at IO boundaries.

## Stepwise Refactor

1. **Introduce DTO layer and upgrade order validation (PR1, ~250 LOC)**
   - File: `the_alchemiser/application/orders/order_validation.py`
   - Replace `@validator` with `@field_validator` and `model_dump`.
   - Provide DTO → domain mapping helpers.
   - Add unit tests for `ValidatedOrder` parsing.

2. **Harden core domain models (PR2, ~280 LOC)**
   - Files: `the_alchemiser/domain/models/account.py`, `order.py`, `market_data.py`, `strategy.py`
   - Add `slots=True, kw_only=True` and enforce invariants in `__post_init__`.
   - Remove manual parsing logic; keep parsing in DTOs.
   - Update affected services to use new constructors.

3. **Refactor tracking dataclasses (PR3, ~200 LOC)**
   - File: `the_alchemiser/application/tracking/strategy_order_tracker.py`
   - Freeze dataclasses and ensure updates return new instances or use mutable methods consciously.
   - Add tests for P&L calculations.

## Test Impact
- New unit tests around DTO ↔ domain conversions.
- Regression tests for trading and tracking services.
- Coverage plugins already configured; ensure >80% coverage for modified modules.

## Rollback Plan
- Each PR limited to <300 LOC and isolated.
- Revert by cherry-picking previous commit if integration tests fail.
- DTOs maintain old interfaces, enabling gradual rollout.
