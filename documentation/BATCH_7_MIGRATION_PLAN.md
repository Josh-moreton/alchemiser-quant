# Phase 2 Migration - Batch 7 Plan

**Execution Time**: January 2025  
**Batch Size**: 15 files (systematic 15-file approach)
**Priority**: HIGH to MEDIUM - Focus on remaining high-import files

## Batch 7 Target Files (15 files)

| Priority | File | Current Location | Target Module | Imports | Size | Effort | Rationale |
|----------|------|------------------|---------------|---------|------|--------|-----------|
| 1 | `manager.py` | `execution/services/` | `execution/core/execution_manager.py` | 48 | 48988 | HIGH | Core execution management |
| 2 | `cli.py` | `interfaces/cli/` | `shared/cli/cli.py` | 44 | 49233 | HIGH | CLI interface is shared concern |
| 3 | `trading_executor.py` | `interfaces/cli/` | `shared/cli/trading_executor.py` | 35 | 24303 | HIGH | CLI trading interface |
| 4 | `alpaca_client.py` | `application/trading/` | `execution/brokers/alpaca_client.py` | 23 | 12773 | MEDIUM | Broker integration |
| 5 | `signal_analyzer.py` | `interfaces/cli/` | `shared/cli/signal_analyzer.py` | 20 | 12266 | MEDIUM | CLI signal analysis |
| 6 | `typed_klm_ensemble_engine.py` | `domain/strategies_backup/` | `strategy/engines/klm_ensemble_engine.py` | 19 | 22576 | MEDIUM | Strategy engine |
| 7 | `canonical_integration_example.py` | `application/execution/` | `execution/examples/canonical_integration.py` | 19 | 5671 | LOW | Execution example |
| 8 | `tecl_strategy_engine.py` | `domain/strategies_backup/` | `strategy/engines/tecl_strategy_engine.py` | 17 | 22598 | MEDIUM | Strategy engine |
| 9 | `policy_orchestrator.py` | `application/policies/` | `portfolio/policies/policy_orchestrator.py` | 17 | 13330 | MEDIUM | Portfolio policy management |
| 10 | `indicator_validator.py` | `infrastructure/validation/` | `strategy/validation/indicator_validator.py` | 16 | 21062 | MEDIUM | Strategy indicator validation |
| 11 | `nuclear_typed_engine.py` | `domain/strategies_backup/` | `strategy/engines/nuclear_typed_engine.py` | 16 | 18167 | MEDIUM | Strategy engine |
| 12 | `cli_formatter.py` | `interfaces/cli/` | `shared/cli/cli_formatter.py` | 15 | 32697 | MEDIUM | CLI formatting utilities |
| 13 | `websocket_order_monitor.py` | `infrastructure/websocket/` | `execution/monitoring/websocket_order_monitor.py` | 15 | 17736 | MEDIUM | Order monitoring |
| 14 | `execution_context_adapter.py` | `application/execution/strategies/` | `execution/adapters/execution_context_adapter.py` | 15 | 5145 | LOW | Execution context adaptation |
| 15 | `typed_strategy_manager.py` | `domain/strategies_backup/` | `strategy/managers/typed_strategy_manager.py` | 14 | 14221 | MEDIUM | Strategy management |

## Target Module Distribution
- **execution/**: 5 files (manager, alpaca client, monitoring, adapters, examples)
- **strategy/**: 5 files (engines, validation, managers) 
- **portfolio/**: 1 file (policy orchestrator)
- **shared/**: 4 files (CLI interfaces and utilities)

## Business Unit Alignment Rationale

### execution/ (5 files)
- **manager.py** → Core execution orchestration and management
- **alpaca_client.py** → Broker API integration and connectivity
- **websocket_order_monitor.py** → Order lifecycle monitoring and tracking
- **execution_context_adapter.py** → Execution context and adaptation logic
- **canonical_integration_example.py** → Execution integration examples

### strategy/ (5 files)  
- **typed_klm_ensemble_engine.py** → KLM ensemble strategy implementation
- **tecl_strategy_engine.py** → TECL strategy implementation
- **nuclear_typed_engine.py** → Nuclear strategy implementation  
- **indicator_validator.py** → Strategy indicator validation logic
- **typed_strategy_manager.py** → Strategy lifecycle management

### portfolio/ (1 file)
- **policy_orchestrator.py** → Portfolio policy management and orchestration

### shared/ (4 files)
- **cli.py** → Main CLI interface used across all modules
- **trading_executor.py** → CLI trading execution interface
- **signal_analyzer.py** → CLI signal analysis utilities
- **cli_formatter.py** → CLI formatting and display utilities

## Estimated Impact
- **Total imports to update**: ~290 (based on file import counts)
- **Business units affected**: All 4 modules
- **Risk level**: MEDIUM-HIGH (large files with complex dependencies)
- **Estimated effort**: 3-4 hours

## Migration Strategy
1. Start with shared/CLI files (lower risk, cross-cutting)
2. Migrate strategy engines (self-contained business logic)
3. Handle execution files (more complex dependencies)
4. Finish with portfolio policy orchestrator
5. Update all import references across codebase
6. Verify business unit boundaries maintained