# Action Checklist: enriched_data.py Remediation

**File**: `the_alchemiser/shared/schemas/enriched_data.py`  
**Review Date**: 2025-01-06  
**Version**: 2.18.3  
**Status**: Action items identified, awaiting implementation

This checklist tracks remediation of issues identified in FILE_REVIEW_enriched_data.md.

---

## Critical Priority (P0) - Must Fix Before Production

### [ ] C1. Add Schema Versioning
**Status**: 🔴 NOT STARTED  
**Effort**: 15 minutes  
**Risk**: CRITICAL - Cannot evolve schemas safely

**Tasks**:
- [ ] Add `schema_version` field to `EnrichedOrderView`
- [ ] Add `schema_version` field to `OpenOrdersView`
- [ ] Add `schema_version` field to `EnrichedPositionView`
- [ ] Add `schema_version` field to `EnrichedPositionsView`
- [ ] Set default value to "1.0" for all
- [ ] Add Field description for schema_version
- [ ] Update tests to validate schema_version presence
- [ ] Add schema_version to checklist for all future schemas

**Implementation**:
```python
class EnrichedOrderView(BaseModel):
    """DTO for enriched order data with domain mapping."""
    
    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )
    
    schema_version: str = Field(default="1.0", description="DTO schema version")
    raw: dict[str, Any]  # TODO: Replace with typed model (see C2)
    domain: dict[str, Any]  # TODO: Replace with typed model (see C2)
    summary: dict[str, Any]  # TODO: Replace with typed model (see C2)
```

**Validation**:
- [ ] Run tests: `pytest tests/shared/schemas/test_enriched_data.py -v`
- [ ] Verify all DTOs serialize with schema_version
- [ ] Check no breaking changes to existing consumers

---

### [ ] C2. Replace dict[str, Any] with Typed Models
**Status**: 🔴 NOT STARTED  
**Effort**: 2-4 hours  
**Risk**: CRITICAL - Type safety violation

**Phase 1: Define Nested Models (1-2 hours)**
- [ ] Create `RawOrderData(BaseModel)` with Alpaca API fields
- [ ] Create `DomainOrderData(BaseModel)` with domain fields
- [ ] Create `OrderSummaryData(BaseModel)` with summary fields
- [ ] Create `RawPositionData(BaseModel)` with Alpaca API fields
- [ ] Create `PositionSummaryData(BaseModel)` with summary fields
- [ ] Use `Decimal` for all financial values (prices, quantities, P&L)
- [ ] Add Field descriptions to all nested model fields
- [ ] Add validators for required fields

**Phase 2: Update DTOs (30 minutes)**
- [ ] Replace `raw: dict[str, Any]` with typed models in EnrichedOrderView
- [ ] Replace `domain: dict[str, Any]` with typed model in EnrichedOrderView
- [ ] Replace `summary: dict[str, Any]` with typed model in EnrichedOrderView
- [ ] Replace `raw: dict[str, Any]` with typed model in EnrichedPositionView
- [ ] Replace `summary: dict[str, Any]` with typed model in EnrichedPositionView

**Phase 3: Update Tests (30 minutes)**
- [ ] Update test fixtures to use typed models instead of dicts
- [ ] Add tests for nested model validation
- [ ] Add tests for Decimal precision handling
- [ ] Add property-based tests with Hypothesis for financial values

**Example Implementation**:
```python
from decimal import Decimal
from datetime import datetime
from pydantic import Field

class OrderSummaryData(BaseModel):
    """Summary of order execution details."""
    
    model_config = ConfigDict(strict=True, frozen=True)
    
    status: Literal["pending", "filled", "cancelled", "rejected"] = Field(
        description="Order execution status"
    )
    filled_qty: Decimal = Field(ge=0, description="Quantity filled")
    filled_avg_price: Decimal | None = Field(
        default=None, gt=0, description="Average fill price"
    )
    order_type: str = Field(description="Order type (market, limit, etc.)")
    side: Literal["buy", "sell"] = Field(description="Order side")
    submitted_at: datetime = Field(description="Order submission timestamp (UTC)")

class EnrichedOrderView(BaseModel):
    """DTO for enriched order data with domain mapping."""
    
    model_config = ConfigDict(strict=True, frozen=True, validate_assignment=True)
    
    schema_version: str = Field(default="1.0", description="DTO schema version")
    raw: RawOrderData = Field(description="Raw Alpaca API response")
    domain: DomainOrderData = Field(description="Domain order object")
    summary: OrderSummaryData = Field(description="Order execution summary")
```

**Validation**:
- [ ] Run type checker: `make type-check`
- [ ] Run all tests: `pytest tests/shared/schemas/test_enriched_data.py -v`
- [ ] Verify no `dict[str, Any]` in file: `grep "dict\[str, Any\]" the_alchemiser/shared/schemas/enriched_data.py`
- [ ] Check mypy passes with no `Any` warnings

**Breaking Changes**:
⚠️ This is a breaking change. Existing code must be updated to use typed models.
- [ ] Find all usages: `grep -r "EnrichedOrderView\|EnrichedPositionView" --include="*.py"`
- [ ] Update consumers to pass typed models instead of dicts
- [ ] Update serialization/deserialization code if needed
- [ ] Consider migration period with both dict and typed versions

---

### [ ] C3. Fix Inaccurate Module Docstring
**Status**: 🔴 NOT STARTED  
**Effort**: 10 minutes  
**Risk**: MEDIUM - Documentation correctness

**Tasks**:
- [ ] Update module docstring to mention both orders AND positions
- [ ] Add Key Features section like accounts.py
- [ ] Add usage examples
- [ ] Document the enrichment pattern (raw + domain + summary)

**Implementation**:
```python
"""Business Unit: shared | Status: current.

Order and position enrichment schemas for The Alchemiser Trading System.

This module contains schemas for enriched order and position data views,
providing a unified pattern for exposing raw API data, domain objects, and
computed summaries through a consistent interface.

Key Features:
- Pydantic v2 BaseModel with strict validation
- Schema versioning for safe evolution
- Typed nested models for raw, domain, and summary data
- Immutable DTOs (frozen=True)
- Type safety for financial values (Decimal)
- Result-oriented response patterns

Usage:
    >>> from decimal import Decimal
    >>> from the_alchemiser.shared.schemas.enriched_data import EnrichedOrderView
    >>> 
    >>> order = EnrichedOrderView(
    ...     schema_version="1.0",
    ...     raw=RawOrderData(...),
    ...     domain=DomainOrderData(...),
    ...     summary=OrderSummaryData(
    ...         status="filled",
    ...         filled_qty=Decimal("10"),
    ...         filled_avg_price=Decimal("150.25"),
    ...         order_type="market",
    ...         side="buy",
    ...         submitted_at=datetime.now(UTC)
    ...     )
    ... )

The enrichment pattern provides three views of the same data:
- raw: Unprocessed data from external APIs (e.g., Alpaca)
- domain: Domain objects with business logic applied
- summary: Computed metrics and human-readable summaries
"""
```

**Validation**:
- [ ] Check docstring formatting: `python -m pydoc the_alchemiser.shared.schemas.enriched_data`
- [ ] Verify examples are accurate and runnable
- [ ] Compare with accounts.py and trade_run_result.py for consistency

---

## High Priority (P1) - Should Fix This Sprint

### [x] H1. Zero Test Coverage
**Status**: ✅ COMPLETED (2025-01-06)  
**Effort**: 3 hours  
**Risk**: HIGH - Cannot verify correctness

**Completed Tasks**:
- [x] Created comprehensive test suite (41 tests)
- [x] Test all 4 DTOs (EnrichedOrderView, OpenOrdersView, EnrichedPositionView, EnrichedPositionsView)
- [x] Test immutability (frozen=True)
- [x] Test validation (strict mode, required fields)
- [x] Test serialization (model_dump, model_dump_json)
- [x] Test backward compatibility aliases
- [x] Test configuration compliance

**File**: `tests/shared/schemas/test_enriched_data.py` (427 lines, 41 tests)

---

### [ ] H2. Add Field-Level Documentation
**Status**: 🔴 NOT STARTED  
**Effort**: 30 minutes  
**Risk**: MEDIUM - API clarity

**Tasks**:
- [ ] Add Field(description=...) to all fields in EnrichedOrderView
- [ ] Add Field(description=...) to all fields in OpenOrdersView
- [ ] Add Field(description=...) to all fields in EnrichedPositionView
- [ ] Add Field(description=...) to all fields in EnrichedPositionsView
- [ ] Document expected dict keys for raw/domain/summary (until C2 is fixed)
- [ ] Add examples in descriptions where helpful

**Implementation**:
```python
class OpenOrdersView(Result):
    """DTO for open orders list response."""
    
    model_config = ConfigDict(
        strict=True,
        frozen=True,
        validate_assignment=True,
    )
    
    orders: list[EnrichedOrderView] = Field(
        description="List of enriched order views. Empty list if no open orders."
    )
    symbol_filter: str | None = Field(
        default=None,
        max_length=10,
        pattern=r"^[A-Z]+$",
        description="Optional symbol filter applied to results. None if no filter."
    )
```

**Validation**:
- [ ] Run tests to ensure Field changes don't break anything
- [ ] Check API docs generation (if using tools like pdoc)

---

### [ ] H3. Add Validators
**Status**: 🔴 NOT STARTED (Will be easier after C2)  
**Effort**: 1 hour  
**Risk**: MEDIUM - Data integrity

**Tasks**:
- [ ] Add model_validator to check dict structure (temporary, until C2)
- [ ] Add field_validator for symbol_filter pattern
- [ ] Add list length constraints
- [ ] Validate timestamp fields are timezone-aware
- [ ] Validate financial values are non-negative where appropriate

**Implementation** (temporary dict validation):
```python
from pydantic import field_validator, model_validator

class EnrichedOrderView(BaseModel):
    # ... fields ...
    
    @model_validator(mode="after")
    def validate_dict_structure(self) -> "EnrichedOrderView":
        """Validate required keys in dict fields."""
        if "id" not in self.raw:
            raise ValueError("raw dict must contain 'id' key")
        if "symbol" not in self.domain:
            raise ValueError("domain dict must contain 'symbol' key")
        if "status" not in self.summary:
            raise ValueError("summary dict must contain 'status' key")
        return self

class OpenOrdersView(Result):
    # ... fields ...
    
    @field_validator("symbol_filter")
    @classmethod
    def validate_symbol_filter(cls, v: str | None) -> str | None:
        """Validate symbol filter is uppercase and alphanumeric."""
        if v is not None:
            if not v.isupper():
                raise ValueError("symbol_filter must be uppercase")
            if not v.isalpha():
                raise ValueError("symbol_filter must contain only letters")
        return v
```

**After C2 is complete**, validators should check:
- Decimal values are properly quantized
- Timestamps are timezone-aware
- Quantities are non-negative
- Prices are positive

**Validation**:
- [ ] Add tests for validators
- [ ] Test both valid and invalid inputs
- [ ] Verify error messages are helpful

---

### [ ] H4. Add Financial Precision Types
**Status**: 🟡 BLOCKED BY C2  
**Effort**: Included in C2  
**Risk**: HIGH - Float imprecision

This issue will be resolved by C2 (replacing dict[str, Any] with typed models).

**Tasks** (part of C2):
- [ ] Use Decimal for all prices
- [ ] Use Decimal for all quantities
- [ ] Use Decimal for all P&L values
- [ ] Set appropriate decimal context (e.g., 2 places for USD)
- [ ] Add quantization in validators

**Note**: Do not attempt this independently; implement as part of C2.

---

## Medium Priority (P2) - Nice to Have

### [ ] M1. Enhance Module Docstring
**Status**: 🔴 NOT STARTED (Partial overlap with C3)  
**Effort**: 20 minutes  
**Risk**: LOW - Documentation quality

**Tasks**:
- [ ] Add Key Features section (covered by C3)
- [ ] Add Usage examples (covered by C3)
- [ ] Add "Related Modules" section
- [ ] Add "Migration Guide" if needed

---

### [ ] M2. Add Deprecation Warnings to Aliases
**Status**: 🔴 NOT STARTED  
**Effort**: 30 minutes  
**Risk**: LOW - API clarity

**Tasks**:
- [ ] Add deprecation warnings using `warnings.warn`
- [ ] Specify removal version (e.g., "3.0.0")
- [ ] Update comments with target removal date
- [ ] Add migration guide in docstring

**Implementation**:
```python
import warnings

# Backward compatibility aliases - DEPRECATED, will be removed in v3.0.0
def __getattr__(name: str):
    """Handle deprecated DTO alias access."""
    deprecated_aliases = {
        "EnrichedOrderDTO": "EnrichedOrderView",
        "OpenOrdersDTO": "OpenOrdersView",
        "EnrichedPositionDTO": "EnrichedPositionView",
        "EnrichedPositionsDTO": "EnrichedPositionsView",
    }
    
    if name in deprecated_aliases:
        new_name = deprecated_aliases[name]
        warnings.warn(
            f"{name} is deprecated and will be removed in v3.0.0. "
            f"Use {new_name} instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return globals()[new_name]
    
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
```

**Validation**:
- [ ] Test deprecation warnings are emitted
- [ ] Verify stacklevel shows correct calling location
- [ ] Update tests to handle warnings

---

### [ ] M3. Add __all__ Export Control
**Status**: 🔴 NOT STARTED  
**Effort**: 5 minutes  
**Risk**: LOW - API clarity

**Tasks**:
- [ ] Add `__all__` list at module level
- [ ] Include only public DTOs (View suffix)
- [ ] Exclude deprecated aliases

**Implementation**:
```python
__all__ = [
    "EnrichedOrderView",
    "OpenOrdersView",
    "EnrichedPositionView",
    "EnrichedPositionsView",
]
```

**Validation**:
- [ ] Check IDE auto-imports only suggest public APIs
- [ ] Verify `from enriched_data import *` only imports __all__ members

---

### [ ] M4. Align Naming Conventions
**Status**: 🟡 NEEDS DISCUSSION  
**Effort**: 2-4 hours (if changing names)  
**Risk**: MEDIUM - Breaking change

**Tasks**:
- [ ] Decide on naming convention: View, Result, Summary, or DTO?
- [ ] Survey existing schema files for dominant pattern
- [ ] If changing, plan migration strategy
- [ ] Update all usages in codebase
- [ ] Update tests
- [ ] Add deprecation period

**Note**: This may be deferred or rejected if "View" is acceptable.

---

## Investigation Tasks

### [ ] I1. Investigate Actual Usage
**Status**: 🔴 NOT STARTED  
**Effort**: 1 hour  
**Risk**: N/A - Information gathering

**Tasks**:
- [ ] Search for dynamic imports (importlib, __import__)
- [ ] Check for serialization/deserialization usage
- [ ] Search for model_validate calls with enriched_data
- [ ] Check Lambda handlers for usage
- [ ] Review CLI code for usage
- [ ] If no usage found, consider deprecating module

**Commands**:
```bash
# Search for imports
grep -r "enriched_data" --include="*.py"
grep -r "EnrichedOrderView\|EnrichedPositionView" --include="*.py"

# Search for dynamic imports
grep -r "importlib.*enriched" --include="*.py"
grep -r "__import__.*enriched" --include="*.py"

# Search for model_validate
grep -r "model_validate.*Enriched" --include="*.py"
```

**Outcomes**:
- If unused: Create issue to deprecate and remove
- If used: Add integration tests for usage patterns
- Document usage patterns in module docstring

---

## Summary

**Total Action Items**: 14
- Critical (P0): 3 items ❌ (C1, C2, C3)
- High (P1): 4 items (1✅ H1, 3❌ H2-H4)
- Medium (P2): 4 items ❌ (M1-M4)
- Investigation: 1 item ❌ (I1)

**Completed**: 1/14 (7%)
**In Progress**: 0/14 (0%)
**Not Started**: 13/14 (93%)

**Estimated Total Effort**: 8-12 hours
- Critical: 3-5 hours
- High: 2-3 hours
- Medium: 1 hour
- Investigation: 1 hour

**Recommended Sprint Allocation**:
- Sprint 1: C1, C3, H2 (2 hours) - Quick wins
- Sprint 2: C2, H3, H4 (4-6 hours) - Major refactor
- Sprint 3: M1-M4, I1 (2 hours) - Polish

---

**Checklist Created**: 2025-01-06  
**Next Review**: After C1, C2, C3 are complete
