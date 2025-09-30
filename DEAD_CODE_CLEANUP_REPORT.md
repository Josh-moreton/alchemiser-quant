# The Alchemiser - Dead Code Cleanup Report

**Generated:** 2024-09-30  
**Repository:** alchemiser-quant  
**Total Python Files Analyzed:** 217  
**Total Commits:** 3000+ (accumulated technical debt)

---

## Executive Summary

This report identifies unused, obsolete, and potentially removable code across The Alchemiser codebase. The analysis was performed using:

- **Vulture** (dead code detection)
- **AST analysis** (unused imports)
- **Pattern matching** (deprecated configs, TODOs)
- **Module reference analysis** (unreferenced modules)

### High-Level Findings

| Category | Count | Risk Level |
|----------|-------|------------|
| **Unused Functions/Variables (Vulture)** | 670 | NEEDS REVIEW |
| **Unreferenced Modules** | 88 | NEEDS REVIEW |
| **TODO/FIXME Markers** | 26 | INFO |
| **Stub Files (minimal code)** | 6 | SAFE |
| **Unused Imports** | 1 | SAFE |
| **Deprecated DTO Imports** | 0 | N/A |

---

## Section 1: SAFE TO REMOVE (Low Risk)

### 1.1 Unused Imports
These imports appear unused and can be safely removed after verification.

#### Finding 1: unused env_loader import
- **File:** `the_alchemiser/shared/config/secrets_adapter.py`
- **Line:** 16
- **Issue:** `env_loader` imported but not used
- **Risk:** LOW
- **Action:** Remove import if confirmed unused

---

## Section 2: NEEDS MANUAL REVIEW (Medium/High Risk)

### 2.1 Unused Functions and Methods (Vulture - 60% confidence)

These findings require manual review to determine if they are:
- **Public API** methods that need to be kept for external callers
- **Future use** methods planned for upcoming features
- **Dead code** that can be safely removed
- **False positives** (called via reflection, dynamic imports, or tests)

#### 2.1.1 Execution Module (execution_v2/)

**High Priority - Likely Dead Code:**

1. **File:** `the_alchemiser/execution_v2/__init__.py:51`
   - **Item:** `__getattr__` function
   - **Confidence:** 60%
   - **Notes:** Lazy import mechanism - verify if needed

2. **File:** `the_alchemiser/execution_v2/core/execution_tracker.py`
   - **Line 18:** `log_plan_received()` method
   - **Line 28:** `log_execution_summary()` method
   - **Line 45:** `check_execution_health()` method
   - **Notes:** Monitoring/logging methods - may be for debugging

3. **File:** `the_alchemiser/execution_v2/core/executor.py`
   - **Line 94, 150:** `_repeg_monitoring_service` attribute (unused)
   - **Line 577:** `shutdown()` method
   - **Notes:** Lifecycle management - verify if needed

4. **File:** `the_alchemiser/execution_v2/core/settlement_monitor.py`
   - **Line 66:** `_settlement_results` attribute
   - **Line 320:** `wait_for_settlement_threshold()` method
   - **Line 364:** `cleanup_completed_monitors()` method
   - **Notes:** Settlement tracking - may be incomplete feature

**Model/Config Fields (likely benign but verify):**

5. **File:** `the_alchemiser/execution_v2/core/smart_execution_strategy/models.py`
   - **Line 26:** `strategy_recommendation` variable
   - **Line 27:** `bid_volume` variable
   - **Line 28:** `ask_volume` variable
   - **Line 43:** `original_order_id` variable
   - **Line 56:** `repeg_threshold_percent` variable
   - **Line 63:** `min_bid_ask_size_high_liquidity` variable
   - **Line 82:** `low_liquidity_symbols` variable
   - **Line 110:** `placement_timestamp` variable
   - **Notes:** These are Pydantic model fields - may be accessed dynamically

6. **File:** `the_alchemiser/execution_v2/core/smart_execution_strategy/tracking.py`
   - **Line 123:** `get_order_request()` method
   - **Line 183:** `get_filled_quantity()` method

7. **File:** `the_alchemiser/execution_v2/models/execution_result.py`
   - **Line 27, 47:** `model_config` variable (Pydantic config)
   - **Line 88:** `is_partial_success` property
   - **Notes:** Pydantic models - verify property usage

8. **File:** `the_alchemiser/execution_v2/utils/liquidity_analysis.py`
   - **Line 23:** `LiquidityLevel` class (entire class unused!)
   - **Line 28:** `depth_percent` variable
   - **Line 281:** `validate_liquidity_for_order()` method
   - **Risk:** MEDIUM - entire class/module may be obsolete

9. **File:** `the_alchemiser/execution_v2/utils/repeg_monitoring_service.py`
   - **Line 34:** `execute_repeg_monitoring_loop()` method
   - **Notes:** Async monitoring loop - may be for future use

#### 2.1.2 Lambda Handler

10. **File:** `the_alchemiser/lambda_handler.py:233`
    - **Item:** `lambda_handler()` function
    - **Confidence:** 60%
    - **Risk:** HIGH - This is AWS Lambda entry point!
    - **Action:** **DO NOT REMOVE** - False positive, used by AWS

#### 2.1.3 Orchestration Module (orchestration/)

11. **File:** `the_alchemiser/orchestration/__init__.py:25`
    - **Item:** `__getattr__` function
    - **Notes:** Lazy import mechanism

12. **File:** `the_alchemiser/orchestration/event_driven_orchestrator.py:643`
    - **Item:** `get_workflow_status()` method
    - **Notes:** Status reporting - may be for monitoring

13. **File:** `the_alchemiser/orchestration/system.py`
    - **Line 60:** `BULLET_LOG_TEMPLATE` variable
    - **Line 98:** `_emit_startup_event()` method

14. **File:** `the_alchemiser/orchestration/trading_orchestrator.py`
    - **Line 61:** `notify()` method
    - **Line 73:** `TradingOrchestrator` class (ENTIRE CLASS!)
    - **Line 140:** `execute_strategy_signals_with_trading()` method
    - **Risk:** HIGH - Entire orchestrator class marked unused
    - **Notes:** May be legacy/deprecated - needs review

#### 2.1.4 Portfolio Module (portfolio_v2/)

15. **File:** `the_alchemiser/portfolio_v2/__init__.py:56`
    - **Item:** `__getattr__` function
    - **Notes:** Lazy import mechanism

#### 2.1.5 Shared Module (shared/)

**Asset Metadata Adapter - Entire Class Unused:**

16. **File:** `the_alchemiser/shared/adapters/alpaca_asset_metadata_adapter.py`
    - **Line 16:** `AlpacaAssetMetadataAdapter` class (entire class!)
    - **Line 40:** `get_asset_class()` method
    - **Line 55:** `should_use_notional_order()` method
    - **Risk:** MEDIUM - Entire adapter unused, likely replaced

**Broker Manager (AlpacaManager):**

17. **File:** `the_alchemiser/shared/brokers/alpaca_manager.py`
    - **Line 146:** `_base_url` attribute
    - **Line 496:** `cancel_all_orders()` method
    - **Line 649:** `get_current_positions()` method
    - **Line 693:** `cleanup_all_instances()` method
    - **Line 712:** `get_connection_health()` method
    - **Notes:** Lifecycle/management methods - verify if needed

**Config Variables (HIGH PRIORITY - Many unused config fields!):**

18. **File:** `the_alchemiser/shared/config/config.py`
    - **Line 46:** `enable_websocket_orders` variable
    - **Line 49:** `secret` variable
    - **Line 55:** `region` variable
    - **Line 57:** `repo_name` variable
    - **Line 58:** `lambda_arn` variable
    - **Line 72:** `default_strategy_allocations` variable
    - **Line 83:** `poll_timeout` variable
    - **Line 84:** `poll_interval` variable
    - **Line 87:** `_parse_dsl_files()` method
    - **Line 118:** `_parse_dsl_allocations()` method
    - **Line 161:** `_apply_env_profile()` method
    - **Line 204:** `default_symbol` variable
    - **Line 210-214:** S3 config variables:
      - `s3_bucket`
      - `strategy_orders_path`
      - `strategy_positions_path`
      - `strategy_pnl_history_path`
      - `order_history_limit`
    - **Line 220-227:** Execution config variables:
      - `max_slippage_bps`
      - `aggressive_timeout_seconds`
      - `enable_premarket_assessment`
      - `market_open_fast_execution`
      - `tight_spread_threshold`
      - `wide_spread_threshold`
      - `leveraged_etf_symbols`
      - `high_volume_etfs`
    - **Line 242-247:** Top-level config groups:
      - `aws` (entire section!)
      - `alerts` (entire section!)
      - `tracking` (entire section!)
    - **Line 250:** `model_config`
    - **Line 258:** `settings_customise_sources()` method
    - **Risk:** CRITICAL - Many config variables unused
    - **Notes:** These are from failed/abandoned features

19. **File:** `the_alchemiser/shared/config/config_providers.py`
    - **Line 35:** `alpaca_endpoint` variable
    - **Line 40:** `email_recipient` variable

20. **File:** `the_alchemiser/shared/config/config_service.py`
    - **Line 15:** `ConfigService` class (entire class!)
    - **Line 49:** `get_endpoint()` method
    - **Risk:** MEDIUM - Entire config service class unused

21. **File:** `the_alchemiser/shared/config/container.py`
    - **Line 23:** `wiring_config` variable
    - **Line 75:** `create_for_testing()` method
    - **Line 86, 93:** `return_value` attributes

22. **File:** `the_alchemiser/shared/config/infrastructure_providers.py`
    - **Line 35:** `trading_repository` variable
    - **Line 36:** `market_data_repository` variable
    - **Line 37:** `account_repository` variable
    - **Notes:** Repository pattern - may be legacy

23. **File:** `the_alchemiser/shared/config/symbols_config.py`
    - **Line 119:** `add_etf_symbol()` function
    - **Line 134:** `get_symbol_universe()` function

**Error Handling:**

24. **File:** `the_alchemiser/shared/errors/catalog.py`
    - **Line 46, 54-58:** Error catalog model fields
    - **Line 204:** `get_error_spec()` function

25. **File:** `the_alchemiser/shared/errors/error_handler.py`
    - **Line 32-33:** Type aliases (ErrorList, ContextDict)
    - **Line 55:** `trading` variable
    - **Line 67:** `email_sent` variable

**Additional findings (670 total lines from Vulture) - see `/tmp/vulture_output.txt` for complete list**

---

### 2.2 Unreferenced Modules (88 modules never imported)

These modules are not imported anywhere in the codebase. They may be:
- **Entry points** (called externally, not imported)
- **Dead code** from refactoring
- **Work in progress** for future features
- **Test utilities** (used only in tests)

**High-Risk Candidates for Removal:**

Based on the analysis, these 88 modules should be reviewed individually. Key patterns:

1. **Legacy/backup files** - Files with `_backup`, `_old`, `_legacy` suffixes
2. **Test fixtures** - Files in test directories (not in scope for src cleanup)
3. **CLI entry points** - `__main__.py` files (intentionally not imported)
4. **Handler/orchestrator modules** - May be called by framework/AWS

**Action Required:** Full module list available in `dead_code_analysis_report.json` under `unreferenced_module_scanner.findings`

---

### 2.3 Stub Files with Minimal Implementation

These files have minimal code (just imports and docstrings). They may be:
- **Intentional package markers** (`__init__.py` files)
- **Placeholder modules** for future implementation
- **Candidates for removal** if truly empty

#### Findings:

1. **File:** `the_alchemiser/shared/math/__init__.py`
   - **Lines:** 3 (just docstring)
   - **Notes:** Package marker - likely intentional
   - **Action:** Keep (standard Python package structure)

2. **File:** `the_alchemiser/shared/logging/__init__.py`
   - **Lines:** 3
   - **Notes:** Package marker
   - **Action:** Keep

3. **File:** `the_alchemiser/shared/adapters/__init__.py`
   - **Lines:** 1
   - **Notes:** Empty package marker
   - **Action:** Keep (required for Python package)

4. **File:** `the_alchemiser/portfolio_v2/models/__init__.py`
   - **Lines:** 3
   - **Notes:** Package marker
   - **Action:** Keep

5. **File:** `the_alchemiser/portfolio_v2/core/__init__.py`
   - **Lines:** 3
   - **Notes:** Package marker
   - **Action:** Keep

6. **File:** `the_alchemiser/portfolio_v2/adapters/__init__.py`
   - **Lines:** 3
   - **Notes:** Package marker
   - **Action:** Keep

**Recommendation:** All stub files are `__init__.py` package markers - **KEEP ALL**

---

## Section 3: INFORMATIONAL (Technical Debt Markers)

### 3.1 TODO/FIXME/PLACEHOLDER Comments (26 findings)

These comments indicate areas needing attention but don't necessarily mean the code is dead. They represent technical debt.

#### High-Priority TODOs:

1. **File:** `the_alchemiser/orchestration/display_utils.py:1`
   - **Marker:** PLACEHOLDER
   - **Content:** "Deprecated module placeholder"
   - **Action:** This entire module is marked deprecated - consider removal

2. **File:** `the_alchemiser/execution_v2/handlers/trading_execution_handler.py:158`
   - **Marker:** NOTE
   - **Content:** ExecutionResult.metadata is read-only (frozen)
   - **Action:** Informational

3. **File:** `the_alchemiser/execution_v2/core/smart_execution_strategy/repeg.py:544`
   - **Marker:** PLACEHOLDER
   - **Content:** Quote calculation placeholder
   - **Action:** Incomplete implementation

4. **File:** `the_alchemiser/strategy_v2/core/orchestrator.py:129`
   - **Marker:** PLACEHOLDER
   - **Content:** "This is a placeholder implementation. In future phases..."
   - **Action:** Planned for future - document timeline

5. **File:** `the_alchemiser/strategy_v2/adapters/market_data_adapter.py:97`
   - **Marker:** NOTE
   - **Content:** Could be optimized for batch requests
   - **Action:** Performance optimization opportunity

**Full list of 26 TODO/FIXME markers available in `dead_code_analysis_report.json`**

---

## Section 4: CRITICAL FINDINGS SUMMARY

### 4.1 High-Priority Deprecated Code

Based on CHANGELOG.md, the following has been removed but needs verification:

1. ✅ **Deprecated DTO imports** - No remaining imports of `the_alchemiser.shared.dto` found (CLEAN)
2. ⚠️ **Legacy orchestrator** - `TradingOrchestrator` class marked as unused (Line 73)
3. ⚠️ **Config bloat** - 20+ unused config variables in `config.py`
4. ⚠️ **Unused adapters** - `AlpacaAssetMetadataAdapter` entire class unused

### 4.2 Unused Config Variables (Abandoned Features)

The following config sections appear completely unused and are candidates for removal:

**AWS Section:**
- `aws.region`
- `aws.repo_name`
- `aws.lambda_arn`
- `aws.secret`

**S3 Tracking (Legacy):**
- `s3_bucket`
- `strategy_orders_path`
- `strategy_positions_path`
- `strategy_pnl_history_path`
- `order_history_limit`

**Advanced Execution Features (Unused):**
- `enable_websocket_orders`
- `enable_premarket_assessment`
- `market_open_fast_execution`
- `max_slippage_bps`
- `aggressive_timeout_seconds`

**Alerts/Notifications:**
- `alerts.*` (entire section)
- `email_recipient`

**Tracking:**
- `tracking.*` (entire section)
- `poll_timeout`
- `poll_interval`

### 4.3 Classes/Modules Likely Obsolete

1. **`TradingOrchestrator`** (orchestration/trading_orchestrator.py)
   - Entire class marked unused
   - May be replaced by `event_driven_orchestrator.py`

2. **`ConfigService`** (shared/config/config_service.py)
   - Entire class unused
   - Likely replaced by pydantic-settings approach

3. **`AlpacaAssetMetadataAdapter`** (shared/adapters/)
   - Entire class unused
   - Functionality may be integrated elsewhere

4. **`LiquidityLevel`** (execution_v2/utils/liquidity_analysis.py)
   - Entire enum/class unused

5. **`display_utils.py`** (orchestration/)
   - Marked as "Deprecated module placeholder"

---

## Section 5: RECOMMENDATIONS

### 5.1 Immediate Actions (Safe)

1. ✅ Remove unused import: `env_loader` from `secrets_adapter.py`
2. ✅ Remove deprecated module: `orchestration/display_utils.py`
3. ✅ Add `.gitignore` entry for analysis reports

### 5.2 Phase 1 Cleanup (Low Risk)

1. Remove unused config variables (after verifying not used in prod):
   - AWS config section (if not using Lambda)
   - S3 tracking paths (if not using S3)
   - Alerts/notifications config (if not implemented)

2. Remove deprecated adapters:
   - `AlpacaAssetMetadataAdapter` (verify replacements)
   - `ConfigService` class (replaced by Settings)

3. Remove unused utility methods:
   - Lifecycle methods in `AlpacaManager` (if not called)
   - Monitoring methods in execution trackers

### 5.3 Phase 2 Cleanup (Medium Risk - Needs Testing)

1. Review and remove unused methods in:
   - `execution_v2/core/executor.py`
   - `execution_v2/core/settlement_monitor.py`
   - `orchestration/event_driven_orchestrator.py`

2. Evaluate `TradingOrchestrator` class:
   - If replaced by `EventDrivenOrchestrator`, remove
   - Update documentation if keeping

3. Clean up model fields:
   - Verify Pydantic model fields are actually used
   - Remove unused fields from DTOs

### 5.4 Phase 3 Review (High Risk - Architecture Changes)

1. Review 88 unreferenced modules individually
2. Identify modules that are:
   - Entry points (keep)
   - Legacy code (remove)
   - Work in progress (document timeline)

3. Consolidate TODO/FIXME items:
   - Create issues for placeholders
   - Set deadlines for incomplete features
   - Document or remove "future phases" code

### 5.5 Ongoing Maintenance

1. **Add pre-commit hook** to detect unused imports (ruff F401)
2. **Run vulture regularly** in CI pipeline
3. **Enforce import boundaries** (already configured in import-linter)
4. **Document public APIs** to prevent false-positive removals
5. **Code review checklist** - verify new code doesn't add dead code

---

## Section 6: FALSE POSITIVES TO IGNORE

These items are flagged but should **NOT** be removed:

1. ❌ `lambda_handler()` - AWS Lambda entry point
2. ❌ `__init__.py` stub files - Python package markers
3. ❌ Pydantic `model_config` - Framework configuration
4. ❌ `__getattr__()` functions - Dynamic imports/lazy loading
5. ❌ `__main__.py` modules - CLI entry points
6. ❌ Test fixtures and utilities (if in tests/)

---

## Section 7: RISK ASSESSMENT

| Category | Files | Risk | Priority |
|----------|-------|------|----------|
| Deprecated modules | 2 | LOW | HIGH |
| Unused imports | 1 | LOW | HIGH |
| Unused config vars | 20+ | MEDIUM | MEDIUM |
| Unused classes | 3 | MEDIUM | MEDIUM |
| Unused methods | 100+ | VARIES | LOW |
| Unreferenced modules | 88 | HIGH | LOW |
| Stub files | 6 | NONE | N/A |
| TODO markers | 26 | NONE | INFO |

**Total Items for Review:** ~200+  
**Safe to Remove Immediately:** ~3 items  
**Needs Manual Review:** ~200 items  

---

## Appendix A: How to Use This Report

### For Immediate Cleanup:
```bash
# 1. Remove deprecated module
git rm the_alchemiser/orchestration/display_utils.py

# 2. Remove unused import (edit file)
# Edit: the_alchemiser/shared/config/secrets_adapter.py:16
```

### For Config Cleanup:
```bash
# 1. Review config.py and remove unused variables
# Edit: the_alchemiser/shared/config/config.py

# 2. Test with: make test-all

# 3. Deploy to staging and verify
```

### For Ongoing Monitoring:
```bash
# Run vulture regularly
poetry run vulture the_alchemiser/ --min-confidence 60

# Check for unused imports
poetry run ruff check the_alchemiser/ --select F401

# Verify import boundaries
make import-check
```

---

## Appendix B: Analysis Tools Used

1. **Vulture 2.14**
   - Minimum confidence: 60%
   - 670 findings
   - File: `/tmp/vulture_output.txt`

2. **AST Parser (Python)**
   - Custom unused import detection
   - Pattern matching for deprecated code

3. **Grep/Regex**
   - TODO/FIXME marker detection
   - Deprecated pattern search

4. **Import Analysis**
   - Module reference graph
   - Unreferenced module detection

---

## Appendix C: Files for Manual Review

**Full detailed report:** `dead_code_analysis_report.json`  
**Vulture output:** `/tmp/vulture_output.txt` (670 lines)  
**This report:** `DEAD_CODE_CLEANUP_REPORT.md`

---

## Contact & Next Steps

This report provides a comprehensive overview of technical debt and unused code. The next steps are:

1. ✅ **Review this report** with the team
2. ⬜ **Prioritize cleanup phases** (1-3)
3. ⬜ **Create cleanup issues** for each phase
4. ⬜ **Schedule cleanup sprints**
5. ⬜ **Add monitoring** to prevent future accumulation

**Report Status:** ✅ COMPLETE  
**Action Required:** Team review and prioritization
