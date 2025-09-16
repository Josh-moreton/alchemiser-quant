# Dead Code Detection Report

Generated on: Tue Sep 16 17:27:42 UTC 2025

## Executive Summary

- **High Confidence Issues**: 0 (safe to remove)
- **Medium Confidence Issues**: 0 (review recommended)
- **Low Confidence Issues**: 0 (manual validation needed)
- **Unused Imports**: 0
- **Unreachable Modules**: 94

## 1. High Confidence Dead Code (Safe to Remove)

These items have been detected with high confidence as unused and can be safely removed:

✅ No high confidence dead code detected


## 2. Medium Confidence Dead Code (Review Recommended)

These items likely contain dead code but should be reviewed before removal:

✅ No medium confidence dead code detected


## 3. Low Confidence Issues (Manual Validation Needed)

These items may contain dead code but require careful manual review:

✅ No low confidence issues detected


## 4. Unused Imports (Auto-Fixable)

These imports are not used and can be automatically removed:

✅ No unused imports detected


## 5. Unreachable Modules

These modules are never imported anywhere and may be orphaned:

- **scripts.probe_realtime_pricing** (never imported)
- **the_alchemiser** (never imported)
- **the_alchemiser.execution_v2** (never imported)
- **the_alchemiser.execution_v2.core** (never imported)
- **the_alchemiser.execution_v2.models** (never imported)
- **the_alchemiser.execution_v2.utils** (never imported)
- **the_alchemiser.lambda_handler** (never imported)
- **the_alchemiser.orchestration** (never imported)
- **the_alchemiser.portfolio_v2.adapters** (never imported)
- **the_alchemiser.portfolio_v2.core** (never imported)
- **the_alchemiser.portfolio_v2.core.planner** (never imported)
- **the_alchemiser.portfolio_v2.core.portfolio_service** (never imported)
- **the_alchemiser.portfolio_v2.core.state_reader** (never imported)
- **the_alchemiser.portfolio_v2.models** (never imported)
- **the_alchemiser.portfolio_v2.models.portfolio_snapshot** (never imported)
- **the_alchemiser.shared** (never imported)
- **the_alchemiser.shared.cli.cli** (never imported)
- **the_alchemiser.shared.cli.dashboard_utils** (never imported)
- **the_alchemiser.shared.config.config_service** (never imported)
- **the_alchemiser.shared.config.env_loader** (never imported)
- **the_alchemiser.shared.errors** (never imported)
- **the_alchemiser.shared.errors.context** (never imported)
- **the_alchemiser.shared.events.base** (never imported)
- **the_alchemiser.shared.events.handlers** (never imported)
- **the_alchemiser.shared.events.schemas** (never imported)
- **the_alchemiser.shared.logging** (never imported)
- **the_alchemiser.shared.mappers.execution_summary_mapping** (never imported)
- **the_alchemiser.shared.mappers.market_data_mappers** (never imported)
- **the_alchemiser.shared.math** (never imported)
- **the_alchemiser.shared.math.asset_info** (never imported)
- **the_alchemiser.shared.math.trading_math** (never imported)
- **the_alchemiser.shared.notifications.config** (never imported)
- **the_alchemiser.shared.notifications.templates.base** (never imported)
- **the_alchemiser.shared.notifications.templates.email_facade** (never imported)
- **the_alchemiser.shared.notifications.templates.multi_strategy** (never imported)
- **the_alchemiser.shared.notifications.templates.performance** (never imported)
- **the_alchemiser.shared.notifications.templates.portfolio** (never imported)
- **the_alchemiser.shared.notifications.templates.signals** (never imported)
- **the_alchemiser.shared.persistence** (never imported)
- **the_alchemiser.shared.persistence.factory** (never imported)
- **the_alchemiser.shared.protocols.alpaca** (never imported)
- **the_alchemiser.shared.protocols.order_like** (never imported)
- **the_alchemiser.shared.schemas** (never imported)
- **the_alchemiser.shared.schemas.accounts** (never imported)
- **the_alchemiser.shared.schemas.cli** (never imported)
- **the_alchemiser.shared.schemas.enriched_data** (never imported)
- **the_alchemiser.shared.schemas.errors** (never imported)
- **the_alchemiser.shared.schemas.market_data** (never imported)
- **the_alchemiser.shared.schemas.operations** (never imported)
- **the_alchemiser.shared.services** (never imported)
- **the_alchemiser.shared.types.account** (never imported)
- **the_alchemiser.shared.types.broker_enums** (never imported)
- **the_alchemiser.shared.types.money** (never imported)
- **the_alchemiser.shared.types.quantity** (never imported)
- **the_alchemiser.shared.types.strategy_protocol** (never imported)
- **the_alchemiser.shared.types.strategy_value_objects** (never imported)
- **the_alchemiser.shared.types.time_in_force** (never imported)
- **the_alchemiser.shared.utils** (never imported)
- **the_alchemiser.shared.utils.config** (never imported)
- **the_alchemiser.shared.utils.context** (never imported)
- **the_alchemiser.shared.utils.decorators** (never imported)
- **the_alchemiser.shared.utils.dto_conversion** (never imported)
- **the_alchemiser.shared.utils.error_reporter** (never imported)
- **the_alchemiser.shared.utils.serialization** (never imported)
- **the_alchemiser.shared.utils.timezone_utils** (never imported)
- **the_alchemiser.shared.value_objects** (never imported)
- **the_alchemiser.strategy_v2** (never imported)
- **the_alchemiser.strategy_v2.adapters** (never imported)
- **the_alchemiser.strategy_v2.adapters.feature_pipeline** (never imported)
- **the_alchemiser.strategy_v2.adapters.market_data_adapter** (never imported)
- **the_alchemiser.strategy_v2.cli** (never imported)
- **the_alchemiser.strategy_v2.core** (never imported)
- **the_alchemiser.strategy_v2.core.factory** (never imported)
- **the_alchemiser.strategy_v2.core.orchestrator** (never imported)
- **the_alchemiser.strategy_v2.core.registry** (never imported)
- **the_alchemiser.strategy_v2.engines** (never imported)
- **the_alchemiser.strategy_v2.engines.klm** (never imported)
- **the_alchemiser.strategy_v2.engines.klm.base_variant** (never imported)
- **the_alchemiser.strategy_v2.engines.klm.variants** (never imported)
- **the_alchemiser.strategy_v2.engines.klm.variants.variant_1200_28** (never imported)
- **the_alchemiser.strategy_v2.engines.klm.variants.variant_1280_26** (never imported)
- **the_alchemiser.strategy_v2.engines.klm.variants.variant_410_38** (never imported)
- **the_alchemiser.strategy_v2.engines.klm.variants.variant_506_38** (never imported)
- **the_alchemiser.strategy_v2.engines.klm.variants.variant_520_22** (never imported)
- **the_alchemiser.strategy_v2.engines.klm.variants.variant_530_18** (never imported)
- **the_alchemiser.strategy_v2.engines.klm.variants.variant_830_21** (never imported)
- **the_alchemiser.strategy_v2.engines.klm.variants.variant_nova** (never imported)
- **the_alchemiser.strategy_v2.engines.nuclear.constants** (never imported)
- **the_alchemiser.strategy_v2.engines.nuclear.logic** (never imported)
- **the_alchemiser.strategy_v2.engines.tecl** (never imported)
- **the_alchemiser.strategy_v2.errors** (never imported)
- **the_alchemiser.strategy_v2.indicators** (never imported)
- **the_alchemiser.strategy_v2.models** (never imported)
- **the_alchemiser.strategy_v2.models.context** (never imported)


## 6. Circular Dependencies (Technical Debt)

These circular import relationships should be resolved:

✅ No circular dependencies detected


## 7. Cleanup Recommendations

### Immediate Actions (Low Risk)

1. **Remove unused imports**:
   ```bash
   poetry run ruff check --fix the_alchemiser --select F401
   ```

2. **High confidence dead code removal**:
   - ✅ No high confidence dead code to remove


### Review Required (Medium Risk)

1. **Medium confidence issues**:
   - ✅ No medium confidence issues to review


2. **Unreachable modules**:
   - Verify these modules are truly unused
   - Check for dynamic imports or runtime loading
   - Modules to review: 94


### Architectural Improvements (Planning Required)

1. **Circular dependency resolution**:
   - ✅ Clean import architecture


## 8. Validation Process

Before removing any dead code:

1. **Run the full test suite**:
   ```bash
   poetry run pytest
   ```

2. **Check for dynamic imports**:
   ```bash
   grep -r "importlib\|__import__" the_alchemiser/
   ```

3. **Verify runtime behavior**:
   ```bash
   poetry run python the_alchemiser/main.py --help
   ```

4. **Review git history** for recent changes to flagged items

## 9. Risk Assessment

| Category | Risk Level | Action Required |
|----------|------------|----------------|
| Unused Imports | 🟢 Low | Auto-fix with ruff |
| High Confidence Dead Code | 🟢 Low | Safe to remove after tests |
| Medium Confidence Issues | 🟡 Medium | Manual review required |
| Low Confidence Issues | 🔴 High | Careful analysis needed |
| Unreachable Modules | 🟡 Medium | Verify usage patterns |
| Circular Dependencies | 🟡 Medium | Architectural refactoring |

---

## Reproducibility

This report was generated using:

```bash
# Dead code detection
poetry run vulture the_alchemiser --min-confidence 80

# Unused import detection  
poetry run ruff check the_alchemiser --select F401

# Custom dependency analysis
python /tmp/codebase_analyzer.py /home/runner/work/alchemiser-quant/alchemiser-quant
```

**Analysis Date**: 2025-09-16
**Vulture Version**: vulture 2.14
