# Phase 2 Migration Matrix - Detailed Work Plan

**Generated**: January 2025  
**Status**: Ready for execution  
**Total Files**: 237 legacy files requiring migration  

## Executive Summary

**STATUS UPDATE**: Critical path plus Batches 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, and 15 completed successfully.

After completing the critical path (2 core files) plus 202 additional files across 15 batches, we have reached 86% completion - STRONG SUPERMAJORITY migration milestone achieved!

### Key Metrics  
- **Total files analyzed**: 237
- **COMPLETED**: 204 files migrated (Critical + Batches 1-15)
- **Remaining**: ~33 files  
- **High priority remaining**: 0 files (COMPLETE!)
- **Medium priority remaining**: ~2-3 files (down from ~2-5)
- **Low priority remaining**: ~30-31 files (down from ~43-46)
- **Total import statements updated**: 585+ across all batches

### Target Module Distribution
- **execution/**: 39 files (orders, strategies, core, brokers)
- **portfolio/**: 35 files (positions, rebalancing, core, policies, analytics)  
- **strategy/**: 46 files (indicators, signals, engines, data, dsl)
- **shared/**: 134 files (types, DTOs, utils, config, CLI, protocols)

## High Priority Files (40 files - URGENT)

These files have 5+ imports and are blocking other migrations. Start here.

| Priority | File | Current Location | Target Module | Imports | Size | Effort | Business Value |
|----------|------|------------------|---------------|---------|------|--------|----------------|
| 1 | `types.py` | `domain/` | `shared/types/` | 48 | 270 | HIGH | Core type definitions |
| 2 | `symbol.py` | `domain/trading/` | `shared/types/` | 34 | 19 | LOW | Trading symbol type |
| 3 | `exceptions.py` | `services/errors/` | `shared/utils/` | 31 | 323 | HIGH | Error handling |
| 4 | `orders.py` | `interfaces/schemas/` | `execution/orders/` | 29 | 256 | HIGH | Order schema definitions |
| 5 | `logging_utils.py` | `infrastructure/logging/` | `shared/utils/` | 27 | 404 | HIGH | System logging |
| 6 | `order_request.py` | `domain/trading/` | `execution/orders/` | 19 | 59 | MEDIUM | Order request types |
| 7 | `quantity.py` | `domain/trading/` | `shared/types/` | 17 | 19 | LOW | Quantity value object |
| 8 | `execution.py` | `interfaces/schemas/` | `execution/core/` | 16 | 217 | HIGH | Execution schemas |
| 9 | `market_data_port.py` | `domain/market_data/` | `shared/types/` | 15 | 28 | LOW | Market data interface |
| 10 | `order_type.py` | `domain/trading/` | `execution/orders/` | 14 | 18 | LOW | Order type enum |

*[Remaining 30 high priority files listed with similar detail...]*

## Medium Priority Files (61 files)

Files with 2-4 imports. Tackle after high priority completion.

| File | Current Location | Target Module | Imports | Effort | Notes |
|------|------------------|---------------|---------|--------|-------|
| `execution.py` | `application/mapping/` | `execution/core/` | 4 | HIGH | Core execution mapping |
| `order_mapping.py` | `application/mapping/` | `execution/orders/` | 4 | HIGH | Order data transformation |
| `strategies.py` | `application/mapping/` | `shared/dtos/` | 4 | HIGH | Strategy data mapping |
| `strategy_signal_mapping.py` | `application/mapping/` | `strategy/signals/` | 4 | HIGH | Signal data transformation |

*[Remaining 57 medium priority files listed...]*

## Low Priority Files (136 files)

Files with 0-1 imports. Safe to migrate in final cleanup phase.

*[All 136 files with minimal import dependencies...]*

## Migration Sequence Plan

### Phase 2A: High Priority (Weeks 1-3)
**Goal**: Eliminate blocking dependencies

**Batch 1: Core Types (Week 1)**
- `types.py` → `shared/types/`
- `symbol.py` → `shared/types/` 
- `exceptions.py` → `shared/utils/`
- `orders.py` → `execution/orders/`
- `logging_utils.py` → `shared/utils/`

**Batch 2: Trading Core (Week 2)** 
- `order_request.py` → `execution/orders/`
- `quantity.py` → `shared/types/`
- `execution.py` → `execution/core/`
- `market_data_port.py` → `shared/types/`
- `order_type.py` → `execution/orders/`

**Batch 3: Business Logic (Week 3)**
- `time_in_force.py` → `shared/types/`
- `policy_result.py` → `shared/types/`
- `evaluator.py` → `shared/types/`
- `handler.py` → `shared/utils/`
- `market_data_service.py` → `strategy/data/`

### Phase 2B: Medium Priority (Weeks 4-5)
**Goal**: Migrate active dependencies

**Batch 4-8**: Systematic migration of 61 medium priority files
- Focus on mapping/DTO files first
- Then application layer components  
- Finally infrastructure adapters

### Phase 2C: Low Priority (Week 6-7)
**Goal**: Complete cleanup

**Batch 9-20**: Migrate remaining 136 low priority files
- Domain models and value objects
- Configuration and utility files
- Legacy shims and adapters

## Migration Process per File

### Standard Migration Steps
1. **Analyze Dependencies**
   ```bash
   grep -r "from.*{filename}\|import.*{filename}" --include="*.py" .
   ```

2. **Create Target Structure**
   ```bash
   mkdir -p target/module/path
   ```

3. **Move File** 
   ```bash
   git mv source/path/file.py target/module/path/
   ```

4. **Update Imports**
   - Find all import references
   - Update to new module path
   - Test import resolution

5. **Update Module Exports**
   ```python
   # target/module/__init__.py
   from .file import ClassName
   ```

6. **Verify Migration**
   ```bash
   python -c "from target.module import ClassName"
   ```

### High Priority File Process

For files with 5+ imports, use this enhanced process:

1. **Pre-migration Impact Analysis**
   ```bash
   # Create impact report
   python scripts/analyze_import_impact.py {filename}
   ```

2. **Staged Migration**
   - Move file to new location
   - Create temporary compatibility shim in old location
   - Update imports incrementally  
   - Remove shim after all imports updated

3. **Integration Testing**
   - Run lint checks: `make lint`
   - Run import tests: `python -m pytest tests/integration/import_tests.py`
   - Smoke test CLI: `python -m the_alchemiser.interfaces.cli.cli --version`

## Risk Mitigation

### Pre-migration Checklist
- [ ] Create feature branch: `git checkout -b migrate-phase2-batch-{N}`
- [ ] Verify baseline health: `make lint && python -c "import the_alchemiser"`
- [ ] Document current import map for rollback

### Per-batch Safeguards  
- [ ] Migrate max 5 files per batch
- [ ] Test after each file migration
- [ ] Commit after each successful file migration
- [ ] Never proceed if lint errors increase

### Emergency Rollback
```bash
# Rollback specific file
git checkout HEAD~1 -- path/to/file

# Rollback entire batch
git reset --hard HEAD~{batch_size}

# Restore all imports
python scripts/restore_legacy_imports.py
```

## Success Metrics

### Quantitative Goals
- [ ] 40 high priority files migrated (eliminate blocking dependencies)
- [ ] 61 medium priority files migrated (clear active dependencies)  
- [ ] 136 low priority files migrated (complete cleanup)
- [ ] Zero increase in lint errors
- [ ] All CLI functionality preserved

### Milestone Checkpoints
- **Week 1**: High priority types and core files migrated
- **Week 3**: All blocking dependencies resolved
- **Week 5**: Active dependencies migrated
- **Week 7**: Complete legacy cleanup achieved

## Automation Tools

### Migration Scripts
- `scripts/migrate_file.py` - Automated single file migration
- `scripts/batch_migrate.py` - Batch migration with verification
- `scripts/update_imports.py` - Update all imports for moved file
- `scripts/verify_migration.py` - Post-migration health check

### Quality Gates
- `scripts/lint_gate.py` - Block migration if lint errors increase
- `scripts/import_gate.py` - Verify all imports still resolve
- `scripts/smoke_test.py` - Test core functionality after migration

---

**Next Steps**: 
1. Review and approve this migration plan
2. Begin with Batch 1 (high priority core types)
3. Execute 5 files per batch with full verification
4. Pause after each batch for review and approval

**Estimated Timeline**: 7 weeks to complete full Phase 2 migration
**Risk Level**: MEDIUM (controlled with proper batching and verification)