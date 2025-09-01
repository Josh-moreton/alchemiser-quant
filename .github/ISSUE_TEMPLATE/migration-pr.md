---
name: Migration PR Template
about: Template for migration-related pull requests
title: '[Migration] '
labels: ['migration']
assignees: ''
---

## Migration PR Checklist

### Required Documentation
- [ ] **Smoke Test Results**: Paste output from `scripts/smoke_tests.sh`
- [ ] **MyPy Report**: Paste output from `poetry run mypy the_alchemiser/`
- [ ] **Architectural Compliance**: Confirm module dependency rules are maintained
- [ ] **Impact Assessment**: Document changes to existing functionality

### Smoke Test Output
```
# Paste the complete output from: ./scripts/smoke_tests.sh
# Must show: "🎉 ALL SMOKE TESTS PASSED!" for approval

```

### MyPy Type Checking Report
```
# Paste the complete output from: poetry run mypy the_alchemiser/
# Must maintain 100% type compliance (with configured ignores)

```

### Migration Details

#### Phase Information
- [ ] Phase 0 - Preparation
- [ ] Phase 1 - Foundation Setup  
- [ ] Phase 2 - Content Migration
- [ ] Phase 3 - Cleanup & Optimization

#### Module(s) Affected
- [ ] strategy/ - Signal generation and indicators
- [ ] portfolio/ - Portfolio state and rebalancing
- [ ] execution/ - Broker integrations and orders
- [ ] shared/ - DTOs, utilities, cross-cutting concerns
- [ ] Migration infrastructure

#### Dependency Rules Compliance
Confirm no forbidden cross-module imports:
- [ ] ✅ strategy/ → shared/ only
- [ ] ✅ portfolio/ → shared/ only
- [ ] ✅ execution/ → shared/ only
- [ ] ✅ shared/ → no other modules

### Changes Summary

#### Files Added
<!-- List new files created -->
- `path/to/new/file.py` - Description

#### Files Modified
<!-- List modified files with brief description -->
- `path/to/modified/file.py` - Changes made

#### Files Removed
<!-- List removed files (should be minimal during migration) -->
- `path/to/removed/file.py` - Reason for removal

### Architectural Impact Assessment

#### Backward Compatibility
- [ ] All existing CLI commands work unchanged
- [ ] All existing API interfaces preserved
- [ ] No breaking changes to external dependencies

#### Performance Impact
- [ ] No performance degradation measured
- [ ] Memory usage remains stable
- [ ] Import times not significantly increased

#### Testing Impact
- [ ] All smoke tests pass
- [ ] No new test failures introduced
- [ ] Type checking compliance maintained

### Migration-Specific Validation

#### For Phase 1 (Foundation Setup)
- [ ] New module directories created with proper structure
- [ ] Module `__init__.py` files with appropriate docstrings
- [ ] Import linting rules configured and enforced

#### For Phase 2 (Content Migration) 
- [ ] Code moved to appropriate modules
- [ ] Imports updated to use new module structure
- [ ] No duplicate code or circular dependencies

#### For Phase 3 (Cleanup & Optimization)
- [ ] Legacy code removed safely
- [ ] Documentation updated to reflect new structure
- [ ] Performance optimizations verified

### Rollback Plan
- [ ] Rollback procedure tested using `migration/ROLLBACK.md`
- [ ] Backup branch created before significant changes
- [ ] Recovery steps documented for this specific change

### Review Requirements

#### Code Review
- [ ] Code follows established patterns in the new module structure
- [ ] Business unit docstrings present (strategy|portfolio|execution|shared)
- [ ] Type annotations complete and correct

#### Architectural Review  
- [ ] Module boundaries respected
- [ ] No unauthorized cross-module dependencies
- [ ] Clean interfaces between modules

#### Quality Assurance
- [ ] Linting passes (baseline error count acceptable)
- [ ] MyPy type checking passes
- [ ] Smoke tests pass completely

### Additional Notes

<!-- Add any additional context, concerns, or special considerations -->

---

**Migration Guidelines:**
- Make minimal changes to achieve migration goals
- Preserve all existing functionality
- Maintain or improve type safety
- Follow the four-module architecture strictly
- Document any deviations from the migration plan