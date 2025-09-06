# Shared Module Comprehensive Audit Report

## Executive Summary

This report provides a comprehensive analysis of all 119 Python files in the `shared` module and their usage across the `strategy`, `portfolio`, and `execution` modules.

### Key Findings

- **Total Files Analyzed**: 119
- **Files with Zero Usage**: 57 (47.9%)
- **Files Used by Single Module**: 27 (22.7%)
- **Files Used by Multiple Modules**: 35 (29.4%)
- **Files Used by All Three Modules**: 19 (16.0%)

## Summary Analysis

### Usage Distribution

| Category | Count | Percentage | Action |
|----------|-------|------------|--------|
| Unused files | 57 | 47.9% | Review for removal |
| Single module usage | 27 | 22.7% | Consider module-specific placement |
| Multi-module usage | 35 | 29.4% | Keep in shared |
| All-module usage | 19 | 16.0% | High-value shared utilities |

### Files by Category

#### 🔴 High Priority for Review (Unused Files)

- `__init__.py` - Business Unit: shared | Status: current.
- `adapters/execution_adapters.py` - Unknown
- `adapters/integration_helpers.py` - Unknown
- `adapters/portfolio_adapters.py` - Unknown
- `adapters/strategy_adapters.py` - Unknown
- `cli/cli.py` - Unknown
- `cli/cli_formatter.py` - Business Unit: shared | Status: current
- `cli/dashboard_utils.py` - Unknown
- `cli/error_display_utils.py` - Unknown
- `cli/portfolio_calculations.py` - Unknown
- ... and 47 more unused files

#### 🟡 Medium Priority (Single Module Usage)

**Portfolio Module Only (7 files):**
- `adapters/__init__.py`
- `config/secrets_manager.py`
- `dto/rebalance_plan_dto.py`
- `math/trading_math.py`
- `schemas/reporting.py`
- ... and 2 more files

**Strategy Module Only (11 files):**
- `config/bootstrap.py`
- `config/container.py`
- `math/math_utils.py`
- `reporting/reporting.py`
- `types/bar.py`
- ... and 6 more files

**Execution Module Only (9 files):**
- `dto/execution_report_dto.py`
- `dto/portfolio_state_dto.py`
- `schemas/accounts.py`
- `schemas/enriched_data.py`
- `schemas/market_data.py`
- ... and 4 more files


#### 🟢 Well-Utilized (Multi-Module Usage)

- `config/__init__.py` - Used by: strategy, portfolio, execution
- `config/config.py` - Used by: strategy, portfolio, execution
- `dto/__init__.py` - Used by: portfolio, execution
- `errors/__init__.py` - Used by: strategy, portfolio, execution
- `errors/error_handler.py` - Used by: strategy, portfolio, execution
- `log/__init__.py` - Used by: strategy, portfolio, execution
- `logging/__init__.py` - Used by: strategy, portfolio, execution
- `logging/logging.py` - Used by: strategy, portfolio, execution
- `logging/logging_utils.py` - Used by: strategy, portfolio, execution
- `mappers/market_data_mappers.py` - Used by: strategy, execution

## Detailed File Analysis


### File: `__init__.py`

**Purpose**: Business Unit: shared | Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: __init__.py, validation/indicator_validator.py, errors/strategy_errors.py
- **portfolio**: __init__.py, utils/portfolio_utilities.py, utils/__init__.py
- **execution**: infrastructure.py, __init__.py, lifecycle_simplified.py

**File Details**:
- Size: 12 lines
- Classes: 0
- Functions: 0
- Status: current

**Recommendation**: Remove - Small unused file

---

### File: `adapters/__init__.py`

**Purpose**: Business Unit: shared | Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 1 files (allocation/portfolio_rebalancing_service.py)
- **execution**: 0 files

**Potential Usage**:
- **strategy**: __init__.py, validation/indicator_validator.py, errors/strategy_errors.py
- **portfolio**: __init__.py, utils/portfolio_utilities.py, utils/__init__.py
- **execution**: infrastructure.py, __init__.py, lifecycle_simplified.py

**File Details**:
- Size: 51 lines
- Classes: 0
- Functions: 0
- Status: current

**Recommendation**: Consider moving to portfolio module - Single module usage

---

### File: `adapters/execution_adapters.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: managers/typed_strategy_manager.py, engines/core/trading_engine.py, engines/core/__init__.py
- **portfolio**: utils/portfolio_utilities.py, pnl/strategy_order_tracker.py, holdings/position_service.py
- **execution**: infrastructure.py, __init__.py, lifecycle_simplified.py

**File Details**:
- Size: 375 lines
- Classes: 0
- Functions: 5
- Status: unknown

**Recommendation**: Review for removal - No current usage found

---

### File: `adapters/integration_helpers.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: engines/engine.py, engines/core/trading_engine.py, schemas/strategies.py
- **portfolio**: calculations/portfolio_calculations.py, tracking/integration.py, mappers/tracking_normalization.py
- **execution**: __init__.py, protocols/trading_repository.py, mappers/__init__.py

**File Details**:
- Size: 327 lines
- Classes: 4
- Functions: 2
- Status: unknown

**Recommendation**: Review for removal - No current usage found

---

### File: `adapters/portfolio_adapters.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: types/__init__.py, types/strategy.py, engines/nuclear/engine.py
- **portfolio**: __init__.py, utils/portfolio_utilities.py, utils/__init__.py
- **execution**: protocols/trading_repository.py, core/manager.py, core/execution_schemas.py

**File Details**:
- Size: 323 lines
- Classes: 0
- Functions: 4
- Status: unknown

**Recommendation**: Review for removal - No current usage found

---

### File: `adapters/strategy_adapters.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: __init__.py, validation/indicator_validator.py, errors/strategy_errors.py
- **portfolio**: __init__.py, pnl/__init__.py, pnl/strategy_order_tracker.py
- **execution**: timing/__init__.py, timing/market_timing_utils.py, config/execution_config.py

**File Details**:
- Size: 192 lines
- Classes: 0
- Functions: 4
- Status: unknown

**Recommendation**: Review for removal - No current usage found

---

### File: `cli/cli.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: managers/typed_strategy_manager.py, engines/core/trading_engine.py, data/price_service.py
- **portfolio**: calculations/portfolio_calculations.py, policies/protocols.py
- **execution**: protocols/trading_repository.py, brokers/alpaca/adapter.py

**File Details**:
- Size: 1193 lines
- Classes: 0
- Functions: 9
- Status: unknown

**Recommendation**: Review for removal - No current usage found

---

### File: `cli/cli_formatter.py`

**Purpose**: Business Unit: shared | Status: current

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: managers/typed_strategy_manager.py, engines/core/trading_engine.py, data/price_service.py
- **portfolio**: calculations/portfolio_calculations.py, policies/protocols.py
- **execution**: protocols/trading_repository.py, brokers/alpaca/adapter.py

**File Details**:
- Size: 869 lines
- Classes: 0
- Functions: 12
- Status: current

**Recommendation**: Review for removal - No current usage found

---

### File: `cli/dashboard_utils.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: managers/typed_strategy_manager.py, engines/engine.py, engines/entities/__init__.py
- **portfolio**: utils/portfolio_utilities.py, utils/__init__.py, pnl/strategy_order_tracker.py
- **execution**: monitoring/websocket_order_monitor.py, orders/consolidated_validation.py, orders/__init__.py

**File Details**:
- Size: 215 lines
- Classes: 0
- Functions: 6
- Status: unknown

**Recommendation**: Review for removal - No current usage found

---

### File: `cli/error_display_utils.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: errors/strategy_errors.py, managers/typed_strategy_manager.py, engines/engine.py
- **portfolio**: utils/portfolio_utilities.py, utils/__init__.py, pnl/strategy_order_tracker.py
- **execution**: monitoring/websocket_order_monitor.py, orders/consolidated_validation.py, orders/__init__.py

**File Details**:
- Size: 255 lines
- Classes: 0
- Functions: 5
- Status: unknown

**Recommendation**: Review for removal - No current usage found

---

### File: `cli/portfolio_calculations.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: types/__init__.py, types/strategy.py, managers/typed_strategy_manager.py
- **portfolio**: __init__.py, utils/portfolio_utilities.py, utils/__init__.py
- **execution**: protocols/trading_repository.py, core/manager.py, core/execution_schemas.py

**File Details**:
- Size: 100 lines
- Classes: 0
- Functions: 1
- Status: unknown

**Recommendation**: Review for removal - No current usage found

---

### File: `cli/signal_analyzer.py`

**Purpose**: Business Unit: shared | Status: current

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: __init__.py, errors/strategy_errors.py, types/__init__.py
- **portfolio**: __init__.py, pnl/strategy_order_tracker.py, holdings/__init__.py
- **execution**: protocols/trading_repository.py, analytics/slippage_analyzer.py, brokers/alpaca/adapter.py

**File Details**:
- Size: 304 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Review for removal - No current usage found

---

### File: `cli/signal_display_utils.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: __init__.py, errors/strategy_errors.py, types/__init__.py
- **portfolio**: utils/portfolio_utilities.py, utils/__init__.py, pnl/strategy_order_tracker.py
- **execution**: monitoring/websocket_order_monitor.py, orders/consolidated_validation.py, orders/__init__.py

**File Details**:
- Size: 262 lines
- Classes: 0
- Functions: 5
- Status: unknown

**Recommendation**: Review for removal - No current usage found

---

### File: `cli/trading_executor.py`

**Purpose**: Business Unit: shared | Status: current

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: __init__.py, validation/indicator_validator.py, managers/typed_strategy_manager.py
- **portfolio**: utils/portfolio_utilities.py, pnl/strategy_order_tracker.py, holdings/position_service.py
- **execution**: __init__.py, orders/request_builder.py, orders/service.py

**File Details**:
- Size: 578 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Review for removal - No current usage found

---

### File: `config/__init__.py`

**Purpose**: Business Unit: shared | Status: current

**Current Usage**:
- **strategy**: 1 files (engines/core/trading_engine.py)
- **portfolio**: 2 files (pnl/strategy_order_tracker.py, core/rebalancing_orchestrator.py)
- **execution**: 3 files (monitoring/websocket_order_monitor.py, config/execution_config.py, examples/canonical_integration.py)

**File Details**:
- Size: 9 lines
- Classes: 0
- Functions: 0
- Status: current

**Recommendation**: Keep - Well-utilized across all modules

---

### File: `config/bootstrap.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 1 files (engines/core/trading_engine.py)
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: validation/indicator_validator.py, engines/core/trading_engine.py, engines/tecl/engine.py
- **portfolio**: pnl/strategy_order_tracker.py, pnl/portfolio_pnl_utils.py, holdings/position_manager.py
- **execution**: infrastructure.py, monitoring/websocket_order_monitor.py, orders/progressive_order_utils.py

**File Details**:
- Size: 256 lines
- Classes: 1
- Functions: 3
- Status: unknown

**Recommendation**: Consider moving to strategy module - Single module usage

---

### File: `config/config.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 1 files (engines/core/trading_engine.py)
- **portfolio**: 1 files (pnl/strategy_order_tracker.py)
- **execution**: 3 files (monitoring/websocket_order_monitor.py, config/execution_config.py, examples/canonical_integration.py)

**File Details**:
- Size: 160 lines
- Classes: 11
- Functions: 1
- Status: current

**Recommendation**: Keep - Well-utilized across all modules

---

### File: `config/config_providers.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: validation/indicator_validator.py, engines/core/trading_engine.py, engines/tecl/engine.py
- **portfolio**: pnl/strategy_order_tracker.py, pnl/portfolio_pnl_utils.py, holdings/position_manager.py
- **execution**: infrastructure.py, monitoring/websocket_order_monitor.py, orders/progressive_order_utils.py

**File Details**:
- Size: 40 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Review for removal - No current usage found

---

### File: `config/config_service.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: validation/indicator_validator.py, errors/strategy_errors.py, engines/core/trading_engine.py
- **portfolio**: utils/portfolio_utilities.py, pnl/strategy_order_tracker.py, pnl/portfolio_pnl_utils.py
- **execution**: infrastructure.py, __init__.py, monitoring/websocket_order_monitor.py

**File Details**:
- Size: 60 lines
- Classes: 1
- Functions: 0
- Status: unknown

**Recommendation**: Review for removal - No current usage found

---

### File: `config/container.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 1 files (engines/core/trading_engine.py)
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: validation/indicator_validator.py, engines/core/trading_engine.py, engines/tecl/engine.py
- **portfolio**: pnl/strategy_order_tracker.py, pnl/portfolio_pnl_utils.py, holdings/position_manager.py
- **execution**: infrastructure.py, monitoring/websocket_order_monitor.py, orders/progressive_order_utils.py

**File Details**:
- Size: 76 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Consider moving to strategy module - Single module usage

---

### File: `config/infrastructure_providers.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: validation/indicator_validator.py, engines/nuclear/logic.py, engines/core/trading_engine.py
- **portfolio**: pnl/strategy_order_tracker.py, pnl/portfolio_pnl_utils.py, holdings/position_manager.py
- **execution**: infrastructure.py, monitoring/websocket_order_monitor.py, orders/progressive_order_utils.py

**File Details**:
- Size: 41 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Review for removal - No current usage found

---

### File: `config/secrets_manager.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 1 files (core/rebalancing_orchestrator.py)
- **execution**: 0 files

**Potential Usage**:
- **strategy**: validation/indicator_validator.py, managers/__init__.py, managers/typed_strategy_manager.py
- **portfolio**: utils/portfolio_utilities.py, pnl/strategy_order_tracker.py, pnl/portfolio_pnl_utils.py
- **execution**: infrastructure.py, __init__.py, monitoring/websocket_order_monitor.py

**File Details**:
- Size: 252 lines
- Classes: 1
- Functions: 0
- Status: unknown

**Recommendation**: Consider moving to portfolio module - Single module usage

---

### File: `config/secrets_service.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: validation/indicator_validator.py, errors/strategy_errors.py, engines/core/trading_engine.py
- **portfolio**: utils/portfolio_utilities.py, pnl/strategy_order_tracker.py, pnl/portfolio_pnl_utils.py
- **execution**: infrastructure.py, __init__.py, monitoring/websocket_order_monitor.py

**File Details**:
- Size: 55 lines
- Classes: 1
- Functions: 0
- Status: unknown

**Recommendation**: Review for removal - No current usage found

---

### File: `config/service_providers.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: validation/indicator_validator.py, errors/strategy_errors.py, engines/core/trading_engine.py
- **portfolio**: utils/portfolio_utilities.py, pnl/strategy_order_tracker.py, pnl/portfolio_pnl_utils.py
- **execution**: infrastructure.py, __init__.py, monitoring/websocket_order_monitor.py

**File Details**:
- Size: 55 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Review for removal - No current usage found

---

### File: `dto/__init__.py`

**Purpose**: Data transfer objects.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 1 files (allocation/portfolio_rebalancing_service.py)
- **execution**: 1 files (core/execution_schemas.py)

**Potential Usage**:
- **strategy**: __init__.py, validation/indicator_validator.py, errors/strategy_errors.py
- **portfolio**: __init__.py, utils/portfolio_utilities.py, utils/__init__.py
- **execution**: infrastructure.py, __init__.py, lifecycle_simplified.py

**File Details**:
- Size: 55 lines
- Classes: 2
- Functions: 0
- Status: unknown

**Recommendation**: Keep - Good cross-module reuse

---

### File: `dto/execution_report_dto.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 1 files (core/execution_schemas.py)

**Potential Usage**:
- **strategy**: validation/indicator_validator.py, types/strategy.py, managers/typed_strategy_manager.py
- **portfolio**: utils/portfolio_utilities.py, pnl/__init__.py, pnl/strategy_order_tracker.py
- **execution**: infrastructure.py, __init__.py, lifecycle_simplified.py

**File Details**:
- Size: 304 lines
- Classes: 2
- Functions: 0
- Status: unknown

**Recommendation**: Consider moving to execution module - Single module usage

---

### File: `dto/order_request_dto.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: validation/indicator_validator.py, types/strategy.py, managers/typed_strategy_manager.py
- **portfolio**: utils/portfolio_utilities.py, pnl/__init__.py, pnl/strategy_order_tracker.py
- **execution**: infrastructure.py, __init__.py, lifecycle_simplified.py

**File Details**:
- Size: 315 lines
- Classes: 2
- Functions: 0
- Status: unknown

**Recommendation**: Review for removal - No current usage found

---

### File: `dto/portfolio_state_dto.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 1 files (core/execution_schemas.py)

**Potential Usage**:
- **strategy**: validation/indicator_validator.py, types/__init__.py, types/strategy.py
- **portfolio**: __init__.py, utils/portfolio_utilities.py, utils/__init__.py
- **execution**: lifecycle_simplified.py, monitoring/websocket_order_monitor.py, orders/consolidated_validation.py

**File Details**:
- Size: 355 lines
- Classes: 3
- Functions: 0
- Status: unknown

**Recommendation**: Consider moving to execution module - Single module usage

---

### File: `dto/rebalance_plan_dto.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 1 files (allocation/portfolio_rebalancing_service.py)
- **execution**: 0 files

**Potential Usage**:
- **strategy**: validation/indicator_validator.py, types/strategy.py, managers/typed_strategy_manager.py
- **portfolio**: __init__.py, pnl/strategy_order_tracker.py, pnl/portfolio_pnl_utils.py
- **execution**: lifecycle_simplified.py, monitoring/websocket_order_monitor.py, orders/consolidated_validation.py

**File Details**:
- Size: 233 lines
- Classes: 2
- Functions: 0
- Status: unknown

**Recommendation**: Consider moving to portfolio module - Single module usage

---

### File: `dto/signal_dto.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: __init__.py, validation/indicator_validator.py, errors/strategy_errors.py
- **portfolio**: pnl/strategy_order_tracker.py, pnl/portfolio_pnl_utils.py, holdings/position_model.py
- **execution**: lifecycle_simplified.py, monitoring/websocket_order_monitor.py, orders/consolidated_validation.py

**File Details**:
- Size: 142 lines
- Classes: 1
- Functions: 0
- Status: unknown

**Recommendation**: Review for removal - No current usage found

---

### File: `dto_communication_demo.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: validation/indicator_validator.py, types/strategy.py, managers/typed_strategy_manager.py
- **portfolio**: pnl/strategy_order_tracker.py, pnl/portfolio_pnl_utils.py, holdings/position_model.py
- **execution**: lifecycle_simplified.py, monitoring/websocket_order_monitor.py, orders/consolidated_validation.py

**File Details**:
- Size: 374 lines
- Classes: 0
- Functions: 5
- Status: unknown

**Recommendation**: Remove - Test/demo file with no usage

---

### File: `errors/__init__.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 1 files (engines/core/trading_engine.py)
- **portfolio**: 3 files (utils/portfolio_utilities.py, allocation/rebalance_execution_service.py, core/rebalancing_orchestrator_facade.py)
- **execution**: 3 files (orders/consolidated_validation.py, core/account_facade.py, lifecycle/dispatcher.py)

**File Details**:
- Size: 1 lines
- Classes: 0
- Functions: 0
- Status: unknown

**Recommendation**: Keep - Well-utilized across all modules

---

### File: `errors/context.py`

**Purpose**: Business Unit: shared | Status: current

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: errors/strategy_errors.py, engines/engine.py, data/price_fetching_utils.py
- **portfolio**: utils/portfolio_utilities.py, holdings/position_manager.py, tracking/integration.py
- **execution**: monitoring/websocket_order_monitor.py, errors/error_categories.py, errors/error_codes.py

**File Details**:
- Size: 31 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Review for removal - No current usage found

---

### File: `errors/error_handler.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 1 files (engines/core/trading_engine.py)
- **portfolio**: 3 files (utils/portfolio_utilities.py, allocation/rebalance_execution_service.py, core/rebalancing_orchestrator_facade.py)
- **execution**: 3 files (orders/consolidated_validation.py, core/account_facade.py, lifecycle/dispatcher.py)

**File Details**:
- Size: 989 lines
- Classes: 10
- Functions: 9
- Status: unknown

**Recommendation**: Keep - Well-utilized across all modules

---

### File: `log/__init__.py`

**Purpose**: Logging setup and utilities.

**Current Usage**:
- **strategy**: 3 files (validation/indicator_validator.py, engines/core/trading_engine.py, data/price_fetching_utils.py)
- **portfolio**: 6 files (holdings/position_manager.py, policies/policy_orchestrator.py, policies/fractionability_policy_impl.py...)
- **execution**: 3 files (orders/asset_order_handler.py, pricing/smart_pricing_handler.py, core/manager.py)

**File Details**:
- Size: 9 lines
- Classes: 0
- Functions: 0
- Status: unknown

**Recommendation**: Keep - Well-utilized across all modules

---

### File: `logging/__init__.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 3 files (validation/indicator_validator.py, engines/core/trading_engine.py, data/price_fetching_utils.py)
- **portfolio**: 6 files (holdings/position_manager.py, policies/policy_orchestrator.py, policies/fractionability_policy_impl.py...)
- **execution**: 3 files (orders/asset_order_handler.py, pricing/smart_pricing_handler.py, core/manager.py)

**File Details**:
- Size: 1 lines
- Classes: 0
- Functions: 0
- Status: unknown

**Recommendation**: Keep - Well-utilized across all modules

---

### File: `logging/logging.py`

**Purpose**: Logging utilities for the modular architecture.

**Current Usage**:
- **strategy**: 3 files (validation/indicator_validator.py, engines/core/trading_engine.py, data/price_fetching_utils.py)
- **portfolio**: 6 files (holdings/position_manager.py, policies/policy_orchestrator.py, policies/fractionability_policy_impl.py...)
- **execution**: 3 files (orders/asset_order_handler.py, pricing/smart_pricing_handler.py, core/manager.py)

**File Details**:
- Size: 52 lines
- Classes: 0
- Functions: 3
- Status: unknown

**Recommendation**: Keep - Well-utilized across all modules

---

### File: `logging/logging_utils.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 3 files (validation/indicator_validator.py, engines/core/trading_engine.py, data/price_fetching_utils.py)
- **portfolio**: 6 files (holdings/position_manager.py, policies/policy_orchestrator.py, policies/fractionability_policy_impl.py...)
- **execution**: 3 files (orders/asset_order_handler.py, pricing/smart_pricing_handler.py, core/manager.py)

**File Details**:
- Size: 405 lines
- Classes: 2
- Functions: 14
- Status: current

**Recommendation**: Keep - Well-utilized across all modules

---

### File: `mappers/execution_summary_mapping.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: managers/typed_strategy_manager.py, engines/protocols/__init__.py, engines/core/trading_engine.py
- **portfolio**: utils/portfolio_utilities.py, pnl/strategy_order_tracker.py, pnl/portfolio_pnl_utils.py
- **execution**: infrastructure.py, __init__.py, lifecycle_simplified.py

**File Details**:
- Size: 215 lines
- Classes: 0
- Functions: 8
- Status: unknown

**Recommendation**: Review for removal - No current usage found

---

### File: `mappers/market_data_mappers.py`

**Purpose**: Business Unit: shared | Status: current

**Current Usage**:
- **strategy**: 1 files (data/market_data_service.py)
- **portfolio**: 0 files
- **execution**: 1 files (brokers/alpaca/adapter.py)

**Potential Usage**:
- **strategy**: validation/indicator_validator.py, types/strategy.py, managers/typed_strategy_manager.py
- **portfolio**: pnl/strategy_order_tracker.py, pnl/portfolio_pnl_utils.py, holdings/position_model.py
- **execution**: lifecycle_simplified.py, orders/consolidated_validation.py, orders/request_builder.py

**File Details**:
- Size: 87 lines
- Classes: 0
- Functions: 3
- Status: current

**Recommendation**: Keep - Good cross-module reuse

---

### File: `mappers/pandas_time_series.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: validation/indicator_validator.py, types/strategy.py, managers/typed_strategy_manager.py
- **portfolio**: allocation/portfolio_rebalancing_service.py, core/portfolio_management_facade.py, mappers/tracking_normalization.py
- **execution**: infrastructure.py, lifecycle_simplified.py, monitoring/websocket_order_monitor.py

**File Details**:
- Size: 36 lines
- Classes: 0
- Functions: 1
- Status: current

**Recommendation**: Review for removal - No current usage found

---

### File: `math/__init__.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 1 files (engines/klm/engine.py)
- **portfolio**: 6 files (holdings/position_model.py, holdings/position_service.py, holdings/position_manager.py...)
- **execution**: 4 files (orders/service.py, orders/asset_order_handler.py, mappers/order_domain_mappers.py...)

**File Details**:
- Size: 1 lines
- Classes: 0
- Functions: 0
- Status: unknown

**Recommendation**: Keep - Well-utilized across all modules

---

### File: `math/asset_info.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 1 files (policies/fractionability_policy_impl.py)
- **execution**: 1 files (orders/asset_order_handler.py)

**Potential Usage**:
- **strategy**: engines/nuclear/logic.py, engines/value_objects/alert.py, dsl/evaluator.py
- **portfolio**: pnl/strategy_order_tracker.py, holdings/position_model.py, holdings/position_manager.py
- **execution**: orders/consolidated_validation.py, orders/request_builder.py, orders/__init__.py

**File Details**:
- Size: 237 lines
- Classes: 2
- Functions: 0
- Status: unknown

**Recommendation**: Keep - Good cross-module reuse

---

### File: `math/math_utils.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 1 files (engines/klm/engine.py)
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: engines/engine.py, engines/entities/__init__.py, engines/protocols/__init__.py
- **portfolio**: utils/portfolio_utilities.py, utils/__init__.py, pnl/strategy_order_tracker.py
- **execution**: monitoring/websocket_order_monitor.py, orders/consolidated_validation.py, orders/__init__.py

**File Details**:
- Size: 250 lines
- Classes: 0
- Functions: 8
- Status: current

**Recommendation**: Consider moving to strategy module - Single module usage

---

### File: `math/num.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 4 files (holdings/position_model.py, holdings/position_service.py, holdings/position_manager.py...)
- **execution**: 3 files (orders/service.py, mappers/order_domain_mappers.py, brokers/account_service.py)

**File Details**:
- Size: 74 lines
- Classes: 0
- Functions: 1
- Status: current

**Recommendation**: Keep - Good cross-module reuse

---

### File: `math/trading_math.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 1 files (allocation/rebalance_calculator.py)
- **execution**: 0 files

**Potential Usage**:
- **strategy**: __init__.py, validation/indicator_validator.py, engines/engine.py
- **portfolio**: utils/portfolio_utilities.py, pnl/strategy_order_tracker.py, holdings/position_model.py
- **execution**: __init__.py, orders/consolidated_validation.py, orders/request_builder.py

**File Details**:
- Size: 371 lines
- Classes: 0
- Functions: 6
- Status: unknown

**Recommendation**: Consider moving to portfolio module - Single module usage

---

### File: `notifications/client.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: data/price_service.py, data/__init__.py, data/market_data_client.py
- **portfolio**: policies/protocols.py
- **execution**: protocols/trading_repository.py, brokers/alpaca/adapter.py, lifecycle/protocols.py

**File Details**:
- Size: 151 lines
- Classes: 1
- Functions: 1
- Status: current

**Recommendation**: Review for removal - No current usage found

---

### File: `notifications/config.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: validation/indicator_validator.py, engines/core/trading_engine.py, engines/tecl/engine.py
- **portfolio**: pnl/strategy_order_tracker.py, pnl/portfolio_pnl_utils.py, holdings/position_manager.py
- **execution**: infrastructure.py, monitoring/websocket_order_monitor.py, orders/progressive_order_utils.py

**File Details**:
- Size: 134 lines
- Classes: 1
- Functions: 2
- Status: current

**Recommendation**: Review for removal - No current usage found

---

### File: `notifications/email_utils.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: engines/engine.py, engines/entities/__init__.py, engines/protocols/__init__.py
- **portfolio**: utils/portfolio_utilities.py, utils/__init__.py, pnl/strategy_order_tracker.py
- **execution**: monitoring/websocket_order_monitor.py, orders/consolidated_validation.py, orders/__init__.py

**File Details**:
- Size: 109 lines
- Classes: 0
- Functions: 6
- Status: current

**Recommendation**: Review for removal - No current usage found

---

### File: `notifications/templates/base.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: engines/engine.py, engines/__init__.py, engines/klm/base_variant.py
- **portfolio**: core/rebalancing_orchestrator.py, policies/rebalancing_policy.py, policies/base_policy.py
- **execution**: monitoring/websocket_order_monitor.py, orders/consolidated_validation.py, orders/progressive_order_utils.py

**File Details**:
- Size: 227 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Review for removal - No current usage found

---

### File: `notifications/templates/error_report.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: errors/strategy_errors.py, engines/engine.py, engines/core/trading_engine.py
- **portfolio**: utils/portfolio_utilities.py, pnl/__init__.py, pnl/strategy_order_tracker.py
- **execution**: orders/consolidated_validation.py, orders/service.py, errors/order_error.py

**File Details**:
- Size: 96 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Review for removal - No current usage found

---

### File: `notifications/templates/multi_strategy.py`

**Purpose**: Business Unit: strategy & signal generation; Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: __init__.py, validation/indicator_validator.py, errors/strategy_errors.py
- **portfolio**: __init__.py, pnl/__init__.py, pnl/strategy_order_tracker.py
- **execution**: timing/__init__.py, timing/market_timing_utils.py, config/execution_config.py

**File Details**:
- Size: 205 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Review for removal - No current usage found

---

### File: `notifications/templates/performance.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: indicators/indicators.py
- **portfolio**: pnl/__init__.py, pnl/portfolio_pnl_utils.py
- **execution**: analytics/slippage_analyzer.py, lifecycle/protocols.py

**File Details**:
- Size: 312 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Review for removal - No current usage found

---

### File: `notifications/templates/portfolio.py`

**Purpose**: Business Unit: portfolio assessment & management; Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: types/__init__.py, types/strategy.py, engines/nuclear/engine.py
- **portfolio**: __init__.py, utils/portfolio_utilities.py, utils/__init__.py
- **execution**: protocols/trading_repository.py, core/manager.py, core/execution_schemas.py

**File Details**:
- Size: 746 lines
- Classes: 2
- Functions: 1
- Status: current

**Recommendation**: Review for removal - No current usage found

---

### File: `notifications/templates/signals.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: errors/strategy_errors.py, types/strategy.py, managers/__init__.py
- **execution**: lifecycle/protocols.py

**File Details**:
- Size: 376 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Review for removal - No current usage found

---

### File: `notifications/templates/trading_report.py`

**Purpose**: Business Unit: order execution/placement; Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: __init__.py, validation/indicator_validator.py, engines/engine.py
- **portfolio**: utils/portfolio_utilities.py, pnl/__init__.py, pnl/strategy_order_tracker.py
- **execution**: __init__.py, orders/consolidated_validation.py, orders/request_builder.py

**File Details**:
- Size: 176 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Review for removal - No current usage found

---

### File: `protocols/account_like.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: engines/protocols/__init__.py, engines/klm/variants/variant_520_22.py, data/price_utils.py
- **portfolio**: calculations/portfolio_calculations.py, policies/buying_power_policy_impl.py, policies/risk_policy_impl.py
- **execution**: infrastructure.py, protocols/trading_repository.py, core/__init__.py

**File Details**:
- Size: 71 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Review for removal - No current usage found

---

### File: `protocols/asset_metadata.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: engines/protocols/__init__.py, dsl/evaluator.py, dsl/parser.py
- **portfolio**: allocation/__init__.py, mappers/tracking_normalization.py, policies/fractionability_policy_impl.py
- **execution**: orders/__init__.py, orders/asset_order_handler.py, schemas/smart_trading.py

**File Details**:
- Size: 60 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Review for removal - No current usage found

---

### File: `protocols/order_like.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: managers/typed_strategy_manager.py, engines/protocols/__init__.py, engines/core/trading_engine.py
- **portfolio**: utils/portfolio_utilities.py, pnl/__init__.py, pnl/strategy_order_tracker.py
- **execution**: infrastructure.py, __init__.py, lifecycle_simplified.py

**File Details**:
- Size: 56 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Review for removal - No current usage found

---

### File: `protocols/position_like.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: types/__init__.py, types/strategy.py, engines/protocols/__init__.py
- **portfolio**: __init__.py, utils/portfolio_utilities.py, pnl/strategy_order_tracker.py
- **execution**: infrastructure.py, core/account_facade.py, core/data_transformation_service.py

**File Details**:
- Size: 51 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Review for removal - No current usage found

---

### File: `protocols/repository.py`

**Purpose**: Business Unit: order execution/placement; Status: current.

**Current Usage**:
- **strategy**: 1 files (data/market_data_service.py)
- **portfolio**: 1 files (holdings/position_service.py)
- **execution**: 3 files (orders/service.py, brokers/account_service.py, brokers/alpaca/adapter.py)

**File Details**:
- Size: 196 lines
- Classes: 3
- Functions: 0
- Status: current

**Recommendation**: Keep - Well-utilized across all modules

---

### File: `protocols/trading.py`

**Purpose**: Business Unit: order execution/placement; Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: __init__.py, validation/indicator_validator.py, engines/engine.py
- **portfolio**: utils/portfolio_utilities.py, pnl/strategy_order_tracker.py, holdings/position_service.py
- **execution**: __init__.py, orders/request_builder.py, orders/service.py

**File Details**:
- Size: 127 lines
- Classes: 5
- Functions: 0
- Status: current

**Recommendation**: Review for removal - No current usage found

---

### File: `reporting/reporting.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 1 files (engines/core/trading_engine.py)
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: engines/core/trading_engine.py
- **portfolio**: pnl/__init__.py, pnl/strategy_order_tracker.py, holdings/position_service.py
- **execution**: orders/consolidated_validation.py

**File Details**:
- Size: 162 lines
- Classes: 0
- Functions: 3
- Status: current

**Recommendation**: Consider moving to strategy module - Single module usage

---

### File: `schemas/__init__.py`

**Purpose**: Shared schemas module.

**Current Usage**:
- **strategy**: 1 files (engines/core/trading_engine.py)
- **portfolio**: 3 files (pnl/strategy_order_tracker.py, schemas/rebalancing.py, schemas/positions.py)
- **execution**: 9 files (orders/schemas.py, core/manager.py, core/refactored_execution_manager.py...)

**File Details**:
- Size: 13 lines
- Classes: 0
- Functions: 0
- Status: current

**Recommendation**: Keep - Well-utilized across all modules

---

### File: `schemas/accounts.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 5 files (core/refactored_execution_manager.py, core/account_facade.py, core/account_management_service.py...)

**File Details**:
- Size: 144 lines
- Classes: 7
- Functions: 0
- Status: unknown

**Recommendation**: Keep - Heavy usage in execution module

---

### File: `schemas/base.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 2 files (schemas/rebalancing.py, schemas/positions.py)
- **execution**: 2 files (orders/schemas.py, schemas/smart_trading.py)

**File Details**:
- Size: 30 lines
- Classes: 1
- Functions: 0
- Status: unknown

**Recommendation**: Keep - Good cross-module reuse

---

### File: `schemas/cli.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: managers/typed_strategy_manager.py, engines/core/trading_engine.py, data/price_service.py
- **portfolio**: calculations/portfolio_calculations.py, allocation/portfolio_rebalancing_service.py, core/rebalancing_orchestrator.py
- **execution**: monitoring/websocket_order_monitor.py, orders/__init__.py, orders/schemas.py

**File Details**:
- Size: 75 lines
- Classes: 6
- Functions: 0
- Status: unknown

**Recommendation**: Review for removal - No current usage found

---

### File: `schemas/common.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 1 files (engines/core/trading_engine.py)
- **portfolio**: 0 files
- **execution**: 1 files (core/manager.py)

**Potential Usage**:
- **strategy**: engines/klm/base_variant.py, engines/klm/variants/variant_410_38.py, engines/klm/variants/variant_830_21.py
- **portfolio**: utils/portfolio_utilities.py, allocation/portfolio_rebalancing_service.py, core/rebalancing_orchestrator.py
- **execution**: monitoring/websocket_order_monitor.py, orders/__init__.py, orders/schemas.py

**File Details**:
- Size: 58 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Keep - Good cross-module reuse

---

### File: `schemas/enriched_data.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 4 files (core/refactored_execution_manager.py, core/data_transformation_service.py, core/order_execution_service.py...)

**File Details**:
- Size: 81 lines
- Classes: 4
- Functions: 0
- Status: unknown

**Recommendation**: Keep - Heavy usage in execution module

---

### File: `schemas/errors.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: errors/strategy_errors.py, engines/engine.py, dsl/__init__.py
- **portfolio**: utils/portfolio_utilities.py, allocation/portfolio_rebalancing_service.py, allocation/rebalance_execution_service.py
- **execution**: monitoring/websocket_order_monitor.py, orders/__init__.py, orders/schemas.py

**File Details**:
- Size: 71 lines
- Classes: 5
- Functions: 0
- Status: unknown

**Recommendation**: Review for removal - No current usage found

---

### File: `schemas/execution_summary.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: managers/typed_strategy_manager.py, engines/core/trading_engine.py, engines/core/__init__.py
- **portfolio**: utils/portfolio_utilities.py, pnl/strategy_order_tracker.py, pnl/portfolio_pnl_utils.py
- **execution**: infrastructure.py, __init__.py, lifecycle_simplified.py

**File Details**:
- Size: 170 lines
- Classes: 6
- Functions: 0
- Status: unknown

**Recommendation**: Review for removal - No current usage found

---

### File: `schemas/market_data.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 3 files (core/refactored_execution_manager.py, core/data_transformation_service.py, mappers/service_dto_mappers.py)

**File Details**:
- Size: 103 lines
- Classes: 5
- Functions: 0
- Status: unknown

**Recommendation**: Keep - Heavy usage in execution module

---

### File: `schemas/operations.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 3 files (core/refactored_execution_manager.py, core/order_execution_service.py, mappers/service_dto_mappers.py)

**File Details**:
- Size: 66 lines
- Classes: 3
- Functions: 0
- Status: unknown

**Recommendation**: Keep - Heavy usage in execution module

---

### File: `schemas/reporting.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 1 files (pnl/strategy_order_tracker.py)
- **execution**: 0 files

**Potential Usage**:
- **strategy**: engines/core/trading_engine.py
- **portfolio**: pnl/__init__.py, pnl/strategy_order_tracker.py, holdings/position_service.py
- **execution**: monitoring/websocket_order_monitor.py, orders/consolidated_validation.py, orders/__init__.py

**File Details**:
- Size: 96 lines
- Classes: 7
- Functions: 0
- Status: unknown

**Recommendation**: Consider moving to portfolio module - Single module usage

---

### File: `services/__init__.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 1 files (engines/core/trading_engine.py)
- **portfolio**: 1 files (pnl/strategy_order_tracker.py)
- **execution**: 2 files (core/manager.py, strategies/repeg_strategy.py)

**File Details**:
- Size: 33 lines
- Classes: 0
- Functions: 0
- Status: current

**Recommendation**: Keep - Well-utilized across all modules

---

### File: `services/alert_service.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: errors/strategy_errors.py, engines/protocols/strategy_engine.py, engines/value_objects/alert.py
- **portfolio**: utils/portfolio_utilities.py, services/__init__.py, holdings/position_service.py
- **execution**: __init__.py, orders/request_builder.py, orders/__init__.py

**File Details**:
- Size: 254 lines
- Classes: 1
- Functions: 4
- Status: current

**Recommendation**: Review for removal - No current usage found

---

### File: `services/real_time_pricing.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: validation/indicator_validator.py, types/strategy.py, managers/typed_strategy_manager.py
- **portfolio**: pnl/strategy_order_tracker.py, mappers/tracking_mapping.py, mappers/position_mapping.py
- **execution**: infrastructure.py, lifecycle_simplified.py, monitoring/websocket_order_monitor.py

**File Details**:
- Size: 753 lines
- Classes: 3
- Functions: 0
- Status: unknown

**Recommendation**: Review for removal - No current usage found

---

### File: `services/tick_size_service.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 1 files (strategies/repeg_strategy.py)

**Potential Usage**:
- **strategy**: errors/strategy_errors.py, data/streaming_service.py, data/price_service.py
- **portfolio**: utils/portfolio_utilities.py, services/__init__.py, holdings/position_service.py
- **execution**: __init__.py, orders/request_builder.py, orders/__init__.py

**File Details**:
- Size: 168 lines
- Classes: 2
- Functions: 2
- Status: unknown

**Recommendation**: Consider moving to execution module - Single module usage

---

### File: `services/websocket_connection_manager.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: managers/__init__.py, managers/typed_strategy_manager.py, engines/strategy_manager.py
- **portfolio**: utils/portfolio_utilities.py, holdings/position_manager.py, tracking/integration.py
- **execution**: __init__.py, monitoring/websocket_order_monitor.py, orders/request_builder.py

**File Details**:
- Size: 135 lines
- Classes: 1
- Functions: 0
- Status: unknown

**Recommendation**: Review for removal - No current usage found

---

### File: `simple_dto_test.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: validation/indicator_validator.py, types/strategy.py, managers/typed_strategy_manager.py
- **portfolio**: pnl/strategy_order_tracker.py, pnl/portfolio_pnl_utils.py, holdings/position_model.py
- **execution**: lifecycle_simplified.py, monitoring/websocket_order_monitor.py, orders/consolidated_validation.py

**File Details**:
- Size: 127 lines
- Classes: 0
- Functions: 4
- Status: unknown

**Recommendation**: Remove - Test/demo file with no usage

---

### File: `types/__init__.py`

**Purpose**: Business Unit: shared | Status: current

**Current Usage**:
- **strategy**: 16 files (types/strategy.py, managers/typed_strategy_manager.py, engines/engine.py...)
- **portfolio**: 6 files (pnl/strategy_order_tracker.py, holdings/position_manager.py, mappers/policy_mapping.py...)
- **execution**: 16 files (orders/consolidated_validation.py, orders/schemas.py, orders/order.py...)

**File Details**:
- Size: 13 lines
- Classes: 0
- Functions: 0
- Status: current

**Recommendation**: Keep - Well-utilized across all modules

---

### File: `types/account.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: __init__.py, types/__init__.py, types/strategy.py
- **portfolio**: pnl/portfolio_pnl_utils.py, holdings/position_model.py, holdings/__init__.py
- **execution**: monitoring/websocket_order_monitor.py, orders/consolidated_validation.py, orders/__init__.py

**File Details**:
- Size: 103 lines
- Classes: 2
- Functions: 0
- Status: current

**Recommendation**: Review for removal - No current usage found

---

### File: `types/bar.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 2 files (data/market_data_service.py, mappers/mappers.py)
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: __init__.py, types/__init__.py, types/strategy.py
- **portfolio**: pnl/portfolio_pnl_utils.py, holdings/position_model.py, holdings/__init__.py
- **execution**: monitoring/websocket_order_monitor.py, orders/consolidated_validation.py, orders/__init__.py

**File Details**:
- Size: 23 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Consider moving to strategy module - Single module usage

---

### File: `types/exceptions.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 3 files (engines/core/trading_engine.py, data/price_fetching_utils.py, data/market_data_client.py)
- **portfolio**: 4 files (pnl/strategy_order_tracker.py, holdings/position_manager.py, policies/buying_power_policy_impl.py...)
- **execution**: 7 files (orders/consolidated_validation.py, orders/asset_order_handler.py, pricing/smart_pricing_handler.py...)

**File Details**:
- Size: 315 lines
- Classes: 25
- Functions: 0
- Status: unknown

**Recommendation**: Keep - Well-utilized across all modules

---

### File: `types/market_data.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 8 files (managers/typed_strategy_manager.py, engines/engine.py, engines/nuclear/engine.py...)
- **portfolio**: 0 files
- **execution**: 0 files

**File Details**:
- Size: 190 lines
- Classes: 3
- Functions: 2
- Status: current

**Recommendation**: Keep - Heavy usage in strategy module

---

### File: `types/market_data_port.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 8 files (managers/typed_strategy_manager.py, engines/engine.py, engines/nuclear/engine.py...)
- **portfolio**: 0 files
- **execution**: 0 files

**File Details**:
- Size: 29 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Keep - Heavy usage in strategy module

---

### File: `types/money.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 1 files (mappers/policy_mapping.py)
- **execution**: 8 files (orders/schemas.py, orders/order.py, mappers/core_execution_mappers.py...)

**File Details**:
- Size: 37 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Keep - Good cross-module reuse

---

### File: `types/order_status.py`

**Purpose**: Business Unit: shared | Status: current

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 2 files (orders/order_types.py, mappers/order_domain_mappers.py)

**Potential Usage**:
- **strategy**: __init__.py, validation/indicator_validator.py, errors/strategy_errors.py
- **portfolio**: __init__.py, utils/portfolio_utilities.py, utils/__init__.py
- **execution**: infrastructure.py, __init__.py, lifecycle_simplified.py

**File Details**:
- Size: 20 lines
- Classes: 0
- Functions: 0
- Status: current

**Recommendation**: Consider moving to execution module - Single module usage

---

### File: `types/percentage.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 6 files (types/strategy.py, engines/nuclear/engine.py, engines/value_objects/strategy_signal.py...)
- **portfolio**: 0 files
- **execution**: 0 files

**File Details**:
- Size: 37 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Keep - Heavy usage in strategy module

---

### File: `types/quantity.py`

**Purpose**: Business Unit: order execution/placement; Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 3 files (mappers/policy_mapping.py, policies/fractionability_policy_impl.py, policies/position_policy_impl.py)
- **execution**: 8 files (orders/schemas.py, orders/order.py, mappers/order_domain_mappers.py...)

**File Details**:
- Size: 19 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Keep - Good cross-module reuse

---

### File: `types/quote.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 2 files (data/market_data_service.py, mappers/mappers.py)
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: __init__.py, types/__init__.py, types/strategy.py
- **portfolio**: pnl/portfolio_pnl_utils.py, holdings/position_model.py, holdings/__init__.py
- **execution**: monitoring/websocket_order_monitor.py, orders/consolidated_validation.py, orders/__init__.py

**File Details**:
- Size: 22 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Consider moving to strategy module - Single module usage

---

### File: `types/shared_kernel_types.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: __init__.py, types/__init__.py, types/strategy.py
- **portfolio**: utils/portfolio_utilities.py, utils/__init__.py, pnl/portfolio_pnl_utils.py
- **execution**: monitoring/websocket_order_monitor.py, orders/consolidated_validation.py, orders/__init__.py

**File Details**:
- Size: 13 lines
- Classes: 0
- Functions: 0
- Status: current

**Recommendation**: Remove - Small unused file

---

### File: `types/strategy_type.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 1 files (registry/strategy_registry.py)
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: __init__.py, validation/indicator_validator.py, errors/strategy_errors.py
- **portfolio**: __init__.py, pnl/__init__.py, pnl/strategy_order_tracker.py
- **execution**: monitoring/websocket_order_monitor.py, orders/consolidated_validation.py, orders/__init__.py

**File Details**:
- Size: 19 lines
- Classes: 1
- Functions: 0
- Status: unknown

**Recommendation**: Consider moving to strategy module - Single module usage

---

### File: `types/time_in_force.py`

**Purpose**: Business Unit: order execution/placement; Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 1 files (mappers/policy_mapping.py)
- **execution**: 8 files (orders/schemas.py, orders/order.py, mappers/order_domain_mappers.py...)

**File Details**:
- Size: 19 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Keep - Good cross-module reuse

---

### File: `types/trading_errors.py`

**Purpose**: Business Unit: shared | Status: current

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 1 files (pnl/strategy_order_tracker.py)
- **execution**: 1 files (orders/consolidated_validation.py)

**Potential Usage**:
- **strategy**: __init__.py, validation/indicator_validator.py, errors/strategy_errors.py
- **portfolio**: utils/portfolio_utilities.py, pnl/strategy_order_tracker.py, pnl/portfolio_pnl_utils.py
- **execution**: __init__.py, monitoring/websocket_order_monitor.py, orders/consolidated_validation.py

**File Details**:
- Size: 49 lines
- Classes: 1
- Functions: 1
- Status: current

**Recommendation**: Keep - Good cross-module reuse

---

### File: `utils/__init__.py`

**Purpose**: Utility functions and helpers.

**Current Usage**:
- **strategy**: 18 files (types/strategy.py, engines/core/trading_engine.py, engines/value_objects/alert.py...)
- **portfolio**: 6 files (pnl/strategy_order_tracker.py, holdings/position_service.py, calculations/portfolio_calculations.py...)
- **execution**: 13 files (lifecycle_simplified.py, orders/service.py, orders/schemas.py...)

**File Details**:
- Size: 36 lines
- Classes: 0
- Functions: 0
- Status: unknown

**Recommendation**: Keep - Well-utilized across all modules

---

### File: `utils/account_utils.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 1 files (calculations/portfolio_calculations.py)
- **execution**: 0 files

**Potential Usage**:
- **strategy**: engines/engine.py, engines/entities/__init__.py, engines/protocols/__init__.py
- **portfolio**: utils/portfolio_utilities.py, utils/__init__.py, pnl/strategy_order_tracker.py
- **execution**: monitoring/websocket_order_monitor.py, orders/consolidated_validation.py, orders/__init__.py

**File Details**:
- Size: 141 lines
- Classes: 0
- Functions: 4
- Status: unknown

**Recommendation**: Consider moving to portfolio module - Single module usage

---

### File: `utils/cache_manager.py`

**Purpose**: Business Unit: shared; Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: managers/__init__.py, managers/typed_strategy_manager.py, engines/strategy_manager.py
- **portfolio**: utils/portfolio_utilities.py, utils/__init__.py, pnl/strategy_order_tracker.py
- **execution**: __init__.py, monitoring/websocket_order_monitor.py, orders/consolidated_validation.py

**File Details**:
- Size: 207 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Review for removal - No current usage found

---

### File: `utils/common.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 11 files (engines/klm/base_variant.py, engines/klm/engine.py, engines/klm/variants/variant_530_18.py...)
- **portfolio**: 0 files
- **execution**: 0 files

**File Details**:
- Size: 35 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Keep - Heavy usage in strategy module

---

### File: `utils/config.py`

**Purpose**: Configuration utilities for the modular architecture.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: validation/indicator_validator.py, engines/engine.py, engines/entities/__init__.py
- **portfolio**: utils/portfolio_utilities.py, utils/__init__.py, pnl/strategy_order_tracker.py
- **execution**: infrastructure.py, monitoring/websocket_order_monitor.py, orders/consolidated_validation.py

**File Details**:
- Size: 73 lines
- Classes: 1
- Functions: 2
- Status: unknown

**Recommendation**: Review for removal - No current usage found

---

### File: `utils/context.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 1 files (engines/core/trading_engine.py)
- **portfolio**: 1 files (core/rebalancing_orchestrator_facade.py)
- **execution**: 0 files

**Potential Usage**:
- **strategy**: engines/engine.py, engines/entities/__init__.py, engines/protocols/__init__.py
- **portfolio**: utils/portfolio_utilities.py, utils/__init__.py, pnl/strategy_order_tracker.py
- **execution**: monitoring/websocket_order_monitor.py, orders/consolidated_validation.py, orders/__init__.py

**File Details**:
- Size: 66 lines
- Classes: 1
- Functions: 1
- Status: unknown

**Recommendation**: Keep - Good cross-module reuse

---

### File: `utils/decorators.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 1 files (data/market_data_service.py)
- **portfolio**: 1 files (holdings/position_service.py)
- **execution**: 5 files (orders/service.py, core/refactored_execution_manager.py, core/account_management_service.py...)

**File Details**:
- Size: 136 lines
- Classes: 0
- Functions: 5
- Status: unknown

**Recommendation**: Keep - Well-utilized across all modules

---

### File: `utils/error_monitoring.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: errors/strategy_errors.py, engines/engine.py, engines/entities/__init__.py
- **portfolio**: utils/portfolio_utilities.py, utils/__init__.py, pnl/strategy_order_tracker.py
- **execution**: infrastructure.py, __init__.py, monitoring/websocket_order_monitor.py

**File Details**:
- Size: 548 lines
- Classes: 8
- Functions: 5
- Status: unknown

**Recommendation**: Review for removal - No current usage found

---

### File: `utils/error_recovery.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: errors/strategy_errors.py, engines/engine.py, engines/entities/__init__.py
- **portfolio**: utils/portfolio_utilities.py, utils/__init__.py, pnl/strategy_order_tracker.py
- **execution**: monitoring/websocket_order_monitor.py, orders/consolidated_validation.py, orders/__init__.py

**File Details**:
- Size: 614 lines
- Classes: 14
- Functions: 4
- Status: unknown

**Recommendation**: Review for removal - No current usage found

---

### File: `utils/error_reporter.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: errors/strategy_errors.py, engines/engine.py, engines/entities/__init__.py
- **portfolio**: utils/portfolio_utilities.py, utils/__init__.py, pnl/strategy_order_tracker.py
- **execution**: monitoring/websocket_order_monitor.py, orders/consolidated_validation.py, orders/__init__.py

**File Details**:
- Size: 139 lines
- Classes: 1
- Functions: 2
- Status: unknown

**Recommendation**: Review for removal - No current usage found

---

### File: `utils/error_scope.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: errors/strategy_errors.py, engines/engine.py, engines/entities/__init__.py
- **portfolio**: utils/portfolio_utilities.py, utils/__init__.py, pnl/strategy_order_tracker.py
- **execution**: monitoring/websocket_order_monitor.py, orders/consolidated_validation.py, orders/__init__.py

**File Details**:
- Size: 106 lines
- Classes: 2
- Functions: 1
- Status: unknown

**Recommendation**: Review for removal - No current usage found

---

### File: `utils/order_completion_utils.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 3 files (orders/service.py, brokers/alpaca/adapter.py, strategies/execution_context_adapter.py)

**File Details**:
- Size: 99 lines
- Classes: 0
- Functions: 1
- Status: unknown

**Recommendation**: Keep - Heavy usage in execution module

---

### File: `utils/price_discovery_utils.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 1 files (data/market_data_client.py)
- **portfolio**: 0 files
- **execution**: 1 files (brokers/alpaca/adapter.py)

**Potential Usage**:
- **strategy**: engines/engine.py, engines/entities/__init__.py, engines/protocols/__init__.py
- **portfolio**: utils/portfolio_utilities.py, utils/__init__.py, pnl/strategy_order_tracker.py
- **execution**: monitoring/websocket_order_monitor.py, orders/consolidated_validation.py, orders/__init__.py

**File Details**:
- Size: 227 lines
- Classes: 2
- Functions: 5
- Status: unknown

**Recommendation**: Keep - Good cross-module reuse

---

### File: `utils/retry_decorator.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: engines/engine.py, engines/entities/__init__.py, engines/protocols/__init__.py
- **portfolio**: utils/portfolio_utilities.py, utils/__init__.py, pnl/strategy_order_tracker.py
- **execution**: monitoring/websocket_order_monitor.py, orders/consolidated_validation.py, orders/__init__.py

**File Details**:
- Size: 113 lines
- Classes: 0
- Functions: 4
- Status: unknown

**Recommendation**: Review for removal - No current usage found

---

### File: `utils/s3_utils.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 1 files (pnl/strategy_order_tracker.py)
- **execution**: 0 files

**Potential Usage**:
- **strategy**: engines/engine.py, engines/entities/__init__.py, engines/protocols/__init__.py
- **portfolio**: utils/portfolio_utilities.py, utils/__init__.py, pnl/strategy_order_tracker.py
- **execution**: monitoring/websocket_order_monitor.py, orders/consolidated_validation.py, orders/__init__.py

**File Details**:
- Size: 229 lines
- Classes: 2
- Functions: 2
- Status: unknown

**Recommendation**: Consider moving to portfolio module - Single module usage

---

### File: `utils/serialization.py`

**Purpose**: Business Unit: shared | Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 1 files (core/portfolio_management_facade.py)
- **execution**: 1 files (core/account_facade.py)

**Potential Usage**:
- **strategy**: engines/engine.py, engines/entities/__init__.py, engines/protocols/__init__.py
- **portfolio**: utils/portfolio_utilities.py, utils/__init__.py, pnl/strategy_order_tracker.py
- **execution**: monitoring/websocket_order_monitor.py, orders/consolidated_validation.py, orders/__init__.py

**File Details**:
- Size: 84 lines
- Classes: 1
- Functions: 3
- Status: current

**Recommendation**: Keep - Good cross-module reuse

---

### File: `utils/service_factory.py`

**Purpose**: Business Unit: shared | Status: current

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: errors/strategy_errors.py, engines/engine.py, engines/entities/__init__.py
- **portfolio**: utils/portfolio_utilities.py, utils/__init__.py, pnl/strategy_order_tracker.py
- **execution**: __init__.py, monitoring/websocket_order_monitor.py, orders/consolidated_validation.py

**File Details**:
- Size: 51 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Review for removal - No current usage found

---

### File: `utils/strategy_utils.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 0 files
- **execution**: 0 files

**Potential Usage**:
- **strategy**: __init__.py, validation/indicator_validator.py, errors/strategy_errors.py
- **portfolio**: __init__.py, utils/portfolio_utilities.py, utils/__init__.py
- **execution**: monitoring/websocket_order_monitor.py, orders/consolidated_validation.py, orders/__init__.py

**File Details**:
- Size: 44 lines
- Classes: 0
- Functions: 1
- Status: unknown

**Recommendation**: Review for removal - No current usage found

---

### File: `utils/timezone_utils.py`

**Purpose**: Unknown

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 1 files (mappers/tracking_mapping.py)
- **execution**: 3 files (lifecycle_simplified.py, mappers/core_execution_mappers.py, lifecycle/events.py)

**File Details**:
- Size: 123 lines
- Classes: 0
- Functions: 3
- Status: unknown

**Recommendation**: Keep - Good cross-module reuse

---

### File: `utils/validation_utils.py`

**Purpose**: Business Unit: shared | Status: current

**Current Usage**:
- **strategy**: 4 files (types/strategy.py, engines/value_objects/alert.py, engines/value_objects/confidence.py...)
- **portfolio**: 0 files
- **execution**: 2 files (orders/schemas.py, orders/order_types.py)

**File Details**:
- Size: 107 lines
- Classes: 0
- Functions: 4
- Status: current

**Recommendation**: Keep - Good cross-module reuse

---

### File: `value_objects/__init__.py`

**Purpose**: Common value objects and types.

**Current Usage**:
- **strategy**: 17 files (types/strategy.py, managers/typed_strategy_manager.py, engines/engine.py...)
- **portfolio**: 9 files (pnl/strategy_order_tracker.py, pnl/portfolio_pnl_utils.py, holdings/position_model.py...)
- **execution**: 15 files (orders/schemas.py, orders/order.py, orders/order_types.py...)

**File Details**:
- Size: 13 lines
- Classes: 0
- Functions: 0
- Status: unknown

**Recommendation**: Keep - Well-utilized across all modules

---

### File: `value_objects/core_types.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 8 files (types/strategy.py, engines/core/trading_engine.py, engines/klm/base_variant.py...)
- **portfolio**: 7 files (pnl/portfolio_pnl_utils.py, holdings/position_model.py, calculations/portfolio_calculations.py...)
- **execution**: 5 files (core/manager.py, core/execution_schemas.py, core/account_facade.py...)

**File Details**:
- Size: 271 lines
- Classes: 22
- Functions: 0
- Status: current

**Recommendation**: Keep - Well-utilized across all modules

---

### File: `value_objects/identifier.py`

**Purpose**: Business Unit: utilities; Status: current.

**Current Usage**:
- **strategy**: 0 files
- **portfolio**: 1 files (pnl/strategy_order_tracker.py)
- **execution**: 3 files (orders/order_types.py, errors/order_error.py, errors/classifier.py)

**File Details**:
- Size: 28 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Keep - Good cross-module reuse

---

### File: `value_objects/symbol.py`

**Purpose**: Business Unit: order execution/placement; Status: current.

**Current Usage**:
- **strategy**: 11 files (types/strategy.py, managers/typed_strategy_manager.py, engines/engine.py...)
- **portfolio**: 1 files (mappers/policy_mapping.py)
- **execution**: 8 files (orders/schemas.py, orders/order.py, mappers/order_domain_mappers.py...)

**File Details**:
- Size: 20 lines
- Classes: 1
- Functions: 0
- Status: current

**Recommendation**: Keep - Well-utilized across all modules

---


## Action Plan

### Priority 1: Remove Unused Files (57 files)

**Immediate Removal Candidates** (4 files):
- `__init__.py`
- `dto_communication_demo.py`
- `simple_dto_test.py`
- `types/shared_kernel_types.py`

**Review for Removal** (53 files):
- `adapters/execution_adapters.py`
- `adapters/integration_helpers.py`
- `adapters/portfolio_adapters.py`
- `adapters/strategy_adapters.py`
- `cli/cli.py`
- `cli/cli_formatter.py`
- `cli/dashboard_utils.py`
- `cli/error_display_utils.py`
- `cli/portfolio_calculations.py`
- `cli/signal_analyzer.py`


### Priority 2: Consolidate Single-Module Files (27 files)

Consider moving these files to their respective modules:

**Move to portfolio module** (7 files):
- `adapters/__init__.py` → `the_alchemiser/portfolio/utils/__init__.py`
- `config/secrets_manager.py` → `the_alchemiser/portfolio/utils/secrets_manager.py`
- `dto/rebalance_plan_dto.py` → `the_alchemiser/portfolio/utils/rebalance_plan_dto.py`
- `math/trading_math.py` → `the_alchemiser/portfolio/utils/trading_math.py`
- `schemas/reporting.py` → `the_alchemiser/portfolio/utils/reporting.py`

**Move to strategy module** (11 files):
- `config/bootstrap.py` → `the_alchemiser/strategy/utils/bootstrap.py`
- `config/container.py` → `the_alchemiser/strategy/utils/container.py`
- `math/math_utils.py` → `the_alchemiser/strategy/utils/math_utils.py`
- `reporting/reporting.py` → `the_alchemiser/strategy/utils/reporting.py`
- `types/bar.py` → `the_alchemiser/strategy/utils/bar.py`

**Move to execution module** (9 files):
- `dto/execution_report_dto.py` → `the_alchemiser/execution/utils/execution_report_dto.py`
- `dto/portfolio_state_dto.py` → `the_alchemiser/execution/utils/portfolio_state_dto.py`
- `schemas/accounts.py` → `the_alchemiser/execution/utils/accounts.py`
- `schemas/enriched_data.py` → `the_alchemiser/execution/utils/enriched_data.py`
- `schemas/market_data.py` → `the_alchemiser/execution/utils/market_data.py`


### Priority 3: Enhance Well-Used Files (35 files)

These files show good cross-module usage and should be maintained/enhanced:
- `config/__init__.py` - 6 files across strategy, portfolio, execution
- `config/config.py` - 5 files across strategy, portfolio, execution
- `dto/__init__.py` - 2 files across portfolio, execution
- `errors/__init__.py` - 7 files across strategy, portfolio, execution
- `errors/error_handler.py` - 7 files across strategy, portfolio, execution
- `log/__init__.py` - 12 files across strategy, portfolio, execution
- `logging/__init__.py` - 12 files across strategy, portfolio, execution
- `logging/logging.py` - 12 files across strategy, portfolio, execution
- `logging/logging_utils.py` - 12 files across strategy, portfolio, execution
- `mappers/market_data_mappers.py` - 2 files across strategy, execution


## Recommendations Summary

1. **Remove 57 unused files** to reduce codebase bloat
2. **Move 27 single-use files** to appropriate modules  
3. **Maintain 35 well-used shared utilities**
4. **Enhance documentation** for frequently-used shared components
5. **Create missing shared utilities** for common patterns found across modules

## Impact Assessment

- **Reduced Complexity**: Removing unused files will reduce maintenance burden
- **Improved Organization**: Moving single-use files to appropriate modules improves discoverability
- **Better Reuse**: Well-documented shared utilities encourage proper code reuse
- **Cleaner Architecture**: Properly organized shared module supports modular architecture goals

---

*Generated by Shared Module Audit Analysis*
*Total files analyzed: 119*
*Analysis date: 2025-09-06 07:03:04*
