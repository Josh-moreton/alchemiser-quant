# Architecture Comparison: Current vs Proposed

## Current Architecture (To Be Replaced)

```
                    ┌─────────────────────────┐
                    │  Strategy Orchestrator  │ (EventBridge Schedule 3:30 PM ET)
                    │  (Coordinator Lambda)   │
                    └────────────┬────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │  Async Lambda Invocations│
                    │  (1 per DSL file)        │
                    └────────────┬────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│  Strategy    │        │  Strategy    │        │  Strategy    │
│  Worker 1    │        │  Worker 2    │        │  Worker N    │
│  (Lambda)    │        │  (Lambda)    │        │  (Lambda)    │
└──────┬───────┘        └──────┬───────┘        └──────┬───────┘
       │                       │                       │
       │ PartialSignalGenerated│                       │
       └───────────────────────┼───────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Signal Aggregator  │ ◄── DynamoDB Session Table
                    │  (Lambda)           │
                    └──────────┬──────────┘
                               │
                               │ SignalGenerated
                               ▼
                    ┌─────────────────────┐
                    │  Rebalance Planner  │
                    │  (Portfolio Lambda) │
                    └──────────┬──────────┘
                               │
                               │ RebalancePlanned
                               ▼
                    ┌─────────────────────┐
                    │  SQS Standard Queue │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  Execution   │      │  Execution   │      │  Execution   │
│  Lambda 1    │      │  Lambda 2    │      │  Lambda N    │
│              │      │              │      │              │
└──────┬───────┘      └──────┬───────┘      └──────┬───────┘
       │                     │                     │
       │ TradeExecuted       │                     │
       └─────────────────────┼─────────────────────┘
                             │
                             ▼
                    ┌─────────────────────┐
                    │  Trade Ledger       │
                    │  (DynamoDB)         │
                    │  Multi-strategy     │
                    │  attribution via    │
                    │  strategy_weights   │
                    └─────────────────────┘

Issues:
❌ Complex aggregation logic
❌ Rebalance planner as bottleneck
❌ Complex strategy_weights attribution
❌ Partial entry/exit complexity
❌ Strategies coupled through aggregation
```

## Proposed Architecture (Per-Strategy Books)

```
                    ┌─────────────────────────┐
                    │  Strategy Orchestrator  │ (EventBridge Schedule 3:30 PM ET)
                    │  (Coordinator Lambda)   │
                    └────────────┬────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │  Async Lambda Invocations│
                    │  (1 per DSL file)        │
                    └────────────┬────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
        ▼                        ▼                        ▼
┌──────────────┐        ┌──────────────┐        ┌──────────────┐
│  Strategy    │        │  Strategy    │        │  Strategy    │
│  Worker 1    │        │  Worker 2    │        │  Worker N    │
│  (Enhanced)  │        │  (Enhanced)  │        │  (Enhanced)  │
│              │        │              │        │              │
│ • Read own   │        │ • Read own   │        │ • Read own   │
│   positions  │        │   positions  │        │   positions  │
│ • Calculate  │        │ • Calculate  │        │ • Calculate  │
│   rebalance  │        │   rebalance  │        │   rebalance  │
│ • Generate   │        │ • Generate   │        │ • Generate   │
│   trades     │        │   trades     │        │   trades     │
└──────┬───────┘        └──────┬───────┘        └──────┬───────┘
       │                       │                       │
       │ StrategyExecutionRequested                    │
       └───────────────────────┼───────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  SQS Standard Queue │
                    └──────────┬──────────┘
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
        ▼                      ▼                      ▼
┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│  Execution   │      │  Execution   │      │  Execution   │
│  Lambda 1    │      │  Lambda 2    │      │  Lambda N    │
│              │      │              │      │              │
└──────┬───────┘      └──────┬───────┘      └──────┬───────┘
       │                     │                     │
       │ TradeExecuted       │                     │
       └─────────────────────┼─────────────────────┘
                             │
                             ▼
              ┌──────────────────────────────┐
              │  Trade Ledger (DynamoDB)     │
              │  Per-Strategy Partitions:    │
              │                              │
              │  PK: STRATEGY#momentum#TRADE#│
              │  PK: STRATEGY#mean_rev#TRADE#│
              │  PK: STRATEGY#breakout#TRADE#│
              │                              │
              │  Simple attribution:         │
              │  Each trade → 1 strategy     │
              └──────────────────────────────┘

Benefits:
- No aggregation needed
- No rebalance planner bottleneck
- Simple per-strategy attribution
- Independent strategy execution
- Strategies decoupled
- Cleaner P&L tracking
```

## Key Differences

| Aspect | Current | Proposed |
|--------|---------|----------|
| **Lambda Functions** | 5 (Orchestrator, Worker, Aggregator, Planner, Execution) | 3 (Orchestrator, Worker, Execution) |
| **DynamoDB Tables** | 2 (AggregationSessions, TradeLedger) | 1 (TradeLedger) |
| **Event Types** | 6 (PartialSignal, Signal, Rebalance, etc.) | 3 (StrategyExecution, TradeExecuted, etc.) |
| **Attribution** | Complex (strategy_weights dict) | Simple (single strategy per trade) |
| **Strategy Coupling** | High (through aggregation) | None (independent) |
| **Rebalance Logic** | Centralized (Portfolio Lambda) | Distributed (per Strategy Worker) |
| **Position State** | Global (all strategies merged) | Per-Strategy (independent books) |
| **P&L Queries** | Complex (attribution calculation) | Direct (query by strategy_id) |

## Component Changes Summary

### Removed Components ❌
- Signal Aggregator Lambda
- Rebalance Planner Lambda
- AggregationSessionsTable (DynamoDB)
- PartialSignalGenerated event
- SignalGenerated event
- RebalancePlanned event

### Enhanced Components ⚡
- Strategy Workers (add rebalance planning)
- Execution Lambda (per-strategy ledger writes)
- TradeLedger (new PK pattern with strategy_id)

### New Components ✨
- StrategyExecutionRequested event
- Per-strategy capital allocation logic
- Per-strategy position tracking

## Migration Path

### Phase 1: Coexistence (Weeks 1-2)
- Deploy new components alongside old
- Feature flag routes strategies to old or new flow
- 1 strategy on new flow for testing

### Phase 2: Gradual Migration (Weeks 3-4)
- Increase strategies on new flow
- Monitor performance, errors, P&L accuracy
- Validate position reconciliation

### Phase 3: Complete Migration (Weeks 5-6)
- All strategies on new flow
- Monitor for 2+ weeks
- Remove old components

### Phase 4: Cleanup (Week 7)
- Delete old Lambda functions
- Delete old DynamoDB table
- Remove old event schemas
- Update documentation

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Position state drift | Periodic reconciliation Lambda |
| Capital over-allocation | Validation in Coordinator |
| Failed execution recovery | Existing SQS retry + DLQ |
| Symbol overlap conflicts | Warning logs + monitoring |
| Migration issues | Feature flag for instant rollback |

## Success Metrics

- ✅ All strategies executing independently
- ✅ P&L accurate per strategy
- ✅ No aggregation or rebalance planner calls
- ✅ Latency ≤ current + 10%
- ✅ Zero data corruption
- ✅ Cost ≤ 1.2x current
