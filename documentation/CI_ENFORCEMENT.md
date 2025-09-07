# Migration CI Enforcement - Exception Process

## Overview

Phase 4 of the modular migration introduces CI enforcement for:
- MyPy type checking on new modular structure  
- Import dependency rules via import-linter
- Smoke tests for functionality validation

## Current Enforcement Level

### **Currently Enforced (CI-blocking)**
- ✅ **Shared module isolation**: `shared/` may not import from other modules
- ✅ **Import-linter tool functionality**: Must run without tool errors

### **Warning Level (Non-blocking)**  
- ⚠️ **MyPy type issues**: Reported but don't fail CI
- ⚠️ **Smoke test failures**: Expected during migration

### **Planned for Future Enforcement**
- 🔄 **Cross-module import prevention**: strategy↔portfolio, portfolio↔execution  
- 🔄 **Strict type checking**: Zero MyPy errors on new modules
- 🔄 **Full smoke test passing**: All functionality preserved

## Adding Temporary Exceptions

### 1. Import Rule Exceptions

To temporarily allow a cross-module import that violates the architecture:

**Step 1**: Document the exception in your PR description:
```markdown
## Temporary Import Exception

**Module**: `the_alchemiser.strategy.engines.foo`  
**Imports**: `the_alchemiser.portfolio.bar`  
**Reason**: Legacy code integration during migration  
**Removal Timeline**: Phase 6 cleanup  
**Issue**: #123
```

**Step 2**: Add a comment in the code:
```python
# MIGRATION EXCEPTION: Remove in Phase 6
# TODO: Replace with proper DTO-based communication
from the_alchemiser.portfolio.legacy_service import LegacyService
```

**Step 3**: Update `pyproject.toml` to exclude from current enforcement:
```toml
# Add to importlinter contracts if needed
[[tool.importlinter.contracts]]
name = "Temporary exception for migration #123"
type = "forbidden"
source_modules = ["the_alchemiser.strategy.engines.foo"]
forbidden_modules = ["the_alchemiser.portfolio"]
ignore_imports = ["the_alchemiser.portfolio.bar"]
```

### 2. MyPy Type Checking Exceptions

For files with complex type issues during migration:

**Step 1**: Add to mypy exclusions in `pyproject.toml`:
```toml
[tool.mypy]
exclude = [
    # ... existing exclusions ...
    "the_alchemiser/strategy/legacy_engine.py",  # MIGRATION: Fix in Phase 5
]
```

**Step 2**: Add issue tracking:
```python
"""Business Unit: strategy | Status: legacy

MIGRATION TODO: Fix type annotations in Phase 5
See issue #456 for type safety improvements needed.
"""
```

### 3. Smoke Test Exceptions

For temporarily broken functionality:

**Step 1**: Update the test script with conditional logic:
```bash
# In scripts/smoke_tests.sh
if [ "$MIGRATION_PHASE" = "4" ]; then
    echo "Skipping legacy CLI test during migration"
else
    run_test "Legacy CLI" "alchemiser legacy-command"
fi
```

**Step 2**: Set environment variable in CI:
```yaml
- name: Set migration phase
  run: echo "MIGRATION_PHASE=4" >> $GITHUB_ENV
```

## Approval Process

### **Auto-Approved Exceptions**
1. **Legacy code exclusions**: Adding files to mypy exclude list
2. **Temporary import shims**: With clear removal timeline
3. **Test adjustments**: During active migration phases

### **Review Required**  
1. **New cross-module dependencies**: Must be justified
2. **Weakening enforcement**: Removing existing rules
3. **Permanent exceptions**: Long-term architectural changes

### **Architect Approval Required**
1. **New module creation**: Adding to the four-module structure  
2. **Dependency rule changes**: Modifying core architectural constraints
3. **Exception policy changes**: Altering this process

## Exception Lifecycle

### **Creation**
1. Document reason and timeline in PR
2. Add appropriate exclusions/exceptions
3. Link to tracking issue
4. Set removal milestone

### **Tracking**
- All exceptions tracked in migration board
- Weekly review of exception list
- Automated reporting of exception count

### **Removal**
1. Create dedicated cleanup PR
2. Remove exception configuration
3. Verify CI passes
4. Update migration documentation

## Emergency Overrides

For critical production issues that need immediate exception:

```yaml
# Add to PR workflow
- name: Emergency override check
  if: contains(github.event.pull_request.labels.*.name, 'emergency-override')
  run: |
    echo "Emergency override detected - skipping import checks"
    echo "MIGRATION_EMERGENCY_OVERRIDE=true" >> $GITHUB_ENV
```

**Requirements**:
- Must have `emergency-override` label
- Requires architect approval within 24 hours
- Follow-up cleanup PR required within 1 week

## Progressive Enforcement Plan

### **Phase 4** (Current)
- Shared module isolation enforced
- Other rules warn only

### **Phase 5** 
- Enable strategy module isolation
- MyPy errors become warnings

### **Phase 6**
- Enable all cross-module rules  
- MyPy warnings become errors
- Full smoke test compliance

### **Post-Migration**
- Zero exceptions policy
- All rules enforced
- Regression prevention mode

## Monitoring and Metrics

Track migration progress via:
- Exception count per module
- MyPy error reduction over time  
- Import violation trends
- Smoke test pass rate

Dashboard available at: [Migration Progress](../migration/PROGRESS.md)