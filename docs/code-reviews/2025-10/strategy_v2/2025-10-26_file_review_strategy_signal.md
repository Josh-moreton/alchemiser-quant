# [File Review] the_alchemiser/shared/schemas/strategy_signal.py

> Purpose: Conduct a rigorous, line-by-line review of a single Python file in the trading system, to institution-grade standards (correctness, controls, auditability, and safety). One issue per file.

---

## 0) Metadata

**File path**: `the_alchemiser/shared/schemas/strategy_signal.py`

**Commit SHA / Tag**: `802cf268358e3299fb6b80a4b7cf3d4bda2994f4`

**Reviewer(s)**: Copilot AI Agent

**Date**: 2025-01-07

**Business function / Module**: shared/schemas (Data Transfer Objects)

**Runtime context**: Synchronous Python module; used for inter-module communication between strategy and portfolio modules in event-driven architecture

**Criticality**: P1 (High) - Core DTO for strategy signals; incorrect validation or serialization could lead to invalid trades or event processing failures

**Direct dependencies (imports)**:
```
Internal:
  - the_alchemiser.shared.utils.timezone_utils (ensure_timezone_aware)
External:
  - pydantic v2 (BaseModel, ConfigDict, Field, field_validator)
  - datetime (datetime)
  - decimal (Decimal)
  - typing (Any)
```

**External services touched**:
```
None - Pure DTO module (no I/O)
```

**Interfaces (DTOs/events) produced/consumed**:
```
Produced: StrategySignal DTO (v1.0)
Used in events: SignalGenerated, RebalancePlanned
Used by: strategy_v2/handlers/signal_generation_handler.py, portfolio_v2 module
```

**Related docs/specs**:
- Copilot Instructions (event-driven workflow section)
- FILE_REVIEW_strategy_value_objects.md (duplicate StrategySignal class)
- AUDIT_COMPLETION_strategy_value_objects.md
- Architecture: Event boundaries between strategy/portfolio/execution

---

## 1) Scope & Objectives

- Verify the file's **single responsibility** and alignment with intended business capability.
- Ensure **correctness**, **numerical integrity**, **deterministic behaviour** where required.
- Validate **error handling**, **idempotency**, **observability**, **security**, and **compliance** controls.
- Confirm **interfaces/contracts** (DTOs/events) are accurate, versioned, and tested.
- Identify **dead code**, **complexity hotspots**, and **performance risks**.
- **CRITICAL**: Resolve duplication issue with `shared/types/strategy_value_objects.py`

---

## 2) Summary of Findings (use severity labels)

### Critical

**None** - File is well-structured and follows best practices

### High

1. **DUPLICATE StrategySignal class exists** (Lines 1-141)
   - `shared/schemas/strategy_signal.py` (this file - DTO focus)
   - `shared/types/strategy_value_objects.py` (value object - domain focus)
   - **Risk**: Confusion about which to use; potential for divergent behavior
   - **Evidence**: Both classes have identical names but different field sets and validators
   - **Impact**: Creates architectural ambiguity; handler uses `shared/types` version

2. **Missing schema versioning** (Lines 1-141)
   - No `schema_version` field for event evolution
   - **Risk**: Breaking changes cannot be detected; replay issues; version skew
   - **Evidence**: Other reviewed files mention `schema_version` in event contracts
   - **Copilot Instructions**: "DTOs in `shared/schemas/` with... versioned via `schema_version`"

### Medium

3. **Inconsistent field set vs shared/types version** (Lines 36-59)
   - This version: `correlation_id`, `causation_id`, `timestamp`, `symbol`, `action`, `reasoning`, `strategy_name`, `allocation_weight`, `signal_strength`, `metadata`
   - Types version: `symbol`, `action`, `target_allocation`, `reasoning`, `timestamp` (plus extra fields via `extra="allow"`)
   - **Risk**: Different field names (`allocation_weight` vs `target_allocation`) cause mapping errors

4. **No Literal type for action field** (Line 44)
   - Uses `str` with validator instead of `Literal["BUY", "SELL", "HOLD"]`
   - **Risk**: Weaker type safety at design time; mypy won't catch invalid actions
   - **Contrast**: `shared/types/strategy_value_objects.py` uses `ActionLiteral = Literal["BUY", "SELL", "HOLD"]`

5. **Missing docstring examples** (Lines 22-26)
   - Docstring lacks usage examples for `from_dict()` and `to_dict()`
   - **Risk**: Lower developer productivity; unclear serialization format

6. **Metadata field accepts Any** (Line 59)
   - `metadata: dict[str, Any]` allows unconstrained data
   - **Risk**: Hidden complexity; no schema validation; potential for injection attacks

### Low

7. **No explicit __all__ export** (Lines 1-141)
   - Module lacks `__all__` declaration (though `__init__.py` exports it)
   - **Info**: Best practice for clarity

8. **reasoning field has no max_length** (Line 45)
   - Could allow unbounded strings (contrast: types version has `max_length=1000`)
   - **Risk**: Memory issues; log spam; JSON serialization problems

9. **No validation for empty correlation/causation IDs** (Lines 36-39)
   - `min_length=1` prevents empty strings, but no semantic validation
   - **Info**: Could add regex pattern for format validation

10. **to_dict() could use model_dump_json()** (Lines 83-101)
    - Manual serialization logic could be replaced by Pydantic's built-in JSON serialization
    - **Info**: Simplification opportunity

### Info/Nits

11. **Consistent with other schemas in formatting** (Lines 1-141)
    - ✅ Good: Follows same pattern as `strategy_allocation.py` and `rebalance_plan.py`
    - ✅ Good: Uses `ConfigDict(strict=True, frozen=True)`

12. **Good use of timezone_utils** (Line 81)
    - ✅ Centralizes timezone handling correctly

---

## 3) Line-by-Line Notes

### Detailed Line-by-Line Analysis

| Line(s) | Issue / Observation | Severity | Evidence / Excerpt | Proposed Action |
|---------|---------------------|----------|-------------------|-----------------|
| 1 | ✅ Correct shebang | Info | `#!/usr/bin/env python3` | None |
| 2-8 | ✅ Good module docstring with Business Unit | Info | `"""Business Unit: shared \| Status: current...` | None |
| 10 | ✅ Future annotations import | Info | `from __future__ import annotations` | None |
| 12-14 | ✅ Standard library imports | Info | `datetime`, `Decimal`, `Any` | None |
| 16 | ✅ Pydantic v2 imports | Info | `BaseModel, ConfigDict, Field, field_validator` | None |
| 18 | ✅ Uses shared timezone utils | Info | `from ..utils.timezone_utils import ensure_timezone_aware` | None |
| 21-26 | ⚠️ Missing usage examples in docstring | Low | Only describes purpose, not usage | Add examples for `from_dict()` / `to_dict()` |
| 28-33 | ✅ Excellent model_config | Info | `strict=True, frozen=True, validate_assignment=True` | None |
| 36-39 | ✅ Correlation fields for event-driven arch | Info | `correlation_id`, `causation_id` | None |
| 36-39 | ⚠️ No semantic validation on IDs | Low | `min_length=1` only | Consider UUID format validation |
| 40 | ✅ Timestamp field required | Info | `timestamp: datetime = Field(..., description=...)` | None |
| 43 | ✅ Symbol validation (max 10 chars) | Info | `max_length=10` prevents excessively long symbols | None |
| 44 | 🔴 Action field is str, not Literal | Medium | `action: str = Field(...)` | Change to `Literal["BUY", "SELL", "HOLD"]` |
| 45 | ⚠️ Reasoning has no max_length | Low | No constraint on length | Add `max_length=1000` (match types version) |
| 48-50 | ✅ Optional strategy_name | Info | `str \| None` with default=None | None |
| 51-53 | ⚠️ Field name inconsistency | Medium | `allocation_weight` vs `target_allocation` (types version) | Align field names across both classes |
| 51-53 | ✅ Good Decimal constraints | Info | `ge=0, le=1` enforces [0,1] range | None |
| 56-58 | ✅ signal_strength validation | Info | `ge=0` ensures non-negative | None |
| 59 | 🔴 metadata allows Any | Medium | `dict[str, Any] \| None` | Document allowed keys or use stricter type |
| 61-65 | ✅ Symbol normalization | Info | Strips whitespace and uppercases | None |
| 67-75 | ✅ Action validation | Info | Enforces BUY/SELL/HOLD with error message | None |
| 67-75 | ⚠️ Could use Literal instead | Medium | Manual validation vs type-level enforcement | Use `ActionLiteral = Literal[...]` |
| 77-81 | ✅ Timezone validation | Info | Delegates to `ensure_timezone_aware` | None |
| 83-101 | ✅ to_dict serialization | Info | Handles datetime → ISO, Decimal → str | None |
| 93-94 | ✅ Defensive timestamp check | Info | `if self.timestamp:` guards against None | None |
| 97-99 | ✅ Decimal serialization loop | Info | Converts allocation_weight, signal_strength to str | None |
| 103-140 | ✅ from_dict deserialization | Info | Handles ISO → datetime, str → Decimal | None |
| 118-126 | ✅ ISO timestamp parsing with Z suffix | Info | `timestamp.endswith("Z")` handling | None |
| 129-138 | ✅ Decimal field conversion | Info | Validates before converting | None |
| N/A | 🔴 Missing schema_version field | High | No version field in DTO | Add `schema_version: str = "1.0"` |
| N/A | 🔴 Duplicate class in codebase | High | Two StrategySignal classes exist | Resolve duplication (deprecate one) |
| N/A | ⚠️ No __all__ declaration | Low | Missing explicit public API | Add `__all__ = ["StrategySignal"]` |
| N/A | ⚠️ No test file specific to this DTO | Medium | Tests exist for types version, not schemas | Create `tests/shared/schemas/test_strategy_signal.py` |

---

## 4) Correctness & Contracts

### Correctness Checklist

- [x] The file has a **clear purpose** and does not mix unrelated concerns (SRP)
  - **Finding**: ✅ Single responsibility - DTO for strategy signals in event-driven communication
  - **Note**: Purpose is clear but overlaps with `shared/types/strategy_value_objects.py`

- [x] Public functions/classes have **docstrings** with inputs/outputs, pre/post-conditions, and failure modes
  - **Finding**: ✅ Class docstring present (lines 22-26)
  - **Issue**: ⚠️ Missing examples for `to_dict()` and `from_dict()` methods

- [x] **Type hints** are complete and precise (no `Any` in domain logic; use `Literal/NewType` where helpful)
  - **Finding**: ⚠️ Partial - `metadata: dict[str, Any]` uses `Any` (line 59)
  - **Finding**: ⚠️ `action: str` should be `Literal["BUY", "SELL", "HOLD"]` (line 44)
  - **Otherwise**: ✅ Good type hints throughout

- [x] **DTOs** are **frozen/immutable** and validated (e.g., Pydantic v2 models with constrained types)
  - **Finding**: ✅ `frozen=True` (line 30)
  - **Finding**: ✅ `strict=True` enforces type validation (line 29)
  - **Finding**: ✅ Field constraints used (`min_length`, `max_length`, `ge`, `le`)

- [x] **Numerical correctness**: currency uses `Decimal`; floats use `math.isclose` or explicit tolerances; no `==`/`!=` on floats
  - **Finding**: ✅ Uses `Decimal` for `allocation_weight` and `signal_strength` (lines 51, 56)
  - **Finding**: ✅ No float comparisons in code

- [x] **Error handling**: exceptions are narrow, typed (from `shared.errors`), logged with context, and never silently caught
  - **Finding**: ✅ Raises `ValueError` with context (lines 74, 126, 138)
  - **Note**: DTOs typically use `ValidationError` from Pydantic, which is appropriate here

- [x] **Idempotency**: handlers tolerate replays; side-effects are guarded by idempotency keys or checks
  - **Finding**: ✅ Pure DTO - no side effects; immutable after creation
  - **Finding**: ✅ Includes `correlation_id` and `causation_id` for idempotency tracking in handlers

- [x] **Determinism**: tests freeze time (`freezegun`), seed RNG; no hidden randomness in business logic
  - **Finding**: ✅ No randomness in DTO; timestamp is explicit parameter
  - **Issue**: ⚠️ No tests exist specifically for this file (tests exist for types version)

- [x] **Security**: no secrets in code/logs; input validation at boundaries; no `eval`/`exec`/dynamic imports
  - **Finding**: ✅ No secrets, eval, or exec
  - **Finding**: ✅ Input validation via Pydantic constraints
  - **Finding**: ⚠️ `metadata: dict[str, Any]` could accept arbitrary data (consider logging redaction)

- [x] **Observability**: structured logging with `correlation_id`/`causation_id`; one log per state change; no spam in hot loops
  - **Finding**: ✅ DTOs include `correlation_id` and `causation_id` fields for tracing
  - **Note**: N/A - DTOs don't log; consuming handlers do

- [x] **Testing**: public APIs have tests; property-based tests for maths; coverage ≥ 80% (≥ 90% for strategy/portfolio)
  - **Finding**: ❌ No test file for `shared/schemas/strategy_signal.py`
  - **Finding**: ✅ Tests exist for `shared/types/strategy_value_objects.py` (likely used instead)
  - **Action**: Create tests or deprecate this version

- [x] **Performance**: no hidden I/O in hot paths; vectorised Pandas ops; HTTP clients pooled with rate limits
  - **Finding**: ✅ N/A - Pure in-memory DTO; no I/O

- [x] **Complexity**: cyclomatic ≤ 10, cognitive ≤ 15, functions ≤ 50 lines, params ≤ 5
  - **Finding**: ✅ All validators ≤ 15 lines
  - **Finding**: ✅ `from_dict()` is 37 lines (acceptable for conversion logic)
  - **Finding**: ✅ `to_dict()` is 19 lines
  - **Cyclomatic**: ≤ 5 per method (simple conditionals only)

- [x] **Module size**: ≤ 500 lines (soft), split if > 800
  - **Finding**: ✅ 141 lines total (well within limit)

- [x] **Imports**: no `import *`; stdlib → third-party → local; no deep relative imports
  - **Finding**: ✅ Clean imports; proper ordering
  - **Finding**: ✅ Uses relative import for `..utils.timezone_utils` (appropriate for internal module)

---

### Contract Issues

#### Issue 1: Duplicate StrategySignal Definitions

**Severity**: 🔴 HIGH

**Files Affected**:
- `the_alchemiser/shared/schemas/strategy_signal.py` (this file)
- `the_alchemiser/shared/types/strategy_value_objects.py` (reviewed separately)

**Field Comparison**:

| Field | schemas/strategy_signal.py | types/strategy_value_objects.py | Notes |
|-------|---------------------------|--------------------------------|-------|
| correlation_id | ✅ Required (str) | ❌ Via extra="allow" | Event-driven field |
| causation_id | ✅ Required (str) | ❌ Via extra="allow" | Event-driven field |
| timestamp | ✅ Required (datetime) | ✅ Required (datetime) | ✅ Consistent |
| symbol | ✅ str (validated) | ✅ Symbol (typed) | Different types |
| action | ✅ str (validated) | ✅ ActionLiteral | Different types |
| reasoning | ✅ Required (str) | ✅ Optional (str, default="") | Different defaults |
| strategy_name | ✅ Optional (str) | ❌ None | Only in schemas |
| allocation_weight | ✅ Optional (Decimal) | ❌ None | **Name mismatch** |
| target_allocation | ❌ None | ✅ Optional (Decimal) | **Name mismatch** |
| signal_strength | ✅ Optional (Decimal) | ❌ None | Only in schemas |
| metadata | ✅ Optional (dict) | ❌ None | Only in schemas |

**Critical Issues**:
1. Field name mismatch: `allocation_weight` vs `target_allocation`
2. Different type representations: `str` vs `Symbol`, `str` vs `ActionLiteral`
3. Different default behaviors: `reasoning` required vs optional
4. Handler uses types version, but this schemas version has richer metadata

**Resolution Required**:
Per Copilot Instructions and architectural review findings:
- **Option A (Recommended)**: Deprecate `shared/types/strategy_value_objects.py`; consolidate on schemas version
  - Rationale: schemas version has richer event-driven metadata (correlation_id, causation_id)
  - Aligns with event-driven architecture requirements
  - More complete for inter-module communication

- **Option B**: Deprecate this file; use types version as canonical
  - Rationale: types version has better type safety (Symbol, ActionLiteral)
  - But lacks correlation fields (workaround via extra="allow" is fragile)

- **Option C**: Merge both into single canonical definition in shared/schemas
  - Use best features of both (strong typing + correlation fields)
  - Create migration path with clear deprecation notices

**Recommendation**: **Option C** - Merge best of both, then deprecate types version
- Add `schema_version` field for event evolution
- Use `Literal` types for better type safety
- Keep correlation fields for event-driven architecture
- Document migration in CHANGELOG
- Bump MINOR version (breaking change for types users)

#### Issue 2: Missing Schema Versioning

**Severity**: 🔴 HIGH

**Evidence**:
- No `schema_version` field in DTO (lines 36-59)
- Copilot Instructions state: "DTOs in `shared/schemas/` with... versioned via `schema_version`"
- Event contracts need versioning for:
  - Event replay tolerance
  - Version evolution
  - Breaking change detection
  - Schema registry compatibility

**Example from other DTOs**:
```python
# From similar schemas (expected pattern)
schema_version: str = Field(default="1.0", description="DTO schema version")
```

**Proposed Fix**:
```python
class StrategySignal(BaseModel):
    # ... existing config ...
    
    # Schema version for evolution tracking
    schema_version: str = Field(
        default="1.0",
        pattern=r"^\d+\.\d+$",
        description="DTO schema version (major.minor)"
    )
    
    # Required correlation fields
    correlation_id: str = Field(...)
    # ... rest of fields ...
```

---

## 5) Additional Notes

### Architecture Clarity

**Purpose of This File**:
- DTO for **inter-module communication** in event-driven architecture
- Used in `SignalGenerated` events (strategy → portfolio boundary)
- Includes correlation/causation IDs for event tracing
- Serialization-focused (to_dict/from_dict for event payloads)

**Contrast with shared/types/strategy_value_objects.py**:
- Value object for **domain logic** within strategy module
- Stronger type safety (Symbol, ActionLiteral)
- Allows extra fields for flexibility
- Used by `strategy_v2/handlers/signal_generation_handler.py`

### Usage Analysis

**Where This Class is Imported**:
```bash
$ grep -r "from.*strategy_signal import" the_alchemiser/
the_alchemiser/shared/schemas/__init__.py:from .strategy_signal import StrategySignal
```

**Where Types Version is Imported**:
```bash
$ grep -r "from.*strategy_value_objects import" the_alchemiser/
the_alchemiser/shared/types/__init__.py:from .strategy_value_objects import StrategySignal
the_alchemiser/shared/types/strategy_protocol.py:from .strategy_value_objects import StrategySignal
the_alchemiser/strategy_v2/handlers/signal_generation_handler.py:from the_alchemiser.shared.types import StrategySignal
```

**Observation**: Types version is actively used; schemas version may be dead code or future intent.

### Security & Compliance

- ✅ No secrets or credentials
- ✅ No eval/exec/dynamic imports
- ⚠️ `reasoning` field might contain sensitive information; consider:
  - Max length validation (add `max_length=1000`)
  - Redaction policy for logging
  - PII scanning if user-generated
- ⚠️ `metadata: dict[str, Any]` could contain sensitive data:
  - Document allowed keys
  - Consider structured metadata DTO instead of free-form dict
  - Add serialization hooks to redact sensitive keys

### Performance

- ✅ Pure in-memory object; no I/O
- ✅ Minimal computational overhead
- ✅ Decimal operations are efficient for the scale of data
- ✅ Pydantic v2 has excellent performance (Rust core)

### Comparison with Best Practice (rebalance_plan.py)

The `rebalance_plan.py` file demonstrates similar patterns:
- ✅ Uses `ConfigDict(strict=True, frozen=True)`
- ✅ Includes correlation_id, causation_id, timestamp
- ✅ Has `to_dict()` and `from_dict()` methods
- ✅ Uses `ensure_timezone_aware` for datetime validation
- ✅ Validates action field against allowed values
- ⚠️ Also missing `schema_version` field (same issue)

### Test Coverage Gap

**Current State**:
- Tests exist for `tests/shared/types/test_strategy_value_objects.py` (519 lines)
- No tests for `tests/shared/schemas/test_strategy_signal.py`

**Required Tests** (if keeping this version):
1. Field validation (correlation_id, causation_id, timestamp, symbol, action, reasoning)
2. Optional field handling (strategy_name, allocation_weight, signal_strength, metadata)
3. Decimal conversion and precision
4. Timezone validation
5. Serialization round-trip (`to_dict()` → `from_dict()`)
6. Error cases (invalid action, missing required fields, invalid Decimal ranges)
7. Symbol normalization (uppercase, strip whitespace)
8. ISO timestamp formats (with/without 'Z' suffix)

---

## 6) Recommended Fixes

### Priority 1: Critical (Must Fix Before Production Use)

#### Fix 1: Resolve Duplicate StrategySignal Classes

**Action**: Merge both versions into single canonical definition

**Location**: Create new consolidated version in `shared/schemas/strategy_signal.py`

**Implementation**:
```python
#!/usr/bin/env python3
"""Business Unit: shared | Status: current.

Strategy signal data transfer objects for inter-module communication.

Canonical StrategySignal DTO combining best practices from both previous versions:
- Strong typing (Literal, Symbol) from shared/types version
- Event-driven fields (correlation_id, causation_id) from shared/schemas version
- Schema versioning for event evolution
"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from ..types.percentage import Percentage
from ..utils.timezone_utils import ensure_timezone_aware
from ..value_objects.symbol import Symbol

# Type alias for valid trading actions
ActionLiteral = Literal["BUY", "SELL", "HOLD"]


class StrategySignal(BaseModel):
    """DTO for strategy signal data transfer (v1.0).

    Used for communication between strategy and portfolio modules in event-driven architecture.
    Includes correlation tracking, serialization helpers, and schema versioning.

    Schema Version: 1.0 (introduced 2025-01-07)

    Attributes:
        schema_version: DTO schema version for evolution tracking
        correlation_id: Unique correlation identifier for event tracing
        causation_id: Causation identifier for traceability
        timestamp: Signal generation timestamp (timezone-aware UTC)
        symbol: Trading symbol (e.g., "AAPL", "SPY")
        action: Trading action (BUY, SELL, or HOLD)
        reasoning: Human-readable explanation for the signal
        strategy_name: Optional strategy identifier
        target_allocation: Optional target portfolio allocation (0.0-1.0)
        signal_strength: Optional raw signal strength value (≥ 0)
        metadata: Optional additional signal metadata

    Examples:
        >>> from datetime import datetime, UTC
        >>> from decimal import Decimal
        >>> 
        >>> # Minimal signal
        >>> signal = StrategySignal(
        ...     correlation_id="corr-123",
        ...     causation_id="cause-456",
        ...     timestamp=datetime.now(UTC),
        ...     symbol="AAPL",
        ...     action="BUY",
        ...     reasoning="Strong momentum detected"
        ... )
        >>> 
        >>> # Full signal with allocation
        >>> signal = StrategySignal(
        ...     correlation_id="corr-789",
        ...     causation_id="cause-012",
        ...     timestamp=datetime.now(UTC),
        ...     symbol=Symbol("SPY"),
        ...     action="BUY",
        ...     reasoning="Defensive rebalance",
        ...     strategy_name="dsl_momentum",
        ...     target_allocation=Decimal("0.3"),
        ...     signal_strength=Decimal("0.85")
        ... )

    Raises:
        ValidationError: If action is not BUY/SELL/HOLD
        ValidationError: If target_allocation is outside [0, 1]
        ValidationError: If timestamp is timezone-naive
        ValueError: If symbol validation fails

    """

    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
        str_strip_whitespace=True,
    )

    # Schema versioning
    schema_version: str = Field(
        default="1.0",
        pattern=r"^\d+\.\d+$",
        description="DTO schema version (major.minor)"
    )

    # Required correlation fields
    correlation_id: str = Field(..., min_length=1, description="Unique correlation identifier")
    causation_id: str = Field(
        ..., min_length=1, description="Causation identifier for traceability"
    )
    timestamp: datetime = Field(..., description="Signal generation timestamp")

    # Signal fields (required)
    symbol: Symbol = Field(..., description="Trading symbol")
    action: ActionLiteral = Field(..., description="Trading action (BUY, SELL, HOLD)")
    reasoning: str = Field(..., min_length=1, max_length=1000, description="Human-readable signal reasoning")

    # Optional strategy context
    strategy_name: str | None = Field(
        default=None, description="Strategy that generated the signal"
    )
    target_allocation: Decimal | None = Field(
        default=None, ge=0, le=1, description="Recommended target allocation (0-1)"
    )

    # Optional signal metadata
    signal_strength: Decimal | None = Field(
        default=None, ge=0, description="Raw signal strength value"
    )
    metadata: dict[str, Any] | None = Field(default=None, description="Additional signal metadata")

    @field_validator("symbol", mode="before")
    @classmethod
    def normalize_symbol(cls, v: Symbol | str) -> Symbol:
        """Convert string to Symbol instance."""
        if isinstance(v, str):
            return Symbol(v.strip().upper())
        return v

    @field_validator("timestamp")
    @classmethod
    def ensure_timezone_aware_timestamp(cls, v: datetime) -> datetime:
        """Ensure timestamp is timezone-aware."""
        result = ensure_timezone_aware(v)
        if result is None:
            raise ValueError("timestamp cannot be None")
        return result

    @field_validator("target_allocation", mode="before")
    @classmethod
    def normalize_allocation(cls, v: Decimal | float | int | Percentage | None) -> Decimal | None:
        """Convert allocation to Decimal."""
        if v is None:
            return None
        if isinstance(v, Percentage):
            return v.value
        if isinstance(v, (float, int)):
            return Decimal(str(v))
        return v

    def to_dict(self) -> dict[str, Any]:
        """Convert DTO to dictionary for serialization.

        Returns:
            Dictionary representation with ISO timestamps and string Decimals.

        """
        data = self.model_dump()

        # Convert datetime to ISO string
        if self.timestamp:
            data["timestamp"] = self.timestamp.isoformat()

        # Convert Symbol to string
        if isinstance(data.get("symbol"), dict):
            data["symbol"] = data["symbol"]["value"]
        elif hasattr(self.symbol, "value"):
            data["symbol"] = self.symbol.value

        # Convert Decimal fields to string for JSON serialization
        for field_name in ["target_allocation", "signal_strength"]:
            if data.get(field_name) is not None:
                data[field_name] = str(data[field_name])

        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> StrategySignal:
        """Create DTO from dictionary.

        Args:
            data: Dictionary containing DTO data

        Returns:
            StrategySignal instance

        Raises:
            ValueError: If data is invalid or missing required fields

        """
        # Convert string timestamp back to datetime
        if "timestamp" in data and isinstance(data["timestamp"], str):
            try:
                timestamp_str = data["timestamp"]
                if timestamp_str.endswith("Z"):
                    timestamp_str = timestamp_str[:-1] + "+00:00"
                data["timestamp"] = datetime.fromisoformat(timestamp_str)
            except ValueError as e:
                raise ValueError(f"Invalid timestamp format: {data['timestamp']}") from e

        # Convert string decimal fields back to Decimal
        for field_name in ["target_allocation", "signal_strength"]:
            if (
                field_name in data
                and data[field_name] is not None
                and isinstance(data[field_name], str)
            ):
                try:
                    data[field_name] = Decimal(data[field_name])
                except (ValueError, TypeError) as e:
                    raise ValueError(f"Invalid {field_name} value: {data[field_name]}") from e

        return cls(**data)


__all__ = ["ActionLiteral", "StrategySignal"]
```

**Migration Steps**:
1. ✅ Create consolidated version above (done)
2. Add deprecation warning to `shared/types/strategy_value_objects.py`
3. Update all imports to use `from the_alchemiser.shared.schemas import StrategySignal`
4. Update tests to cover new consolidated version
5. Remove deprecated type after one minor version cycle
6. Bump version: `make bump-minor` (breaking change)

#### Fix 2: Add Schema Versioning

**Status**: ✅ Included in Fix 1 above

**Justification**: Event-driven architecture requires version tracking for:
- Schema evolution (adding/removing fields)
- Event replay compatibility
- Breaking change detection
- Schema registry integration

---

### Priority 2: High (Should Fix This Sprint)

#### Fix 3: Use Literal Type for Action Field

**Status**: ✅ Included in Fix 1 above (uses `ActionLiteral`)

**Benefits**:
- Type checker catches invalid actions at design time
- Better IDE autocomplete
- Self-documenting code

#### Fix 4: Add Max Length to Reasoning Field

**Current**:
```python
reasoning: str = Field(..., min_length=1, description="Human-readable signal reasoning")
```

**Fixed**:
```python
reasoning: str = Field(
    ...,
    min_length=1,
    max_length=1000,
    description="Human-readable signal reasoning"
)
```

**Justification**: Prevents unbounded strings (memory, logs, JSON size)

---

### Priority 3: Medium (Nice to Have)

#### Fix 5: Document Metadata Schema

**Issue**: `metadata: dict[str, Any]` allows unconstrained data

**Options**:

**Option A**: Document allowed keys in docstring
```python
metadata: dict[str, Any] | None = Field(
    default=None,
    description=(
        "Additional signal metadata. "
        "Allowed keys: 'indicators' (dict), 'confidence' (float 0-1), "
        "'data_source' (str), 'strategy_params' (dict)"
    )
)
```

**Option B**: Create structured metadata DTO (preferred)
```python
class SignalMetadata(BaseModel):
    indicators: dict[str, Decimal] | None = None
    confidence: Decimal | None = Field(default=None, ge=0, le=1)
    data_source: str | None = None
    strategy_params: dict[str, Any] | None = None

# Then in StrategySignal:
metadata: SignalMetadata | None = Field(default=None, description="Signal metadata")
```

#### Fix 6: Add __all__ Declaration

**Add to end of file**:
```python
__all__ = ["ActionLiteral", "StrategySignal"]
```

---

## 7) Test Coverage Requirements

If keeping this version, create `tests/shared/schemas/test_strategy_signal.py`:

```python
"""Business Unit: shared | Status: current.

Comprehensive unit tests for StrategySignal DTO.

Tests StrategySignal schema validation, serialization, and deserialization.
"""

import pytest
from datetime import datetime, UTC
from decimal import Decimal
from pydantic import ValidationError

from the_alchemiser.shared.schemas.strategy_signal import StrategySignal


class TestStrategySignalValidation:
    """Test StrategySignal field validation."""

    def test_minimal_valid_signal(self):
        """Test creating minimal valid signal."""
        signal = StrategySignal(
            correlation_id="test-corr-123",
            causation_id="test-cause-456",
            timestamp=datetime.now(UTC),
            symbol="AAPL",
            action="BUY",
            reasoning="Test signal"
        )
        assert signal.symbol == "AAPL"
        assert signal.action == "BUY"
        assert signal.schema_version == "1.0"

    def test_invalid_action_rejected(self):
        """Test invalid action raises ValidationError."""
        with pytest.raises(ValidationError):
            StrategySignal(
                correlation_id="test-corr",
                causation_id="test-cause",
                timestamp=datetime.now(UTC),
                symbol="AAPL",
                action="INVALID",
                reasoning="Test"
            )

    # ... more tests ...


class TestStrategySignalSerialization:
    """Test to_dict and from_dict methods."""

    def test_round_trip_serialization(self):
        """Test serialization round-trip preserves data."""
        original = StrategySignal(
            correlation_id="test-corr",
            causation_id="test-cause",
            timestamp=datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC),
            symbol="AAPL",
            action="BUY",
            reasoning="Test",
            target_allocation=Decimal("0.5")
        )
        
        # Serialize
        data = original.to_dict()
        assert isinstance(data["timestamp"], str)
        assert isinstance(data["target_allocation"], str)
        
        # Deserialize
        restored = StrategySignal.from_dict(data)
        assert restored.symbol == original.symbol
        assert restored.target_allocation == original.target_allocation

    # ... more tests ...
```

---

## 8) Conclusion

**Overall Assessment**: ⚠️ REQUIRES ATTENTION

The file implements a clean, well-structured DTO but has **critical architectural duplication** and **missing schema versioning**. The biggest concerns are:

1. Duplicate StrategySignal class in codebase (schemas vs types)
2. Missing schema_version field for event evolution
3. Field name inconsistency (allocation_weight vs target_allocation)
4. Weaker type safety (str action vs Literal)

**Risk Level**: 🟡 MEDIUM-HIGH
- Won't cause immediate failures (good validation)
- **CAN cause confusion** (which class to use?)
- **CAN cause integration issues** (field name mismatches)
- Missing version tracking hampers event evolution

**Recommended Action**:
- 🔴 Fix all Critical and High severity issues immediately (before next release)
- Consolidate duplicate StrategySignal classes (Option C - merge best of both)
- Add schema_version field for event evolution
- Use Literal types for better type safety
- Add comprehensive test coverage
- Document migration path clearly
- Bump MINOR version (new features + breaking changes)

**Lines of Code**: 141 (well within limit)

**Complexity**: Low (all methods < 40 lines, simple logic)

**Maintainability**: Good (clear structure, good documentation) but duplication is confusing

**Recommendation to User**: Merge both StrategySignal versions into single canonical definition in `shared/schemas/` with:
- Strong typing from types version (Symbol, ActionLiteral)
- Event-driven fields from schemas version (correlation_id, causation_id)
- Schema versioning for evolution
- Comprehensive tests
- Clear deprecation notices and migration guide

---

**Auto-generated**: 2025-01-07  
**Reviewer**: Copilot AI Agent  
**File**: `the_alchemiser/shared/schemas/strategy_signal.py`  
**Status**: COMPLETE - Ready for stakeholder review
