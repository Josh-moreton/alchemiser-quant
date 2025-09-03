# Master Legacy & Deprecation Cleanup Action Plan

**Issue**: #482 - Comprehensive Legacy & Deprecation Audit  
**Generated**: January 2025  
**Priority**: High - Technical Debt Reduction  

## Executive Summary

This master action plan provides **immediate, prioritized steps** to clean up all legacy, deprecated, and archived items identified in the comprehensive audit. The plan is organized by risk level and impact to ensure safe, systematic cleanup.

**Total Items to Address**: 102
- 🔴 **High Risk**: 30 items (immediate attention required)
- 🟡 **Medium Risk**: 8 items (planned cleanup)
- 🟢 **Low Risk**: 64 items (safe to clean up)

## Immediate Action Items (Next 48 Hours)

### 1. Safe Deletions - Zero Risk (12 items)
**Execute immediately** - These are safe to delete with no dependencies:

```bash
# Remove build artifacts
rm -rf the_alchemiser/__pycache__

# Remove historical migration documentation (keep final reports)
rm BATCH_*_MIGRATION_*.md

# Remove duplicate audit reports (keep COMPREHENSIVE_LEGACY_AUDIT_REPORT.md)
rm SHIMS_COMPATIBILITY_AUDIT_REPORT.md
rm REFINED_SHIMS_AUDIT_REPORT.md
```

**Impact**: Reduces repository clutter, no functional impact  
**Risk**: None  

### 2. Strategy Module Legacy Status - High Priority (5 items)
**Critical** - Strategy files marked with "Status: legacy" need review:

```bash
# Files marked with "Status: legacy"
the_alchemiser/strategy/engines/models/strategy_signal_model.py
the_alchemiser/strategy/engines/models/strategy_position_model.py  
the_alchemiser/strategy/engines/models/__init__.py
the_alchemiser/strategy/data/strategy_market_data_service.py
the_alchemiser/strategy/data/shared_market_data_service.py

# Action Required:
# 1. Review each file to determine if still needed
# 2. If operational: Update Status: legacy -> Status: current  
# 3. If deprecated: Plan migration/removal
# 4. Test strategy functionality after changes
```

**Impact**: Clarifies strategy module architecture  
**Risk**: Medium - requires understanding business logic  

## Weekly Action Plan

### Week 1: Critical Legacy Cleanup
- [ ] Execute immediate safe deletions (cache dirs, historical docs)
- [ ] Review 5 strategy files marked with "Status: legacy"
- [ ] Update legacy status markers where appropriate
- [ ] Test strategy functionality after each change

### Week 2: Strategy Module Legacy Status
Review and migrate 5 files marked with "Status: legacy":
- [ ] `the_alchemiser/strategy/engines/models/strategy_signal_model.py`
- [ ] `the_alchemiser/strategy/engines/models/strategy_position_model.py`
- [ ] `the_alchemiser/strategy/engines/models/__init__.py`
- [ ] `the_alchemiser/strategy/data/strategy_market_data_service.py`
- [ ] `the_alchemiser/strategy/data/shared_market_data_service.py`

### Week 3: Script Cleanup
Remove one-time migration scripts (7 items):
- [ ] Review and remove completed migration scripts
- [ ] Archive essential audit tools
- [ ] Update documentation references

### Week 4: Documentation Consolidation
- [ ] Archive historical migration reports
- [ ] Consolidate final audit findings
- [ ] Update architecture documentation

## Detailed Action Scripts

### Script 1: Safe Deletion (Zero Risk)
```bash
#!/bin/bash
# safe_cleanup_phase1.sh

echo "🧹 Phase 1: Safe deletions - Zero risk"

# Remove build artifacts
echo "Removing build artifacts..."
find . -name "__pycache__" -type d -exec rm -rf {} +
find . -name "*.pyc" -delete

# Remove historical migration documentation
echo "Removing historical migration docs..."
rm -f BATCH_*_MIGRATION_*.md
rm -f SHIMS_COMPATIBILITY_AUDIT_REPORT.md
rm -f REFINED_SHIMS_AUDIT_REPORT.md

echo "✅ Phase 1 complete - No functional impact"
```

### Script 2: Import Migration (High Risk)
```bash
#!/bin/bash
# import_migration_phase2.sh

echo "🔧 Phase 2: Import migration - Test after each change"

echo "Step 1: Finding symbol_legacy imports..."
grep -r "symbol_legacy" the_alchemiser/ --include="*.py" > legacy_imports.txt

echo "Found imports in:"
cat legacy_imports.txt

echo "⚠️ MANUAL ACTION REQUIRED:"
echo "1. Update each import manually"
echo "2. Test after each file update"
echo "3. Only then delete symbol_legacy.py"

echo "Next: python -m pytest tests/ # After each change"
```

### Script 3: Strategy Legacy Review
```bash
#!/bin/bash
# strategy_legacy_review.sh

echo "📋 Phase 3: Strategy module legacy review"

echo "Files marked with 'Status: legacy':"
find the_alchemiser/strategy -name "*.py" -exec grep -l "Status.*legacy" {} \;

echo "⚠️ TEAM REVIEW REQUIRED:"
echo "1. Assess if these modules can be migrated"
echo "2. Update Status: legacy -> Status: current if migrated"
echo "3. Plan replacement if business logic needs extraction"
```

## Success Metrics & Validation

### Completion Checkpoints
- [ ] **Zero legacy imports**: `grep -r "legacy" the_alchemiser/ --include="*.py"` returns no results
- [ ] **No broken imports**: `python -c "import the_alchemiser"` succeeds
- [ ] **Tests pass**: All existing tests continue to pass
- [ ] **Clean repository**: No unnecessary files or directories

### Before/After Metrics
- **Before**: 102 legacy/deprecated items identified
- **Target**: <10 remaining items (only current operational files)
- **Repository size**: Reduce by ~20% (remove historical docs)
- **Import clarity**: 100% imports use current module paths

## Risk Mitigation

### High-Risk Operations
- ⚠️ **Never delete a file with active imports** without migration
- ⚠️ **Always test after import changes** before proceeding
- ⚠️ **Coordinate with team** for "Status: legacy" files

### Rollback Plan
```bash
# If issues arise, rollback specific changes:
git checkout HEAD~1 -- the_alchemiser/shared/types/symbol_legacy.py
git checkout HEAD~1 -- the_alchemiser/portfolio/positions/legacy_position_manager.py
```

### Team Communication
- 📢 **Announce**: Before starting high-risk migrations
- 🔍 **Review**: Have team review "Status: legacy" file migrations
- ✅ **Validate**: Confirm functionality after each phase

## Long-term Architecture Goals

### Target State (After Cleanup)
- **Zero legacy compatibility layers**
- **Clear modular boundaries** (strategy/, portfolio/, execution/, shared/)
- **Consistent naming conventions**
- **No technical debt from historical migrations**

### Maintenance Practices
- **New code review**: Prevent new legacy patterns
- **Regular audits**: Quarterly technical debt review
- **Clear deprecation process**: Formal process for deprecating features

---

**Next Actions**: Execute Phase 1 safe deletions immediately, then proceed with import migration following the detailed scripts above.