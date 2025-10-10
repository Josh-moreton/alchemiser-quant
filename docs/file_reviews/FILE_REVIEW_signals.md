# [File Review] Financial-grade, line-by-line audit

> Purpose: Conduct a rigorous, line-by-line review of a single Python file in the trading system, to institution-grade standards (correctness, controls, auditability, and safety). One issue per file.

---

## 0) Metadata

**File path**: `the_alchemiser/shared/notifications/templates/signals.py`

**Commit SHA / Tag**: `802cf268358e3299fb6b80a4b7cf3d4bda2994f4`

**Reviewer(s)**: GitHub Copilot (AI Agent)

**Date**: 2025-01-10

**Business function / Module**: shared / notifications / templates

**Runtime context**: Invoked by email notification system when building HTML content for trading signals, strategy analysis, and technical indicators. Non-critical path (notifications only).

**Criticality**: P3 (Low-Medium) - Email template generation is not in critical trading path, but incorrect data presentation could mislead users

**Direct dependencies (imports)**:
```
Internal: .base (BaseEmailTemplate)
External: typing.Any (stdlib)
```

**External services touched**:
```
None - Pure HTML generation utility (outputs consumed by email service)
```

**Interfaces (DTOs/events) produced/consumed**:
```
Consumed: Strategy signals dictionaries, technical indicators, signal objects
Produced: HTML strings for email templates
No formal DTOs/events - works with untyped dictionaries
```

**Related docs/specs**:
- [Copilot Instructions](.github/copilot-instructions.md)
- [BaseEmailTemplate](the_alchemiser/shared/notifications/templates/base.py)
- Module header indicates: Business Unit: utilities | Status: current

---

## 1) Scope & Objectives

- Verify the file's **single responsibility** and alignment with intended business capability.
- Ensure **correctness**, **numerical integrity**, **deterministic behaviour** where required.
- Validate **error handling**, **idempotency**, **observability**, **security**, and **compliance** controls.
- Confirm **interfaces/contracts** (DTOs/events) are accurate, versioned, and tested.
- Identify **dead code**, **complexity hotspots**, and **performance risks**.

---

## 2) Summary of Findings (use severity labels)

### Critical

**C1. Pervasive use of `Any` type violates strict typing policy**
- Lines 11, 39, 70, 101, 156, 229: `dict[Any, Any]` and `Any` used throughout
- **Violation**: Copilot instructions: "No `Any` in domain logic. DTOs are frozen."
- **Impact**: Type safety is completely bypassed; mypy cannot catch errors
- **Evidence**: `strategy_signals: dict[Any, Any]`, `signal: Any`, `indicators: dict[str, Any]`

**C2. Silent exception handling violates error policy**
- Line 93: `except Exception:` catches all exceptions without logging or re-raising
- **Violation**: Copilot instructions: "never silently caught"
- **Impact**: Errors in signal processing are hidden; users see generic error message
- **Risk**: Data corruption or bugs in signal objects won't be detected

### High

**H1. Missing structured logging for observability**
- No logging statements anywhere in the module (398 lines)
- **Violation**: Copilot instructions require "structured logging with correlation_id/causation_id"
- **Impact**: Cannot trace HTML generation issues, signal processing errors, or data anomalies
- **Risk**: Debugging production issues impossible

**H2. Missing custom typed exceptions**
- No use of exceptions from `shared.errors`
- Line 93: Returns error HTML silently instead of raising typed exception
- **Violation**: Copilot instructions require "typed (from shared.errors), logged with context"
- **Impact**: Error handling is inconsistent; callers cannot catch specific errors

**H3. Float comparisons without tolerance**
- Lines 25-28: Direct comparison `rsi_value > 80`, `rsi_value > 70`
- Lines 34-36: Direct comparison `current_price > ma_200`
- Lines 251-258: Direct comparison `current_price > ma_200`
- Lines 262-270: Direct comparison `rsi_10 > 80`, `rsi_10 < 20`
- **Violation**: Copilot instructions: "no `==`/`!=` on floats; use `math.isclose` or explicit tolerances"
- **Note**: While these are `>` comparisons (not `==`), financial data should use explicit thresholds
- **Risk**: Borderline cases (80.0000001 vs 79.9999999) treated differently due to floating point precision

**H4. Missing docstrings on public methods**
- Lines 23-29: `_get_rsi_color` missing docstring
- Lines 32-36: `_get_price_vs_ma_info` missing docstring  
- Lines 39-67: `_format_indicator_row` missing docstring
- **Violation**: Copilot instructions: "docstrings on all public APIs"
- **Impact**: Intent and contract unclear; inputs/outputs/preconditions not documented

### Medium

**M1. No test coverage**
- No test file exists for `signals.py`
- **Violation**: Copilot instructions: "Every public function/class has at least one test"
- **Impact**: No validation that HTML generation is correct; regressions will go undetected

**M2. Function complexity concerns**
- Line 155-226: `build_detailed_strategy_signals` is 72 lines (exceeds 50 line limit)
- Line 313-397: `build_strategy_signals_neutral` is 85 lines (exceeds 50 line limit)
- **Violation**: Copilot instructions: "functions ≤ 50 lines"
- **Impact**: Hard to understand, test, and maintain

**M3. Magic string constants not defined**
- Lines 177-188, 339-347: Action color mappings repeated
- Hard-coded color values scattered throughout
- **Impact**: Inconsistent styling if colors need to change; no single source of truth

**M4. String truncation without business rationale**
- Line 191: `reason[:300]` - why 300?
- Line 350: `reason[:100]` - why 100? Different from above
- **Impact**: Inconsistent user experience; no documented business rule

**M5. Missing input validation**
- No validation that dictionaries contain expected keys
- No validation of data types in dictionaries
- Relies on `.get()` with defaults but no validation of values
- **Impact**: Could produce misleading HTML if data format changes

**M6. Inconsistent strategy name handling**
- Lines 113, 165: `str(strategy_type).replace(_STRATEGY_TYPE_PREFIX, "")`
- Lines 328-336: Complex logic to handle both enum and string
- **Impact**: Fragile code; assumptions about string format could break

### Low

**L1. Unused noqa comment**
- Line 70: `# noqa: ANN401` to suppress `Any` warning
- **Impact**: Acknowledges violation but doesn't fix it

**L2. Inconsistent return value for empty data**
- Line 81: Returns `""` when signal is falsy
- Line 104: Returns `BaseEmailTemplate.create_alert_box(...)`
- Line 232: Returns `""`
- **Impact**: Callers need to handle different empty states

**L3. Module size approaching limit**
- 398 lines (soft limit is 500)
- **Status**: Within limits but growing
- **Recommendation**: Consider splitting into multiple builders

### Info/Nits

**I1. Business unit classification**
- Line 1: Module marked as "Business Unit: utilities"
- **Question**: Should this be "shared" or "notifications"?
- **Impact**: None - informational only

**I2. Constant naming**
- Line 16: `_STRATEGY_TYPE_PREFIX` uses underscore prefix (private)
- **Observation**: Consistent with Python convention for module-level private constants

**I3. HTML string formatting**
- Uses f-strings for HTML generation (appropriate)
- Long multi-line HTML strings are readable but verbose
- **Observation**: Current approach is acceptable for template generation

---

## 3) Line-by-Line Notes

### Detailed Line-by-Line Analysis

| Line(s) | Issue / Observation | Severity | Evidence / Excerpt | Proposed Action | Status |
|---------|---------------------|----------|-------------------|-----------------|--------|
| 1-7 | Module header and docstring | ✅ Good | Includes required "Business Unit: utilities; Status: current" | Consider updating to "shared" | Pass |
| 9 | Future annotations import | ✅ Good | Enables PEP 563 postponed evaluation | None | Pass |
| 11 | **Use of `Any` type** | ❌ Critical | `from typing import Any` | Replace with specific types | Fix |
| 13 | Base template import | ✅ Good | Relative import from `.base` | None | Pass |
| 16 | Private constant | ✅ Good | `_STRATEGY_TYPE_PREFIX = "StrategyType."` | None | Pass |
| 19-20 | Class definition | ✅ Good | Clear class name and docstring | Expand docstring | Pass |
| 23-29 | `_get_rsi_color` | ⚠️ High | Missing docstring; float comparison | Add docstring; document thresholds | Fix |
| 25, 27 | Float comparison | ⚠️ High | `if rsi_value > 80:`, `if rsi_value > 70:` | Use explicit constants | Fix |
| 32-36 | `_get_price_vs_ma_info` | ⚠️ High | Missing docstring; float comparison | Add docstring | Fix |
| 34 | Float comparison | ⚠️ High | `if current_price > ma_200:` | Document threshold semantics | Fix |
| 39-67 | `_format_indicator_row` | ⚠️ High | Missing docstring; uses `dict[str, Any]` | Add docstring; type dict values | Fix |
| 41-44 | Default values | ⚠️ Medium | `.get("rsi_10", 0)` returns 0 if missing | Could produce misleading display (0 is valid RSI) | Consider |
| 55, 58, 61 | f-string formatting | ✅ Good | `{rsi_10:.1f}`, `{current_price:.2f}` | None | Pass |
| 70 | **`Any` type with noqa** | ❌ Critical | `signal: Any) -> str:  # noqa: ANN401` | Replace with Union type or Protocol | Fix |
| 71-79 | Docstring | ⚠️ Medium | Basic docstring; missing failure modes | Add preconditions, error cases | Fix |
| 80-81 | Early return | ✅ Good | Returns `""` for falsy signal | None | Pass |
| 83-92 | Try block | ✅ Good | Generates HTML with f-string | None | Pass |
| 88-89 | Hasattr check | ⚠️ Low | `hasattr(signal, "reason")` - duck typing | Could use Protocol or explicit type | Consider |
| 93-98 | **Silent exception** | ❌ Critical | `except Exception:` with no logging | Add logging; raise typed error | Fix |
| 101-152 | `build_technical_indicators` | ⚠️ High | Uses `dict[Any, Any]`; no logging | Type properly; add logging | Fix |
| 103-104 | Empty check | ✅ Good | Returns alert box for empty data | None | Pass |
| 108-119 | Loop and filter | ✅ Good | Checks `technical_indicators` exists | None | Pass |
| 116-119 | Comprehension | ✅ Good | Clean comprehension with helper method | None | Pass |
| 155-226 | `build_detailed_strategy_signals` | ⚠️ Medium | 72 lines (exceeds 50 limit); uses `dict[Any, Any]` | Extract helper; type properly | Fix |
| 156 | **`Any` type** | ❌ Critical | `strategy_signals: dict[Any, Any]` | Type with specific structure | Fix |
| 164-174 | Data extraction | ⚠️ Medium | Multiple `.get()` calls with defaults | Could validate data schema | Consider |
| 177-188 | Color mapping | ⚠️ Medium | Repeated if/elif logic | Extract to constant dict or function | Refactor |
| 191-192 | String truncation | ⚠️ Medium | `reason[:300]` - magic number | Define constant with rationale | Fix |
| 204 | f-string formatting | ✅ Good | `{allocation:.1%}` percentage format | None | Pass |
| 229-310 | `build_market_regime_analysis` | ✅ Good | Reasonable size (82 lines) | Could still extract helper | Consider |
| 251-258 | Float comparison | ⚠️ High | `if current_price > ma_200:` for regime | Document threshold semantics | Fix |
| 262-270 | Float comparison | ⚠️ High | `if rsi_10 > 80:`, `elif rsi_10 < 20:` | Document threshold semantics | Fix |
| 285, 291, 297, 303 | f-string formatting | ✅ Good | `{current_price:.2f}`, `{rsi_10:.1f}` | None | Pass |
| 313-397 | `build_strategy_signals_neutral` | ⚠️ Medium | 85 lines (exceeds 50 limit); complex logic | Extract helpers; type properly | Fix |
| 314-316 | Empty check | ✅ Good | Returns `""` for empty data | None | Pass |
| 320-322 | Type check | ⚠️ Medium | `if not isinstance(signal_data, dict):` | Could use TypeGuard | Consider |
| 328-336 | Strategy name handling | ⚠️ Medium | Complex enum vs string logic | Define clear interface | Refactor |
| 329-331 | Hasattr check | ⚠️ Low | `if hasattr(strategy_name, "name"):` | Could use isinstance check | Consider |
| 339-347 | Color mapping | ⚠️ Medium | Duplicate of lines 177-188 | Extract to shared constant | Fix |
| 350 | String truncation | ⚠️ Medium | `reason[:100]` - different from line 191 | Unify or document difference | Fix |
| 397 | Delegation | ✅ Good | Uses `BaseEmailTemplate.create_section` | None | Pass |

---

## 4) Correctness & Contracts

### Correctness Checklist

- [x] The file has a **clear purpose** and does not mix unrelated concerns (SRP)
  - ✅ Focused solely on building HTML content for signal-related emails
  
- [❌] Public functions/classes have **docstrings** with inputs/outputs, pre/post-conditions, and failure modes
  - ❌ Multiple private methods missing docstrings (lines 23, 32, 39)
  - ⚠️ Existing docstrings lack preconditions, postconditions, failure modes
  
- [❌] **Type hints** are complete and precise (no `Any` in domain logic; use `Literal/NewType` where helpful)
  - ❌ **MAJOR VIOLATION**: `Any` used extensively (lines 11, 39, 70, 101, 156, 229)
  - ❌ Dictionary values untyped: `dict[str, Any]`
  
- [N/A] **DTOs** are **frozen/immutable** and validated (e.g., Pydantic v2 models with constrained types)
  - N/A - This module produces HTML, doesn't define DTOs
  - ⚠️ **ISSUE**: Consumes untyped dictionaries instead of proper DTOs
  
- [⚠️] **Numerical correctness**: currency uses `Decimal`; floats use `math.isclose` or explicit tolerances; no `==`/`!=` on floats
  - ⚠️ **VIOLATION**: Float comparisons without tolerance (lines 25-28, 34-36, 251-258, 262-270)
  - ⚠️ No `Decimal` usage, but prices displayed as floats in HTML (acceptable for display)
  - Note: These are display-only; not used for calculations
  
- [❌] **Error handling**: exceptions are narrow, typed (from `shared.errors`), logged with context, and never silently caught
  - ❌ **MAJOR VIOLATION**: Line 93 silently catches `Exception`
  - ❌ No typed exceptions from `shared.errors`
  - ❌ No logging of errors
  
- [N/A] **Idempotency**: handlers tolerate replays; side-effects are guarded by idempotency keys or checks
  - ✅ Pure functions; no side effects; inherently idempotent
  
- [N/A] **Determinism**: tests freeze time (`freezegun`), seed RNG; no hidden randomness in business logic
  - ✅ No randomness in this module
  
- [✅] **Security**: no secrets in code/logs; input validation at boundaries; no `eval`/`exec`/dynamic imports
  - ✅ No secrets, eval, or dynamic imports
  - ⚠️ **ISSUE**: Minimal input validation; trusts caller data
  
- [❌] **Observability**: structured logging with `correlation_id`/`causation_id`; one log per state change; no spam in hot loops
  - ❌ **MAJOR VIOLATION**: No logging anywhere in 398 lines
  - ❌ No correlation_id propagation
  
- [❌] **Testing**: public APIs have tests; property-based tests for maths; coverage ≥ 80% (≥ 90% for strategy/portfolio)
  - ❌ **MAJOR VIOLATION**: No test file for this module
  - ❌ Zero test coverage
  
- [N/A] **Performance**: no hidden I/O in hot paths; vectorised Pandas ops; HTTP clients pooled with rate limits
  - ✅ No I/O; pure string generation
  - ✅ No performance concerns for this use case
  
- [⚠️] **Complexity**: cyclomatic ≤ 10, cognitive ≤ 15, functions ≤ 50 lines, params ≤ 5
  - ⚠️ **VIOLATION**: Two functions exceed 50 lines (72 and 85 lines)
  - ✅ Complexity appears reasonable (many if/else but straightforward)
  - ✅ Parameter counts ≤ 5
  
- [✅] **Module size**: ≤ 500 lines (soft), split if > 800
  - ✅ 398 lines (within limits)
  
- [✅] **Imports**: no `import *`; stdlib → third-party → local; no deep relative imports
  - ✅ Clean import structure
  - ✅ Proper ordering

---

## 5) Additional Notes

### Architectural Observations

**Positive Aspects:**
1. Single responsibility: focused on HTML generation for signals
2. Good use of helper methods to break down complexity
3. Clean separation from BaseEmailTemplate
4. No external dependencies (beyond standard library and base template)
5. Consistent HTML structure and styling approach

**Areas for Improvement:**
1. Should define proper DTOs for signal data instead of using untyped dicts
2. Error handling needs complete overhaul
3. Observability (logging) completely missing
4. Type safety needs dramatic improvement
5. Test coverage is non-existent

### Recommended Remediations (Priority Order)

#### 1. Replace `Any` with specific types (CRITICAL)

```python
from typing import TypedDict, Literal, Protocol

class TechnicalIndicators(TypedDict, total=False):
    """Technical indicator data structure."""
    rsi_10: float
    rsi_20: float
    current_price: float
    ma_200: float

class SignalData(TypedDict, total=False):
    """Signal data structure."""
    action: Literal["BUY", "SELL", "HOLD", "UNKNOWN"]
    symbol: str
    reason: str
    timestamp: str
    technical_indicators: dict[str, TechnicalIndicators]

# Update function signatures
@staticmethod
def build_technical_indicators(
    strategy_signals: dict[str, SignalData]
) -> str:
    """Build technical indicators HTML section."""
```

#### 2. Add structured logging (HIGH)

```python
from the_alchemiser.shared.logging import get_logger

logger = get_logger(__name__)

@staticmethod
def build_signal_information(signal: Signal) -> str:
    """Build HTML for signal information section."""
    if not signal:
        logger.debug("build_signal_information_skipped", reason="no_signal")
        return ""
    
    try:
        logger.debug(
            "building_signal_information",
            action=signal.action,
            symbol=signal.symbol,
        )
        # ... generate HTML ...
        return html
    except Exception as e:
        logger.error(
            "signal_information_build_failed",
            error=str(e),
            signal_action=getattr(signal, "action", None),
            signal_symbol=getattr(signal, "symbol", None),
            module="signals",
        )
        raise TemplateGenerationError(
            f"Failed to build signal information: {e}",
            context={"signal": signal},
        ) from e
```

#### 3. Replace silent exception with typed error (CRITICAL)

```python
from the_alchemiser.shared.errors import AlchemiserError

class TemplateGenerationError(AlchemiserError):
    """Raised when email template generation fails."""
    pass

# In build_signal_information:
except Exception as e:
    logger.error(
        "signal_information_generation_failed",
        error=str(e),
        signal_type=type(signal).__name__,
    )
    raise TemplateGenerationError(
        f"Failed to generate signal information HTML: {e}"
    ) from e
```

#### 4. Document RSI thresholds and extract constants (HIGH)

```python
# Module-level constants
RSI_OVERBOUGHT_CRITICAL = 80.0
RSI_OVERBOUGHT_WARNING = 70.0
RSI_OVERSOLD = 20.0

@staticmethod
def _get_rsi_color(rsi_value: float) -> str:
    """Get color for RSI value based on overbought/oversold thresholds.
    
    Args:
        rsi_value: RSI indicator value (0-100)
        
    Returns:
        Hex color code for the RSI value
        
    Note:
        Thresholds:
        - Above 80: Overbought (critical) - Red
        - 70-80: Overbought (warning) - Orange  
        - Below 70: Normal range - Green
    """
    if rsi_value > RSI_OVERBOUGHT_CRITICAL:
        return "#EF4444"  # Red - Overbought
    if rsi_value > RSI_OVERBOUGHT_WARNING:
        return "#F59E0B"  # Orange - Warning
    return "#10B981"  # Green - Normal
```

#### 5. Extract color mappings to constants (MEDIUM)

```python
# Module-level constants
ACTION_COLORS = {
    "BUY": {
        "text": "#10B981",
        "background": "#D1FAE5",
        "label": "BUY",
    },
    "SELL": {
        "text": "#EF4444",
        "background": "#FEE2E2",
        "label": "SELL",
    },
    "HOLD": {
        "text": "#6B7280",
        "background": "#F3F4F6",
        "label": "HOLD",
    },
}

# Usage:
colors = ACTION_COLORS.get(action, ACTION_COLORS["HOLD"])
action_color = colors["text"]
action_bg = colors["background"]
action_label = colors["label"]
```

#### 6. Unify string truncation logic (MEDIUM)

```python
# Module-level constants
MAX_REASON_LENGTH_DETAILED = 300  # For detailed signal view
MAX_REASON_LENGTH_SUMMARY = 100   # For summary table view

def _truncate_reason(reason: str, max_length: int) -> str:
    """Truncate reason string to maximum length.
    
    Args:
        reason: The reason text to truncate
        max_length: Maximum length before truncation
        
    Returns:
        Truncated string with ellipsis if longer than max_length
    """
    if len(reason) > max_length:
        return reason[:max_length] + "..."
    return reason
```

#### 7. Add comprehensive tests (HIGH)

```python
# tests/shared/notifications/templates/test_signals.py
import pytest
from the_alchemiser.shared.notifications.templates.signals import SignalsBuilder

def test_get_rsi_color_overbought_critical():
    """Test RSI color for critical overbought (>80)."""
    assert SignalsBuilder._get_rsi_color(85.0) == "#EF4444"

def test_get_rsi_color_overbought_warning():
    """Test RSI color for warning overbought (70-80)."""
    assert SignalsBuilder._get_rsi_color(75.0) == "#F59E0B"

def test_get_rsi_color_normal():
    """Test RSI color for normal range (<70)."""
    assert SignalsBuilder._get_rsi_color(50.0) == "#10B981"

def test_build_signal_information_empty():
    """Test signal information with None signal."""
    result = SignalsBuilder.build_signal_information(None)
    assert result == ""

def test_build_signal_information_with_reason():
    """Test signal information with complete signal data."""
    # Create mock signal object
    signal = type('Signal', (), {
        'action': 'BUY',
        'symbol': 'SPY',
        'reason': 'Strong uptrend'
    })()
    
    result = SignalsBuilder.build_signal_information(signal)
    assert 'BUY SPY' in result
    assert 'Strong uptrend' in result

def test_build_technical_indicators_empty():
    """Test technical indicators with empty dict."""
    result = SignalsBuilder.build_technical_indicators({})
    assert 'No technical indicators available' in result

# Add property-based tests with Hypothesis
from hypothesis import given, strategies as st

@given(
    rsi=st.floats(min_value=0.0, max_value=100.0),
)
def test_get_rsi_color_always_returns_valid_color(rsi):
    """Property: RSI color should always return a valid hex color."""
    color = SignalsBuilder._get_rsi_color(rsi)
    assert color.startswith("#")
    assert len(color) == 7
```

### Security Considerations

1. **HTML injection risk**: Currently uses f-strings with user data
   - **Mitigation**: All data should be HTML-escaped before insertion
   - **Note**: Python's `html.escape()` should be used for user-provided content

2. **Data validation**: No validation of input dictionaries
   - **Mitigation**: Define TypedDicts or Pydantic models for all inputs
   - **Impact**: Could lead to confusing error messages or silent failures

### Performance Considerations

1. String concatenation in loops (lines 116-119, 352-369)
   - **Current**: Uses list + join pattern (efficient)
   - **Status**: No performance concerns for email generation

2. Multiple passes over data
   - **Observation**: Some data accessed multiple times
   - **Impact**: Negligible for email generation use case

### Migration Path

**Phase 1 (Critical):**
1. Add TemplateGenerationError to shared.errors.exceptions
2. Replace `except Exception` with proper error handling and logging
3. Replace all `Any` types with TypedDicts or Protocols
4. Add structured logging to all public methods

**Phase 2 (High):**
5. Add comprehensive test suite (target >90% coverage)
6. Extract magic numbers to named constants
7. Add docstrings to all methods with preconditions/postconditions
8. Unify color mappings and string truncation logic

**Phase 3 (Medium):**
9. Extract helper functions from long methods (>50 lines)
10. Consider splitting into multiple builder classes if grows further
11. Add HTML escaping for user-provided content

### Version Management

Per Copilot instructions, code changes require version bump:
- **Recommended**: `make bump-minor` (new error handling, logging, types are enhancements)
- If only documentation: `make bump-patch`

---

**Review completed**: 2025-01-10  
**Reviewer**: GitHub Copilot (AI Agent)  
**Status**: Ready for remediation
