# Facade Serialization Strategy

## Decision: Option B - Serialize at Facade Boundary

**Date**: 2025-08-26
**Context**: Issue #255 - Standardize facade serialization strategy for DTOs

## Problem

PortfolioManagementFacade and other facades had inconsistent return patterns:
- Some methods returned DTO objects (e.g., `get_rebalancing_summary() -> RebalancingSummaryDTO`)
- Some methods returned serialized dicts (e.g., `get_portfolio_analysis() -> dict[str, Any]`)
- Composite methods manually called `.model_dump()` on some returns but not others

This inconsistency increased cognitive load for callers and made the facade boundary contract unclear.

## Options Considered

### Option A: Return DTO objects everywhere
- **Pros**: Type safety, better IDE support, validation, can be serialized later by callers
- **Cons**: Callers need to handle serialization when needed (e.g., for JSON responses)

### Option B: Serialize (model_dump()) everything at facade boundary
- **Pros**: Simple dict interface, immediately JSON serializable, no type complications for callers
- **Cons**: Loss of type safety, no validation after facade boundary, harder debugging

## Decision Rationale

**Chose Option B** for the following reasons:

1. **Facade Pattern Purpose**: Facades are application-layer boundaries that should provide presentation-ready data
2. **Consumer Expectations**: Most downstream consumers (email templates, CLI displays, JSON APIs) expect dict-like structures
3. **Consistency**: Eliminates mixed approaches and manual `.model_dump()` calls
4. **Internal Type Safety**: DTOs can still be used internally within facades for validation and type safety, then serialized at the boundary
5. **JSON Compatibility**: Immediate serialization for email reports, API responses, and logging

## Implementation Strategy

1. **Internal Usage**: Continue using DTOs internally for type safety and validation
2. **Boundary Serialization**: Call `.model_dump()` on all DTO returns at facade methods
3. **Return Type Updates**: Update all facade method return types to `dict[str, Any]` for consistency
4. **Documentation**: Clear docstrings indicating that methods return serialized dictionaries

## Impact

- **Breaking Change**: Yes, for callers expecting DTO objects
- **Migration**: Callers should expect `dict[str, Any]` instead of DTO objects
- **Benefits**: Consistent, JSON-ready interface across all facade methods
- **Type Safety**: Maintained internally, sacrificed at boundary for simplicity (structural typing can be reintroduced with `TypedDict` if needed)
- **Decimal Handling**: All Decimals serialized to string to ensure native JSON compatibility without custom encoder.

### Migration Notes
| Method | Old Return | New Return | Action |
|--------|------------|-----------|--------|
| calculate_rebalancing_plan | RebalancePlanCollectionDTO | dict[str, Any] | Remove `.model_dump()`; treat as dict |
| get_rebalancing_summary | RebalancingSummaryDTO | dict[str, Any] | Remove `.model_dump()` |
| estimate_rebalancing_impact | RebalancingImpactDTO | dict[str, Any] | Remove `.model_dump()` |
| get_enriched_account_summary | EnrichedAccountSummaryDTO | dict[str, Any] | Replace attribute access with key lookup |
| execute_rebalancing.rebalance_plan | DTO | serialized dict | Access via `['rebalance_plan']` |
| perform_portfolio_rebalancing_workflow.rebalancing_plan | DTOs | serialized dict entries | Use key access |

## Examples

### Before (Inconsistent)
```python
def get_rebalancing_summary(self, target_weights: dict[str, Decimal]) -> RebalancingSummaryDTO:
    return self.rebalancing_service.get_rebalancing_summary(target_weights)

def get_portfolio_analysis(self) -> dict[str, Any]:
    return self.analysis_service.get_comprehensive_portfolio_analysis()

def get_complete_portfolio_overview(self, target_weights: dict[str, Decimal] | None = None) -> dict[str, Any]:
    overview = {
        "rebalancing_summary": self.get_rebalancing_summary(target_weights).model_dump(),  # Manual serialization
        "portfolio_analysis": self.get_portfolio_analysis(),  # Already dict
    }
```

### After (Consistent)
```python
def get_rebalancing_summary(self, target_weights: dict[str, Decimal]) -> dict[str, Any]:
    """Get comprehensive rebalancing summary as serialized dictionary."""
    dto = self.rebalancing_service.get_rebalancing_summary(target_weights)
    return dto.model_dump()

def get_portfolio_analysis(self) -> dict[str, Any]:
    """Get comprehensive portfolio analysis as serialized dictionary."""
    return self.analysis_service.get_comprehensive_portfolio_analysis()

def get_complete_portfolio_overview(self, target_weights: dict[str, Decimal] | None = None) -> dict[str, Any]:
    """Get complete portfolio overview as serialized dictionary."""
    overview = {
        "rebalancing_summary": self.get_rebalancing_summary(target_weights),  # Consistent dict
        "portfolio_analysis": self.get_portfolio_analysis(),  # Consistent dict
    }
```

## Decimal Serialization Policy

Decimals are converted to their exact string form at the facade boundary using `to_serializable` (in `the_alchemiser/utils/serialization.py`). Consumers needing arithmetic should cast back via `Decimal(str_value)`.

## Post-Review Adjustments

- Added centralized serialization utility.
- Ensured nested DTOs in composite responses are serialized.
- Added migration table & decimal policy.
