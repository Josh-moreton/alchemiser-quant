# Validation Utils - Implementation Checklist for Fixes

**File**: `the_alchemiser/shared/utils/validation_utils.py`  
**Review**: See `FILE_REVIEW_validation_utils.md` for full details

---

## Priority 1: Float Comparison Fixes (HIGH SEVERITY - Must Fix)

### Fix 1: `validate_spread_reasonable` (Lines 159-177)

**Current Issue**: Raw float division and comparison without tolerance

#### Implementation Steps:

- [ ] **Step 1.1**: Import `math` module at top of file
  ```python
  import math
  from datetime import UTC, datetime
  from decimal import Decimal
  ```

- [ ] **Step 1.2**: Update `validate_spread_reasonable` function
  ```python
  def validate_spread_reasonable(
      bid_price: float, ask_price: float, max_spread_percent: float = 0.5
  ) -> bool:
      """Validate that the bid-ask spread is reasonable for trading.
      
      Uses math.isclose for float comparison with explicit tolerance per
      financial-grade guardrails.
      
      Args:
          bid_price: Bid price
          ask_price: Ask price
          max_spread_percent: Maximum allowed spread as percentage (default 0.5%)
      
      Returns:
          True if spread is reasonable
      
      """
      if bid_price <= 0 or ask_price <= 0:
          return False
      
      spread_ratio = (ask_price - bid_price) / ask_price
      max_ratio = max_spread_percent / 100.0
      
      # Use math.isclose with explicit tolerance for float comparison
      # Spread is reasonable if strictly less than max or within tolerance of max
      return spread_ratio < max_ratio or math.isclose(
          spread_ratio, max_ratio, rel_tol=1e-9, abs_tol=1e-9
      )
  ```

- [ ] **Step 1.3**: Update test cases if needed
  - Review `tests/shared/utils/test_validation_utils_comprehensive.py`
  - Add edge case tests for boundary values
  - Test: `validate_spread_reasonable(100.0, 100.5, 0.5)` should return True
  - Test: `validate_spread_reasonable(100.0, 100.50000001, 0.5)` should handle tolerance

- [ ] **Step 1.4**: Run tests
  ```bash
  make test-unit
  # or
  poetry run pytest tests/shared/utils/test_validation_utils_comprehensive.py::TestValidateSpreadReasonable -v
  ```

---

### Fix 2: `detect_suspicious_quote_prices` (Lines 214-217)

**Current Issue**: Raw float arithmetic for percentage calculation

#### Implementation Steps:

- [ ] **Step 2.1**: Update spread percentage calculation in `detect_suspicious_quote_prices`
  ```python
  # Check for excessive spread (may indicate stale/bad data)
  if bid_price > 0 and ask_price > 0:
      spread_ratio = (ask_price - bid_price) / ask_price
      spread_percent = spread_ratio * 100
      max_percent = max_spread_percent
      
      # Use math.isclose for comparison with tolerance
      if spread_percent > max_percent and not math.isclose(
          spread_percent, max_percent, rel_tol=1e-9, abs_tol=1e-9
      ):
          reasons.append(f"excessive spread: {spread_percent:.2f}% > {max_spread_percent}%")
  ```

- [ ] **Step 2.2**: Update test cases
  - Review `tests/execution_v2/test_validation_utils.py`
  - Review `tests/shared/utils/test_validation_utils_comprehensive.py`
  - Add edge case tests for boundary spread percentages

- [ ] **Step 2.3**: Run tests
  ```bash
  poetry run pytest tests/execution_v2/test_validation_utils.py -v
  poetry run pytest tests/shared/utils/test_validation_utils_comprehensive.py::TestDetectSuspiciousQuotePrices -v
  ```

---

## Priority 2: Observability & Type Handling (MEDIUM SEVERITY - Should Fix)

### Enhancement 1: Add Structured Logging

- [ ] **Step 3.1**: Add logging to validation failures (example for one function)
  ```python
  def validate_decimal_range(
      value: Decimal,
      min_value: Decimal,
      max_value: Decimal,
      field_name: str = "Value",
  ) -> None:
      """Validate that a Decimal value is within the specified range [min_value, max_value]."""
      if not (min_value <= value <= max_value):
          logger.warning(
              "Validation failed: decimal_range",
              extra={
                  "field_name": field_name,
                  "value": str(value),
                  "min_value": str(min_value),
                  "max_value": str(max_value),
                  "validation_type": "decimal_range",
              }
          )
          raise ValueError(f"{field_name} must be between {min_value} and {max_value}")
  ```

- [ ] **Step 3.2**: Apply logging pattern to other validation functions
  - `validate_enum_value`
  - `validate_non_negative_integer`
  - `validate_order_limit_price`
  - `validate_price_positive`

- [ ] **Step 3.3**: Verify logging output in tests
  - Use `caplog` fixture in pytest to verify log messages
  - Ensure no PII or sensitive data is logged

### Enhancement 2: Document Float vs Decimal Policy

- [ ] **Step 4.1**: Add module-level docstring section
  ```python
  """Business Unit: shared | Status: current.
  
  Centralized validation utilities for eliminating duplicate __post_init__() methods.
  
  This module consolidates common validation patterns found across schema classes
  to eliminate the duplicate __post_init__() methods identified in Priority 2.1.
  
  Type Precision Policy:
  ----------------------
  - Use Decimal for: Money amounts, portfolio percentages, financial ratios
  - Use float for: Quote validation (detection heuristics), non-financial ratios
  - Float comparisons: Always use math.isclose() with explicit tolerances
  - Never use == or != on float values
  
  Validation vs Detection:
  ------------------------
  - Validation functions raise ValueError on contract violations
  - Detection functions return bool/tuple for advisory checks
  """
  ```

- [ ] **Step 4.2**: Update function docstrings with precision notes
  - Document precision guarantees where relevant
  - Note when float arithmetic is acceptable (detection only)

---

## Priority 3: Constants & Documentation (LOW SEVERITY - Nice to Have)

### Enhancement 3: Move Hard-coded Constants

- [ ] **Step 5.1**: Add constant to `the_alchemiser/shared/constants.py`
  ```python
  # Minimum price for trading (1 cent)
  MINIMUM_PRICE = Decimal("0.01")
  ```

- [ ] **Step 5.2**: Update `validate_price_positive` to use constant
  ```python
  from the_alchemiser.shared.constants import MINIMUM_PRICE
  
  def validate_price_positive(price: Decimal, field_name: str = "Price") -> None:
      """Validate that a price is positive and reasonable."""
      if price <= 0:
          raise ValueError(f"{field_name} must be positive, got {price}")
      if price < MINIMUM_PRICE:
          raise ValueError(f"{field_name} must be at least {MINIMUM_PRICE}, got {price}")
  ```

- [ ] **Step 5.3**: Export constant in constants `__all__`

### Enhancement 4: Improve Docstrings

- [ ] **Step 6.1**: Add examples to `validate_order_limit_price`
  ```python
  def validate_order_limit_price(
      order_type_value: str,
      limit_price: float | Decimal | int | None,
  ) -> None:
      """Validate order limit price constraints based on order type.
      
      Valid order types:
      - "market": Limit price must be None
      - "limit": Limit price is required
      
      Args:
          order_type_value: The order type ("market" or "limit")
          limit_price: The limit price (may be None)
      
      Raises:
          ValueError: If limit price constraints are violated
      
      Examples:
          >>> validate_order_limit_price("limit", 100.0)  # OK
          >>> validate_order_limit_price("market", None)  # OK
          >>> validate_order_limit_price("limit", None)   # Raises ValueError
          >>> validate_order_limit_price("market", 100.0) # Raises ValueError
      
      """
  ```

---

## Testing Checklist

### Unit Tests

- [ ] Run full test suite for validation_utils
  ```bash
  poetry run pytest tests/shared/utils/test_validation_utils_comprehensive.py -v
  ```

- [ ] Run execution tests that use validation functions
  ```bash
  poetry run pytest tests/execution_v2/test_validation_utils.py -v
  poetry run pytest tests/execution_v2/test_suspicious_quote_validation.py -v
  ```

- [ ] Run integration tests
  ```bash
  make test-integration
  ```

### Type Checking

- [ ] Run mypy type checker
  ```bash
  make type-check
  # or
  poetry run mypy the_alchemiser/shared/utils/validation_utils.py
  ```

### Linting & Formatting

- [ ] Run linters
  ```bash
  make lint
  ```

- [ ] Run formatter
  ```bash
  make format
  ```

---

## Version Management (MANDATORY)

- [ ] **Determine version bump type**:
  - **PATCH**: Bug fixes only (float comparison fixes) → `make bump-patch`
  - **MINOR**: If adding new features (logging, new functions) → `make bump-minor`
  - **MAJOR**: Breaking changes (signature changes) → `make bump-major`

- [ ] **Run version bump** (before committing code changes)
  ```bash
  make bump-patch  # Most likely for this fix
  ```

- [ ] **Verify version updated** in `pyproject.toml`

---

## Commit Strategy

### Commit 1: Float Comparison Fixes (P1)
```bash
git add the_alchemiser/shared/utils/validation_utils.py
git add tests/shared/utils/test_validation_utils_comprehensive.py
git commit -m "Fix float comparison violations in validation_utils

- Add math.isclose with explicit tolerance to validate_spread_reasonable
- Add math.isclose to detect_suspicious_quote_prices spread calculation
- Update tests for boundary cases
- Complies with guardrail: Never use ==/!= on floats

Fixes: #[issue-number]"
```

### Commit 2: Add Observability (P2)
```bash
git add the_alchemiser/shared/utils/validation_utils.py
git commit -m "Add structured logging to validation failures

- Log validation context before raising ValueError
- Include field names, values, and limits in structured logs
- No PII or sensitive data logged

Enhances: Observability and debugging"
```

### Commit 3: Documentation & Constants (P3)
```bash
git add the_alchemiser/shared/utils/validation_utils.py
git add the_alchemiser/shared/constants.py
git commit -m "Improve validation_utils documentation and constants

- Move MINIMUM_PRICE to shared constants
- Add type precision policy to module docstring
- Enhance docstrings with examples
- Document validation vs detection patterns"
```

---

## Validation Before PR Merge

- [ ] All tests pass
- [ ] Type checking passes
- [ ] Linting passes
- [ ] No regressions in dependent modules
- [ ] Version number bumped appropriately
- [ ] Documentation updated
- [ ] Review comments addressed

---

## Post-Merge Actions

- [ ] Close related issues
- [ ] Update `FILE_REVIEW_SUMMARY.md` if it exists
- [ ] Monitor production logs for validation patterns
- [ ] Consider adding property-based tests with Hypothesis (future enhancement)

---

**Created**: 2025-01-06  
**Based on**: `FILE_REVIEW_validation_utils.md`  
**Priority**: P1 fixes should be completed before next release
