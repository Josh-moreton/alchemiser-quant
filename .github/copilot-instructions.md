"""Alchemiser Copilot Instructions

This file defines enforced rules and architectural guidance for AI-driven contributions.

CORE ENFORCED RULES:
1. Never use == or != with floats (use Decimal for money; math.isclose for non-financial floats).
2. Use assert_close()/numpy.testing.assert_allclose for numerical test comparisons (when tests exist).
3. Do NOT create new tests or introduce testing frameworks (project currently excludes them for AI agents).
4. Each new module MUST start with a module docstring declaring Business Unit and Status (current|legacy).
     Business Units (bounded-context aligned):
         - strategy & signal generation
         - portfolio assessment & management
         - order execution/placement
         - utilities (shared kernel / cross-cutting) – keep minimal
5. Keep BUSINESS_UNITS_REPORT.md consistent when adding/removing files.
6. No legacy fallbacks: never reintroduce removed legacy providers or silent downgrade paths.

-------------------------------------------------------------------------------
DDD EVOLUTION: THREE BOUNDED CONTEXTS
-------------------------------------------------------------------------------
We are restructuring around THREE explicit bounded contexts, each internally
layered (Domain, Application, Infrastructure, Interfaces):

1. Strategy Context
     Purpose: Signal generation, indicator calculation, regime detection, strategy composition.
     Domain: Strategy engines, value objects (StrategySignal, Confidence, Alert), policies.
     Application: Orchestrates multi-strategy runs, normalization, scoring, DTO mappers.
     Infrastructure: Data acquisition adapters (market data fetchers, indicator caches) specific to strategy needs.
     Interfaces: CLI signal display, potential HTTP exports, validation utilities.

2. Portfolio Context
     Purpose: Portfolio state, valuation, allocations, risk constraints, rebalancing decisions.
     Domain: Account, Position, Portfolio Aggregate, Value Objects (Money, Percentage, Symbol, Quantity), risk policies.
     Application: Rebalancing use cases, target allocation computation, exposure analytics, mapping to/from external DTOs.
     Infrastructure: Brokerage/account adapters (account balances, positions, historical equity), persistence/storage.
     Interfaces: Portfolio status CLI tables, reporting/email views, external query endpoints.

3. Execution Context
     Purpose: Order validation, smart execution strategies, routing, monitoring fill lifecycle.
     Domain: Order, OrderIntent, ExecutionPolicy, OrderStatus, SlippageModel.
     Application: PlaceOrderCommand / CancelOrderCommand handlers, smart execution pipeline, order sizing rules.
     Infrastructure: Broker order API adapters, WebSocket listeners, retry & backoff utilities.
     Interfaces: Execution CLI (trade), deployment entrypoints (Lambda), event publishing of fills.

Cross-Cutting Shared Kernel (Minimal):
 - Immutable primitives & ubiquitous value objects (Money, Percentage, Identifier, Symbol)
 - Pure functions with no external side-effects
 - MUST NOT depend on any bounded context packages

BOUNDARY PRINCIPLES:
 - No cross-context domain imports. Communication ONLY via versioned Application contracts (DTOs) serialized across a message boundary (SQS, CLI simulation) – never direct domain object sharing.
 - Contexts depend inward on shared_kernel ONLY (value objects, enums, minimal helpers); never laterally.
 - All external <-> internal translation centralized in top-level anti_corruption/ (contexts MUST NOT import anti_corruption; dependency direction is external -> anti_corruption -> context via DTO construction).
 - Infrastructure adapters expose only Protocol (Port) implementations declared in application.ports (or application/ports.py) – domain stays tech-agnostic.
 - Interfaces layer never contains business rules; it parses/validates input, invokes a use case, formats output.

RETIRED LAYERS / PACKAGES:
 - Generic services/ and utils/ are being dismantled. Code is re-homed into context-aligned layers.
 - Do NOT add new modules under services/ or utils/ (except temporary shim flagged legacy during migration).

PACKAGE NAMING (ILLUSTRATIVE TARGET STRUCTURE):
the_alchemiser/
    shared_kernel/               # Pure immutable VOs, enums, tiny stateless helpers (no inbound deps)
        value_objects/
        tooling/
    anti_corruption/             # External ↔ internal mappers (alpaca_order_to_domain, dto serializers)
        brokers/
        market_data/
        serialization/
    strategy/
        domain/
        application/
            contracts/           # SignalV1, internal command/query/result types
            ports.py             # MarketDataPort, SignalPublisher
            use_cases/
        infrastructure/
            adapters/            # AlpacaMarketDataAdapter, SqsSignalPublisher
        interfaces/
            lambda/
            cli/
    portfolio/
        domain/
        application/
            contracts/           # RebalancePlanV1, (ExecutionReportV1 consumer shape if mirrored)
            ports.py             # PositionRepositoryPort, PlanPublisher, ExecReportHandlerPort
            use_cases/
        infrastructure/
            adapters/            # SqsPlanPublisher, PortfolioStateRepository, S3 writers
        interfaces/
            lambda/
            cli/
    execution/
        domain/
        application/
            contracts/           # ExecutionReportV1, Plan consumption DTO mirror
            ports.py             # OrderRouterPort, ExecutionReportPublisher
            use_cases/
        infrastructure/
            adapters/            # AlpacaOrderRouter, SqsExecutionReportPublisher
        interfaces/
            lambda/
            cli/
    main.py                      # Optional orchestration / CLI entry
    lambda_handler.py            # (May delegate or be deprecated)

-------------------------------------------------------------------------------
TYPING & CODE QUALITY
-------------------------------------------------------------------------------
 - 100% mypy compliance: disallow_untyped_defs, disallow_incomplete_defs.
 - Every function annotated (parameters + explicit return). Use None explicitly.
 - Money & quantities: Decimal only (no float arithmetic for financial values).
 - Non-financial float comparisons: math.isclose or explicit epsilon helpers.
 - Prefer Protocol over ABC for ports (repository, gateway, provider patterns).
 - Domain layer: framework-free (NO Pydantic, logging, requests, boto3, pandas, rich).
 - Application layer: orchestrates use cases (Commands, Queries, Results) + mapping.
 - Infrastructure layer: external side-effects (I/O, network, persistence, brokers, AWS, Alpaca).
 - Interfaces layer: CLI, presentation, serialization, transport.
 - Shared Kernel: leaf-only; cannot import from any bounded context.

DTO / MESSAGE NAMING & VERSIONING RULES:
 - Domain: Plain nouns (Order, Position, StrategySignal, Portfolio, ExecutionPolicy).
 - Inter-context contracts (application/contracts): Version suffix (SignalV1, RebalancePlanV1, ExecutionReportV1, PlannedOrderV1, FillV1).
 - Use-case internal I/O: Command / Query / Result suffix.
 - Interfaces (CLI/API): Request / Response / View.
 - Events: <Noun><Action/Event>V<version> (TradeExecutedEventV1) when modeled explicitly.
 - Persistence mapping: Record / Row / Model.
 - Prefer semantic names over generic *Dto; retain version for backward compatibility. NEVER mutate an existing version in-place; add V2+ with upgrade mapper in anti_corruption.serialization.
PRIMARY CONTRACT FLOWS:
 - Strategy -> Portfolio: SignalV1(symbol, action (ActionType), confidence (float), target_allocation (Percentage/Decimal), reasoning, timestamp, correlation_id, deduplication_id, causation_id)
 - Portfolio -> Execution: RebalancePlanV1(plan_id, correlation_id, generated_at, planned_orders[list[PlannedOrderV1]])
 - Execution -> Portfolio: ExecutionReportV1(report_id, correlation_id, fills[list[FillV1]], summary, account_delta, generated_at)
 - Correlation chain preserved across lifecycle for traceability.

MAPPING & ANTI-CORRUPTION:
 - Centralized in anti_corruption/ (NOT inside context application.mapping anymore – that folder is deprecated).
 - Provides pure functions/classes translating external SDK payloads → domain VOs / DTOs and vice versa (e.g., alpaca_order_to_domain, domain_order_to_alpaca_request).
 - Contexts receive already-mapped objects (DTOs / VOs); they do NOT import anti_corruption (one-way dependency to avoid leakage of external schemas).
 - Document any lossy conversions; ensure round-trip invariants where required for idempotency.

ERROR HANDLING:
 - Never fail silently. Raise typed exceptions (StrategyExecutionError, OrderExecutionError, DataAccessError, etc.).
 - Central error handler categorizes: CRITICAL, STRATEGY, PORTFOLIO, EXECUTION, DATA, CONFIGURATION, NOTIFICATION, WARNING.
 - Execution context owns order lifecycle error semantics; Portfolio context handles valuation/risk anomalies.
 - Provide component="Context.Layer.Class.method" in error metadata for traceability.

CONCURRENCY & INTEGRITY:
 - Avoid shared mutable state across contexts; pass immutable DTO snapshots.
 - Recompute derived values instead of caching mutable cross-context state unless a formal cache adapter exists.

IMPORT RULES (TO BE ENFORCED VIA import-linter):
 - Layer direction inside a context: interfaces -> application -> domain; infrastructure -> application/domain (infrastructure must NOT import interfaces; prefer factories/wiring outside domain logic).
 - Domain imports: shared_kernel only.
 - Application imports: own domain, shared_kernel, own contracts/ports; cross-context only via serialized DTO payloads (avoid importing another context's application module – treat foreign DTOs as external JSON, rehydrate locally if necessary).
 - Infrastructure imports: own application + domain + shared_kernel; never other contexts' infrastructure.
 - Interfaces imports: own application + shared_kernel (+ optional foreign DTO class ONLY if no alternative; prefer boundary JSON).
 - anti_corruption may import context domain + application contracts + shared_kernel; contexts MUST NOT import anti_corruption.
 - Hard forbidden: any reference to legacy services/ or utils/; cross-context domain/infrastructure imports; domain -> application/infrastructure; application -> interfaces.
 - Example contracts for import-linter (abridged):
     * Layers per context (interfaces > application > domain) + infrastructure isolation.
     * Forbidden: strategy.domain -> portfolio.* / execution.* (and symmetric), * -> the_alchemiser.services.* / the_alchemiser.utils.* / other_context.infrastructure.*

LEGACY & MIGRATION FLAGS:
 - Mark temporary shims with module docstring Status: legacy and schedule removal.
 - Do not extend legacy modules; create current replacements and migrate call sites.

PERFORMANCE & OBSERVABILITY:
 - Domain functions must be deterministic and side-effect free.
 - Infrastructure network calls must include minimal structured logging (context id, symbol, operation).
 - Avoid premature micro-optimizations; focus on clarity with O(1)/O(n) reasoning documented when non-trivial.

SECURITY & CONFIGURATION:
 - All secrets via environment / AWS Secrets Manager adapters (in infrastructure layer only).
 - No hard-coded API keys or credentials in any layer.

STYLE SUMMARY:
 - Line length 100. Ruff formatter enforced.
 - Import order auto (ruff). No unused imports.
 - Use Decimal quantize only in infrastructure or presentation formatting, not for internal math unless rounding policy documented.

PROHIBITED PATTERNS:
 - Direct cross-context domain imports.
 - Logic in interfaces layer.
 - Silent except: or broad except Exception without re-raise via typed error.
 - Adding new generic helpers to a catch-all utils/ directory.
 - Float equality checks.

RECOMMENDED WORKFLOW:
 1. Define or refine Domain model (value objects, entities, policies) inside the owning context.
 2. Define Protocol(s)/Ports in application/ports.py (MarketDataPort, OrderRouterPort, Publishers...).
 3. Implement adapters in infrastructure/adapters/ satisfying Ports.
 4. Implement application use cases (verb_noun modules under application/use_cases/).
 5. Define/extend versioned DTO contracts in application/contracts/ (never mutate an existing version).
 6. Interfaces layer (CLI/Lambda) materializes inbound DTOs from JSON, invokes use case, publishes outbound DTO via Port.
 7. Add/adjust anti_corruption mappers only when integrating new external payload shapes.

FLOAT & NUMERIC POLICY:
 - Money/quantity/risk metrics -> Decimal.
 - Statistical ratios -> float permitted but compare with tolerance via helpers.

EVENT-DRIVEN COMMUNICATION & OUTBOX:
 - Default flow: SignalV1 -> RebalancePlanV1 -> ExecutionReportV1 across FIFO queues (signals.fifo, plans.fifo, exec-reports.fifo).
 - Each message includes metadata: message_id, correlation_id (root), causation_id (immediate predecessor), deduplication_id (FIFO idempotency), timestamp.
 - Producers SHOULD persist an outbox record (minimal store acceptable) before publish for reliability where state change + message must be atomic.
 - Consumers MUST be idempotent (skip if message_id already processed).
 - CLI/demo path may shortcut queue delivery but MUST still construct DTOs exactly as production.

PORT DEFINITIONS (MINIMUM SET):
 - strategy.application.ports: MarketDataPort, SignalPublisher.
 - portfolio.application.ports: PositionRepositoryPort, PlanPublisher, ExecutionReportHandlerPort / callback, PortfolioStateRepositoryPort.
 - execution.application.ports: OrderRouterPort, ExecutionReportPublisher, (optional) ExecutionMarketDataPort.
 - Adapters named <tech>_<role>.py (alpaca_order_router.py, sqs_signal_publisher.py).

PORTFOLIO STATE OWNERSHIP:
 - ONLY Portfolio context mutates portfolio/position state; Execution reports outcomes; Strategy suggests intents.
 - Sizing happens in Portfolio planning; Execution MUST NOT recompute target quantities (except broker lot normalization inside its domain logic).

NAMING CONVENTIONS (ADDITIONAL):
 - Use cases: verb_noun modules (generate_signals.py, create_rebalance_plan.py, execute_plan.py, apply_execution_report.py).
 - Value objects: singular files (money.py, symbol.py, percentage.py) inside shared_kernel/value_objects/.
 - Mappers (anti_corruption): <external>_to_<internal>.py / <internal>_to_<external>.py.
 - DTO files: snake_case with version suffix (signal_v1.py, rebalance_plan_v1.py, execution_report_v1.py).

ARCHITECTURE ENFORCEMENT:
 - Configure import-linter in CI to enforce contracts above.
 - mypy strict mode required for all new/modified modules.
 - No direct anti_corruption usage in domain/application; mapping performed at interface boundary before invoking use case.

LEGACY CLEANUP GUIDELINES:
 - When touching code under deprecated services/ or utils/, migrate logic into proper context layer before extending functionality.
 - application.mapping modules are deprecated – create mapping in anti_corruption/ instead.

BUSINESS UNIT DOCSTRINGS:
Example top-of-file docstring:
"""Business Unit: portfolio assessment & management | Status: current

Rebalancing engine computing target allocations from strategy signals and risk constraints.
"""

LINT & TYPE COMMANDS (always with poetry run):
 - make format
 - make lint
 - poetry run mypy the_alchemiser/

DEPLOYMENT:
 - Lambda entrypoint remains top-level; Execution context application orchestrates cross-context calls.

FINAL NOTE:
This document supersedes older references to a monolithic services/ layer. All new code must align with the three bounded contexts and layered structure.
"""
