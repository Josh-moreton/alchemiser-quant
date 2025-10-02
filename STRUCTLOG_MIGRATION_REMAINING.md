# Structlog Migration - Remaining Work

## Summary of Progress

### ✅ Completed
- **Phase 1**: Removed backward compatibility layer
  - Deleted `the_alchemiser/shared/logging/logging_utils.py`
  - Updated `__init__.py` to remove legacy comments
  
- **Phase 2 (Partial)**: Fixed f-string logging in critical files
  - **8 files fixed**: main.py, lambda_handler.py, alpaca_manager.py, alpaca_trading_service.py, asset_metadata_service.py, buying_power_service.py, pnl_service.py, websocket_manager.py
  - **71 instances converted** from f-string to structured logging
  - **Version bumped**: 2.1.6 → 2.2.0

### 🔄 Remaining Work
- **302 instances** of f-string logging across **47 files**

## Files Remaining (by Priority)

### High Priority (11 instances)
- `portfolio_v2/handlers/portfolio_analysis_handler.py` (11 instances)

### Medium Priority - Execution Module (112 instances)
- `execution_v2/core/executor.py` (12)
- `execution_v2/core/execution_tracker.py` (11)
- `execution_v2/core/smart_execution_strategy/repeg.py` (17)
- `execution_v2/core/smart_execution_strategy/quotes.py` (16)
- `execution_v2/core/smart_execution_strategy/strategy.py` (4)
- `execution_v2/core/phase_executor.py` (7)
- `execution_v2/core/market_order_executor.py` (7)
- `execution_v2/core/settlement_monitor.py` (6)
- `execution_v2/core/order_finalizer.py` (5)
- `execution_v2/handlers/trading_execution_handler.py` (6)
- `execution_v2/utils/position_utils.py` (13)
- `execution_v2/utils/repeg_monitoring_service.py` (5)
- Other execution files (3 instances)

### Medium Priority - Strategy Module (14 instances)
- `strategy_v2/handlers/signal_generation_handler.py` (7)
- `strategy_v2/adapters/feature_pipeline.py` (4)
- `strategy_v2/engines/dsl/strategy_engine.py` (3)

### Medium Priority - Shared Services & Utils (97 instances)
- `shared/math/trading_math.py` (45) - **LARGEST FILE**
- `shared/utils/price_discovery_utils.py` (11)
- `shared/services/alpaca_account_service.py` (12)
- `shared/services/market_data_service.py` (10)
- `shared/services/real_time_stream_manager.py` (10)
- `shared/services/real_time_pricing.py` (6)
- `shared/services/subscription_manager.py` (4)
- Other shared files (9 instances)

### Medium Priority - Orchestration & Notifications (31 instances)
- `orchestration/event_driven_orchestrator.py` (15)
- `orchestration/system.py` (8)
- `notifications_v2/service.py` (8)

## Conversion Patterns

### Simple Pattern (Safe for Automation)
```python
# Before
logger.error(f"Failed to process {symbol}: {e}")

# After
logger.error("Failed to process symbol", symbol=symbol, error=str(e))
```

### Format Spec Pattern (Requires Care)
```python
# Before
logger.info(f"Price: ${price:.2f}")

# After
logger.info("Price available", price=f"${price:.2f}")
```

### Expression Pattern (Manual Conversion Required)
```python
# Before
logger.debug(f"Found {len(items)} items")

# After
logger.debug("Found items", count=len(items))
```

### Multiline Pattern (Manual Conversion Required)
```python
# Before
logger.error(
    f"Failed after {max_retries} attempts. "
    f"Last error: {error}"
)

# After
logger.error(
    "Failed after retries",
    max_retries=max_retries,
    last_error=str(error),
)
```

## Tools Available

### Auto-Fix Script
Located at `/tmp/auto_fix_fstring.py`

**Usage:**
```bash
# Dry run (preview changes)
python /tmp/auto_fix_fstring.py <file_path>

# Apply changes
python /tmp/auto_fix_fstring.py <file_path> --apply
```

**Limitations:**
- Cannot handle expressions like `len(items)`, `attempt + 1`
- May produce invalid syntax for complex format specs
- Requires manual review for multiline f-strings

### Batch Processing
```bash
# Preview all files in a directory
for file in the_alchemiser/execution_v2/core/*.py; do
    python /tmp/auto_fix_fstring.py "$file"
done

# Apply to all files (after review)
for file in the_alchemiser/execution_v2/core/*.py; do
    python /tmp/auto_fix_fstring.py "$file" --apply
done
```

## Recommended Approach

### For Each File:
1. **Run the auto-fix script in dry-run mode**
2. **Review the proposed changes**
3. **If all look good, apply**
4. **If there are issues:**
   - Apply the script anyway to fix simple cases
   - Manually fix remaining complex patterns
5. **Test imports**: `python -c "from the_alchemiser.module import ClassName"`
6. **Commit in small batches** (5-10 files at a time)

### Priority Order:
1. Portfolio handlers (high business impact)
2. Strategy modules (core logic)
3. Shared utilities (wide impact)
4. Execution modules (large but isolated)
5. Orchestration & notifications (lower priority)

## Testing Strategy

After each batch of fixes:
```bash
# Run logging tests
python -m pytest tests/shared/logging/ -v

# Test imports
python -c "from the_alchemiser import main, lambda_handler"

# Run broader tests if needed
python -m pytest tests/ -x
```

## Notes

- All error/exception variables should use `str(e)` or `error=str(e)`
- Format specs like `:.2f` should be kept in f-strings passed as values
- Complex expressions should be assigned to descriptive variables first
- Multiline messages should use multiple keyword arguments instead

## Example Manual Conversion

### trading_math.py (45 instances - largest file)
This file likely has many debug statements with calculations. Pattern:

```python
# Before
logger.debug(f"Calculating position size: quantity={quantity}, price=${price:.2f}, total=${total:.2f}")

# After
logger.debug(
    "Calculating position size",
    quantity=quantity,
    price_formatted=f"${price:.2f}",
    total_formatted=f"${total:.2f}",
)
```

## Completion Checklist

After completing all conversions:
- [ ] All 302 remaining instances converted
- [ ] All 47 files updated
- [ ] All imports successful
- [ ] Logging tests passing
- [ ] Type checking clean (`make type-check`)
- [ ] Linting clean (`make lint`)
- [ ] Documentation updated
- [ ] Version finalized (currently 2.2.0)
