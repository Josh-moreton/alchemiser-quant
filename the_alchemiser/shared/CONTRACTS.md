# Shared Contracts

Semantic contract catalogue for modules consuming shared events and schemas. All contracts are versioned with `CONTRACT_VERSION` (`1.0.0`) and validated by automated tests under `tests/<module>/`.

## strategy_v2
- **Events (consume/produce)**: `StartupEvent`, `WorkflowStarted`, `SignalGenerated`, `WorkflowFailed`, `StrategyEvaluationRequested`, `StrategyEvaluated`, `IndicatorComputed`, `PortfolioAllocationProduced`, `FilterEvaluated`, `TopNSelected`.
- **Schemas/DTOs**: `ASTNode`, `IndicatorRequest`, `PortfolioFragment`, `TechnicalIndicator`, `Trace`, `StrategyAllocation`, `StrategySignal`, `MarketBar`, `ConsolidatedPortfolio`.

## portfolio_v2
- **Events (consume/produce)**: `SignalGenerated`, `RebalancePlanned`, `WorkflowFailed`.
- **Schemas/DTOs**: `ConsolidatedPortfolio`, `AllocationComparison`, `RebalancePlan`, `RebalancePlanItem`, `StrategyAllocation`.

## execution_v2
- **Events (consume/produce)**: `RebalancePlanned`, `TradeExecuted`, `WorkflowCompleted`, `WorkflowFailed`, `BulkSettlementCompleted`, `OrderSettlementCompleted`, `ExecutionPhaseCompleted`.
- **Schemas/DTOs**: `RebalancePlan`, `RebalancePlanItem`, `ExecutedOrder`, `TradeLedger`, `TradeLedgerEntry`.

## orchestration
- **Events (consume/produce)**: `StartupEvent`, `WorkflowStarted`, `WorkflowCompleted`, `WorkflowFailed`, `TradingNotificationRequested`, `SystemNotificationRequested`, `ReportReady`.
- **Schemas/DTOs**: `OrderResultSummary`, `ExecutionSummary`, `TradeRunResult`.
