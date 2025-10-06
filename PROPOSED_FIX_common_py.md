# Proposed Fix: Delete the_alchemiser/shared/utils/common.py

## Overview

Based on the institution-grade audit completed in `FILE_REVIEW_common_py.md`, this document outlines the proposed fix for the critical dead code violation.

## Problem Statement

- **File**: `the_alchemiser/shared/utils/common.py`
- **Issue**: 100% dead code - `ActionType` enum is completely unused
- **Severity**: Critical (violates dead code policy)
- **Impact**: No breaking changes if deleted

## Proposed Solution

**DELETE** the file entirely.

## Implementation Steps

### 1. Remove the file

```bash
git rm the_alchemiser/shared/utils/common.py
```

### 2. Verify no breakage

```bash
# Type check
poetry run mypy the_alchemiser/ --config-file=pyproject.toml

# Import check
poetry run importlinter --config pyproject.toml

# Confirm no references
git grep "ActionType" -- "*.py"
git grep "shared.utils.common" -- "*.py"
git grep "utils.common" -- "*.py"
```

### 3. Update version

```bash
make bump-patch  # For dead code removal
```

### 4. Commit

```bash
git commit -m "refactor: Remove dead code - unused ActionType enum

- Delete the_alchemiser/shared/utils/common.py
- File contained ActionType enum with zero usage
- Not imported anywhere in codebase
- Not exported from shared/utils module
- Confirmed by vulture dead code detector
- No breaking changes (zero references)
- Complies with dead code elimination policy
- Reduces maintenance burden
- Version bumped to 2.10.6

Refs: FILE_REVIEW_common_py.md
"
```

## Testing Plan

### Before Deletion

1. ✅ **Confirm zero usage**
   ```bash
   git grep "ActionType" -- "*.py" | grep -v "common.py"
   # Result: No matches
   ```

2. ✅ **Confirm not exported**
   ```bash
   grep "ActionType" the_alchemiser/shared/utils/__init__.py
   # Result: No matches
   ```

3. ✅ **Run vulture**
   ```bash
   poetry run vulture the_alchemiser/shared/utils/common.py
   # Result: 100% unused
   ```

### After Deletion

1. **Type checking**
   ```bash
   poetry run mypy the_alchemiser/
   # Expected: Should pass (may have unrelated errors in other files)
   ```

2. **Import linting**
   ```bash
   poetry run importlinter --config pyproject.toml
   # Expected: Should pass
   ```

3. **Run tests**
   ```bash
   poetry run pytest
   # Expected: Should pass (no tests for common.py exist)
   ```

4. **Verify file is gone**
   ```bash
   ls the_alchemiser/shared/utils/common.py
   # Expected: No such file or directory
   ```

## Risk Assessment

### Risks: ❌ NONE

- ✅ **No imports**: Zero references in entire codebase
- ✅ **No exports**: Not in module's `__all__`
- ✅ **No tests**: No tests to update
- ✅ **No documentation**: Only internal docstrings (removed with file)
- ✅ **No dependencies**: File imports only stdlib `enum`

### Benefits: ✅ HIGH

- ✅ **Compliance**: Resolves dead code policy violation
- ✅ **Clarity**: Eliminates confusion with `schemas/common.py`
- ✅ **Maintenance**: Reduces codebase complexity
- ✅ **Size**: 35 fewer lines to maintain

## Alternative: Keep and Integrate

If stakeholders decide to keep the file, the following work is required:

### Required Changes

1. **Add tests**
   ```python
   # tests/shared/utils/test_common.py
   import pytest
   from the_alchemiser.shared.utils.common import ActionType

   def test_action_type_values():
       assert ActionType.BUY.value == "BUY"
       assert ActionType.SELL.value == "SELL"
       assert ActionType.HOLD.value == "HOLD"

   def test_action_type_members():
       assert len(ActionType) == 3
       assert set(ActionType) == {ActionType.BUY, ActionType.SELL, ActionType.HOLD}

   def test_action_type_immutable():
       with pytest.raises(AttributeError):
           ActionType.BUY.value = "MODIFIED"
   ```

2. **Export from module**
   ```python
   # the_alchemiser/shared/utils/__init__.py
   from .common import ActionType

   __all__ = [
       # ... existing exports ...
       "ActionType",
   ]
   ```

3. **Integrate into codebase**
   - Find all string literals: "BUY", "SELL", "HOLD"
   - Replace with `ActionType.BUY.value`, etc.
   - Update DTOs to use ActionType
   - Document usage patterns

4. **Add usage documentation**
   ```python
   """
   Usage:
       # In strategy signals
       signal = StrategySignal(action=ActionType.BUY.value)

       # In rebalance plans
       trade = TradeItem(action=ActionType.SELL.value)

       # Type hints
       def process_action(action: ActionType) -> None:
           ...
   """
   ```

### Estimated Effort

- Testing: 1-2 hours
- Integration: 4-8 hours (depends on string literal usage)
- Documentation: 1 hour
- Review and testing: 2 hours

**Total**: 8-13 hours of work

## Recommendation

**DELETE** the file.

**Rationale**:
1. Integration requires 8-13 hours of work
2. No clear business requirement for enum
3. String literals work fine for current needs
4. Can be reintroduced later if needed
5. Immediate compliance with dead code policy
6. Zero risk of breakage

## Sign-off

- [ ] Product Owner: Approved deletion / Approved integration
- [ ] Tech Lead: Reviewed and approved
- [ ] QA: Verified no test failures
- [ ] Security: Confirmed no security impact

---

**Prepared by**: Copilot AI Agent  
**Date**: 2025-01-09  
**Related**: FILE_REVIEW_common_py.md, AUDIT_COMPLETION_common_py.md
