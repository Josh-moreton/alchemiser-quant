# Per-Strategy Books Architecture - Summary

## Overview

This proposal addresses the issue request to "explore this idea in depth, and create the plan to action it" for removing the rebalance planner aggregation step and having each strategy run its own book.

## Deliverables

### 1. Comprehensive Architecture Document
**Location**: `docs/ARCH_PER_STRATEGY_BOOKS.md` (21KB, 620 lines)

**Contents**:
- Current architecture analysis (event flow, components, data structures)
- Proposed architecture (new event flow, removed components, new data structures)
- Detailed 6-phase implementation plan
- Migration strategy (gradual vs big bang - gradual recommended)
- Risk assessment (technical and operational)
- Open questions with recommendations
- Success criteria and timeline estimate (4-6 weeks)

### 2. Proof-of-Concept Event Schema
**Location**: `layers/shared/the_alchemiser/shared/events/schemas.py`

**Added**: `StrategyExecutionRequested` event class
- Demonstrates feasibility of proposed architecture
- Fully typed Pydantic schema with validation
- Includes all fields needed for per-strategy execution
- Documented as "PROOF OF CONCEPT"
- Syntax validated (Python compilation successful)

## Key Design Decisions

### Architecture Changes
1. **Remove Aggregation**: No more Signal Aggregator Lambda or AggregationSessionsTable
2. **Remove Rebalance Planner**: No more Portfolio/Rebalance Planner Lambda
3. **Strategy Workers Enhanced**: Each strategy calculates its own rebalance plan
4. **Independent Execution**: Each strategy triggers its own trades
5. **Per-Strategy Ledger**: Trades recorded with strategy_id in partition key

### Event Flow Transformation
```
OLD (Current):
Strategy Workers (parallel)
    ↓ PartialSignalGenerated
Signal Aggregator
    ↓ SignalGenerated
Rebalance Planner
    ↓ RebalancePlanned
Execution
    ↓ TradeExecuted
Notifications

NEW (Proposed):
Strategy Workers (parallel)
    ↓ StrategyExecutionRequested
Execution
    ↓ TradeExecuted
Notifications
```

### Benefits
- **Simplified Architecture**: Remove 2 Lambdas, 1 DynamoDB table, 3 event types
- **Cleaner Attribution**: Each trade belongs to exactly one strategy
- **Independent Strategies**: No coupling through aggregation
- **Easier Testing**: Test strategies in isolation
- **Better P&L Tracking**: Direct per-strategy queries

### Trade-offs
- **Symbol Overlap**: Multiple strategies can't easily coordinate on same symbol
- **Capital Management**: Need proportional cash allocation logic
- **Position Tracking**: Need per-strategy position state management

## Implementation Phases

### Phase 1: Schema and Event Changes (2-3 days)
- Create StrategyExecutionRequested event ✅ (POC done)
- Update TradeLedgerEntry schema
- Create StrategyPosition schema

### Phase 2: Strategy Worker Enhancement (5-7 days)
- Add rebalance planning logic to workers
- Add position reading logic
- Generate trade messages
- Remove PartialSignalGenerated publishing

### Phase 3: Execution Lambda Updates (3-4 days)
- Update trade recording with new PK pattern
- Update event handling for new event type
- Update position tracking per strategy

### Phase 4: Infrastructure Changes (2-3 days)
- Remove Aggregator and Planner Lambdas from template.yaml
- Remove AggregationSessionsTable
- Update EventBridge routing
- Update IAM policies

### Phase 5: Code Cleanup (2-3 days)
- Remove aggregator_v2 module
- Remove portfolio_v2 module (conditional)
- Update schemas to mark deprecated events
- Update documentation

### Phase 6: Testing and Validation (5-7 days)
- Type checking (make type-check)
- Integration testing
- Manual validation
- Deploy to dev and monitor

## Migration Strategy (Recommended: Gradual)

1. Deploy new StrategyExecutionRequested handler (doesn't affect existing flow)
2. Add feature flag in Coordinator to select flow per strategy
3. Route 1 strategy to new flow, rest to old flow
4. Monitor for 1+ week
5. Gradually increase strategies on new flow
6. Once 100% on new flow for 2+ weeks, remove old flow

**Rollback Plan**: Flip feature flag back to route strategies through old flow

## Open Questions & Recommendations

1. **Capital Rebalancing**: Rebalance when drift exceeds threshold (e.g., ±10%)
2. **Symbol Overlap**: Warn but allow - monitor if issues arise
3. **Cash Management**: Proportional cash allocation per strategy
4. **Hedge Management**: Keep as system-level (not per-strategy)
5. **Performance Reporting**: Maintain both per-strategy and total portfolio

## Timeline

**Total Estimate**: 4-6 weeks for full migration
- Implementation: 3-4 weeks (phases 1-6)
- Gradual Migration: 2-3 weeks (monitoring period)

## Next Steps

1. **Review & Approval**: Review this proposal and POC event schema
2. **Decision**: Approve to proceed with implementation or request changes
3. **Phase 1 Start**: Begin with schema and event changes if approved
4. **Iterative Development**: Complete phases 1-6 with progress reporting
5. **Testing**: Deploy to dev environment for validation
6. **Gradual Rollout**: Migrate strategies incrementally to new flow

## References

- **Architecture Document**: `docs/ARCH_PER_STRATEGY_BOOKS.md`
- **POC Event Schema**: `layers/shared/the_alchemiser/shared/events/schemas.py` (line 1100+)
- **Current Architecture**: `CLAUDE.md`, `README.md`
- **Template**: `template.yaml`

## Status

**[DONE] EXPLORATION COMPLETE**: This proposal fulfills the issue requirement to "explore this idea in depth, and create the plan to action it."

**[PENDING] IMPLEMENTATION**: Awaiting approval to proceed with implementation phases.
