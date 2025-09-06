# Refined Shims & Compatibility Layers Audit Report

## Executive Summary

This report provides a focused audit of **ACTUAL** shims, compatibility layers, and backward-compatibility code in the codebase. Unlike broader audits, this focuses on files that are genuinely shims or compatibility layers.

**Total Actual Shims Found**: 158

**Risk Distribution:**
- 🔴 **High Risk**: 125 items (active shims requiring careful migration)
- 🟡 **Medium Risk**: 33 items (import redirections and compatibility layers)
- 🟢 **Low Risk**: 0 items (backup files and cleanup items)

## Summary by Category

### Deprecated Code (48 items)

- 🔴 `scripts/rollback_legacy_deletions.py` - File explicitly marked with legacy/deprecated status
- 🔴 `scripts/focused_shim_auditor.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/main.py` (4 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/execution/monitoring/websocket_order_monitor.py` (4 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/execution/orders/service.py` (2 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/execution/core/executor.py` (4 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/execution/core/execution_schemas.py` (11 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/execution/core/account_management_service.py` (1 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/execution/core/order_execution_service.py` (1 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/execution/examples/canonical_integration.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/execution/strategies/smart_execution.py` (6 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/execution/schemas/smart_trading.py` (1 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/execution/brokers/alpaca/adapter.py` (1 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/strategy/data/domain_mapping.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/strategy/data/market_data_service.py` (9 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/strategy/data/strategy_market_data_service.py` (1 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/strategy/data/shared_market_data_service.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/strategy/mappers/mappers.py` (6 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/strategy/schemas/strategies.py` (2 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/strategy/engines/protocols/__init__.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/strategy/engines/nuclear/engine.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/strategy/engines/nuclear/logic.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/strategy/engines/core/trading_engine.py` (3 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/strategy/engines/models/strategy_signal_model.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/strategy/engines/models/strategy_position_model.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/strategy/engines/models/__init__.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/shared/cli/signal_analyzer.py` (2 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/shared/cli/cli_formatter.py` (4 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/shared/cli/cli.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/shared/cli/trading_executor.py` (1 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/shared/cli/dashboard_utils.py` (1 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/shared/value_objects/core_types.py` (34 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/shared/mappers/execution_summary_mapping.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/shared/mappers/market_data_mappers.py` (2 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/shared/schemas/execution_summary.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/shared/schemas/reporting.py` (3 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/shared/schemas/enriched_data.py` (4 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/portfolio/pnl/strategy_order_tracker.py` (6 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/portfolio/calculations/portfolio_calculations.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/portfolio/mappers/tracking_normalization.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/portfolio/mappers/tracking.py` - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/portfolio/policies/fractionability_policy_impl.py` (2 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/portfolio/schemas/tracking.py` (4 imports) - File explicitly marked with legacy/deprecated status
- 🔴 `the_alchemiser/portfolio/state/symbol_classifier.py` - File explicitly marked with legacy/deprecated status
- 🔴 `scripts/focused_shim_auditor.py` - Contains actual deprecation warnings
- 🔴 `the_alchemiser/strategy/data/strategy_market_data_service.py` (1 imports) - Contains actual deprecation warnings
- 🔴 `the_alchemiser/strategy/engines/models/strategy_signal_model.py` - Contains actual deprecation warnings
- 🔴 `the_alchemiser/strategy/engines/models/strategy_position_model.py` - Contains actual deprecation warnings

### Import Redirections (62 items)

- 🟡 `scripts/migrate_phase2_imports.py` - Contains import redirections
- 🟡 `scripts/focused_shim_auditor.py` - Contains import redirections
- 🟡 `the_alchemiser/lambda_handler.py` - Contains import redirections
- 🟡 `the_alchemiser/execution/orders/__init__.py` - Contains import redirections
- 🟡 `the_alchemiser/execution/core/__init__.py` - Contains import redirections
- 🟡 `the_alchemiser/execution/mappers/__init__.py` - Contains import redirections
- 🟡 `the_alchemiser/execution/examples/canonical_integration.py` - Contains import redirections
- 🟡 `the_alchemiser/execution/strategies/execution_context_adapter.py` - Contains import redirections
- 🟡 `the_alchemiser/execution/lifecycle/observers.py` - Contains import redirections
- 🟡 `the_alchemiser/strategy/data/__init__.py` - Contains import redirections
- 🟡 `the_alchemiser/strategy/data/domain_mapping.py` - Contains import redirections
- 🟡 `the_alchemiser/strategy/data/shared_market_data_service.py` - Contains import redirections
- 🟡 `the_alchemiser/strategy/schemas/__init__.py` - Contains import redirections
- 🟡 `the_alchemiser/strategy/dsl/__init__.py` - Contains import redirections
- 🟡 `the_alchemiser/strategy/engines/nuclear/engine.py` - Contains import redirections
- 🟡 `the_alchemiser/strategy/engines/klm/engine.py` - Contains import redirections
- 🟡 `the_alchemiser/strategy/engines/tecl/engine.py` - Contains import redirections
- 🟡 `the_alchemiser/strategy/engines/models/strategy_signal_model.py` - Contains import redirections
- 🟡 `the_alchemiser/strategy/engines/models/strategy_position_model.py` - Contains import redirections
- 🟡 `the_alchemiser/strategy/engines/models/__init__.py` - Contains import redirections
- 🟡 `the_alchemiser/shared/utils/__init__.py` - Contains import redirections
- 🟡 `the_alchemiser/shared/services/real_time_pricing.py` - Contains import redirections
- 🟡 `the_alchemiser/shared/types/__init__.py` - Contains import redirections
- 🟡 `the_alchemiser/shared/config/__init__.py` - Contains import redirections
- 🟡 `the_alchemiser/shared/value_objects/__init__.py` - Contains import redirections
- 🟡 `the_alchemiser/shared/mappers/execution_summary_mapping.py` - Contains import redirections
- 🟡 `the_alchemiser/shared/notifications/config.py` - Contains import redirections
- 🟡 `the_alchemiser/shared/schemas/execution_summary.py` - Contains import redirections
- 🟡 `the_alchemiser/shared/schemas/__init__.py` - Contains import redirections
- 🟡 `the_alchemiser/portfolio/services/__init__.py` - Contains import redirections
- 🟡 `the_alchemiser/portfolio/mappers/__init__.py` - Contains import redirections
- 🟡 `the_alchemiser/portfolio/schemas/__init__.py` - Contains import redirections
- 🔴 `the_alchemiser/main.py` (4 imports) - Contains import redirections
- 🔴 `the_alchemiser/execution/services/tick_size_service.py` (2 imports) - Contains import redirections
- 🔴 `the_alchemiser/execution/orders/schemas.py` (3 imports) - Contains import redirections
- 🔴 `the_alchemiser/execution/core/execution_schemas.py` (11 imports) - Contains import redirections
- 🔴 `the_alchemiser/execution/core/account_facade.py` (1 imports) - Contains import redirections
- 🔴 `the_alchemiser/execution/strategies/smart_execution.py` (6 imports) - Contains import redirections
- 🔴 `the_alchemiser/execution/brokers/alpaca/adapter.py` (1 imports) - Contains import redirections
- 🔴 `the_alchemiser/strategy/types/strategy.py` (4 imports) - Contains import redirections
- 🔴 `the_alchemiser/strategy/data/strategy_market_data_service.py` (1 imports) - Contains import redirections
- 🔴 `the_alchemiser/strategy/mappers/mappers.py` (6 imports) - Contains import redirections
- 🔴 `the_alchemiser/strategy/schemas/strategies.py` (2 imports) - Contains import redirections
- 🔴 `the_alchemiser/strategy/engines/core/trading_engine.py` (3 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/utils/service_factory.py` (1 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/errors/error_handler.py` (11 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/config/service_providers.py` (1 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/config/infrastructure_providers.py` (1 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/config/bootstrap.py` (3 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/protocols/repository.py` (5 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/value_objects/core_types.py` (34 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/notifications/email_utils.py` (1 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/notifications/client.py` (1 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/schemas/base.py` (8 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/schemas/accounts.py` (5 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/schemas/enriched_data.py` (4 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/schemas/operations.py` (3 imports) - Contains import redirections
- 🔴 `the_alchemiser/shared/schemas/market_data.py` (3 imports) - Contains import redirections
- 🔴 `the_alchemiser/portfolio/pnl/strategy_order_tracker.py` (6 imports) - Contains import redirections
- 🔴 `the_alchemiser/portfolio/core/rebalancing_orchestrator_facade.py` (1 imports) - Contains import redirections
- 🔴 `the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py` (2 imports) - Contains import redirections
- 🔴 `the_alchemiser/portfolio/schemas/positions.py` (3 imports) - Contains import redirections

### Legacy Named Files (3 items)

- 🟡 `scripts/focused_shim_auditor.py` - File explicitly named with *shim*
- 🔴 `scripts/rollback_legacy_deletions.py` - File explicitly named with *legacy*
- 🔴 `scripts/delete_legacy_safe.py` - File explicitly named with *legacy*

### Compatibility Shims (45 items)

- 🔴 `scripts/focused_shim_auditor.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/main.py` (4 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/lambda_handler.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/execution/orders/schemas.py` (3 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/execution/core/__init__.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/execution/core/execution_schemas.py` (11 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/execution/core/account_facade.py` (1 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/execution/strategies/smart_execution.py` (6 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/execution/lifecycle/observers.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/execution/brokers/alpaca/adapter.py` (1 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/strategy/types/strategy.py` (4 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/strategy/data/domain_mapping.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/strategy/data/strategy_market_data_service.py` (1 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/strategy/data/shared_market_data_service.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/strategy/mappers/mappers.py` (6 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/strategy/schemas/strategies.py` (2 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/strategy/engines/nuclear/engine.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/strategy/engines/core/trading_engine.py` (3 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/strategy/engines/klm/engine.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/strategy/engines/tecl/engine.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/strategy/engines/models/strategy_signal_model.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/strategy/engines/models/strategy_position_model.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/strategy/engines/models/__init__.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/utils/service_factory.py` (1 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/services/real_time_pricing.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/errors/error_handler.py` (11 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/config/service_providers.py` (1 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/config/infrastructure_providers.py` (1 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/config/bootstrap.py` (3 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/protocols/repository.py` (5 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/value_objects/core_types.py` (34 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/mappers/execution_summary_mapping.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/notifications/email_utils.py` (1 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/notifications/config.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/notifications/client.py` (1 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/schemas/base.py` (8 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/schemas/execution_summary.py` - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/schemas/accounts.py` (5 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/schemas/enriched_data.py` (4 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/schemas/operations.py` (3 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/shared/schemas/market_data.py` (3 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/portfolio/pnl/strategy_order_tracker.py` (6 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/portfolio/core/rebalancing_orchestrator_facade.py` (1 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py` (2 imports) - File explicitly describes itself as a compatibility shim
- 🔴 `the_alchemiser/portfolio/schemas/positions.py` (3 imports) - File explicitly describes itself as a compatibility shim

## Detailed Analysis

### 🔴 HIGH RISK SHIMS (125 items)

**1. rollback_legacy_deletions.py**
- **File**: `scripts/rollback_legacy_deletions.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """
Legacy Deletion Rollback Script

This script can rollback the safe deletions if needed by restor...

**2. focused_shim_auditor.py**
- **File**: `scripts/focused_shim_auditor.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Focused Shims Audit - Only Obvious Shims.

This script identifies only the most obvious shims and...

**3. main.py**
- **File**: `the_alchemiser/main.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 4 files importing this shim
- **Evidence**: Status markers: """Business Unit: utilities; Status: current.

Main Entry Point for The Alchemiser Trading System.

...; Actively imported by 4 files

**4. websocket_order_monitor.py**
- **File**: `the_alchemiser/execution/monitoring/websocket_order_monitor.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 4 files importing this shim
- **Evidence**: Status markers: """Business Unit: execution | Status: current

WebSocket Order Monitoring Utilities.

This module pr...; Actively imported by 4 files

**5. service.py**
- **File**: `the_alchemiser/execution/orders/service.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 2 files importing this shim
- **Evidence**: Status markers: """Business Unit: execution; Status: current.

Enhanced Order Service.

This service provides type-s...; Actively imported by 2 files

**6. executor.py**
- **File**: `the_alchemiser/execution/core/executor.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 4 files importing this shim
- **Evidence**: Status markers: """Business Unit: execution | Status: current

Order execution core functionality.
"""

from __futur...; Actively imported by 4 files

**7. execution_schemas.py**
- **File**: `the_alchemiser/execution/core/execution_schemas.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 11 files importing this shim
- **Evidence**: Status markers: """Business Unit: order execution/placement; Status: current.

Trading execution and result DTOs for...; Actively imported by 11 files

**8. account_management_service.py**
- **File**: `the_alchemiser/execution/core/account_management_service.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 1 files importing this shim
- **Evidence**: Status markers: """Business Unit: execution | Status: current

Account management service handling account operation...; Actively imported by 1 files

**9. order_execution_service.py**
- **File**: `the_alchemiser/execution/core/order_execution_service.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 1 files importing this shim
- **Evidence**: Status markers: """Business Unit: execution | Status: current

Order execution service handling order placement, can...; Actively imported by 1 files

**10. canonical_integration.py**
- **File**: `the_alchemiser/execution/examples/canonical_integration.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: execution | Status: current.

Integration example for canonical order executor.

T...

**11. smart_execution.py**
- **File**: `the_alchemiser/execution/strategies/smart_execution.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 6 files importing this shim
- **Evidence**: Status markers: """Business Unit: order execution/placement; Status: current.

Smart Execution Engine with Professio...; Actively imported by 6 files

**12. smart_trading.py**
- **File**: `the_alchemiser/execution/schemas/smart_trading.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 1 files importing this shim
- **Evidence**: Status markers: """Business Unit: shared | Status: current

Smart Trading - migrated from legacy location.
"""

#!/u...; Actively imported by 1 files

**13. adapter.py**
- **File**: `the_alchemiser/execution/brokers/alpaca/adapter.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 1 files importing this shim
- **Evidence**: Status markers: """Business Unit: execution; Status: current.

Alpaca broker adapter for execution module.

This mod...; Actively imported by 1 files

**14. domain_mapping.py**
- **File**: `the_alchemiser/strategy/data/domain_mapping.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: strategy & signal generation; Status: current.

Mapping utilities between strategy...

**15. market_data_service.py**
- **File**: `the_alchemiser/strategy/data/market_data_service.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 9 files importing this shim
- **Evidence**: Status markers: """Business Unit: utilities; Status: current.

Market Data Service - Enhanced market data operations...; Actively imported by 9 files

**16. strategy_market_data_service.py**
- **File**: `the_alchemiser/strategy/data/strategy_market_data_service.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 1 files importing this shim
- **Evidence**: Status markers: """Business Unit: strategy & signal generation; Status: legacy

DEPRECATED: Strategy Market Data Ser...; Actively imported by 1 files

**17. shared_market_data_service.py**
- **File**: `the_alchemiser/strategy/data/shared_market_data_service.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: strategy | Status: legacy

Market data services package exports.

StrategyMarketDa...

**18. mappers.py**
- **File**: `the_alchemiser/strategy/mappers/mappers.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 6 files importing this shim
- **Evidence**: Status markers: """Business Unit: strategy | Status: current.

Consolidated mapping utilities for strategy module.

...; Actively imported by 6 files

**19. strategies.py**
- **File**: `the_alchemiser/strategy/schemas/strategies.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 2 files importing this shim
- **Evidence**: Status markers: """Business Unit: utilities; Status: current.

Pure mapping functions for strategy signals to displa...; Actively imported by 2 files

**20. __init__.py**
- **File**: `the_alchemiser/strategy/engines/protocols/__init__.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: utilities; Status: current."""

from __future__ import annotations

from .strategy...

**21. engine.py**
- **File**: `the_alchemiser/strategy/engines/nuclear/engine.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: strategy | Status: current

Nuclear Strategy Engine.

Typed implementation of the ...

**22. logic.py**
- **File**: `the_alchemiser/strategy/engines/nuclear/logic.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: strategy | Status: current

Pure evaluation logic for the Nuclear strategy (typed,...

**23. trading_engine.py**
- **File**: `the_alchemiser/strategy/engines/core/trading_engine.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 3 files importing this shim
- **Evidence**: Status markers: """Business Unit: order execution/placement; Status: current.

Trading Engine for The Alchemiser.

U...; Actively imported by 3 files

**24. strategy_signal_model.py**
- **File**: `the_alchemiser/strategy/engines/models/strategy_signal_model.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: strategy & signal generation; Status: legacy

DEPRECATED: Strategy signal model us...

**25. strategy_position_model.py**
- **File**: `the_alchemiser/strategy/engines/models/strategy_position_model.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: strategy & signal generation; Status: legacy

DEPRECATED: Strategy position model ...

**26. __init__.py**
- **File**: `the_alchemiser/strategy/engines/models/__init__.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: strategy | Status: legacy

Legacy strategy domain models package - DEPRECATED.

Th...

**27. signal_analyzer.py**
- **File**: `the_alchemiser/shared/cli/signal_analyzer.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 2 files importing this shim
- **Evidence**: Status markers: """Business Unit: shared | Status: current

Signal analysis CLI module.

Handles signal generation a...; Actively imported by 2 files

**28. cli_formatter.py**
- **File**: `the_alchemiser/shared/cli/cli_formatter.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 4 files importing this shim
- **Evidence**: Status markers: """Business Unit: shared | Status: current

CLI formatting utilities for the trading system.
"""

fr...; Actively imported by 4 files

**29. cli.py**
- **File**: `the_alchemiser/shared/cli/cli.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: shared | Status: current

Command-Line Interface for The Alchemiser Quantitative T...

**30. trading_executor.py**
- **File**: `the_alchemiser/shared/cli/trading_executor.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 1 files importing this shim
- **Evidence**: Status markers: """Business Unit: shared | Status: current

Trading execution CLI module.

Handles trading execution...; Actively imported by 1 files

**31. dashboard_utils.py**
- **File**: `the_alchemiser/shared/cli/dashboard_utils.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 1 files importing this shim
- **Evidence**: Status markers: """Business Unit: shared | Status: current

Dashboard Utils - migrated from legacy location.
"""

#!...; Actively imported by 1 files

**32. core_types.py**
- **File**: `the_alchemiser/shared/value_objects/core_types.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 34 files importing this shim
- **Evidence**: Status markers: """Business Unit: utilities; Status: current.

Core type definitions for The Alchemiser trading syst...; Actively imported by 34 files

**33. execution_summary_mapping.py**
- **File**: `the_alchemiser/shared/mappers/execution_summary_mapping.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: shared | Status: current

Execution Summary Mapping - migrated from legacy locatio...

**34. market_data_mappers.py**
- **File**: `the_alchemiser/shared/mappers/market_data_mappers.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 2 files importing this shim
- **Evidence**: Status markers: """Business Unit: shared | Status: current

Market Data Mappers - migrated from legacy location.
"""...; Actively imported by 2 files

**35. execution_summary.py**
- **File**: `the_alchemiser/shared/schemas/execution_summary.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: shared | Status: current

Execution Summary - migrated from legacy location.
"""

...

**36. reporting.py**
- **File**: `the_alchemiser/shared/schemas/reporting.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 3 files importing this shim
- **Evidence**: Status markers: """Business Unit: shared | Status: current

Reporting - migrated from legacy location.
"""

#!/usr/b...; Actively imported by 3 files

**37. enriched_data.py**
- **File**: `the_alchemiser/shared/schemas/enriched_data.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 4 files importing this shim
- **Evidence**: Status markers: """Business Unit: shared | Status: current

Enriched Data - migrated from legacy location.
"""

#!/u...; Actively imported by 4 files

**38. strategy_order_tracker.py**
- **File**: `the_alchemiser/portfolio/pnl/strategy_order_tracker.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 6 files importing this shim
- **Evidence**: Status markers: """Business Unit: strategy & signal generation; Status: current.

Strategy Order Tracker for Per-Str...; Actively imported by 6 files

**39. portfolio_calculations.py**
- **File**: `the_alchemiser/portfolio/calculations/portfolio_calculations.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: portfolio assessment & management; Status: current.

Portfolio calculation utiliti...

**40. tracking_normalization.py**
- **File**: `the_alchemiser/portfolio/mappers/tracking_normalization.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: portfolio | Status: current

Tracking Normalization - migrated from legacy locatio...

**41. tracking.py**
- **File**: `the_alchemiser/portfolio/mappers/tracking.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: portfolio | Status: current

Tracking - migrated from legacy location.
"""

from _...

**42. fractionability_policy_impl.py**
- **File**: `the_alchemiser/portfolio/policies/fractionability_policy_impl.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 2 files importing this shim
- **Evidence**: Status markers: """Business Unit: portfolio | Status: current

Fractionability policy implementation.

Concrete impl...; Actively imported by 2 files

**43. tracking.py**
- **File**: `the_alchemiser/portfolio/schemas/tracking.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Active Imports**: 4 files importing this shim
- **Evidence**: Status markers: """Business Unit: utilities; Status: current.

Strategy Tracking DTOs for The Alchemiser Trading Sys...; Actively imported by 4 files

**44. symbol_classifier.py**
- **File**: `the_alchemiser/portfolio/state/symbol_classifier.py`
- **Description**: File explicitly marked with legacy/deprecated status
- **Purpose**: File with explicit legacy/deprecated status marker
- **Suggested Action**: review_for_migration
- **Evidence**: Status markers: """Business Unit: strategy & signal generation; Status: current.

Symbol classification for strategy...

**45. focused_shim_auditor.py**
- **File**: `scripts/focused_shim_auditor.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: File issues deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: warnings\.warn\s*\(

**46. strategy_market_data_service.py**
- **File**: `the_alchemiser/strategy/data/strategy_market_data_service.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: File issues deprecation warnings
- **Suggested Action**: review_for_removal
- **Active Imports**: 1 files importing this shim
- **Evidence**: DEPRECATED:; Actively imported by 1 files

**47. strategy_signal_model.py**
- **File**: `the_alchemiser/strategy/engines/models/strategy_signal_model.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: File issues deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: DEPRECATED:

**48. strategy_position_model.py**
- **File**: `the_alchemiser/strategy/engines/models/strategy_position_model.py`
- **Description**: Contains actual deprecation warnings
- **Purpose**: File issues deprecation warnings
- **Suggested Action**: review_for_removal
- **Evidence**: DEPRECATED:

**49. main.py**
- **File**: `the_alchemiser/main.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 4 files importing this shim
- **Evidence**: Redirection: )  # Keep global for backward compatibility during transition; Actively imported by 4 files

**50. tick_size_service.py**
- **File**: `the_alchemiser/execution/services/tick_size_service.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Redirection: # NOTE: Global singleton access was removed to align with DDD and DI rules.; Actively imported by 2 files

**51. schemas.py**
- **File**: `the_alchemiser/execution/orders/schemas.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 3 files importing this shim
- **Evidence**: Redirection: # Backward compatibility aliases; Actively imported by 3 files

**52. execution_schemas.py**
- **File**: `the_alchemiser/execution/core/execution_schemas.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 11 files importing this shim
- **Evidence**: Redirection: # NOTE: LimitOrderResultDTO moved to interfaces/schemas/orders.py to avoid duplicate; Redirection: # Backward compatibility aliases; Redirection: # Backward compatibility aliases - will be removed in future version; Actively imported by 11 files

**53. account_facade.py**
- **File**: `the_alchemiser/execution/core/account_facade.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Redirection: pass  # Fallback for backward compatibility; Actively imported by 1 files

**54. smart_execution.py**
- **File**: `the_alchemiser/execution/strategies/smart_execution.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 6 files importing this shim
- **Evidence**: Redirection: def trading_client(self) -> Any: ...  # Backward compatibility; Actively imported by 6 files

**55. adapter.py**
- **File**: `the_alchemiser/execution/brokers/alpaca/adapter.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Redirection: 3. Maintains backward compatibility; Redirection: """Get the trading client for backward compatibility."""; Redirection: """Get the data client for backward compatibility."""; Actively imported by 1 files

**56. strategy.py**
- **File**: `the_alchemiser/strategy/types/strategy.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 4 files importing this shim
- **Evidence**: Redirection: # Convenience methods for backward compatibility; Redirection: """Get unrealized P&L as float for backward compatibility."""; Redirection: """Get unrealized P&L percentage as float for backward compatibility."""; Actively imported by 4 files

**57. strategy_market_data_service.py**
- **File**: `the_alchemiser/strategy/data/strategy_market_data_service.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Redirection: # This file is kept for backward compatibility but will be removed; Redirection: # All functionality has been moved to the canonical MarketDataService; Actively imported by 1 files

**58. mappers.py**
- **File**: `the_alchemiser/strategy/mappers/mappers.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 6 files importing this shim
- **Evidence**: Redirection: """Convert QuoteModel to tuple format for backward compatibility.; Actively imported by 6 files

**59. strategies.py**
- **File**: `the_alchemiser/strategy/schemas/strategies.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Redirection: Backward Compatibility:; Actively imported by 2 files

**60. trading_engine.py**
- **File**: `the_alchemiser/strategy/engines/core/trading_engine.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 3 files importing this shim
- **Evidence**: Redirection: This is an alias for get_positions() to maintain backward compatibility.; Actively imported by 3 files

**61. service_factory.py**
- **File**: `the_alchemiser/shared/utils/service_factory.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Redirection: # Backward compatibility: direct instantiation; Actively imported by 1 files

**62. error_handler.py**
- **File**: `the_alchemiser/shared/errors/error_handler.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 11 files importing this shim
- **Evidence**: Redirection: # For any other object that might have a to_dict method (backward compatibility); Redirection: # Global enhanced error reporter instance (for backward compatibility); Actively imported by 11 files

**63. service_providers.py**
- **File**: `the_alchemiser/shared/config/service_providers.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Redirection: # Backward compatibility: provide TradingServiceManager; Actively imported by 1 files

**64. infrastructure_providers.py**
- **File**: `the_alchemiser/shared/config/infrastructure_providers.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Redirection: # Backward compatibility: provide same interface; Actively imported by 1 files

**65. bootstrap.py**
- **File**: `the_alchemiser/shared/config/bootstrap.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 3 files importing this shim
- **Evidence**: Redirection: and AlpacaManager for backward compatibility.; Actively imported by 3 files

**66. repository.py**
- **File**: `the_alchemiser/shared/protocols/repository.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 5 files importing this shim
- **Evidence**: Redirection: """Access to underlying trading client for backward compatibility.; Redirection: Note: This property is for backward compatibility during migration.; Actively imported by 5 files

**67. core_types.py**
- **File**: `the_alchemiser/shared/value_objects/core_types.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 34 files importing this shim
- **Evidence**: Redirection: core business entities and concepts. Interface/UI types have been moved to; Redirection: # Legacy field aliases for backward compatibility; Redirection: # Trading Execution Types (moved to interfaces/schemas/execution.py); Actively imported by 34 files

**68. email_utils.py**
- **File**: `the_alchemiser/shared/notifications/email_utils.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Redirection: This module now imports from the new modular email system for backward compatibility.; Redirection: This file maintains backward compatibility for existing imports.; Redirection: # Backward compatibility aliases for internal functions that might still be referenced; Actively imported by 1 files

**69. client.py**
- **File**: `the_alchemiser/shared/notifications/client.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Redirection: # Global instance for backward compatibility; Redirection: """Send an email notification (backward compatibility function)."""; Actively imported by 1 files

**70. base.py**
- **File**: `the_alchemiser/shared/schemas/base.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 8 files importing this shim
- **Evidence**: Redirection: # Backward compatibility alias - will be removed in future version; Actively imported by 8 files

**71. accounts.py**
- **File**: `the_alchemiser/shared/schemas/accounts.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 5 files importing this shim
- **Evidence**: Redirection: # Backward compatibility aliases - will be removed in future version; Actively imported by 5 files

**72. enriched_data.py**
- **File**: `the_alchemiser/shared/schemas/enriched_data.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 4 files importing this shim
- **Evidence**: Redirection: # Backward compatibility aliases - will be removed in future version; Actively imported by 4 files

**73. operations.py**
- **File**: `the_alchemiser/shared/schemas/operations.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 3 files importing this shim
- **Evidence**: Redirection: # Backward compatibility aliases - will be removed in future version; Actively imported by 3 files

**74. market_data.py**
- **File**: `the_alchemiser/shared/schemas/market_data.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 3 files importing this shim
- **Evidence**: Redirection: # Backward compatibility aliases - will be removed in future version; Actively imported by 3 files

**75. strategy_order_tracker.py**
- **File**: `the_alchemiser/portfolio/pnl/strategy_order_tracker.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 6 files importing this shim
- **Evidence**: Redirection: # Process orders with backward compatibility; Actively imported by 6 files

**76. rebalancing_orchestrator_facade.py**
- **File**: `the_alchemiser/portfolio/core/rebalancing_orchestrator_facade.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Redirection: async rebalancing cycle in a new event loop to maintain backward compatibility.; Redirection: # Run the async orchestrator method using asyncio.run for backward compatibility; Actively imported by 1 files

**77. portfolio_rebalancing_mapping.py**
- **File**: `the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Redirection: Provides backward compatibility for incomplete dict structures.; Redirection: Provides backward compatibility for incomplete dict structures.; Actively imported by 2 files

**78. positions.py**
- **File**: `the_alchemiser/portfolio/schemas/positions.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 3 files importing this shim
- **Evidence**: Redirection: # Backward compatibility aliases - will be removed in future version; Actively imported by 3 files

**79. rollback_legacy_deletions.py**
- **File**: `scripts/rollback_legacy_deletions.py`
- **Description**: File explicitly named with *legacy*
- **Purpose**: File explicitly named with legacy/deprecated pattern
- **Suggested Action**: review_for_migration
- **Evidence**: Filename pattern: *legacy*

**80. delete_legacy_safe.py**
- **File**: `scripts/delete_legacy_safe.py`
- **Description**: File explicitly named with *legacy*
- **Purpose**: File explicitly named with legacy/deprecated pattern
- **Suggested Action**: review_for_migration
- **Evidence**: Filename pattern: *legacy*

**81. focused_shim_auditor.py**
- **File**: `scripts/focused_shim_auditor.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: shim maintains, backward compatibility, import redirected

**82. main.py**
- **File**: `the_alchemiser/main.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 4 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 4 files

**83. lambda_handler.py**
- **File**: `the_alchemiser/lambda_handler.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: backward compatibility

**84. schemas.py**
- **File**: `the_alchemiser/execution/orders/schemas.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 3 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 3 files

**85. __init__.py**
- **File**: `the_alchemiser/execution/core/__init__.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: backward compatibility

**86. execution_schemas.py**
- **File**: `the_alchemiser/execution/core/execution_schemas.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 11 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 11 files

**87. account_facade.py**
- **File**: `the_alchemiser/execution/core/account_facade.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 1 files

**88. smart_execution.py**
- **File**: `the_alchemiser/execution/strategies/smart_execution.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 6 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 6 files

**89. observers.py**
- **File**: `the_alchemiser/execution/lifecycle/observers.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: backward compatibility

**90. adapter.py**
- **File**: `the_alchemiser/execution/brokers/alpaca/adapter.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Shim indicators: backward compatibility, maintains backward; Actively imported by 1 files

**91. strategy.py**
- **File**: `the_alchemiser/strategy/types/strategy.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 4 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 4 files

**92. domain_mapping.py**
- **File**: `the_alchemiser/strategy/data/domain_mapping.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: backward compatibility

**93. strategy_market_data_service.py**
- **File**: `the_alchemiser/strategy/data/strategy_market_data_service.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 1 files

**94. shared_market_data_service.py**
- **File**: `the_alchemiser/strategy/data/shared_market_data_service.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: backward compatibility

**95. mappers.py**
- **File**: `the_alchemiser/strategy/mappers/mappers.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 6 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 6 files

**96. strategies.py**
- **File**: `the_alchemiser/strategy/schemas/strategies.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 2 files

**97. engine.py**
- **File**: `the_alchemiser/strategy/engines/nuclear/engine.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: backward compatibility

**98. trading_engine.py**
- **File**: `the_alchemiser/strategy/engines/core/trading_engine.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 3 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 3 files

**99. engine.py**
- **File**: `the_alchemiser/strategy/engines/klm/engine.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: backward compatibility

**100. engine.py**
- **File**: `the_alchemiser/strategy/engines/tecl/engine.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: backward compatibility

**101. strategy_signal_model.py**
- **File**: `the_alchemiser/strategy/engines/models/strategy_signal_model.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: backward compatibility

**102. strategy_position_model.py**
- **File**: `the_alchemiser/strategy/engines/models/strategy_position_model.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: backward compatibility

**103. __init__.py**
- **File**: `the_alchemiser/strategy/engines/models/__init__.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: backward compatibility

**104. service_factory.py**
- **File**: `the_alchemiser/shared/utils/service_factory.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 1 files

**105. real_time_pricing.py**
- **File**: `the_alchemiser/shared/services/real_time_pricing.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: backward compatibility

**106. error_handler.py**
- **File**: `the_alchemiser/shared/errors/error_handler.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 11 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 11 files

**107. service_providers.py**
- **File**: `the_alchemiser/shared/config/service_providers.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 1 files

**108. infrastructure_providers.py**
- **File**: `the_alchemiser/shared/config/infrastructure_providers.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 1 files

**109. bootstrap.py**
- **File**: `the_alchemiser/shared/config/bootstrap.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 3 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 3 files

**110. repository.py**
- **File**: `the_alchemiser/shared/protocols/repository.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 5 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 5 files

**111. core_types.py**
- **File**: `the_alchemiser/shared/value_objects/core_types.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 34 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 34 files

**112. execution_summary_mapping.py**
- **File**: `the_alchemiser/shared/mappers/execution_summary_mapping.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: backward compatibility

**113. email_utils.py**
- **File**: `the_alchemiser/shared/notifications/email_utils.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Shim indicators: backward compatibility, maintains backward; Actively imported by 1 files

**114. config.py**
- **File**: `the_alchemiser/shared/notifications/config.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: backward compatibility

**115. client.py**
- **File**: `the_alchemiser/shared/notifications/client.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 1 files

**116. base.py**
- **File**: `the_alchemiser/shared/schemas/base.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 8 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 8 files

**117. execution_summary.py**
- **File**: `the_alchemiser/shared/schemas/execution_summary.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Shim indicators: backward compatibility

**118. accounts.py**
- **File**: `the_alchemiser/shared/schemas/accounts.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 5 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 5 files

**119. enriched_data.py**
- **File**: `the_alchemiser/shared/schemas/enriched_data.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 4 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 4 files

**120. operations.py**
- **File**: `the_alchemiser/shared/schemas/operations.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 3 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 3 files

**121. market_data.py**
- **File**: `the_alchemiser/shared/schemas/market_data.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 3 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 3 files

**122. strategy_order_tracker.py**
- **File**: `the_alchemiser/portfolio/pnl/strategy_order_tracker.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 6 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 6 files

**123. rebalancing_orchestrator_facade.py**
- **File**: `the_alchemiser/portfolio/core/rebalancing_orchestrator_facade.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 1 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 1 files

**124. portfolio_rebalancing_mapping.py**
- **File**: `the_alchemiser/portfolio/mappers/portfolio_rebalancing_mapping.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 2 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 2 files

**125. positions.py**
- **File**: `the_alchemiser/portfolio/schemas/positions.py`
- **Description**: File explicitly describes itself as a compatibility shim
- **Purpose**: Explicit compatibility/backward-compatibility shim
- **Suggested Action**: migrate_imports
- **Active Imports**: 3 files importing this shim
- **Evidence**: Shim indicators: backward compatibility; Actively imported by 3 files

### 🟡 MEDIUM RISK SHIMS (33 items)

**1. migrate_phase2_imports.py**
- **File**: `scripts/migrate_phase2_imports.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: print("🎯 Legacy files moved to proper modular locations")

**2. focused_shim_auditor.py**
- **File**: `scripts/focused_shim_auditor.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: # 1. Have "import *" statements; Star import: has_star_import = any("import *" in line for line in lines); Star import: star_imports = [line for line in lines if "import *" in line]; Redirection: 3. Files that explicitly redirect imports; Redirection: # 4. Files that are obviously import redirections; Redirection: self._audit_obvious_import_redirections()

**3. lambda_handler.py**
- **File**: `the_alchemiser/lambda_handler.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: Backward Compatibility:

**4. __init__.py**
- **File**: `the_alchemiser/execution/orders/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from .asset_order_handler import *; Star import: from .consolidated_validation import *; Star import: from .order_types import *

**5. __init__.py**
- **File**: `the_alchemiser/execution/core/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from .execution_schemas import *; Redirection: # Provide backward compatibility alias

**6. __init__.py**
- **File**: `the_alchemiser/execution/mappers/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from .broker_integration_mappers import *; Star import: from .core_execution_mappers import *; Star import: from .order_domain_mappers import *

**7. canonical_integration.py**
- **File**: `the_alchemiser/execution/examples/canonical_integration.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: Duplicate file core/canonical_integration_example.py was removed to eliminate redundancy.

**8. execution_context_adapter.py**
- **File**: `the_alchemiser/execution/strategies/execution_context_adapter.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: Duplicate file adapters/execution_context_adapter.py was removed to eliminate redundancy.

**9. observers.py**
- **File**: `the_alchemiser/execution/lifecycle/observers.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: ) -> None:  # Transitional: bool retained for backward compatibility

**10. __init__.py**
- **File**: `the_alchemiser/strategy/data/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from .price_fetching_utils import *; Star import: from .price_service import *; Star import: from .price_utils import *

**11. domain_mapping.py**
- **File**: `the_alchemiser/strategy/data/domain_mapping.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: # Legacy signal normalization (for backward compatibility); Redirection: strategy_signal_mapping module for backward compatibility.

**12. shared_market_data_service.py**
- **File**: `the_alchemiser/strategy/data/shared_market_data_service.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: # Import deprecated service for backward compatibility

**13. __init__.py**
- **File**: `the_alchemiser/strategy/schemas/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from .strategies import *

**14. __init__.py**
- **File**: `the_alchemiser/strategy/dsl/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from .errors import *; Star import: from .evaluator import *; Star import: from .evaluator_cache import *

**15. engine.py**
- **File**: `the_alchemiser/strategy/engines/nuclear/engine.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: Supports two calling conventions for backward compatibility:

**16. engine.py**
- **File**: `the_alchemiser/strategy/engines/klm/engine.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: Supports two calling conventions for backward compatibility:

**17. engine.py**
- **File**: `the_alchemiser/strategy/engines/tecl/engine.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: self.data_provider = data_provider  # Keep for backward compatibility with existing methods

**18. strategy_signal_model.py**
- **File**: `the_alchemiser/strategy/engines/models/strategy_signal_model.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: # Import from canonical location for backward compatibility

**19. strategy_position_model.py**
- **File**: `the_alchemiser/strategy/engines/models/strategy_position_model.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: # Import from canonical location for backward compatibility

**20. __init__.py**
- **File**: `the_alchemiser/strategy/engines/models/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: # Import from canonical location for backward compatibility

**21. __init__.py**
- **File**: `the_alchemiser/shared/utils/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from ..types.exceptions import *; Star import: from .error_reporter import *

**22. real_time_pricing.py**
- **File**: `the_alchemiser/shared/services/real_time_pricing.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: existing trading systems while maintaining backward compatibility.

**23. __init__.py**
- **File**: `the_alchemiser/shared/types/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from .broker_enums import *; Star import: from .time_in_force import *

**24. __init__.py**
- **File**: `the_alchemiser/shared/config/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from .config import *

**25. __init__.py**
- **File**: `the_alchemiser/shared/value_objects/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from .core_types import *; Star import: from .symbol import *

**26. execution_summary_mapping.py**
- **File**: `the_alchemiser/shared/mappers/execution_summary_mapping.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: Provides backward compatibility for incomplete dict structures.

**27. config.py**
- **File**: `the_alchemiser/shared/notifications/config.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: # Global instance for backward compatibility; Redirection: """Get email configuration (backward compatibility function)."""

**28. execution_summary.py**
- **File**: `the_alchemiser/shared/schemas/execution_summary.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Redirection: # Backward compatibility aliases - will be removed in future version

**29. __init__.py**
- **File**: `the_alchemiser/shared/schemas/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from .accounts import *; Star import: from .base import *; Star import: from .common import *

**30. __init__.py**
- **File**: `the_alchemiser/portfolio/services/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from .rebalancing_policy import *

**31. __init__.py**
- **File**: `the_alchemiser/portfolio/mappers/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from .portfolio_rebalancing_mapping import *; Star import: from .position_mapping import *

**32. __init__.py**
- **File**: `the_alchemiser/portfolio/schemas/__init__.py`
- **Description**: Contains import redirections
- **Purpose**: Import redirection/compatibility shim
- **Suggested Action**: migrate_imports
- **Evidence**: Star import: from .rebalancing import *; Star import: from .tracking import *

**33. focused_shim_auditor.py**
- **File**: `scripts/focused_shim_auditor.py`
- **Description**: File explicitly named with *shim*
- **Purpose**: File explicitly named with legacy/deprecated pattern
- **Suggested Action**: review_for_migration
- **Evidence**: Filename pattern: *shim*

## Specific Recommendations

### High Priority Actions

1. **Review 125 high-risk shims** - These require immediate attention
2. **Migrate 86 actively imported shims** - Update import statements first
3. **Remove backup files** - These can likely be safely deleted

### Migration Strategy

1. **Phase 1**: Update import statements for actively used shims
2. **Phase 2**: Remove or replace deprecated shims with warnings
3. **Phase 3**: Clean up backup files and unused legacy code
4. **Phase 4**: Validate no broken imports remain

### Safety Guidelines

- **Never remove a shim with active imports without migration**
- **Test after each shim removal**
- **Keep migration atomic - one shim at a time**
- **Document replacement paths for team awareness**

---

**Generated**: January 2025
**Scope**: Actual shims and compatibility layers only
**Issue**: #492
**Tool**: scripts/refined_shim_auditor.py