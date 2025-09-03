# Legacy Audit Tools Documentation

This directory contains comprehensive tools for auditing and cleaning up legacy code in the alchemiser-quant codebase. These tools were created to address Issue #482 - Comprehensive Legacy & Deprecation Audit.

## 🎯 Overview

The legacy audit identified **271 items** across the codebase requiring attention:
- **HIGH RISK**: 27 items (legacy directory structures)
- **MEDIUM RISK**: 185 items (legacy imports and shims)  
- **LOW RISK**: 59 items (deprecated comments and backup files)

## 🛠️ Tools Available

### 1. `comprehensive_legacy_audit.py` - Master Audit Tool
**Purpose**: Scans the entire codebase for legacy patterns and generates comprehensive audit report.

**Usage**:
```bash
python scripts/comprehensive_legacy_audit.py .
```

**Outputs**:
- `COMPREHENSIVE_LEGACY_AUDIT_REPORT.md` - Human-readable audit report
- `legacy_audit_findings.json` - Machine-readable findings data

**What it finds**:
- Shims & compatibility layers with deprecation warnings
- Deprecated features, functions, and classes
- Archived/obsolete code patterns  
- Legacy files not conforming to current structure
- Old import patterns from DDD structure

### 2. `legacy_cleanup_helper.py` - Cleanup Planning Tool
**Purpose**: Generates actionable cleanup plans based on audit findings.

**Usage**:
```bash
python scripts/legacy_cleanup_helper.py .
```

**Output**:
- `LEGACY_CLEANUP_PLAN.md` - Phased cleanup strategy with specific recommendations

**Features**:
- Categorizes findings by cleanup complexity
- Provides step-by-step cleanup phases
- Identifies safe vs. risky cleanup operations

### 3. `safe_legacy_remover.py` - Automated Safe Cleanup
**Purpose**: Safely removes low-risk backup files and performs automated cleanup.

**Usage**:
```bash
# Dry run (recommended first)
python scripts/safe_legacy_remover.py

# Execute actual removal
python scripts/safe_legacy_remover.py --execute
```

**Output**:
- `SAFE_REMOVAL_REPORT.md` - Record of what was safely removed

**Safety features**:
- Only removes `.backup` files with corresponding originals
- Verifies file sizes are reasonable
- Dry-run mode by default

### 4. `import_dependency_analyzer.py` - Migration Prioritization
**Purpose**: Analyzes import dependencies to prioritize migration efforts.

**Usage**:
```bash
python scripts/import_dependency_analyzer.py .
```

**Outputs**:
- `IMPORT_MIGRATION_PRIORITY_REPORT.md` - Migration priorities based on usage
- `import_dependencies.json` - Raw dependency data

**Analysis provides**:
- High-priority modules (3+ importers)
- Medium-priority modules (1-2 importers)
- Low-priority shims for cleanup

## 📊 Generated Reports

### Master Reports
1. **COMPREHENSIVE_LEGACY_AUDIT_REPORT.md** - Complete audit with all 271 findings
2. **LEGACY_CLEANUP_PLAN.md** - Actionable 3-phase cleanup strategy
3. **IMPORT_MIGRATION_PRIORITY_REPORT.md** - Import-based migration priorities
4. **SAFE_REMOVAL_REPORT.md** - Record of completed safe deletions

### Data Files
1. **legacy_audit_findings.json** - All findings in machine-readable format
2. **import_dependencies.json** - Complete import dependency graph

## 🗂️ Key Findings Summary

### High Priority Items (27 items)
**Focus**: Legacy directory structures that need migration
- `the_alchemiser/utils/` directory (17 files)
- `the_alchemiser/shared/utils/` directory (8 files)  
- `the_alchemiser/shared/services/` directory (4 files)
- Legacy `services/` directories (3 files)

**Action**: Migrate to new modular structure (strategy/portfolio/execution/shared)

### Medium Priority Items (185 items)
**Focus**: Legacy imports and compatibility shims
- Legacy import patterns (83 items) - `from the_alchemiser.*.utils.`
- Compatibility shims (125 items) - Files with deprecation warnings
- Legacy naming conventions (various)

**Action**: Update import statements and remove shims after migration

### Low Priority Items (59 items)
**Focus**: Deprecated comments and cleanup
- Deprecated code comments (34 items)
- Legacy field aliases (8 items)
- TODO/FIXME removal comments (17 items)

**Action**: Clean up comments and documentation

## 🚀 Recommended Workflow

### Phase 1: Safe Cleanup (COMPLETED ✅)
```bash
# Already completed - removed 2 backup files
python scripts/safe_legacy_remover.py --execute
```

### Phase 2: Legacy Structure Migration
1. Migrate `utils/` directories to appropriate modules
2. Move `services/` files to correct business unit modules
3. Update all import statements
4. Test thoroughly after each migration

### Phase 3: Shim Removal
1. Update import statements to use new locations
2. Remove compatibility shims
3. Clean up deprecated comments
4. Run final audit to verify completion

## 🔒 Safety Guidelines

### Before Making Changes
1. **Run the audit tools** to understand current state
2. **Create a feature branch** for cleanup work
3. **Review import dependencies** to understand impact
4. **Start with lowest-risk items** (backup files, comments)

### During Migration
1. **Migrate in small batches** (≤10 files at a time)
2. **Test after each batch** (run linting, type checking, tests)
3. **Use the dry-run modes** when available
4. **Keep detailed records** of what was changed

### After Changes
1. **Run import-linter** to verify module boundaries
2. **Update documentation** to reflect new structure
3. **Monitor CI/CD** for any import-related failures
4. **Re-run audit tools** to track progress

## 📈 Progress Tracking

To track cleanup progress:
```bash
# Re-run audit to see remaining items
python scripts/comprehensive_legacy_audit.py .

# Check import dependencies after migration
python scripts/import_dependency_analyzer.py .

# Verify safe cleanup opportunities
python scripts/safe_legacy_remover.py
```

## 🆘 Rollback Procedures

If issues arise:
```bash
# Rollback specific files
git checkout HEAD~1 -- path/to/problematic/file

# Rollback entire cleanup batch
git reset --hard <commit_before_changes>

# Restore removed backup files (if needed)
git checkout <commit_with_backups> -- *.backup
```

## 🎯 Success Metrics

**Quantitative Goals**:
- Reduce legacy file count from 271 to <50
- Eliminate all compatibility shims (125 items)
- Remove legacy directory structures (27 high-priority items)
- Maintain 0 new linting/type errors

**Qualitative Goals**:
- Clear modular architecture boundaries
- No legacy import paths remaining  
- Documentation reflects clean structure
- Team confidence in new architecture

---

*Generated for Issue #482 - Comprehensive Legacy & Deprecation Audit*
*Tools created: September 2025*