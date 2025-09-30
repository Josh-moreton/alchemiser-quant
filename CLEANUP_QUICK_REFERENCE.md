# Dead Code Cleanup - Quick Reference

## Files Generated

1. **DEAD_CODE_CLEANUP_REPORT.md** - Comprehensive 200+ item analysis
2. **dead_code_analysis_report.json** - Machine-readable detailed findings
3. **/tmp/vulture_output.txt** - Raw vulture tool output (670 lines)

## Key Statistics

- **Total Python files:** 217
- **Vulture findings:** 670 unused items
- **Unreferenced modules:** 88
- **TODO/FIXME markers:** 26
- **Stub files:** 6 (all intentional `__init__.py`)
- **Unused imports:** 1
- **Deprecated DTO imports:** 0 ✅

## Critical Findings

### ✅ Safe to Remove (3 items)

1. **display_utils.py** - Already marked deprecated with RuntimeError
   - File: `the_alchemiser/orchestration/display_utils.py`
   - Contains: `raise RuntimeError("...has been removed")`
   - Action: Can be deleted entirely

2. **Unused import** - env_loader
   - File: `the_alchemiser/shared/config/secrets_adapter.py:16`
   - Action: Remove import statement

3. **Empty analysis files** (created by this analysis)
   - `/tmp/vulture_output.txt`
   - `dead_code_analysis_report.json` (after review)

### ⚠️ Needs Review (20+ config variables)

**Unused Config Variables in `config.py`:**
```python
# AWS Section (Lines 49-58)
secret, region, repo_name, lambda_arn

# S3 Section (Lines 210-214)
s3_bucket, strategy_orders_path, strategy_positions_path, 
strategy_pnl_history_path, order_history_limit

# Execution Features (Lines 46, 83-84, 220-227)
enable_websocket_orders, poll_timeout, poll_interval,
max_slippage_bps, aggressive_timeout_seconds,
enable_premarket_assessment, market_open_fast_execution,
tight_spread_threshold, wide_spread_threshold,
leveraged_etf_symbols, high_volume_etfs

# Config Groups (Lines 242-247)
aws (entire section), alerts (entire section), tracking (entire section)
```

### ⚠️ Classes Likely Obsolete

1. **AlpacaAssetMetadataAdapter** - entire class unused
   - File: `the_alchemiser/shared/adapters/alpaca_asset_metadata_adapter.py`
   - Used: 0 times (grep confirmed)

2. **ConfigService** - entire class unused
   - File: `the_alchemiser/shared/config/config_service.py`

3. **TradingOrchestrator** - marked by vulture but IS USED
   - File: `the_alchemiser/orchestration/trading_orchestrator.py`
   - Status: **KEEP** - Used for test compatibility (confirmed in docstring)
   - False positive!

## Priority Actions

### Phase 1: Immediate (Low Risk)
```bash
# 1. Remove deprecated module
rm the_alchemiser/orchestration/display_utils.py

# 2. Remove unused import
# Edit: the_alchemiser/shared/config/secrets_adapter.py:16
# Remove: from ... import env_loader
```

### Phase 2: Config Cleanup (Medium Risk)
1. Review each unused config variable
2. Verify not used in production environment
3. Remove if confirmed obsolete
4. Test thoroughly

### Phase 3: Class Removal (Medium Risk)
1. Verify `AlpacaAssetMetadataAdapter` has replacement
2. Remove class if confirmed unused
3. Same for `ConfigService`

### Phase 4: Method Review (High Volume)
- 670 vulture findings need individual review
- Many are:
  - Public API methods (keep)
  - Pydantic model fields (keep)
  - Future features (document or remove)
  - Dead code (remove)

## False Positives - DO NOT REMOVE

1. ✅ `lambda_handler()` - AWS entry point
2. ✅ `TradingOrchestrator` - Used in tests
3. ✅ All `__init__.py` stub files
4. ✅ `model_config` in Pydantic models
5. ✅ `__getattr__()` functions - Dynamic imports

## How to Use Vulture Output

```bash
# See all findings
cat /tmp/vulture_output.txt

# Filter by module
grep "execution_v2" /tmp/vulture_output.txt

# Filter by confidence
grep "60% confidence" /tmp/vulture_output.txt | wc -l

# Rerun analysis
cd /home/runner/work/alchemiser-quant/alchemiser-quant
poetry run vulture the_alchemiser/ --min-confidence 60
```

## Next Steps

1. ✅ **Review this document and main report**
2. ⬜ **Create GitHub issues for each phase**
3. ⬜ **Get team approval for removals**
4. ⬜ **Execute Phase 1 cleanup**
5. ⬜ **Test after each phase**
6. ⬜ **Add CI checks to prevent future accumulation**

## CI/CD Recommendations

Add to pre-commit or CI:
```yaml
# .github/workflows/dead-code-check.yml
- name: Check for unused imports
  run: poetry run ruff check --select F401

- name: Run vulture (warning only)
  run: poetry run vulture the_alchemiser/ --min-confidence 80 || true
```

## Questions?

- Full details: See `DEAD_CODE_CLEANUP_REPORT.md`
- Raw data: See `dead_code_analysis_report.json`
- Vulture output: See `/tmp/vulture_output.txt`
