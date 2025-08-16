# Modular Lambda Deployment Plan for Alchemiser-Quant

This document outlines a phased, non-breaking approach to refactor the current monolithic AWS Lambda into three decoupled functions: **Data Provider**, **Strategy Engine**, and **Trading Module**. Each phase is designed to be independently deployable and reversible to minimise operational risk.

## Phase 0 – Preparation and Baseline
1. **Establish run identifier** – add a UUID generated at the start of each trading cycle that is logged and propagated through all messages. This enables end-to-end traceability once the pipeline is distributed.
2. **Harden idempotency** – review data retrieval, strategy evaluation, and order submission code to ensure repeated invocations with the same run ID produce the same outcome (e.g., target allocations instead of incremental orders).
3. **Externalise persistent state** – migrate any in-memory tracking (fills, P&L, last run time) to DynamoDB/S3 so that later Lambdas remain stateless.
4. **Create test fixtures** – capture representative market data, strategy outputs, and trade decisions for unit and integration tests of each future Lambda handler.

## Phase 1 – Internal Code Separation
1. **Extract data access layer**
   - Refactor the existing `UnifiedDataProvider` and account/position fetches into a callable module that returns a serialisable payload.
   - Ensure strategy classes no longer instantiate data providers directly; they must accept market data and positions as arguments.
2. **Isolate strategy evaluation**
   - Wrap `MultiStrategyManager` (and rebalancer if kept here) behind a function that accepts the data payload and returns trade decisions or a target portfolio.
   - Guarantee the function has no side effects except pure computation.
3. **Encapsulate trade execution**
   - Adapt `SmartExecution` and related Alpaca client code into a function that takes a decision payload and performs order placement/monitoring.
4. **Update unit tests** to cover the newly separated modules.

At the end of Phase 1 the monolithic Lambda still orchestrates all steps, but the underlying components are now decoupled and easier to invoke independently.

## Phase 2 – Infrastructure Introduction (Disabled Path)
1. **Define SQS queues** (or EventBridge Bus) for `MarketDataQueue` and `TradeDecisionQueue` with corresponding DLQs.
2. **Create new Lambda functions** in SAM template for Data, Strategy, and Trading, each pointing to the refactored modules but **disabled from triggering** (no event sources attached yet).
3. **Provision IAM roles** with least‑privilege policies:
   - Data Lambda: secrets retrieval and queue publish.
   - Strategy Lambda: queue consume/publish only.
   - Trading Lambda: secrets retrieval and trade execution permissions.
4. **Deploy to a staging environment** and invoke the new Lambdas manually using test events derived from Phase 0 fixtures to verify functionality in isolation.

## Phase 3 – Event‑Driven Pipeline (Shadow Mode)
1. **Attach event sources** so that:
   - EventBridge schedule triggers the Data Lambda.
   - `MarketDataQueue` triggers Strategy Lambda.
   - `TradeDecisionQueue` triggers Trading Lambda.
2. **Shadow execution** – keep the monolithic Lambda running as the production path while the new pipeline runs in parallel using read‑only trading credentials. Compare strategy outputs and trade decisions to ensure parity.
3. **Implement monitoring** – CloudWatch dashboards/alarms for each Lambda and queue; include DLQ alerts and correlation ID logging.
4. **Validate latency** – measure end‑to‑end time from Data to Trade to confirm it meets business requirements.

## Phase 4 – Cutover
1. **Disable trading actions** in the monolithic Lambda (configuration flag) and enable live trading credentials for the Trading Lambda.
2. **Switch EventBridge schedule** to target Data Lambda only, removing the old function.
3. **Monitor closely** during initial trading sessions; maintain ability to re‑enable monolith if critical issues arise.
4. **Update documentation and runbooks** to reflect the new architecture and operational procedures.

## Phase 5 – Optimisation and Extensions
1. **Fine‑tune concurrency and memory** settings per Lambda based on observed performance.
2. **Add optional consumers** (e.g., risk monitoring or analytics Lambdas) by subscribing them to the existing queues or EventBridge events.
3. **Introduce warm‑start mechanisms** (Provisioned Concurrency or scheduled invocations) if cold‑start latency affects trading windows.
4. **Periodically review IAM policies** and remove unused permissions to uphold least privilege.

---
Following this plan ensures a gradual, reversible migration from a single Lambda to a modular, event‑driven architecture without disrupting existing trading operations.
