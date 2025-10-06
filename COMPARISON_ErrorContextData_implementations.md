# ErrorContextData Implementations Comparison

**Purpose**: Compare the three different `ErrorContextData` implementations to support consolidation decision.

**Date**: 2025-01-06

---

## Summary

Three different implementations of `ErrorContextData` exist in the codebase with **incompatible schemas**:

| Implementation | Location | Type | Status | Tests | Usage |
|----------------|----------|------|--------|-------|-------|
| **Version 1** | `shared/utils/context.py` | Frozen dataclass | 🔴 UNUSED | 0 | 0 imports |
| **Version 2** | `shared/errors/context.py` | Regular dataclass | ✅ ACTIVE | 13 | 2+ imports |
| **Version 3** | `shared/schemas/errors.py` | TypedDict | ✅ ACTIVE | N/A | Schema only |

---

## Detailed Field Comparison

### Version 1: shared/utils/context.py (UNUSED)

```python
@dataclass(frozen=True)
class ErrorContextData:
    operation: str
    component: str
    function_name: str | None = None
    request_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    additional_data: dict[str, Any] | None = None
```

**Features**:
- ✅ Frozen (immutable)
- ✅ Factory function: `create_error_context()`
- ✅ to_dict() method with timestamp
- ❌ No correlation_id
- ❌ No causation_id
- ❌ Non-deterministic timestamp
- 🔴 **0 test coverage**
- 🔴 **0 usage in codebase**

**Created**: Oct 6, 2025  
**Last Modified**: Oct 6, 2025

---

### Version 2: shared/errors/context.py (ACTIVE)

```python
@dataclass
class ErrorContextData:
    module: str | None = None
    function: str | None = None
    operation: str | None = None
    correlation_id: str | None = None
    additional_data: dict[str, Any] | None = None
```

**Features**:
- ❌ Not frozen (mutable)
- ✅ Has correlation_id (event-driven requirement)
- ✅ to_dict() method (no timestamp)
- ❌ No component field
- ❌ No request_id/user_id/session_id
- ✅ **13 passing tests**
- ✅ **Active usage in error handlers**

**Test Coverage**:
```python
tests/shared/errors/test_context.py:
- TestErrorContextData (5 tests)
- TestErrorContextDataToDict (6 tests)
- TestErrorContextDataSerialization (2 tests)
```

**Used By**:
- `the_alchemiser/shared/errors/error_handler.py`
- `the_alchemiser/shared/errors/enhanced_exceptions.py`
- Tests

---

### Version 3: shared/schemas/errors.py (TYPEDDICT)

```python
class ErrorContextData(TypedDict):
    operation: str
    component: str
    function_name: str | None
    request_id: str | None
    user_id: str | None
    session_id: str | None
    additional_data: dict[str, Any]
    timestamp: str
```

**Features**:
- ✅ TypedDict for serialization
- ✅ Has timestamp field
- ✅ Matches Version 1 schema (almost)
- ❌ No correlation_id
- ❌ Not a runtime class (just type hints)
- 📋 **Used for schema definitions only**

**Purpose**: Type annotations and schema validation

---

## Field Matrix

| Field | Version 1 (utils) | Version 2 (errors) | Version 3 (schemas) | Event Architecture Required? |
|-------|-------------------|-------------------|---------------------|----------------------------|
| operation | ✅ Required | ✅ Optional | ✅ Required | ✅ Yes |
| component | ✅ Required | ❌ | ✅ Required | ✅ Yes |
| module | ❌ | ✅ Optional | ❌ | ❌ No |
| function | ❌ | ✅ Optional | ❌ | ❌ No |
| function_name | ✅ Optional | ❌ | ✅ Optional | ❌ No |
| correlation_id | ❌ | ✅ Optional | ❌ | ✅ **YES - Required!** |
| causation_id | ❌ (in additional_data) | ❌ (in additional_data) | ❌ | ✅ **YES - Required!** |
| request_id | ✅ Optional | ❌ | ✅ Optional | ⚠️ Nice to have |
| user_id | ✅ Optional | ❌ | ✅ Optional | ⚠️ Nice to have |
| session_id | ✅ Optional | ❌ | ✅ Optional | ⚠️ Nice to have |
| additional_data | ✅ Optional | ✅ Optional | ✅ Required | ✅ Yes |
| timestamp | ❌ (in to_dict) | ❌ | ✅ Required | ✅ Yes |

---

## Architecture Requirements Analysis

According to `.github/copilot-instructions.md`, the event-driven architecture requires:

> **Event-driven workflow**
> - Strategy emits `SignalGenerated` after adapter data pull; payload includes `schema_version`, **correlation/causation IDs**, and DTO dumps.

> **Idempotency & traceability**: Event handlers must be idempotent; **propagate `correlation_id` and `causation_id`**; tolerate replays.

**Verdict**: 
- ❌ Version 1 (utils) - Missing correlation_id/causation_id
- ✅ Version 2 (errors) - Has correlation_id
- ❌ Version 3 (schemas) - Missing correlation_id

---

## Usage Analysis

### Version 1 Usage: 🔴 NONE

```bash
$ grep -r "shared.utils.context import" --include="*.py" .
# Returns: 0 results
```

### Version 2 Usage: ✅ ACTIVE

```bash
$ grep -r "shared.errors.context import" --include="*.py" .
./tests/shared/errors/test_enhanced_exceptions.py
./tests/shared/errors/test_context.py
```

### Version 3 Usage: ✅ ACTIVE (as schema)

Used in schema definitions and type annotations.

---

## Recommendations

### Option 1: Delete Version 1 ⭐ (RECOMMENDED)

**Action**: `git rm the_alchemiser/shared/utils/context.py`

**Rationale**:
- Version 1 is completely unused (0 imports)
- Version 2 is the active implementation
- Deleting eliminates confusion and maintenance burden
- No breaking changes (nothing imports it)

**Impact**: None (file is dead code)

---

### Option 2: Consolidate All Three

**Action**: Create unified implementation combining best features

**Proposed Unified Schema**:
```python
@dataclass(frozen=True)
class ErrorContextData:
    """Unified error context for all error reporting and events.
    
    Combines fields from all three implementations to support:
    - Error reporting and tracking
    - Event-driven architecture (correlation/causation IDs)
    - User/session tracking
    - Deterministic testing
    """
    # Core required fields
    operation: str
    component: str
    
    # Event-driven architecture (REQUIRED by copilot-instructions.md)
    correlation_id: str | None = None
    causation_id: str | None = None  # Move from additional_data
    
    # Context identification
    module: str | None = None
    function: str | None = None
    
    # Request tracking
    request_id: str | None = None
    user_id: str | None = None
    session_id: str | None = None
    
    # Timestamp (set at creation for determinism)
    timestamp: datetime = field(default_factory=lambda: datetime.now(UTC))
    
    # Flexible additional data
    additional_data: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary with ISO timestamp."""
        return {
            "operation": self.operation,
            "component": self.component,
            "correlation_id": self.correlation_id,
            "causation_id": self.causation_id,
            "module": self.module,
            "function": self.function,
            "request_id": self.request_id,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "timestamp": self.timestamp.isoformat(),
            "additional_data": self.additional_data,
        }
```

**Location**: `shared/errors/context.py` (keep existing location)

**Migration Steps**:
1. Update `shared/errors/context.py` with unified schema
2. Update all 13 tests to use new schema
3. Update `shared/schemas/errors.py` TypedDict to match
4. Delete `shared/utils/context.py`
5. Run full test suite

**Impact**: Breaking changes to Version 2 users (need migration)

---

### Option 3: Keep Separate (NOT RECOMMENDED)

**Action**: Document differences and maintain both

**Rationale**: If they serve different purposes (none found)

**Issues**:
- Increases confusion
- Duplicates maintenance effort
- Violates DRY principle
- Version 1 still has no tests or usage

---

## Decision Matrix

| Criteria | Option 1: Delete | Option 2: Consolidate | Option 3: Keep Both |
|----------|-----------------|----------------------|---------------------|
| Effort | Low | Medium | Low |
| Risk | None | Medium | High (confusion) |
| Benefits | Simplicity | Best features | None |
| Alignment with Architecture | N/A | High | Low |
| Breaking Changes | None | Medium | None |
| Maintenance Burden | Reduced | Medium | Increased |
| **Recommendation** | ⭐⭐⭐ | ⭐⭐ | ❌ |

---

## Conclusion

**Immediate Action**: Delete `shared/utils/context.py` (Option 1)
- No usage found
- No breaking changes
- Eliminates confusion

**Future Enhancement**: Consider Option 2 consolidation
- Add missing fields to Version 2 (correlation_id already present)
- Ensure compliance with event-driven architecture
- Maintain backward compatibility where possible

---

**Prepared By**: AI Copilot Agent  
**Date**: 2025-01-06  
**Status**: Ready for stakeholder decision

