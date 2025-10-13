# [File Review] Financial-grade, line-by-line audit - symbols_config.py

> **Purpose**: Conduct a rigorous, line-by-line review of `symbols_config.py` to institution-grade standards (correctness, controls, auditability, and safety).

---

## 0) Metadata

**File path**: `the_alchemiser/shared/config/symbols_config.py`

**Commit SHA / Tag**: `802cf268358e3299fb6b80a4b7cf3d4bda2994f4`

**Reviewer(s)**: GitHub Copilot Agent

**Date**: 2025-10-10

**Business function / Module**: shared / Symbol Classification Configuration

**Runtime context**: 
- **Deployment**: All contexts (AWS Lambda, local development, CI/CD)
- **Trading modes**: Paper trading, Live trading
- **Usage**: Symbol universe definition and asset type classification
- **Concurrency**: Not thread-safe (mutable global state)
- **Latency**: N/A (in-memory lookups, O(1) for sets)

**Criticality**: **P2 (Medium)** - Foundation for symbol validation and asset classification

**Direct dependencies (imports)**:
```python
Internal:
- None (standalone configuration module)

External:
- typing.Literal - Standard library type hint
```

**External services touched**:
- None (pure in-memory configuration)

**Interfaces (DTOs/events) produced/consumed**:
```
Produces:
- AssetType: Literal type for asset classification
- Symbol sets: ETF, CRYPTO universes

Consumed by:
- the_alchemiser/shared/config/__init__.py (public API)
- Strategy modules (indirectly via config)
- Portfolio modules (indirectly via config)

Schema version: N/A (configuration, not a DTO)
```

**Related docs/specs**:
- Copilot Instructions (.github/copilot-instructions.md)
- Symbol value object: the_alchemiser/shared/value_objects/symbol.py
- Symbol tests: tests/shared/value_objects/test_symbol.py

---

## 1) Scope & Objectives

This review verifies:

- ✅ **Single responsibility**: Symbol universe configuration and classification
- ⚠️ **Correctness**: Type safety, validation, symbol classification logic
- ✅ **Numerical integrity**: N/A (no numerical operations)
- ⚠️ **Deterministic behaviour**: Mutable global state is a concern
- ⚠️ **Error handling**: No validation or error handling
- ⚠️ **Idempotency**: add_etf_symbol() mutates global state
- ✅ **Observability**: No logging needed (pure config)
- ⚠️ **Security**: Input validation missing
- ⚠️ **Compliance**: Several Copilot Instructions violations
- ⚠️ **Interfaces/contracts**: Inconsistent with Symbol value object
- ✅ **Dead code**: None (144 lines, all used)
- ✅ **Complexity**: Simple (max complexity = 7, within limits)
- ⚠️ **Performance**: Sets are efficient, but no validation overhead

---

## 2) Summary of Findings (use severity labels)

### Critical

**CRIT-1: Mutable Global State (Thread-Safety Risk)** (Lines 16-43)
- **Risk**: `KNOWN_ETFS` and `KNOWN_CRYPTO` are mutable sets that can be modified at runtime
- **Impact**: 
  * **Thread-safety violation**: Multiple threads could modify these sets concurrently
  * `add_etf_symbol()` modifies global state without synchronization
  * In AWS Lambda, concurrent invocations could cause race conditions
  * Violates immutability principle for financial systems
  * Production note in docstring (line 126-128) warns about this but doesn't fix it
- **Violation**: Copilot Instructions: "DTOs are frozen/immutable"
- **Evidence**: 
  ```python
  KNOWN_ETFS = {  # ❌ Mutable set
      "SPY", "QQQ", ...
  }
  
  def add_etf_symbol(symbol: str) -> None:
      KNOWN_ETFS.add(symbol.upper().strip())  # ❌ Modifies global state
  ```
- **Recommendation**: 
  1. Convert to `frozenset` for immutability
  2. Remove `add_etf_symbol()` function or load from external config
  3. Add docstring warning about immutability in production
- **Priority**: **Critical (P0)** - Thread-safety is paramount in trading systems

### High

**HIGH-1: Inconsistent Symbol Validation with Symbol Value Object** (Lines 72, 106, 131)
- **Risk**: Symbol validation uses simple `upper().strip()` inconsistent with system's `Symbol` value object
- **Impact**: 
  * System has comprehensive `Symbol` value object (shared/value_objects/symbol.py) with strict validation:
    - No spaces allowed
    - Only alphanumeric, dots, and hyphens
    - No consecutive dots/hyphens
    - No leading/trailing dots/hyphens
    - Max length: 10 characters
  * This module accepts any string, including invalid symbols like "A B", "...", ".", "-"
  * Could accept symbols that would fail downstream in `Symbol` value object
  * **Inconsistent validation across system boundaries**
- **Violation**: Copilot Instructions: "Validate all external data at boundaries with DTOs (fail-closed)"
- **Evidence**: 
  ```python
  # symbols_config.py - minimal validation
  symbol_upper = symbol.upper().strip()  # ❌ No format validation
  
  # Symbol value object - comprehensive validation
  if " " in normalized:
      raise ValueError("Symbol must not contain spaces")
  if ".." in normalized or "--" in normalized:
      raise ValueError("Symbol contains invalid characters")
  ```
- **Recommendation**: 
  1. Import and use `Symbol` value object for validation
  2. Or replicate Symbol validation logic here
  3. Add `ValueError` for invalid symbols
- **Priority**: **High (P1)** - Inconsistent validation can propagate invalid data

**HIGH-2: No Input Validation or Error Handling** (Lines 54-144)
- **Risk**: All functions accept raw string input without validation
- **Impact**: 
  * `classify_symbol("")` → "STOCK" (empty string classified as stock)
  * `classify_symbol("   ")` → "STOCK" (whitespace classified as stock)
  * `is_etf(None)` → AttributeError (crashes instead of returning False)
  * `add_etf_symbol("")` → adds empty string to KNOWN_ETFS
  * No protection against malicious or malformed input
- **Violation**: Copilot Instructions: "Error handling: exceptions are narrow, typed, never silently caught"
- **Evidence**: 
  ```python
  def classify_symbol(symbol: str) -> AssetType:
      symbol_upper = symbol.upper().strip()  # ❌ No validation after strip
      # If symbol_upper is empty, still returns "STOCK"
  ```
- **Recommendation**: 
  1. Add validation at function entry points
  2. Raise `ValueError` for invalid inputs
  3. Import from `shared.errors` for typed exceptions
- **Priority**: **High (P1)** - Input validation is fundamental

**HIGH-3: Naive Option and Future Detection Logic** (Lines 82-90)
- **Risk**: Pattern matching for options and futures is overly simplistic and error-prone
- **Impact**: 
  * Options: Checks if symbol ends with "C" or "P" → False positives (e.g., "AAPC", "MSFTC")
  * Futures: Checks if symbol > 5 chars and last 2 chars are digits → False positives (e.g., "STOCK12", "TEST99")
  * Real option symbols have complex formats (e.g., "AAPL230120C00150000")
  * Real futures symbols have standard codes (e.g., "ESH23", "CLM23")
  * **High probability of misclassification**
- **Violation**: Copilot Instructions: "Correctness: public functions have docstrings with failure modes"
- **Evidence**: 
  ```python
  # False positive examples:
  classify_symbol("AAPC")     # → "OPTION" (should be "STOCK" or unknown)
  classify_symbol("STOCK12")  # → "FUTURE" (should be "STOCK")
  classify_symbol("A")        # → "STOCK" (correct, but no validation)
  ```
- **Recommendation**: 
  1. Document limitations in docstring
  2. Consider removing option/future detection or using proper regex
  3. Return explicit "UNKNOWN" asset type for ambiguous symbols
- **Priority**: **High (P1)** - Misclassification affects trading decisions

### Medium

**MED-1: Missing Docstrings for Module-Level Constants** (Lines 14-49)
- **Risk**: No documentation for what symbols are included/excluded in universes
- **Impact**: 
  * Developers don't know criteria for inclusion
  * No guidance on when to add new symbols
  * No versioning or change tracking
- **Violation**: Copilot Instructions: "Module docstring explains responsibility and invariants"
- **Evidence**: 
  ```python
  KNOWN_ETFS = {  # ❌ No docstring explaining criteria
      "SPY", "QQQ", ...
  }
  ```
- **Recommendation**: Add module-level docstrings explaining:
  1. Inclusion criteria for each universe
  2. Update process
  3. Source of truth (manual vs. external config)
- **Priority**: Medium (P2) - Documentation for maintainability

**MED-2: No Tests for symbols_config Module** (Not in file, but critical gap)
- **Risk**: No test coverage for this configuration module
- **Impact**: 
  * Cannot verify classification logic works correctly
  * No regression tests for edge cases
  * Changes could break downstream modules silently
  * No property-based tests for symbol validation
- **Violation**: Copilot Instructions: "Every public function/class has at least one test"
- **Evidence**: 
  ```bash
  $ find tests -name "*symbols_config*"
  # No results - no tests exist
  ```
- **Recommendation**: Create `tests/shared/config/test_symbols_config.py` with:
  1. Tests for each function
  2. Edge cases (empty, whitespace, special chars)
  3. Property-based tests (Hypothesis)
  4. Integration with Symbol value object
- **Priority**: Medium (P2) - Test coverage is required per guidelines

**MED-3: AssetType Literal Doesn't Match Industry Standards** (Line 51)
- **Risk**: Asset type classifications may not align with broker APIs or industry standards
- **Impact**: 
  * Alpaca API uses different asset class names
  * May need mapping layer between internal and external representations
  * "FUTURE" and "OPTION" detection is unreliable (see HIGH-3)
- **Violation**: Copilot Instructions: "Use industry standards"
- **Evidence**: 
  ```python
  AssetType = Literal["STOCK", "ETF", "CRYPTO", "OPTION", "FUTURE"]
  # Alpaca API uses: "us_equity", "crypto", etc.
  ```
- **Recommendation**: 
  1. Document mapping to external APIs
  2. Consider adding "UNKNOWN" type for ambiguous symbols
  3. Align with broker API enums if possible
- **Priority**: Medium (P2) - API compatibility

**MED-4: add_etf_symbol() Function Violates 12-Factor Config** (Lines 119-131)
- **Risk**: Runtime modification of configuration violates 12-factor principles
- **Impact**: 
  * Configuration should be immutable after load
  * Production systems should use external config (DB, S3, etc.)
  * Current implementation encourages runtime mutations
  * Docstring warns about this but doesn't prevent it
- **Violation**: Copilot Instructions: "No Hardcoding: 12-factor friendly"
- **Evidence**: 
  ```python
  def add_etf_symbol(symbol: str) -> None:
      """Add a new ETF symbol to the known list.
      
      Note:
          This modifies the global KNOWN_ETFS set. In production,
          this configuration should be loaded from a database or
          configuration service rather than modified at runtime.  # ❌ Warns but doesn't fix
      """
      KNOWN_ETFS.add(symbol.upper().strip())
  ```
- **Recommendation**: 
  1. Remove this function entirely
  2. Or make it raise `NotImplementedError` in production
  3. Load config from external source (S3, DynamoDB, etc.)
- **Priority**: Medium (P2) - Production readiness

### Low

**LOW-1: No Type Guards for String Input** (Lines 54-144)
- **Risk**: Functions accept `str` but don't verify input type at runtime
- **Impact**: 
  * Passing `int`, `float`, or `None` causes AttributeError
  * No Pydantic validation for function parameters
  * Type hints don't enforce runtime checks
- **Violation**: Copilot Instructions: "Type hints are complete and precise"
- **Evidence**: 
  ```python
  def is_etf(symbol: str) -> bool:
      return symbol.upper().strip() in KNOWN_ETFS  # ❌ Crashes if symbol is None
  ```
- **Recommendation**: Add runtime type checks or use Pydantic `@validate_call` decorator
- **Priority**: Low (P3) - Type hints should catch this in development

**LOW-2: Missing Examples in classify_symbol Docstring** (Lines 64-70)
- **Risk**: Limited examples in docstring don't cover edge cases
- **Impact**: 
  * Developers don't know how options/futures are classified
  * No examples for ambiguous cases
  * No examples for invalid inputs
- **Violation**: Copilot Instructions: "Docstrings include examples"
- **Evidence**: 
  ```python
  Examples:
      >>> classify_symbol("AAPL")
      'STOCK'
      >>> classify_symbol("SPY")
      'ETF'
      >>> classify_symbol("BTCUSD")
      'CRYPTO'
      # ❌ No examples for options, futures, or edge cases
  ```
- **Recommendation**: Add examples for all asset types and edge cases
- **Priority**: Low (P3) - Documentation completeness

**LOW-3: get_symbol_universe() Returns Incomplete Universe** (Lines 134-144)
- **Risk**: Function only returns ETF and CRYPTO universes, not STOCK, OPTION, or FUTURE
- **Impact**: 
  * Misleading function name suggests "all" universes
  * Incomplete data for callers expecting full universe
  * No way to get stock symbols programmatically
- **Violation**: Copilot Instructions: "Public functions have docstrings with returns"
- **Evidence**: 
  ```python
  def get_symbol_universe() -> dict[str, set[str]]:
      """Get all known symbol universes.  # ❌ Misleading - only 2 of 5 types
      
      Returns:
          Dictionary mapping asset types to symbol sets
      """
      return {
          "ETF": KNOWN_ETFS.copy(),
          "CRYPTO": KNOWN_CRYPTO.copy(),
          # ❌ Missing STOCK, OPTION, FUTURE
      }
  ```
- **Recommendation**: 
  1. Rename to `get_known_symbol_universes()` for clarity
  2. Or return all asset types (STOCK would be empty set)
  3. Update docstring to clarify which types are included
- **Priority**: Low (P3) - API clarity

### Info/Nits

**INFO-1: Good Module Header** (Lines 1-8)
- ✅ Proper business unit and status declaration
- ✅ Clear module purpose
- ✅ PEP 257 compliant docstring

**INFO-2: Appropriate Use of Sets for O(1) Lookups** (Lines 16-43)
- ✅ Sets provide efficient membership testing
- ✅ Correct data structure choice for known symbols

**INFO-3: Clean Import Structure** (Lines 10-12)
- ✅ Future annotations import
- ✅ Minimal dependencies (only typing.Literal)
- ✅ No circular imports

**INFO-4: Reasonable Complexity** (Radon analysis)
- ✅ classify_symbol: B (7) - Within acceptable range (≤10)
- ✅ All other functions: A (1) - Simple
- ✅ Module size: 144 lines - Well within 500 line soft limit

---

## 3) Line-by-Line Notes

### Detailed Line-by-Line Analysis

| Line(s) | Issue / Observation | Severity | Evidence / Excerpt | Proposed Action |
|---------|---------------------|----------|-------------------|-----------------|
| 1 | ✅ Proper shebang | Info | `#!/usr/bin/env python3` | None |
| 2-8 | ✅ Module header with business unit | Info | `"""Business Unit: shared \| Status: current."""` | None |
| 10 | ✅ Future annotations import | Info | `from __future__ import annotations` | None |
| 12 | ✅ Minimal dependencies | Info | `from typing import Literal` | None |
| 14-15 | Missing docstring for KNOWN_ETFS | Medium | No docstring explaining inclusion criteria | Add module-level constant docs |
| 16-35 | ❌ Mutable set (thread-safety) | Critical | `KNOWN_ETFS = {` (mutable) | Convert to `frozenset` |
| 16-35 | ✅ Comprehensive ETF coverage | Info | SPY, QQQ, TQQQ, SOXL, TECL, etc. | Good coverage of major ETFs |
| 37-38 | Missing docstring for KNOWN_CRYPTO | Medium | No docstring explaining inclusion criteria | Add constant docs |
| 38-43 | ❌ Mutable set (thread-safety) | Critical | `KNOWN_CRYPTO = {` (mutable) | Convert to `frozenset` |
| 45-49 | Questionable option patterns | High | `"C", "P"` too generic | Document limitations or remove |
| 51 | AssetType Literal definition | Medium | May not match broker APIs | Document mapping to external APIs |
| 54-93 | classify_symbol function | Multiple | Core classification logic | See detailed findings below |
| 72 | ❌ No validation after strip | High | `symbol_upper = symbol.upper().strip()` | Validate not empty |
| 75-76 | ✅ ETF check first (most specific) | Info | Correct precedence order | None |
| 79-80 | ✅ Crypto check | Info | Second in precedence | None |
| 82-85 | ❌ Naive option detection | High | `endswith(pattern) for pattern in OPTION_PATTERNS` | Document limitations or fix |
| 87-90 | ❌ Naive future detection | High | `len(symbol_upper) > 5 and symbol_upper[-2:].isdigit()` | Document limitations or fix |
| 93 | Default to STOCK classification | Low | Always returns STOCK if no match | Could return "UNKNOWN" |
| 96-107 | is_etf function | High | No input validation | Add Symbol validation |
| 106 | ❌ No validation | High | `symbol.upper().strip()` | Use Symbol value object |
| 109-117 | get_etf_symbols function | Low | Simple getter | Returns copy (good) |
| 119-131 | ❌ add_etf_symbol mutates global | Critical | `KNOWN_ETFS.add(...)` | Remove or deprecate |
| 126-128 | Docstring warns but doesn't fix | Medium | "In production, this configuration should be loaded..." | Implement the recommendation |
| 131 | ❌ No validation | High | `KNOWN_ETFS.add(symbol.upper().strip())` | Validate symbol format |
| 134-144 | get_symbol_universe function | Low | Incomplete universe | Rename or include all types |
| 142-143 | ✅ Returns copies of sets | Info | `.copy()` prevents external mutation | Good defensive programming |

---

## 4) Correctness & Contracts

### Correctness Checklist

- [x] The file has a **clear purpose** and does not mix unrelated concerns (SRP)
  - ✅ Single responsibility: Symbol universe configuration and classification
- [ ] Public functions/classes have **docstrings** with inputs/outputs, pre/post-conditions, and failure modes
  - ⚠️ Docstrings exist but lack failure modes and edge cases
  - ❌ No docstrings for module-level constants
- [x] **Type hints** are complete and precise (no `Any` in domain logic; use `Literal/NewType` where helpful)
  - ✅ All functions have type hints
  - ✅ AssetType uses Literal (good practice)
- [ ] **DTOs** are **frozen/immutable** and validated (e.g., Pydantic v2 models with constrained types)
  - ❌ KNOWN_ETFS and KNOWN_CRYPTO are mutable sets
  - ❌ No validation on module-level constants
- [x] **Numerical correctness**: currency uses `Decimal`; floats use `math.isclose` or explicit tolerances; no `==`/`!=` on floats
  - ✅ N/A - No numerical operations
- [ ] **Error handling**: exceptions are narrow, typed (from `shared.errors`), logged with context, and never silently caught
  - ❌ No error handling at all
  - ❌ No input validation
  - ❌ Functions can crash with AttributeError
- [ ] **Idempotency**: handlers tolerate replays; side-effects are guarded by idempotency keys or checks
  - ❌ add_etf_symbol() is not idempotent (mutates global state)
  - ✅ Read operations are idempotent
- [x] **Determinism**: tests freeze time (`freezegun`), seed RNG; no hidden randomness in business logic
  - ✅ Fully deterministic (no randomness or time-based logic)
- [ ] **Security**: no secrets in code/logs; input validation at boundaries; no `eval`/`exec`/dynamic imports
  - ✅ No secrets
  - ❌ No input validation (accepts any string)
  - ✅ No eval/exec
- [ ] **Observability**: structured logging with `correlation_id`/`causation_id`; one log per state change; no spam in hot loops
  - ✅ N/A - Pure configuration, no logging needed
- [ ] **Testing**: public APIs have tests; property-based tests for maths; coverage ≥ 80% (≥ 90% for strategy/portfolio)
  - ❌ No tests exist for this module
  - ❌ 0% coverage
- [x] **Performance**: no hidden I/O in hot paths; vectorised Pandas ops; HTTP clients pooled with rate limits
  - ✅ Pure in-memory operations
  - ✅ O(1) set lookups
- [x] **Complexity**: cyclomatic ≤ 10, cognitive ≤ 15, functions ≤ 50 lines, params ≤ 5
  - ✅ Max complexity: 7 (classify_symbol)
  - ✅ All functions < 50 lines
  - ✅ All functions ≤ 1 parameter
- [x] **Module size**: ≤ 500 lines (soft), split if > 800
  - ✅ 144 lines (well within limits)
- [x] **Imports**: no `import *`; stdlib → third-party → local; no deep relative imports
  - ✅ Clean import structure
  - ✅ Only stdlib imports

### Compliance Summary

**Compliant**: 9/16 (56%)
**Non-Compliant**: 7/16 (44%)

### Contract Analysis

#### Symbol Classification Contract

**Expected behavior:**
```python
classify_symbol("AAPL")   → "STOCK"
classify_symbol("SPY")    → "ETF"
classify_symbol("BTCUSD") → "CRYPTO"
classify_symbol("")       → Should raise ValueError (currently returns "STOCK")
classify_symbol("   ")    → Should raise ValueError (currently returns "STOCK")
classify_symbol(None)     → Should raise TypeError (currently crashes)
```

**Gap**: No contract enforcement for invalid inputs.

#### Symbol Universe Contract

**Expected immutability:**
```python
# Should be immutable
etfs = get_etf_symbols()
etfs.add("NEW_ETF")  # Should not affect KNOWN_ETFS

# But this modifies global state:
add_etf_symbol("NEW_ETF")  # ❌ Violates immutability
```

**Gap**: Mutable global state violates financial system best practices.

---

## 5) Additional Notes

### Strengths

1. **Simple and focused**: Module has clear single responsibility
2. **Efficient data structures**: Sets provide O(1) lookups
3. **Good module header**: Follows project standards
4. **Low complexity**: Easy to understand and maintain
5. **Defensive copying**: `get_etf_symbols()` and `get_symbol_universe()` return copies

### Critical Weaknesses

1. **Mutable global state**: Biggest issue - violates thread-safety and immutability
2. **No validation**: Accepts any string input without checks
3. **Inconsistent with Symbol value object**: Two different validation approaches in same system
4. **No tests**: 0% coverage is unacceptable per Copilot Instructions
5. **Naive classification**: Option/future detection is unreliable

### Immediate Action Items (Must Fix)

1. **Convert sets to frozensets** (Critical - thread-safety)
2. **Add input validation** (High - correctness)
3. **Create comprehensive tests** (High - required per guidelines)
4. **Use Symbol value object for validation** (High - consistency)
5. **Remove or deprecate add_etf_symbol()** (Medium - immutability)
6. **Document classification limitations** (Medium - transparency)

### Long-Term Recommendations

1. **Externalize configuration**: Load symbol universes from S3/DynamoDB
2. **Add versioning**: Track changes to symbol universes
3. **Improve classification**: Use proper regex or external API for option/future detection
4. **Add UNKNOWN asset type**: For ambiguous symbols
5. **Align with broker APIs**: Map AssetType to Alpaca's asset classes

### Actionable Remediation Plan

**Phase 1 - Critical (Complete within 1 day)**:

1. ✅ Convert mutable sets to frozensets:
   ```python
   KNOWN_ETFS: frozenset[str] = frozenset({
       "SPY", "QQQ", ...
   })
   ```

2. ✅ Remove or deprecate `add_etf_symbol()`:
   ```python
   def add_etf_symbol(symbol: str) -> None:
       raise NotImplementedError(
           "Runtime symbol addition is not supported in production. "
           "Load configuration from external source instead."
       )
   ```

3. ✅ Add input validation using Symbol value object:
   ```python
   from ..value_objects.symbol import Symbol
   
   def classify_symbol(symbol: str) -> AssetType:
       """Classify a trading symbol into its asset type.
       
       Args:
           symbol: Trading symbol to classify
       
       Returns:
           Asset type classification
       
       Raises:
           ValueError: If symbol is invalid (empty, contains spaces, invalid chars)
       
       Examples:
           >>> classify_symbol("AAPL")
           'STOCK'
           >>> classify_symbol("SPY")
           'ETF'
           >>> classify_symbol("BTCUSD")
           'CRYPTO'
           >>> classify_symbol("")
           ValueError: Symbol must not be empty
       """
       # Validate using Symbol value object
       validated = Symbol(symbol)
       symbol_upper = validated.value  # Already normalized and validated
       
       # Rest of classification logic...
   ```

**Phase 2 - High Priority (Complete within 1 sprint)**:

4. ✅ Create comprehensive test suite (`tests/shared/config/test_symbols_config.py`):
   ```python
   import pytest
   from hypothesis import given, strategies as st
   from the_alchemiser.shared.config.symbols_config import (
       classify_symbol, is_etf, get_etf_symbols, get_symbol_universe
   )
   
   class TestClassifySymbol:
       def test_classify_known_etf(self):
           assert classify_symbol("SPY") == "ETF"
       
       def test_classify_stock_default(self):
           assert classify_symbol("AAPL") == "STOCK"
       
       def test_classify_crypto(self):
           assert classify_symbol("BTCUSD") == "CRYPTO"
       
       def test_classify_empty_raises_error(self):
           with pytest.raises(ValueError):
               classify_symbol("")
       
       @given(st.text(min_size=1, max_size=10))
       def test_classify_always_returns_valid_type(self, symbol):
           try:
               result = classify_symbol(symbol)
               assert result in ["STOCK", "ETF", "CRYPTO", "OPTION", "FUTURE"]
           except ValueError:
               pass  # Invalid symbols should raise ValueError
   ```

5. ✅ Document classification limitations in docstrings
6. ✅ Add docstrings for module-level constants

**Phase 3 - Medium Priority (Complete within 2 sprints)**:

7. ✅ Externalize configuration (load from S3/DynamoDB)
8. ✅ Add schema versioning for configuration
9. ✅ Improve option/future detection or remove it
10. ✅ Add "UNKNOWN" asset type for ambiguous symbols

---

## 6) Testing Recommendations

### Unit Tests Needed

1. **Test classify_symbol()**:
   - Known ETFs return "ETF"
   - Known crypto returns "CRYPTO"
   - Unknown symbols return "STOCK"
   - Empty string raises ValueError
   - Whitespace-only raises ValueError
   - Invalid characters raise ValueError
   - Case insensitivity (lowercase → uppercase)

2. **Test is_etf()**:
   - Known ETFs return True
   - Non-ETFs return False
   - Empty string raises ValueError
   - Case insensitivity

3. **Test get_etf_symbols()**:
   - Returns set of ETFs
   - Returns copy (not reference)
   - Contains expected symbols

4. **Test get_symbol_universe()**:
   - Returns dict with ETF and CRYPTO keys
   - Returns copies of sets
   - Each set contains expected symbols

5. **Test add_etf_symbol()** (if not removed):
   - Raises NotImplementedError in production
   - Or add test if kept for development

### Property-Based Tests (Hypothesis)

1. **Symbol validation properties**:
   ```python
   @given(st.text(alphabet=string.ascii_letters + string.digits + ".-", min_size=1, max_size=10))
   def test_valid_symbols_classified(self, symbol):
       result = classify_symbol(symbol)
       assert result in ["STOCK", "ETF", "CRYPTO", "OPTION", "FUTURE"]
   ```

2. **Idempotency property**:
   ```python
   @given(st.text())
   def test_classify_idempotent(self, symbol):
       try:
           result1 = classify_symbol(symbol)
           result2 = classify_symbol(symbol)
           assert result1 == result2
       except ValueError:
           pass
   ```

### Integration Tests

1. **Test with Symbol value object**:
   ```python
   def test_classify_symbol_accepts_symbol_value_object():
       sym = Symbol("AAPL")
       result = classify_symbol(str(sym))
       assert result == "STOCK"
   ```

2. **Test with real broker symbols**:
   - Test against Alpaca's supported symbols
   - Verify classifications match broker's asset classes

---

## 7) References

- Copilot Instructions: `.github/copilot-instructions.md`
- Symbol value object: `the_alchemiser/shared/value_objects/symbol.py`
- Symbol tests: `tests/shared/value_objects/test_symbol.py`
- Asset info review: `docs/file_reviews/FILE_REVIEW_asset_info_2025_10_09.md`
- Technical indicator review: `docs/file_reviews/AUDIT_COMPLETION_technical_indicator.md`

---

**Review completed**: 2025-10-10  
**Reviewer**: GitHub Copilot Agent  
**Total findings**: 15 (1 Critical, 3 High, 4 Medium, 3 Low, 4 Info)  
**Compliance score**: 56% (9/16 checklist items)
