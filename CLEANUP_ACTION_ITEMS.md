# Dead Code Cleanup - Action Items

This document lists all actionable items from the dead code analysis in a structured format for tracking.

## Legend
- **Priority:** HIGH (immediate), MEDIUM (phase 1-2), LOW (phase 3+), INFO (track only)
- **Risk:** LOW (safe), MEDIUM (needs testing), HIGH (breaking change), CRITICAL (affects production)
- **Status:** TODO, IN_REVIEW, DONE, WONTFIX

---

## SAFE TO REMOVE - Immediate Action Items

| ID | Priority | Risk | File | Line | Item | Status | Notes |
|----|----------|------|------|------|------|--------|-------|
| S1 | HIGH | LOW | `orchestration/display_utils.py` | - | Entire file | TODO | Already raises RuntimeError, can delete |
| S2 | HIGH | LOW | `shared/config/secrets_adapter.py` | 16 | `env_loader` import | TODO | Unused import |

---

## CONFIG CLEANUP - Phase 1

| ID | Priority | Risk | File | Line | Variable | Status | Notes |
|----|----------|------|------|------|----------|--------|-------|
| C1 | MEDIUM | MEDIUM | `shared/config/config.py` | 46 | `enable_websocket_orders` | TODO | Verify not used in prod |
| C2 | MEDIUM | MEDIUM | `shared/config/config.py` | 49 | `secret` | TODO | AWS config |
| C3 | MEDIUM | MEDIUM | `shared/config/config.py` | 55 | `region` | TODO | AWS config |
| C4 | MEDIUM | MEDIUM | `shared/config/config.py` | 57 | `repo_name` | TODO | AWS config |
| C5 | MEDIUM | MEDIUM | `shared/config/config.py` | 58 | `lambda_arn` | TODO | AWS config |
| C6 | MEDIUM | MEDIUM | `shared/config/config.py` | 72 | `default_strategy_allocations` | TODO | Strategy config |
| C7 | MEDIUM | MEDIUM | `shared/config/config.py` | 83 | `poll_timeout` | TODO | Tracking config |
| C8 | MEDIUM | MEDIUM | `shared/config/config.py` | 84 | `poll_interval` | TODO | Tracking config |
| C9 | MEDIUM | MEDIUM | `shared/config/config.py` | 204 | `default_symbol` | TODO | Symbol config |
| C10 | MEDIUM | HIGH | `shared/config/config.py` | 210 | `s3_bucket` | TODO | S3 tracking |
| C11 | MEDIUM | HIGH | `shared/config/config.py` | 211 | `strategy_orders_path` | TODO | S3 tracking |
| C12 | MEDIUM | HIGH | `shared/config/config.py` | 212 | `strategy_positions_path` | TODO | S3 tracking |
| C13 | MEDIUM | HIGH | `shared/config/config.py` | 213 | `strategy_pnl_history_path` | TODO | S3 tracking |
| C14 | MEDIUM | HIGH | `shared/config/config.py` | 214 | `order_history_limit` | TODO | S3 tracking |
| C15 | MEDIUM | MEDIUM | `shared/config/config.py` | 220 | `max_slippage_bps` | TODO | Execution feature |
| C16 | MEDIUM | MEDIUM | `shared/config/config.py` | 221 | `aggressive_timeout_seconds` | TODO | Execution feature |
| C17 | MEDIUM | MEDIUM | `shared/config/config.py` | 223 | `enable_premarket_assessment` | TODO | Execution feature |
| C18 | MEDIUM | MEDIUM | `shared/config/config.py` | 224 | `market_open_fast_execution` | TODO | Execution feature |
| C19 | MEDIUM | MEDIUM | `shared/config/config.py` | 225 | `tight_spread_threshold` | TODO | Execution feature |
| C20 | MEDIUM | MEDIUM | `shared/config/config.py` | 226 | `wide_spread_threshold` | TODO | Execution feature |
| C21 | MEDIUM | MEDIUM | `shared/config/config.py` | 227 | `leveraged_etf_symbols` | TODO | Execution feature |
| C22 | MEDIUM | MEDIUM | `shared/config/config.py` | 230 | `high_volume_etfs` | TODO | Execution feature |
| C23 | MEDIUM | HIGH | `shared/config/config.py` | 242 | `aws` (section) | TODO | Entire config section |
| C24 | MEDIUM | MEDIUM | `shared/config/config.py` | 243 | `alerts` (section) | TODO | Entire config section |
| C25 | MEDIUM | MEDIUM | `shared/config/config.py` | 247 | `tracking` (section) | TODO | Entire config section |

---

## CLASS REMOVAL - Phase 2

| ID | Priority | Risk | File | Line | Class/Module | Status | Notes |
|----|----------|------|------|------|--------------|--------|-------|
| CL1 | MEDIUM | MEDIUM | `shared/adapters/alpaca_asset_metadata_adapter.py` | 16 | `AlpacaAssetMetadataAdapter` | TODO | Entire class - 0 imports found |
| CL2 | MEDIUM | MEDIUM | `shared/config/config_service.py` | 15 | `ConfigService` | TODO | Entire class unused |
| CL3 | LOW | MEDIUM | `execution_v2/utils/liquidity_analysis.py` | 23 | `LiquidityLevel` | TODO | Enum/class unused |

---

## METHOD CLEANUP - Phase 3 (High Priority Subset)

### Execution Module

| ID | Priority | Risk | File | Line | Method | Status | Notes |
|----|----------|------|------|------|--------|--------|-------|
| M1 | LOW | MEDIUM | `execution_v2/core/execution_tracker.py` | 18 | `log_plan_received()` | TODO | Monitoring method |
| M2 | LOW | MEDIUM | `execution_v2/core/execution_tracker.py` | 28 | `log_execution_summary()` | TODO | Monitoring method |
| M3 | LOW | MEDIUM | `execution_v2/core/execution_tracker.py` | 45 | `check_execution_health()` | TODO | Monitoring method |
| M4 | LOW | MEDIUM | `execution_v2/core/executor.py` | 577 | `shutdown()` | TODO | Lifecycle method |
| M5 | LOW | MEDIUM | `execution_v2/core/settlement_monitor.py` | 320 | `wait_for_settlement_threshold()` | TODO | Settlement tracking |
| M6 | LOW | MEDIUM | `execution_v2/core/settlement_monitor.py` | 364 | `cleanup_completed_monitors()` | TODO | Cleanup method |
| M7 | LOW | LOW | `execution_v2/utils/liquidity_analysis.py` | 281 | `validate_liquidity_for_order()` | TODO | Validation method |
| M8 | LOW | MEDIUM | `execution_v2/utils/repeg_monitoring_service.py` | 34 | `execute_repeg_monitoring_loop()` | TODO | Async monitoring |

### Orchestration Module

| ID | Priority | Risk | File | Line | Method | Status | Notes |
|----|----------|------|------|------|--------|--------|-------|
| M9 | LOW | MEDIUM | `orchestration/event_driven_orchestrator.py` | 643 | `get_workflow_status()` | TODO | Status reporting |
| M10 | LOW | MEDIUM | `orchestration/system.py` | 98 | `_emit_startup_event()` | TODO | Event emission |

### Shared/Broker Module

| ID | Priority | Risk | File | Line | Method | Status | Notes |
|----|----------|------|------|------|--------|--------|-------|
| M11 | LOW | MEDIUM | `shared/brokers/alpaca_manager.py` | 496 | `cancel_all_orders()` | TODO | Order management |
| M12 | LOW | MEDIUM | `shared/brokers/alpaca_manager.py` | 649 | `get_current_positions()` | TODO | Position query |
| M13 | LOW | LOW | `shared/brokers/alpaca_manager.py` | 693 | `cleanup_all_instances()` | TODO | Lifecycle |
| M14 | LOW | LOW | `shared/brokers/alpaca_manager.py` | 712 | `get_connection_health()` | TODO | Health check |

### Config Module

| ID | Priority | Risk | File | Line | Method | Status | Notes |
|----|----------|------|------|------|--------|--------|-------|
| M15 | MEDIUM | MEDIUM | `shared/config/config.py` | 87 | `_parse_dsl_files()` | TODO | DSL parsing |
| M16 | MEDIUM | MEDIUM | `shared/config/config.py` | 118 | `_parse_dsl_allocations()` | TODO | DSL parsing |
| M17 | MEDIUM | MEDIUM | `shared/config/config.py` | 161 | `_apply_env_profile()` | TODO | Profile config |
| M18 | LOW | LOW | `shared/config/symbols_config.py` | 119 | `add_etf_symbol()` | TODO | Symbol management |
| M19 | LOW | LOW | `shared/config/symbols_config.py` | 134 | `get_symbol_universe()` | TODO | Symbol query |

---

## FALSE POSITIVES - DO NOT REMOVE

| ID | File | Line | Item | Reason |
|----|------|------|------|--------|
| FP1 | `lambda_handler.py` | 233 | `lambda_handler()` | AWS Lambda entry point |
| FP2 | `orchestration/trading_orchestrator.py` | 73 | `TradingOrchestrator` | Used for test compatibility |
| FP3 | `*/models/*.py` | Various | `model_config` | Pydantic configuration |
| FP4 | `*/__init__.py` | Various | `__getattr__` | Dynamic import mechanism |
| FP5 | All stub `__init__.py` files | - | Package markers | Required for Python packages |

---

## INFORMATIONAL - TODO/FIXME Markers

| ID | Priority | File | Line | Marker | Notes |
|----|----------|------|------|--------|-------|
| T1 | INFO | `orchestration/display_utils.py` | 1 | PLACEHOLDER | Already deprecated |
| T2 | INFO | `strategy_v2/core/orchestrator.py` | 129 | PLACEHOLDER | Future implementation |
| T3 | INFO | `execution_v2/core/smart_execution_strategy/repeg.py` | 544 | PLACEHOLDER | Quote calculation |
| T4 | INFO | Various files | - | NOTE | 26 total markers |

See `DEAD_CODE_CLEANUP_REPORT.md` Section 3.1 for full list.

---

## UNREFERENCED MODULES - Phase 4 Review

88 modules found that are never imported. Requires individual review.

**Categories:**
1. Entry points (CLI, Lambda handlers) - KEEP
2. Test utilities - KEEP or move to tests/
3. Legacy/backup files - REMOVE
4. Work in progress - DOCUMENT or REMOVE

See `dead_code_analysis_report.json` for full list.

---

## Tracking Progress

### Summary Stats
- **Total items identified:** 200+
- **Safe to remove:** 2 items
- **Config cleanup:** 25 items
- **Class removal:** 3 items
- **Method cleanup:** 19+ high priority (670 total)
- **Unreferenced modules:** 88 items (needs review)

### Completion Tracking
```
Phase 1 (Safe):         [  ] 0/2   (0%)
Phase 2 (Config):       [  ] 0/25  (0%)
Phase 3 (Classes):      [  ] 0/3   (0%)
Phase 4 (Methods):      [  ] 0/19  (0%)
Phase 5 (Modules):      [  ] 0/88  (0%)
```

---

## How to Update This Document

After completing an item:
1. Change Status from TODO → DONE
2. Add completion date in Notes
3. Update progress bars
4. Commit changes to track progress
5. Close related GitHub issues

---

## Related Documents

1. **DEAD_CODE_CLEANUP_REPORT.md** - Full detailed analysis
2. **CLEANUP_QUICK_REFERENCE.md** - Executive summary
3. **dead_code_analysis_report.json** - Machine-readable data
4. **/tmp/vulture_output.txt** - Raw vulture output (670 lines)
