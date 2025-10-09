# [File Review] Financial-grade, line-by-line audit

> Purpose: Conduct a rigorous, line-by-line review of a single Python file in the trading system, to institution-grade standards (correctness, controls, auditability, and safety). One issue per file.

---

## 0) Metadata

**File path**: `the_alchemiser/shared/events/schemas.py`

**Commit SHA / Tag**: `main` (commit 802cf268358e3299fb6b80a4b7cf3d4bda2994f4 not found - reviewing current main)

**Reviewer(s)**: Copilot AI

**Date**: 2025-01-16

**Business function / Module**: shared / Events

**Runtime context**: AWS Lambda / Local execution (Python 3.12), Event-driven architecture messaging

**Criticality**: P1 (High) - Event schemas are critical for system-wide inter-module communication

**Direct dependencies (imports)**:
```
Internal:
- the_alchemiser.shared.constants.{EVENT_TYPE_DESCRIPTION, RECIPIENT_OVERRIDE_DESCRIPTION}
- the_alchemiser.shared.schemas.common.AllocationComparison
- the_alchemiser.shared.schemas.portfolio_state.PortfolioState
- the_alchemiser.shared.schemas.rebalance_plan.RebalancePlan
- the_alchemiser.shared.events.base.BaseEvent

External:
- pydantic (BaseModel, Field)
- decimal.Decimal
- typing.Any
```

**External services touched**:
```
None directly - events are published to in-memory EventBus
(EventBus may forward to external systems like EventBridge but that's out of scope)
```

**Interfaces (DTOs/events) produced/consumed**:
```
Events Defined (all extend BaseEvent):
- StartupEvent: System initialization
- SignalGenerated: Strategy signal generation (v1.0 expected)
- RebalancePlanned: Portfolio rebalancing plan (v1.0 expected)
- TradeExecuted: Trade execution completion (v1.0 expected)
- TradeExecutionStarted: Trade execution initiation
- PortfolioStateChanged: Portfolio state transitions
- AllocationComparisonCompleted: Allocation analysis results
- OrderSettlementCompleted: Order settlement notification
- BulkSettlementCompleted: Multiple settlement notification
- ExecutionPhaseCompleted: Execution phase coordination
- WorkflowStarted: Workflow initiation
- WorkflowCompleted: Workflow success
- WorkflowFailed: Workflow failure
- ErrorNotificationRequested: Error notification trigger
- TradingNotificationRequested: Trading notification trigger
- SystemNotificationRequested: System notification trigger

All events inherit base fields from BaseEvent:
- correlation_id, causation_id, event_id, event_type, timestamp
- source_module, source_component, metadata
```

**Related docs/specs**:
- [Copilot Instructions](.github/copilot-instructions.md)
- [Event-driven Architecture](the_alchemiser/shared/events/)
- [Base Event Schema](the_alchemiser/shared/events/base.py)

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

1. **Float used for financial data** (Line 328) - `total_trade_value: float` violates the mandatory requirement to use `Decimal` for all monetary values. This can cause precision errors in financial calculations and reporting.

### High

1. **Missing schema_version fields** (All event classes) - Events lack explicit `schema_version` fields required by event-driven architecture patterns per Copilot Instructions. This breaks event evolution and compatibility tracking.

2. **No idempotency keys** (All event classes) - Events don't include idempotency keys (e.g., hash-based deduplication IDs), making handlers vulnerable to duplicate processing on replays.

3. **Unversioned event contracts** - While the file defines 16 event types, none have explicit versioning to support schema evolution. Handlers cannot safely handle multiple versions.

### Medium

1. **Loose typing with dict[str, Any]** (Lines 40, 55-56, 60, 78, 93, 97, 119, 124, 142, 167, 210, 231, 248, 266, 282, 329) - Using `dict[str, Any]` for critical business data (signals_data, execution_data, configuration, metadata) bypasses type safety and validation. Should use typed DTOs.

2. **No field constraints on critical fields** - Fields like `startup_mode`, `change_type`, `phase_type`, `workflow_type` lack `Literal` type constraints to enforce valid values.

3. **Inconsistent metadata patterns** - Some events define `metadata` field explicitly (SignalGenerated, RebalancePlanned, TradeExecuted), others inherit it from BaseEvent. This creates confusion about which metadata is event-specific vs. base.

4. **No docstring examples** - Event class docstrings lack usage examples showing how to construct events properly with all required fields.

### Low

1. **No validation for mutually exclusive fields** - TradeExecuted has both `success` and `failure_reason` but no validation ensuring they're mutually consistent (e.g., success=True shouldn't have failure_reason).

2. **Missing field descriptions for business rules** - Fields like `trades_required` (line 77) don't document the business rule for when this is true/false.

3. **No max_length constraints on string fields** - Fields like `failure_reason`, `error_report`, `html_content` have no size limits, risking memory issues with extremely large payloads.

4. **Inconsistent ordering of Field parameters** - Some fields have `...` first, others have `default` first, reducing readability.

### Info/Nits

1. **Empty comment line 27** - Orphaned comment "# Constants" with no actual constants following it.

2. **Inconsistent event_type descriptions** - All use `EVENT_TYPE_DESCRIPTION` but don't specify the actual type value in docstring.

3. **Import ordering** - Correct (stdlib → pydantic → internal) ✅

4. **Line count** - 351 lines total, well within 500 line target ✅

5. **Module header** - Correct business unit and status ✅

---

## 3) Line-by-Line Notes

### Detailed Line-by-Line Analysis

| Line(s) | Issue / Observation | Severity | Evidence / Excerpt | Proposed Action |
|---------|---------------------|----------|-------------------|-----------------|
| 1-11 | **Module header and docstring** | ✅ Info | Correct business unit ("shared") and status ("current"). Clear purpose statement. | None - compliant |
| 13-24 | **Imports** | ✅ Info | Proper ordering: stdlib → third-party → internal. Clean structure. | None - good practice |
| 27 | **Empty constants section** | Low | `# Constants` comment but no constants defined | Remove comment or add actual constants |
| 29-43 | **StartupEvent definition** | Medium | Uses `dict[str, Any]` for configuration (line 40-42), no schema_version field | Add schema_version, type configuration better |
| 36 | **event_type default** | ✅ Info | Good practice to set default matching class name | None - pattern works well |
| 39 | **startup_mode field** | Medium | Required field with no Literal constraints. What are valid values? | Add Literal["signal", "trade", "paper", "live"] or document |
| 45-61 | **SignalGenerated definition** | High | Missing schema_version, uses dict[str, Any] for critical business data (lines 55-56, 60) | Add schema_version="1.0", use typed DTOs for signals_data |
| 55-56 | **signals_data: dict[str, Any]** | Medium | Critical strategy output using untyped dict | Replace with `StrategySignals` DTO |
| 56-58 | **consolidated_portfolio: dict[str, Any]** | Medium | Should use ConsolidatedPortfolio DTO, not dict | Use `ConsolidatedPortfolio` type |
| 63-81 | **RebalancePlanned definition** | High | Missing schema_version field | Add schema_version="1.0" |
| 73 | **rebalance_plan field** | ✅ Info | Uses proper typed DTO (RebalancePlan) | None - good practice |
| 74-76 | **allocation_comparison field** | ✅ Info | Uses proper typed DTO (AllocationComparison) | None - good practice |
| 83-107 | **TradeExecuted definition** | High | Missing schema_version, dict[str, Any] for execution_data (line 93) | Add schema_version="1.0", type execution_data |
| 93 | **execution_data: dict[str, Any]** | Medium | Critical execution results untyped | Use `ExecutionResult` or similar DTO |
| 101-103 | **failure_reason field** | Low | No mutual exclusivity validation with success=True | Add model_validator |
| 109-127 | **TradeExecutionStarted** | Medium | Missing schema_version, untyped execution_plan and market_conditions | Add schema_version, type fields |
| 123 | **trade_mode field** | Medium | No Literal constraint on valid modes | Add Literal["live", "paper"] |
| 129-145 | **PortfolioStateChanged** | High | Missing schema_version field | Add schema_version="1.0" |
| 141 | **change_type field** | Medium | No Literal constraint on valid types | Add Literal or document values |
| 147-170 | **AllocationComparisonCompleted** | ✅ High | Uses Decimal for financial data ✅, but missing schema_version | Add schema_version="1.0" |
| 159-165 | **Decimal fields** | ✅ Info | Correct use of Decimal for allocation percentages | None - compliant |
| 172-194 | **OrderSettlementCompleted** | ✅ High | Uses Decimal for financial data ✅, but missing schema_version | Add schema_version="1.0" |
| 184 | **side field** | Medium | No Literal constraint | Add Literal["BUY", "SELL"] |
| 186-190 | **Decimal fields** | ✅ Info | Correct use of Decimal for financial values | None - compliant |
| 196-214 | **BulkSettlementCompleted** | High | Missing schema_version, uses Decimal correctly ✅ | Add schema_version="1.0" |
| 216-234 | **ExecutionPhaseCompleted** | High | Missing schema_version field | Add schema_version="1.0" |
| 226 | **phase_type field** | Medium | No Literal constraint on valid phases | Add Literal["SELL_PHASE", "BUY_PHASE"] |
| 236-251 | **WorkflowStarted** | High | Missing schema_version field | Add schema_version="1.0" |
| 246 | **workflow_type field** | Medium | No Literal constraint | Add Literal or document valid values |
| 253-267 | **WorkflowCompleted** | High | Missing schema_version field | Add schema_version="1.0" |
| 264 | **workflow_duration_ms field** | ✅ Info | Good precision using milliseconds | None - appropriate |
| 269-285 | **WorkflowFailed** | High | Missing schema_version field | Add schema_version="1.0" |
| 290-310 | **ErrorNotificationRequested** | High | Missing schema_version field | Add schema_version="1.0" |
| 302 | **error_severity field** | Medium | Values in description but no Literal constraint | Add Literal["CRITICAL", "HIGH", "MEDIUM", "LOW"] |
| 303 | **error_priority field** | Medium | Values in description but no Literal constraint | Add Literal["URGENT", "HIGH", "MEDIUM", "LOW"] |
| 312-333 | **TradingNotificationRequested** | **Critical** | Missing schema_version, **uses float for money** (line 328) | Add schema_version="1.0", change float to Decimal |
| 328 | **total_trade_value: float** | **Critical** | `total_trade_value: float = Field(...)` violates mandatory Decimal requirement | **MUST change to Decimal** |
| 335-351 | **SystemNotificationRequested** | High | Missing schema_version field | Add schema_version="1.0" |
| 347 | **notification_type field** | Medium | Values in description but no Literal constraint | Add Literal["INFO", "WARNING", "ALERT"] |

---

## 4) Correctness & Contracts

### Correctness Checklist

- [x] The file has a **clear purpose** and does not mix unrelated concerns (SRP) - ✅ Only defines event schemas
- [x] Public functions/classes have **docstrings** - ⚠️ Present but missing usage examples and failure modes
- [x] **Type hints** are complete and precise - ❌ Uses `dict[str, Any]` extensively instead of typed DTOs; missing Literal types
- [x] **DTOs** are **frozen/immutable** and validated - ✅ All events inherit frozen config from BaseEvent
- [ ] **Numerical correctness**: currency uses `Decimal` - ❌ **CRITICAL: Line 328 uses float for total_trade_value**
- [x] **Error handling** - N/A (DTOs don't perform operations that can fail)
- [ ] **Idempotency**: handlers tolerate replays - ❌ No idempotency keys in events
- [x] **Determinism** - ✅ Events are data structures, no randomness
- [x] **Security**: no secrets in code/logs - ✅ No secrets, but ensure runtime doesn't log sensitive fields
- [ ] **Observability**: structured logging - N/A for DTOs, but events lack schema_version for tracking
- [ ] **Testing**: public APIs have tests - ⚠️ Used in integration tests but no dedicated unit tests for event schemas
- [x] **Performance**: no hidden I/O - ✅ Pure data structures
- [x] **Complexity**: cyclomatic ≤ 10, cognitive ≤ 15, functions ≤ 50 lines, params ≤ 5 - ✅ All event classes < 30 lines
- [x] **Module size**: ≤ 500 lines (soft), split if > 800 - ✅ 351 lines total
- [x] **Imports**: no `import *` - ✅ Clean imports

### Contract Violations

1. **Missing schema_version across all events**: Events should include `schema_version: str = Field(default="1.0", ...)` for evolution tracking
2. **Float for financial data** (Line 328): Violates core financial integrity requirement
3. **Untyped business data**: Using `dict[str, Any]` for critical business data defeats type safety
4. **No idempotency keys**: Events should include computed idempotency keys (hash of core fields) for deduplication
5. **Missing Literal constraints**: String fields with fixed valid values should use Literal types

---

## 5) Additional Notes

### Architecture Alignment

The file correctly defines event schemas for the event-driven architecture, following the pattern:
- Strategy → SignalGenerated → Portfolio → RebalancePlanned → Execution → TradeExecuted

Events properly inherit from BaseEvent which provides:
- ✅ Correlation/causation tracking
- ✅ Immutability (frozen=True)
- ✅ Strict validation
- ✅ Timestamp with timezone awareness

### Testing Gaps

1. No dedicated unit tests for event schema validation
2. No tests verifying Decimal precision requirements
3. No tests for serialization/deserialization (to_dict/from_dict)
4. No property-based tests for event field constraints

### Recommended Immediate Actions

**CRITICAL (Must Fix):**
1. Change `total_trade_value: float` to `Decimal` (line 328)
2. Add `schema_version` field to all event classes

**HIGH (Should Fix Soon):**
3. Add idempotency key field (computed hash) to support replay tolerance
4. Replace `dict[str, Any]` with typed DTOs for business data
5. Add Literal constraints for enum-like string fields

**MEDIUM (Technical Debt):**
6. Add usage examples to event class docstrings
7. Add model validators for mutually exclusive fields
8. Add max_length constraints on text fields
9. Create dedicated unit tests for event schemas

### Security Considerations

✅ No secrets in code
✅ Immutable structures prevent tampering
⚠️ Ensure runtime logging redacts sensitive fields (account IDs, prices in some contexts)
⚠️ Consider PII implications in notification events (email addresses in recipient_override)

### Performance Notes

✅ Events are lightweight DTOs with minimal overhead
✅ No I/O or heavy computation in constructors
✅ Proper use of default_factory for mutable defaults (dict, list)

---

## 6) Compliance with Copilot Instructions

### ✅ Compliant
- Module header with Business Unit and Status
- Proper import ordering
- Frozen, immutable DTOs
- Type hints present
- Module size within limits
- SRP (single responsibility)

### ❌ Non-Compliant
- **CRITICAL**: Float used for money (line 328) - violates core requirement
- Missing schema_version for event evolution
- No idempotency keys for replay tolerance
- Loose typing (dict[str, Any]) in domain logic
- Missing tests for event schemas

### ⚠️ Partial Compliance
- Type hints present but not precise (needs Literal types)
- Documentation present but missing examples
- Events support correlation tracking but lack idempotency

---

## 7) Recommended Changes Summary

### Phase 1: Critical Fixes (Required)
1. Change line 328: `total_trade_value: Decimal` (not float)
2. Add `schema_version: str = Field(default="1.0", ...)` to all 16 event classes
3. Run version bump: `make bump-minor` (breaking contract changes)

### Phase 2: High Priority (Strongly Recommended)
4. Add idempotency_key field computed from event core fields
5. Replace dict[str, Any] with typed DTOs:
   - signals_data → StrategySignals DTO
   - consolidated_portfolio → ConsolidatedPortfolio (already exists)
   - execution_data → ExecutionResult DTO
   - configuration → Configuration DTO (already exists)
6. Add Literal type constraints for enum fields

### Phase 3: Technical Debt (Future)
7. Add comprehensive unit tests for event schemas
8. Add usage examples to docstrings
9. Add model validators for business rule enforcement
10. Remove orphaned comment on line 27

---

**Auto-generated**: 2025-01-16  
**Review Type**: Institution-Grade Line-by-Line Audit  
**File**: `the_alchemiser/shared/events/schemas.py` (351 lines)  
**Status**: ⚠️ **NON-COMPLIANT - CRITICAL ISSUES FOUND**

**Reviewer Signature**: Copilot AI  
**Approval Status**: ❌ **REJECTED - REQUIRES FIXES** (Critical float usage, missing schema versions)
