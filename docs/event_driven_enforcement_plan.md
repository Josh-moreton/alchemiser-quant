# Event-Driven Enforcement Plan

## Purpose

Deliver a concrete execution plan to remove direct orchestration imports and enforce a pure event-driven workflow across `strategy_v2`, `portfolio_v2`, and `execution_v2`. The plan ensures each business unit communicates exclusively via shared event contracts and DTOs, while preserving idempotency, correlation tracking, and existing success metrics defined in the import linter remediation program.

## Target Outcomes

- ✅ Zero direct imports from orchestration into `strategy_v2`, `portfolio_v2`, or `execution_v2`.
- ✅ Strategy emits `strategy.signal.generated.v1` events derived from market data without downstream awareness.
- ✅ Portfolio consumes strategy events, evaluates account state, and emits `portfolio.rebalance.planned.v1` events.
- ✅ Execution consumes portfolio events, executes orders via Alpaca adapters, and emits `execution.order.settled.v1` events plus workflow completion signals.
- ✅ Event Bus and handler registry support idempotent, at-least-once delivery with correlation and causation identifiers.
- ✅ Comprehensive verification via unit, integration, and smoke tests with event replay scenarios.

## Current Gaps

1. **Direct Imports:** `EventDrivenOrchestrator` imports handlers and DTOs from business modules, breaking isolation.
2. **Implicit Wiring:** Handlers self-initialize during orchestrator boot, preventing independent lifecycle management.
3. **Event Contracts:** Existing schemas (`SignalGenerated`, `RebalancePlanned`, `TradeExecuted`) lack field-level guardrails for downstream consumers (e.g., schema versions, deterministic identifiers for dedupe).
4. **Idempotency:** No persistent dedupe keys beyond correlation ID; repeated events risk duplicated execution.
5. **Observability:** Correlated metrics exist but are not normalized across modules (missing consistent causation propagation, span timings, and structured logs).

## End-to-End Event Flow

1. **Market Data Ingestion (Strategy)**
   - Trigger: `StartupEvent` or `WorkflowStarted` from orchestrator.
   - Action: Strategy engines pull market data via shared adapter protocols.
   - Output: `strategy.signal.generated.v1` (current `SignalGenerated`).

2. **Portfolio Rebalance Planning**
   - Trigger: `SignalGenerated` event.
   - Action: Portfolio service reconciles account info, positions, and target allocations.
   - Output: `portfolio.rebalance.planned.v1` (current `RebalancePlanned`).

3. **Execution**
   - Trigger: `RebalancePlanned` event.
   - Action: Execution manager submits orders through Alpaca SDK adapters; reconciles fills.
   - Output: `execution.order.settled.v1` (current `TradeExecuted`) and `WorkflowCompleted`.

4. **Cross-Cutting Concerns**
   - Notifications, reconciliation, and recovery subscribe to events via shared registry without direct module imports.

## Module Responsibilities & Required Changes

### Strategy (`strategy_v2`)

- **Inputs:** `StartupEvent`, `WorkflowStarted`.
- **Outputs:** `SignalGenerated` with schema updates (add `schema_version`, `signal_hash`, `market_snapshot_id`).
- **Tasks:**
  - Extract market data via protocol-compliant adapter methods (no direct SDK objects beyond shared DTOs).
  - Publish `SignalGenerated` with deterministic `signal_hash` (hash of sorted signals) for idempotency.
  - Register handler via new shared handler registry (see below) instead of being instantiated by orchestrator.
  - Provide module-level bootstrap function `register_strategy_handlers(container, registry)` for orchestrator startup use.

### Portfolio (`portfolio_v2`)

- **Inputs:** `SignalGenerated`.
- **Outputs:** `RebalancePlanned` enriched with `plan_hash`, `account_snapshot_id`, and `schema_version`.
- **Tasks:**
  - Introduce adapters returning DTOs for account info, positions, and orders (eliminate raw dict usage).
  - Ensure `RebalancePlanDTO` serialization includes stable ordering for deterministic hashing.
  - Emit `WorkflowFailed` when portfolio analysis fails, preserving causation IDs.
  - Register handler via shared registry bootstrap.
  - Persist idempotency keys (`plan_hash`, `correlation_id`) in shared persistence for dedupe (leveraging `shared.persistence` module).

### Execution (`execution_v2`)

- **Inputs:** `RebalancePlanned`.
- **Outputs:** `TradeExecuted` (rename event type to `execution.order.settled.v1` via alias) and `WorkflowCompleted` (or `WorkflowFailed`).
- **Tasks:**
  - Wrap Alpaca SDK calls in DTO-returning adapters; confirm conversions obey `Decimal` policy.
  - Persist execution attempts keyed by `{correlation_id, plan_hash}` to guarantee idempotent retries.
  - Emit final event with `execution_plan_hash`, fill summaries, and `schema_version`.
  - Register handler through shared registry bootstrap.

## Orchestration Layer Changes

1. **Handler Registry (Shared Module)**
   - Create `shared/registry/handler_registry.py` providing:
     - `HandlerRegistration` dataclass (event_type, handler_factory, metadata).
     - `EventHandlerRegistry` to register and retrieve handlers by module and event type.
     - Optional priority ordering for multiple handlers per event.
   - Registry owns lifecycle; orchestrator simply iterates registrations and attaches them to `EventBus`.

2. **Bootstrap Contracts**
   - Each business module exposes `register_<module>_handlers(container, registry)` in `__init__.py`.
   - Startup sequence (`orchestration/system.py`) invokes these functions, not direct class imports.
   - Use import-linter-friendly import: `from the_alchemiser.strategy_v2 import register_handlers as register_strategy_handlers` (allowed boundary) while restricting orchestrator to interfaces defined at module root.

3. **EventDrivenOrchestrator Refactor**
   - Remove `_initialize_domain_handlers` direct imports; replace with registry-driven subscription.
   - Subscribe orchestrator to events using registry metadata.
   - Manage workflow state independently of handler instantiation.

4. **Dependency Injection**
   - Service container exposes registry instance for modules to register during startup.
   - Execution config and infrastructure dependencies resolved within module boundaries (no cross import).

## Event Contract Enhancements

| Event Type | Required Fields | Notes |
| --- | --- | --- |
| `SignalGenerated` | `schema_version:int`, `signal_hash:str`, `signals_data:dict[str,Any]`, `consolidated_portfolio:dict[str,Any]`, `market_snapshot_id:str` | `signals_data` remains summary; `consolidated_portfolio` stays DTO dump |
| `RebalancePlanned` | `schema_version:int`, `plan_hash:str`, `rebalance_plan:dict`, `allocation_comparison:dict`, `account_snapshot_id:str` | Use DTO `.model_dump()` with stable sort to maintain determinism |
| `TradeExecuted` | `schema_version:int`, `execution_plan_hash:str`, `orders:list[dict]`, `orders_placed:int`, `orders_succeeded:int`, `total_trade_value:str` | Provide map for reconciliations and notifications |

Each schema update increments `schema_version` and must remain backward compatible (additive fields, defaults).

## Reliability & Idempotency

- **Deterministic Hashes:** Compute `signal_hash`, `plan_hash`, and `execution_plan_hash` by hashing sorted DTO content plus correlation ID.
- **Persistent Deduplication:** Use `shared.persistence.event_store` or add a lightweight repository keyed by `(event_type, correlation_id, hash)`.
- **Idempotent Handlers:** Each handler checks persistence before acting; if already processed, it logs and exits without side effects.
- **Correlation & Causation IDs:** Propagate incoming `correlation_id`; set `causation_id` to triggering event ID.

## Observability

- Structured logging with `event_id`, `event_type`, `correlation_id`, `causation_id`.
- Emit metrics via `shared.logging` hooks (`event_published_total`, `event_handler_latency_ms`).
- Add tracing hooks for future OpenTelemetry integration (stub methods in EventBus).

## Testing Strategy

1. **Unit Tests**
   - Handler registry registration & retrieval.
   - Hash generation helpers for event idempotency.
   - DTO serialization with strict config.

2. **Integration Tests**
   - Simulate full event chain using in-memory EventBus and mock adapters.
   - Replay duplicate events to confirm idempotent behavior.
   - Failure injection tests (e.g., portfolio analysis failure emits `WorkflowFailed`).

3. **Smoke Tests**
   - End-to-end `poetry run python -m the_alchemiser` with paper trading mode verifying expected event sequence in logs.

## Implementation Phases

1. **Infrastructure Setup** (2-3 days)
   - Build handler registry and module registration contracts.
   - Refactor orchestrator startup to use registry.
   - Add minimal tests for registry + orchestrator boot.

2. **Strategy Module Refactor** (2-4 days)
   - Adopt registration entrypoint.
   - Add event hash metadata + schema version.
   - Implement idempotency guard (persisted or in-memory) for signal generation.

3. **Portfolio Module Refactor** (3-5 days)
   - Introduce DTO-compliant account adapter.
   - Emit enhanced `RebalancePlanned` event with metadata and idempotency.
   - Persist plan hashes to prevent duplicate calculations.

4. **Execution Module Refactor** (3-5 days)
   - Wrap Alpaca SDK interactions; ensure DTO usage.
   - Emit enriched `TradeExecuted` events.
   - Provide recovery workflow hooks for failures.

5. **Validation & Hardening** (2 days)
   - Add tests for duplicate event replay.
   - Verify logging + metrics coverage.
   - Update documentation and READMEs.

## Success Metrics

- `import-linter` reports zero orchestration → business module violations.
- Event-driven smoke test runs cleanly with no direct imports across modules.
- Idempotency tests confirm no duplicate executions under event replay.
- Structured logs show consistent correlation/causation propagation.

## Follow-Up & Risks

- **External Broker Reliability:** Real Alpaca SDK calls may not be idempotent; ensure execution layer records fill IDs before retries.
- **Schema Versioning:** Downstream consumers must default missing fields; coordinate release order to avoid breaking changes.
- **Performance:** Event bus remains in-memory; monitor for potential need to offload to managed queue in future phases.
