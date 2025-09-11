# Cross-Module Import Violations Report

## Executive Summary

The Strategy module contains **7 direct import violations** and **multiple indirect violations** that break the modular architecture by importing from the legacy Execution module. These violations indicate that the Strategy module is performing execution coordination tasks that should be handled by the Execution module.

## Architectural Context

According to the modular architecture rules:
- ✅ **Allowed**: `strategy/ → shared/`
- ❌ **Forbidden**: `strategy/ → execution/`  
- ❌ **Forbidden**: `strategy/ → portfolio/`

## Detailed Violation Analysis

### 1. strategy/engines/core/trading_engine.py (5 violations)

This file contains the most violations and appears to be acting as an execution coordinator rather than a pure strategy engine.

#### 1.1 AccountService Import
```python
from the_alchemiser.execution.brokers.account_service import (
    AccountService as TypedAccountService,
)
```
**Usage**: Creates account service instances for account operations
```python
self.account_service = TypedAccountService(alpaca_manager)
```
**Issue**: Strategy module should not manage account services directly

#### 1.2 AccountFacade Import  
```python
from the_alchemiser.execution.core.account_facade import AccountFacade
```
**Usage**: Coordinates account operations and provides account info
```python
self._account_facade = AccountFacade(
    account_service=self.account_service,
    market_data_service=market_data_service,
    position_service=position_service,
)
```
**Issue**: Account coordination belongs in execution module

#### 1.3 ExecutionResultDTO Import
```python
from the_alchemiser.execution.core.execution_schemas import ExecutionResultDTO
```
**Usage**: Return type for rebalancing execution results
```python
def execute_rebalancing(self, target_allocations: dict[str, float], mode: str = "market") -> ExecutionResultDTO:
    # ... execution logic ...
    return ExecutionResultDTO(
        orders_executed=orders,
        account_info_before=account_info_before,
        # ... more fields
    )
```
**Issue**: Strategy should return signals, not execution results

#### 1.4 MultiStrategyExecutor Import
```python
from the_alchemiser.execution.execution_protocols import MultiStrategyExecutor
```
**Usage**: Type annotation for execution manager
```python
self._multi_strategy_executor: MultiStrategyExecutor = (
    self._execution_manager_for_multi_strategy
)
```
**Issue**: Strategy should not implement execution protocols

#### 1.5 SmartExecution Import
```python
from the_alchemiser.execution.strategies.smart_execution import SmartExecution
```
**Usage**: Order placement functionality
```python
self.order_manager = SmartExecution(
    order_executor=alpaca_manager,
    data_provider=self.data_provider,
    ignore_market_hours=self.ignore_market_hours,
)
```
**Issue**: Strategy should not handle order placement

### 2. strategy/mappers/mappers.py (1 violation)

#### 2.1 ValidatedOrderDTO Import
```python
from the_alchemiser.execution.orders.schemas import ValidatedOrderDTO
```
**Usage**: Converts strategy signals to execution-ready orders
```python
def typed_strategy_signal_to_validated_order(
    signal: TypedStrategySignal,
    portfolio_value: Decimal,
    # ... other params
) -> ValidatedOrderDTO:
    # ... conversion logic ...
    return ValidatedOrderDTO(
        symbol=signal.symbol.value,
        side=side,
        quantity=quantity,
        # ... more fields
    )
```
**Issue**: Creates tight coupling between strategy and execution schemas

### 3. Indirect Violations (Import Chain)

#### 3.1 KLM Engine Chain
```
strategy/engines/klm/engine.py → 
strategy/mappers/mappers.py → 
execution/orders/schemas.py
```

#### 3.2 Nuclear Engine Chain  
```
strategy/engines/nuclear/engine.py → 
strategy/mappers/mappers.py → 
execution/orders/schemas.py
```

#### 3.3 TECL Engine Chain
```
strategy/engines/tecl/engine.py → 
strategy/mappers/mappers.py → 
execution/orders/schemas.py
```

## Root Cause Analysis

### Architectural Violations

1. **Strategy Module Doing Execution**: The `trading_engine.py` file is performing execution coordination, order placement, and account management rather than focusing on signal generation.

2. **Tight Coupling**: The mapper functions create direct dependencies between strategy signals and execution DTOs, violating the principle of loose coupling through shared DTOs.

3. **Legacy Integration**: The imports target the legacy execution module that is marked for deprecation according to `EXECUTION_MODULE_REBUILD_PLAN.md`.

### Design Issues

1. **Mixed Responsibilities**: The strategy module contains both signal generation logic and execution coordination logic.

2. **Wrong Return Types**: Strategy functions return `ExecutionResultDTO` instead of strategy-specific DTOs.

3. **Direct Service Dependencies**: Strategy code directly instantiates and manages execution services.

## Impact Assessment

### Current Problems

1. **Module Isolation Broken**: Strategy module cannot be developed/tested independently from execution module.

2. **Legacy Dependency**: Strategy module depends on deprecated execution components.

3. **Architectural Debt**: Violates the clean modular architecture principles established for the project.

4. **Testing Complexity**: Strategy tests require execution module setup.

### Migration Blockers

These violations prevent:
- Clean separation of strategy and execution concerns
- Independent deployment of strategy module
- Migration to the new execution_v2 module
- Proper testing isolation

## Recommended Resolution Strategy

### Phase 1: Create Proper DTOs
- Move execution-related DTOs to `shared/` module
- Create strategy-specific result DTOs for signal generation

### Phase 2: Extract Execution Logic
- Move execution coordination from `trading_engine.py` to execution module
- Keep only signal generation logic in strategy module

### Phase 3: Break Mapper Dependencies  
- Create signal-to-DTO mappers in shared module or execution module
- Remove direct ValidatedOrderDTO dependencies from strategy

### Phase 4: Update Import Chain
- Fix all engines that import mappers to use proper DTOs
- Ensure strategy engines only return strategy signals

## Files Requiring Changes

### Critical (Direct Violations)
- `strategy/engines/core/trading_engine.py` - Major refactoring needed
- `strategy/mappers/mappers.py` - Remove execution dependencies

### Secondary (Indirect Violations)  
- `strategy/engines/klm/engine.py` - Update mapper usage
- `strategy/engines/nuclear/engine.py` - Update mapper usage
- `strategy/engines/tecl/engine.py` - Update mapper usage

## Estimated Effort

- **High Complexity**: `trading_engine.py` refactoring (execution coordination extraction)
- **Medium Complexity**: Mapper function migration to appropriate module
- **Low Complexity**: Engine import updates after mapper changes

## Next Steps

1. **Immediate**: Document all violations (✅ Complete)
2. **Phase 1**: Create shared DTOs for cross-module communication
3. **Phase 2**: Extract execution logic from strategy module
4. **Phase 3**: Update all import chains to use proper DTOs
5. **Phase 4**: Validate with import-linter and enable stricter rules

---

*This report provides the detailed analysis requested for planning the removal of cross-module import violations in the Strategy module.*