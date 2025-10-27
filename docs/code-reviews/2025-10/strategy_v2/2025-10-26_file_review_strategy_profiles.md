# [File Review] Financial-grade, line-by-line audit

> Purpose: Conduct a rigorous, line-by-line review of a single Python file in the trading system, to institution-grade standards (correctness, controls, auditability, and safety). One issue per file.

---

## 0) Metadata

**File path**: `the_alchemiser/shared/config/strategy_profiles.py`

**Commit SHA / Tag**: `802cf268358e3299fb6b80a4b7cf3d4bda2994f4`

**Reviewer(s)**: Copilot Agent

**Date**: 2025-10-10

**Business function / Module**: shared/config

**Runtime context**: 
- Configuration constants loaded at import time (module-level constants)
- Used as fallback defaults when JSON config files fail to load
- No runtime I/O or external calls (pure constant definitions)
- Immutable after module load (constants never reassigned)
- Accessed by StrategySettings._get_stage_profile() in config.py

**Criticality**: P2 (Medium) - Fallback configuration for strategy allocation, but primary source is now JSON config files

**Direct dependencies (imports)**:
```python
Internal: None
External: 
  - __future__.annotations (stdlib, for type hint forward references)
```

**External services touched**:
```
None - Pure constant definitions with no I/O
```

**Interfaces (DTOs/events) produced/consumed**:
```
Produces: 
  - Module-level constants (STRATEGY_* strings, DEV_DSL_FILES, PROD_DSL_FILES, etc.)
  - Used as fallback by StrategySettings._get_stage_profile() in config.py

Consumed by:
  - the_alchemiser.shared.config.config.StrategySettings (imports and uses as fallback)
  
Schema version: N/A (constants, not DTOs)
```

**Related docs/specs**:
- [Copilot Instructions](/.github/copilot-instructions.md)
- [Config Module](/the_alchemiser/shared/config/config.py) - Primary consumer
- [JSON Config Files](/the_alchemiser/config/) - Primary source (this file is fallback)
- [Test Coverage](/tests/shared/config/test_config_package.py) - Indirect tests via JSON validation

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
None identified.

### High
None identified.

### Medium
1. **No allocation sum validation** - Lines 26-34, 43-48: Allocations should programmatically validate they sum to ~1.0 to catch human errors
2. **Missing comprehensive docstrings** - Lines 8-14, 16-24, 26-34, 36-48: Constants lack docstrings explaining purpose, constraints, and usage
3. **No dedicated test file** - No direct unit tests for the constants; only indirect testing through config.py tests

### Low
1. **Magic float comparisons** - Lines 27-33, 44-48: Float allocations use `==` comparisons implicitly; should document tolerance policy or use Decimal
2. **Inconsistency with JSON files** - Strategy names in constants vs JSON files use different formats (constants vs full filenames)
3. **Module-level comment style** - Line 5: Comment doesn't follow docstring convention for module-level documentation
4. **No __all__ export list** - Missing explicit export list for public API

### Info/Nits
1. **Module header correct** - Line 1: Business unit "utilities" is reasonable; could arguably be "config" but acceptable
2. **Import order correct** - Line 3: Single import follows conventions
3. **Type hints present** - Lines 16, 26, 36, 43: Proper type annotations for lists and dicts
4. **Naming convention good** - Constants use UPPER_SNAKE_CASE per PEP 8
5. **File size excellent** - 48 lines, well under 500-line soft limit
6. **No complexity** - Zero cyclomatic complexity (no functions, only constants)
7. **Security clean** - Bandit found no issues

---

## 3) Line-by-Line Notes

### Detailed Line-by-Line Analysis

| Line(s) | Issue / Observation | Severity | Evidence / Excerpt | Proposed Action |
|---------|---------------------|----------|-------------------|-----------------|
| 1 | Module header present and correct | ✓ Pass | `"""Business Unit: utilities \| Status: current."""` | No action - acceptable classification |
| 2 | Blank line | ✓ Pass | Follows module header | No action |
| 3 | Future annotations import | ✓ Pass | `from __future__ import annotations` enables PEP 563 | No action |
| 4 | Blank line separator | ✓ Pass | Separates imports from code | No action |
| 5 | Module-level comment | ⚠️ Low | `# Central place to define per-environment DSL strategy defaults.` | Consider converting to module docstring or keeping as-is |
| 6 | Blank line | ✓ Pass | Separates comment from section | No action |
| 7 | Section comment | ✓ Pass | `# Strategy file name constants` helps readability | No action |
| 8-14 | Strategy name constants | ⚠️ Medium | Missing docstrings for each constant explaining what strategy it represents | Add docstrings or inline comments describing each strategy |
| 8 | STRATEGY_KMLM definition | ✓ Pass | `STRATEGY_KMLM = "1-KMLM.clj"` - clear naming | Consider adding docstring explaining KMLM strategy |
| 9 | STRATEGY_NUCLEAR definition | ✓ Pass | `STRATEGY_NUCLEAR = "2-Nuclear.clj"` | Consider adding docstring explaining Nuclear strategy |
| 10 | STRATEGY_STARBURST definition | ✓ Pass | `STRATEGY_STARBURST = "3-Starburst.clj"` | Consider adding docstring explaining Starburst strategy |
| 11 | STRATEGY_WHAT definition | ✓ Pass | `STRATEGY_WHAT = "4-What.clj"` | Consider adding docstring explaining What strategy |
| 12 | STRATEGY_COIN definition | ✓ Pass | `STRATEGY_COIN = "5-Coin.clj"` | Consider adding docstring explaining Coin strategy |
| 13 | STRATEGY_TQQQ_FLT definition | ✓ Pass | `STRATEGY_TQQQ_FLT = "6-TQQQ-FLT.clj"` | Consider adding docstring explaining TQQQ-FLT strategy |
| 14 | STRATEGY_PHOENIX definition | ✓ Pass | `STRATEGY_PHOENIX = "7-Phoenix.clj"` | Consider adding docstring explaining Phoenix strategy |
| 15 | Blank line | ✓ Pass | Separates sections | No action |
| 16-24 | DEV_DSL_FILES list | ⚠️ Medium | Missing docstring explaining purpose and constraints | Add docstring: "List of DSL strategy files for development environment. Order preserved for consistency." |
| 16 | Type annotation present | ✓ Pass | `list[str]` properly typed | No action |
| 17-23 | List contents | ✓ Pass | All 7 strategies included for dev | Verify this matches business requirements |
| 24 | List closing | ✓ Pass | Proper bracket and newline | No action |
| 25 | Blank line | ✓ Pass | Separates sections | No action |
| 26-34 | DEV_DSL_ALLOCATIONS dict | 🔴 **Medium** | **No validation that values sum to 1.0** | Add assertion/validation or document in docstring |
| 26 | Type annotation present | ✓ Pass | `dict[str, float]` properly typed | No action |
| 27-33 | Allocation values | ⚠️ Low | Using float for money/allocation weights; sums to exactly 1.0 | Verify: 0.2+0.15+0.15+0.1+0.1+0.15+0.15=1.0 ✓ |
| 27 | KMLM allocation | ✓ Pass | `STRATEGY_KMLM: 0.2` = 20% | Reasonable allocation |
| 28 | Nuclear allocation | ✓ Pass | `STRATEGY_NUCLEAR: 0.15` = 15% | Reasonable allocation |
| 29 | Starburst allocation | ✓ Pass | `STRATEGY_STARBURST: 0.15` = 15% | Reasonable allocation |
| 30 | What allocation | ✓ Pass | `STRATEGY_WHAT: 0.1` = 10% | Reasonable allocation |
| 31 | Coin allocation | ✓ Pass | `STRATEGY_COIN: 0.1` = 10% | Reasonable allocation |
| 32 | TQQQ-FLT allocation | ✓ Pass | `STRATEGY_TQQQ_FLT: 0.15` = 15% | Reasonable allocation |
| 33 | Phoenix allocation | ✓ Pass | `STRATEGY_PHOENIX: 0.15` = 15% | Reasonable allocation |
| 34 | Dict closing | ✓ Pass | Proper bracket and newline | No action |
| 35 | Blank line | ✓ Pass | Separates sections | No action |
| 36-41 | PROD_DSL_FILES list | ⚠️ Medium | Missing docstring explaining purpose and constraints | Add docstring: "List of DSL strategy files for production. Subset of dev strategies." |
| 36 | Type annotation present | ✓ Pass | `list[str]` properly typed | No action |
| 37-40 | List contents | ✓ Pass | 4 strategies for prod (subset of dev) | Intentional prod subset - verify with business |
| 41 | List closing | ✓ Pass | Proper bracket and newline | No action |
| 42 | Blank line | ✓ Pass | Separates sections | No action |
| 43-48 | PROD_DSL_ALLOCATIONS dict | 🔴 **Medium** | **No validation that values sum to 1.0** | Add assertion/validation or document in docstring |
| 43 | Type annotation present | ✓ Pass | `dict[str, float]` properly typed | No action |
| 44-47 | Allocation values | ⚠️ Low | Using float for allocations; sums to exactly 1.0 | Verify: 0.4+0.25+0.1+0.25=1.0 ✓ |
| 44 | KMLM prod allocation | ✓ Pass | `STRATEGY_KMLM: 0.4` = 40% (doubled from dev) | Higher confidence in prod |
| 45 | Nuclear prod allocation | ✓ Pass | `STRATEGY_NUCLEAR: 0.25` = 25% (increased from dev) | Higher confidence in prod |
| 46 | Coin prod allocation | ✓ Pass | `STRATEGY_COIN: 0.1` = 10% (same as dev) | Consistent allocation |
| 47 | TQQQ-FLT prod allocation | ✓ Pass | `STRATEGY_TQQQ_FLT: 0.25` = 25% (increased from dev) | Higher confidence in prod |
| 48 | Dict closing | ✓ Pass | Proper bracket and newline | No action |
| 49 | EOF | ✓ Pass | File ends with newline | No action |

---

## 4) Correctness & Contracts

### Correctness Checklist

- [x] The file has a **clear purpose** and does not mix unrelated concerns (SRP)
  - **Status**: PASS - Single responsibility: define strategy profile constants as fallback defaults
  
- [x] Public functions/classes have **docstrings** with inputs/outputs, pre/post-conditions, and failure modes
  - **Status**: N/A - No functions or classes, only module-level constants
  - **Note**: Constants lack individual docstrings but have section comments
  
- [x] **Type hints** are complete and precise (no `Any` in domain logic; use `Literal/NewType` where helpful)
  - **Status**: PASS - All constants properly typed with `list[str]` and `dict[str, float]`
  - **Note**: Could use `Literal` for strategy name strings, but not critical for constants
  
- [x] **DTOs** are **frozen/immutable** and validated (e.g., Pydantic v2 models with constrained types)
  - **Status**: N/A - No DTOs, only module-level constants which are effectively immutable
  
- [x] **Numerical correctness**: currency uses `Decimal`; floats use `math.isclose` or explicit tolerances; no `==`/`!=` on floats
  - **Status**: PARTIAL - Float allocations sum to exactly 1.0, but no validation enforcing this
  - **Issue**: Should validate sum or document acceptable tolerance
  
- [x] **Error handling**: exceptions are narrow, typed (from `shared.errors`), logged with context, and never silently caught
  - **Status**: N/A - No code paths that can raise exceptions (constants only)
  
- [x] **Idempotency**: handlers tolerate replays; side-effects are guarded by idempotency keys or checks
  - **Status**: N/A - No handlers or side-effects (constants only)
  
- [x] **Determinism**: tests freeze time (`freezegun`), seed RNG; no hidden randomness in business logic
  - **Status**: PASS - Fully deterministic (constants only)
  
- [x] **Security**: no secrets in code/logs; input validation at boundaries; no `eval`/`exec`/dynamic imports
  - **Status**: PASS - No secrets, no dynamic code execution, bandit clean
  
- [x] **Observability**: structured logging with `correlation_id`/`causation_id`; one log per state change; no spam in hot loops
  - **Status**: N/A - No runtime behavior to log (constants only)
  
- [x] **Testing**: public APIs have tests; property-based tests for maths; coverage ≥ 80% (≥ 90% for strategy/portfolio)
  - **Status**: FAIL - No dedicated tests for this module
  - **Note**: Indirectly tested through config.py tests and JSON file validation tests
  
- [x] **Performance**: no hidden I/O in hot paths; vectorised Pandas ops; HTTP clients pooled with rate limits
  - **Status**: N/A - No I/O or performance-sensitive operations (constants only)
  
- [x] **Complexity**: cyclomatic ≤ 10, cognitive ≤ 15, functions ≤ 50 lines, params ≤ 5
  - **Status**: PASS - Zero cyclomatic complexity (no functions)
  
- [x] **Module size**: ≤ 500 lines (soft), split if > 800
  - **Status**: PASS - 48 lines total, excellent size
  
- [x] **Imports**: no `import *`; stdlib → third-party → local; no deep relative imports
  - **Status**: PASS - Single import from __future__, proper ordering

---

## 5) Additional Notes

### Current Status

This file serves as a **fallback configuration source** for DSL strategy allocations. The primary configuration source is now JSON files (`strategy.dev.json` and `strategy.prod.json` in the `the_alchemiser/config/` package directory). This file is only used when JSON loading fails.

### Usage Analysis

**Direct Consumers:**
- `the_alchemiser/shared/config/config.py` - Imports all constants and uses as fallback in `StrategySettings._get_stage_profile()`

**Indirect Testing:**
- `tests/shared/config/test_config_package.py` - Tests validate JSON files contain correct structure
- No direct tests for the fallback constants in this file

### Architectural Role

This file represents a **migration phase artifact**:
1. **Phase 1 (Legacy)**: Strategy profiles hardcoded in this file
2. **Phase 2 (Current)**: JSON files as primary source, this file as fallback
3. **Phase 3 (Future)**: Possibly eliminate this file entirely or keep as safety net

### Numerical Correctness Analysis

**Development Allocations:**
- KMLM: 0.2 (20%)
- Nuclear: 0.15 (15%)
- Starburst: 0.15 (15%)
- What: 0.1 (10%)
- Coin: 0.1 (10%)
- TQQQ-FLT: 0.15 (15%)
- Phoenix: 0.15 (15%)
- **Sum**: 1.0 ✓ (exactly)

**Production Allocations:**
- KMLM: 0.4 (40%)
- Nuclear: 0.25 (25%)
- Coin: 0.1 (10%)
- TQQQ-FLT: 0.25 (25%)
- **Sum**: 1.0 ✓ (exactly)

Both profiles sum correctly, but there's **no programmatic validation** to prevent future errors.

### Comparison with JSON Config Files

The JSON files in `the_alchemiser/config/` contain **identical data** to these constants:
- `strategy.dev.json` matches `DEV_DSL_FILES` and `DEV_DSL_ALLOCATIONS`
- `strategy.prod.json` matches `PROD_DSL_FILES` and `PROD_DSL_ALLOCATIONS`

This redundancy is intentional for fallback safety but creates maintenance burden.

### Security Considerations

- **No secrets**: File contains only strategy names and allocation weights
- **No injection risks**: Pure constant definitions with no user input
- **Bandit scan**: Clean (no issues identified)

### Recommendations

#### Immediate (Required for compliance)

1. **Add module-level docstring** (Medium priority)
   - Document purpose: fallback configuration for strategy allocations
   - Explain relationship to JSON config files
   - Document maintenance policy (keep in sync with JSON files)

2. **Add constant docstrings** (Medium priority)
   - Document each strategy's purpose (KMLM, Nuclear, Starburst, etc.)
   - Or add inline comments explaining strategy characteristics
   - Document constraints (e.g., "Allocations must sum to 1.0")

3. **Add validation or documentation** (Medium priority)
   - Either: Add assertion checking sum(allocations.values()) ≈ 1.0
   - Or: Document in comments that allocations MUST sum to 1.0
   - Prevents human error when updating allocations

4. **Add dedicated test file** (Medium priority)
   - Create `tests/shared/config/test_strategy_profiles.py`
   - Test that constants are defined and have expected types
   - Test that allocations sum to 1.0 (within tolerance)
   - Test that all files in FILES lists are present in ALLOCATIONS dicts

#### Short-term (Before next major release)

5. **Add __all__ export list** (Low priority)
   - Explicitly list public constants for better API clarity
   - Helps with wildcard imports (even though they're discouraged)

6. **Consider Decimal for allocations** (Low priority)
   - Current float usage is acceptable for these magnitudes
   - But Decimal would align with copilot instructions for financial data
   - Probably overkill for allocation weights (not actual money amounts)

7. **Document strategy characteristics** (Low priority)
   - Add comments or separate doc explaining what each strategy does
   - Helps maintainers understand allocation choices
   - Could live in separate documentation file

#### Long-term (Future phases)

8. **Evaluate elimination of this file** (Info)
   - If JSON config loading is reliable, this fallback may be unnecessary
   - Or keep as safety net for deployment failures
   - Decision should be based on operational experience

9. **Consider single source of truth** (Info)
   - Current dual-source (Python + JSON) creates maintenance burden
   - Options: Generate JSON from Python, or eliminate Python constants
   - Tradeoff: Safety vs. simplicity

10. **Add schema validation** (Info)
    - If keeping dual-source, add CI check that they stay in sync
    - Could use property-based tests to verify consistency

### Risk Assessment

**Current Risk Level**: LOW

**Justification:**
- File is simple, well-structured, and deterministic
- Used only as fallback (primary source is JSON files)
- No I/O, no external dependencies, no complex logic
- Bandit scan clean, mypy passes
- Allocations correctly sum to 1.0

**Potential Risks:**
- Manual updates could introduce arithmetic errors (sum ≠ 1.0)
- Divergence between Python constants and JSON files
- No automated validation of allocation sums

**Mitigation:**
- Add tests validating allocation sums
- Add CI check for Python/JSON consistency
- Add assertions or documentation about sum constraint

---

## 6) Compliance with Copilot Instructions

### ✅ Core Guardrails Compliance

| Guardrail | Status | Evidence | Pass/Fail |
|-----------|--------|----------|-----------|
| **Floats**: Never use `==`/`!=` on floats | ⚠️ PARTIAL | Floats used for allocations, but no direct comparisons in this file | ✅ ACCEPTABLE |
| **Module header** | ✅ PASS | Line 1: `"""Business Unit: utilities \| Status: current."""` | ✅ PASS |
| **Typing**: Strict, no `Any` | ✅ PASS | All constants properly typed; no `Any` usage | ✅ PASS |
| **Idempotency & traceability** | N/A | No event handlers in this file | ✅ N/A |
| **Tooling**: Use Poetry | ✅ PASS | Project uses Poetry (verified in pyproject.toml) | ✅ PASS |
| **Version Management** | 🔄 PENDING | Will bump PATCH version after review changes | 🔄 PENDING |

### ✅ Python Coding Rules Compliance

| Rule | Requirement | Status | Pass/Fail |
|------|-------------|--------|-----------|
| **SRP** | One clear purpose | ✅ PASS | Single responsibility: define strategy profile constants | ✅ PASS |
| **File Size** | ≤ 500 lines (soft limit) | ✅ PASS | 48 lines | ✅ PASS |
| **Function Size** | N/A (no functions) | ✅ N/A | Constants only | ✅ PASS |
| **Complexity** | Cyclomatic ≤ 10 | ✅ PASS | Zero complexity (no functions) | ✅ PASS |
| **Naming** | Clear, purposeful | ✅ PASS | UPPER_SNAKE_CASE for constants, descriptive names | ✅ PASS |
| **Imports** | No `import *`, ordered | ✅ PASS | Single import, proper ordering | ✅ PASS |
| **Tests** | Every public API tested | ❌ FAIL | No dedicated test file | ❌ NEEDS TESTS |
| **Error Handling** | Narrow, typed, logged | ✅ N/A | No error handling needed (constants only) | ✅ PASS |
| **Documentation** | Docstrings on public APIs | ⚠️ PARTIAL | Module header present, but constants lack docstrings | ⚠️ IMPROVE |
| **No Hardcoding** | Constants/config for values | ✅ PASS | This file IS the configuration | ✅ PASS |

### ✅ Architecture Boundaries Compliance

| Boundary | Requirement | Status | Pass/Fail |
|----------|-------------|--------|-----------|
| **Module Location** | shared/config | ✅ PASS | Correctly placed in shared/config | ✅ PASS |
| **Import Rules** | No cross-business imports | ✅ PASS | No imports from business modules | ✅ PASS |
| **Shared Utilities** | Zero business logic deps | ✅ PASS | No dependencies on business modules | ✅ PASS |

---

**Auto-generated**: 2025-10-10  
**Agent**: Copilot  
**Script**: File review process for strategy_profiles.py
