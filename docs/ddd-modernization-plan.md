# DDD Modernization and Strong Typing Adoption Plan

This document describes a complete, actionable plan to migrate The Alchemiser to a Domain‑Driven Design (DDD) architecture with strong typing throughout:
- Pydantic v2 models at the system edges (I/O, provider adapters, CLI/API)
- Dataclasses and Value Objects (VOs) in the domain core
- Typed ports (Protocols) and adapters between domain and infrastructure
- Incremental rollout with tests, acceptance criteria, and rollback strategy

The plan aligns with existing docs/typing-migration/phase-plan.md and extends it to define DDD boundaries, aggregates, and implementation rules.


## 1. Current state (as of 2025‑08‑19)
- Domain shared kernel already contains VOs: Identifier, Money, Percentage with invariants.
- Widespread usage of TypedDict for domain/application/CLI shapes in `the_alchemiser/domain/types.py`.
- Application: `MultiStrategyExecutionResult` is a dataclass; TODO references Pydantic at edges.
- Strategy layer: `StrategyRegistry` defines `StrategyType` and maps to engines. `StrategyManager` orchestrates runs using dict-shaped payloads. `KLMStrategyEnsemble` consumes a typed data provider adapter.
- Services: `TypedDataProviderAdapter` is an explicit edge shim over `MarketDataClient`.
- Tooling: Pydantic >= 2, mypy, ruff for development

Implication: We have the right tools and some domain VOs, but most inter‑module contracts are dictionary‑shaped. The migration should formalize boundaries, replace internals with dataclasses/VOs, and validate at edges with Pydantic.


## 2. Target architecture (DDD‑aligned)
- Bounded Contexts:
  - Market Data: fetching quotes/bars/prices; time series utilities
  - Strategy/Signal: strategy engines, signal computation, ensemble selection
  - Execution/Orders: order planning, placement, acknowledgments, fills
  - Portfolio/Accounting: positions, PnL, snapshots, performance
  - Reporting/Interfaces: CLI, email, dashboards
- Layers per context:
  - Domain: entities, aggregates, VOs, domain services, domain events
  - Application: use cases, orchestration, transaction boundaries, DTO mapping
  - Infrastructure: adapters to providers, persistence, HTTP/SDK integrations
  - Interface: CLI/HTTP/email — accept/produce edge models
- Typing strategy:
  - Domain core: Python dataclasses (frozen where possible) + VOs; no Pydantic inside
  - Edges: Pydantic v2 BaseModel for request/response validation and serialization
  - Ports: typing.Protocol interfaces in domain/application; adapters in infrastructure implement them
  - Mappers: explicit mappers translate between Pydantic edge DTOs and domain models
- Mutability rules: domain entities/VOs are immutable where possible; aggregates expose behavior methods that return new instances or internal mutations guarded by invariants.
- Error strategy: typed domain exceptions; edge validation errors are Pydantic ValidationError; adapters translate provider errors to typed errors.


## 3. Domain model outline (initial set)
- Value Objects (existing): Identifier[T], Money, Percentage
- Additional VOs to add as needed:
  - Symbol(str wrapper), Timeframe(enum), Allocation(Percentage), OrderId(Identifier[Order])
- Entities/Aggregates:
  - Account: id, equity, cash, buying_power, status, etc.
  - Position: symbol, qty, entry_price, current_price, PnL helpers
  - Portfolio (aggregate): holdings: dict[Symbol, Position], cash: Money
  - Order: id, symbol, side, type, tif, qty, price, status
  - Strategy: type, current recommendation/signal, rationale
- Domain events (optional in this phase): OrderPlaced, OrderFilled, PositionClosed, SignalGenerated


## 4. Edge models (Pydantic v2)
- Market data:
  - Quote: symbol, bid, ask, ts
  - Bar: symbol, open, high, low, close, volume, start/end
- Execution:
  - OrderRequest: symbol, side, type, tif, qty, price
  - OrderAck: order_id, status, filled_qty, avg_price, ts
- Account/Portfolio snapshots for interfaces:
  - AccountView, PositionView, PortfolioSnapshotView, StrategySignalView

Note: Prefer compiled models (default in v2) and from_attributes for easy mapping; use field validators for normalization.


## 5. Ports (Protocols) and adapters
- MarketDataPort:
  - get_historical_bars(symbol: str, period: str, interval: str) -> list[Bar]
  - get_latest_quote(symbol: str) -> Quote | None
  - get_current_price(symbol: str) -> float | None
- ExecutionPort:
  - place_order(req: OrderRequest) -> OrderAck
  - get_order(id: OrderId) -> OrderAck | None
- PortfolioRepository (if persistence introduced later):
  - load_account(account_id) -> Account
  - save_portfolio(portfolio) -> None
- Adapters implement ports using provider SDKs; edge validation occurs using Pydantic models at adapter boundary.


## 6. Migration strategy — synchronized with existing Phases 5–15
This adds a DDD‑alignment track and concrete deliverables per phase.

- Phase 5 (Baseline models) — existing plan
  - Deliver dataclass models for OrderDetails and ExecutionResultDTO (align with domain Order/OrderAck naming)
  - Keep TypedDict adapters for compatibility

- Phase 6 (Service return typing) — existing plan
  - Replace service dict returns with Pydantic edge models where the service is an edge (provider clients)
  - Where service is internal to domain, replace with dataclasses/VOs

- Phase 7 (Domain model uplift) — existing plan
  - Replace Any with domain models; introduce Portfolio, Position
  - Strategy interfaces return StrategySignal (domain dataclass), not dict

- Phase 8 (Application cleanup) — existing plan
  - Introduce PositionSnapshot and SignalPayload as application DTOs
  - Mappers between application DTOs and domain models

- Phase 9 (Provider contracts) — existing plan, emphasize Pydantic
  - Define Quote, Bar, OrderAck as Pydantic models
  - Implement MarketDataPort and ExecutionPort adapters with validation

- Phase 10 (Typed cache) — existing plan

- Phase 11 (Portfolio snapshots) — existing plan

- Phase 12 (CLI adoption) — existing plan

- Phase 13 (Email templates) — existing plan

- Phase 14 (Remove shims) — existing plan

- Phase 15 (Strict typing finish) — existing plan

DDD alignment-specific milestones to insert alongside phases:
1) Define core domain dataclasses and VOs (Account, Portfolio, Position, Order, StrategySignal)
2) Introduce Ports as Protocols and refactor adapters to implement them
3) Add mapping layer: edge <-> app DTOs <-> domain models
4) Harden invariants and behavior on aggregates (e.g., Portfolio.apply_order)


## 7. Concrete work items, deliverables, and acceptance criteria

A. Domain core introduction
- Deliverables:
  - the_alchemiser/domain/models/account.py (Account dataclass)
  - the_alchemiser/domain/models/position.py (Position dataclass)
  - the_alchemiser/domain/models/portfolio.py (Portfolio aggregate)
  - the_alchemiser/domain/models/order.py (Order, OrderSide, OrderType, TIF enums)
  - the_alchemiser/domain/models/signal.py (StrategySignal dataclass)
- Acceptance Criteria:
  - Unit tests for invariants (Money non-negative; Percentage in [0,1]; Portfolio weight sum ≤ 1.0)
  - No mypy “Any” in these modules; public types exported via __all__

B. Edge models and ports
- Deliverables:
  - the_alchemiser/interfaces/models/market_data.py (Pydantic: Quote, Bar)
  - the_alchemiser/interfaces/models/execution.py (Pydantic: OrderRequest, OrderAck)
  - the_alchemiser/domain/ports/market_data.py (Protocol: MarketDataPort)
  - the_alchemiser/domain/ports/execution.py (Protocol: ExecutionPort)
- Acceptance Criteria:
  - Adapters perform .model_validate(...) on provider responses
  - Protocols covered by mypy structural typing

C. Mappers and application services
- Deliverables:
  - the_alchemiser/application/mapping/market_data_mapper.py
  - the_alchemiser/application/mapping/execution_mapper.py
  - the_alchemiser/application/services/strategy_runner.py (use-case orchestrating ports and domain)
- Acceptance Criteria:
  - Existing CLI flows produce identical JSON snapshot outputs
  - Application service unit tests exercising DTO<->domain mapping

D. Strategy layer refactor (incremental)
- Deliverables:
  - Update StrategyManager to consume MarketDataPort and return StrategySignal models
  - Update KLMStrategyEnsemble to accept MarketDataPort and emit structured StrategySignal
- Acceptance Criteria:
  - Regression tests for strategy selection logic; no change in behavior vs baseline fixtures

E. Remove temporary shims and TypedDicts (endgame)
- Deliverables:
  - Delete TypedDict variants in domain/types.py as their dataclass/Pydantic replacements reach 100% coverage
  - Remove TypedDataProviderAdapter when strategies consume MarketDataPort
- Acceptance Criteria:
  - mypy --strict passes (or ≤5 errors allowed as per phase 15)


## 8. Code conventions and rules
- Domain:
  - dataclass(frozen=True) for VOs; entities may be mutable with controlled methods
  - Business methods live on aggregates/entities; avoid anemic models
  - No provider SDK imports in domain; depend only on ports and VOs
- Pydantic v2:
  - Use BaseModel, field validators for normalization, model_config with from_attributes=True where useful
  - Keep edge models stable; version if breaking changes are needed
- Mapping:
  - Keep mappers pure and unit tested; no IO side-effects
- Error handling:
  - Use typed exceptions per context (e.g., StrategyExecutionError, DataProviderError)
- Testing:
  - Contract tests around ports; snapshot tests for CLI output


## 9. Tooling and CI
- mypy: incrementally increase strictness per phase (see docs/typing-migration/phase-plan.md)
- ruff: keep current rules; enable additional DDD checks via custom pre-commit (optional)
- coverage: maintain or improve current coverage; add snapshot tests for interfaces


## 10. Incremental rollout plan with timeline
- Week 1–2 (S/M):
  - Introduce domain models (Account, Position, Portfolio, Order, StrategySignal)
  - Create Ports and initial Pydantic edge models
  - Add mappers and unit tests
- Week 3–4 (M):
  - Refactor MarketData adapters to MarketDataPort with Pydantic validation
  - StrategyManager consumes port; KLM ensemble uses port; preserve behavior
- Week 5–6 (M):
  - ExecutionPort and order flow adoption; replace dict payloads with models in application layer
- Week 7–8 (L):
  - Portfolio snapshots and PnL utilities refactor; CLI/Email adoption with typed context
- Week 9+:
  - Remove shims, finalize strict typing, enable mypy --strict in CI


## 11. Risk management and rollback
- Maintain compatibility adapters until all callers migrate
- Keep JSON output snapshots stable during CLI/email refactors
- Use feature toggles or environment flags to select typed vs legacy paths while migrating


## 12. Concrete next steps (actionable)
1) Create domain dataclasses: StrategySignal, Order, Position (minimal fields) and integrate into StrategyManager return types behind a feature flag (no behavior change) 
2) Define Pydantic edge models: Quote, Bar; wrap MarketDataClient in an adapter implementing MarketDataPort using these models
3) Add a mapping module for StrategySignalView and PortfolioSnapshotView for CLI rendering; update one CLI command to use it and snapshot‑test
4) Open tracking issues for each module per this plan and link to phases 5–15


## 13. Acceptance criteria for “migration complete”
- No non‑test code uses dict‑shaped payloads for domain/application boundaries
- All provider responses are validated at edges using Pydantic v2 models
- Domain aggregates/entities/VOs enforce invariants through constructors/methods
- CLI and email outputs unchanged (snapshot tests passing)
- mypy --strict passes in CI (or ≤5 residual issues as per Phase 15), ruff clean


## 14. Appendix — Mapping from current types to new models (initial)
- AccountInfo (TypedDict) → AccountView (Pydantic) at interface, Account (dataclass) in domain
- StrategySignal (TypedDict) → StrategySignal (dataclass) in domain, StrategySignalView (Pydantic) at interface
- OrderDetails (TypedDict) → Order (domain dataclass) + OrderAck (Pydantic at edge)
- PortfolioSnapshot (TypedDict) → Portfolio (domain aggregate) + PortfolioSnapshotView (Pydantic)

This plan is designed to minimize disruptions by keeping adapters and snapshots stable while progressively introducing domain models and typed edges.
