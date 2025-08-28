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
 - No cross-context domain imports. Communication ONLY via published Application layer DTOs or Interface contracts.
 - A context may depend inward on Shared Kernel; never laterally on another context's Domain package.
 - Anti-Corruption Mappers live in each context's application.mapping module; never in infrastructure.
 - Infrastructure adapters expose only Protocol implementations declared in the owning Domain.
 - Interfaces layer never contains business rules; it formats, transports, or orchestrates user interaction.

RETIRED LAYERS / PACKAGES:
 - Generic services/ and utils/ are being dismantled. Code is re-homed into context-aligned layers.
 - Do NOT add new modules under services/ or utils/ (except temporary shim flagged legacy during migration).

PACKAGE NAMING (ILLUSTRATIVE TARGET STRUCTURE):
the_alchemiser/
    shared_kernel/               # Cross-context immutable value objects & helpers
        value_objects/
    strategy/                    # Strategy bounded context
        domain/
        application/
        infrastructure/
        interfaces/
    portfolio/                   # Portfolio bounded context
        domain/
        application/
        infrastructure/
        interfaces/
    execution/                   # Execution bounded context
        domain/
        application/
        infrastructure/
        interfaces/
    main.py
    lambda_handler.py

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

DTO / MESSAGE NAMING RULES:
 - Domain: Plain nouns (Order, Position, StrategySignal, Portfolio, ExecutionPolicy).
 - Application I/O: Command / Query / Result suffix.
 - Interfaces (CLI/API): Request / Response / View.
 - Events: Event (versioned externally) e.g., TradeExecutedEventV1.
 - Persistence mapping: Record / Row / Model.
 - Use Dto only when unavoidable for clash ambiguity.

MAPPING & ANTI-CORRUPTION:
 - All translation between external API payloads and Domain objects occurs in application.mapping modules.
 - Never embed third-party payload shapes inside Domain entities.
 - Round-trip invariants must hold (serialization <-> domain) for stable contracts.

ERROR HANDLING:
 - Never fail silently. Raise typed exceptions (StrategyExecutionError, OrderExecutionError, DataAccessError, etc.).
 - Central error handler categorizes: CRITICAL, STRATEGY, PORTFOLIO, EXECUTION, DATA, CONFIGURATION, NOTIFICATION, WARNING.
 - Execution context owns order lifecycle error semantics; Portfolio context handles valuation/risk anomalies.
 - Provide component="Context.Layer.Class.method" in error metadata for traceability.

CONCURRENCY & INTEGRITY:
 - Avoid shared mutable state across contexts; pass immutable DTO snapshots.
 - Recompute derived values instead of caching mutable cross-context state unless a formal cache adapter exists.

IMPORT RULES (ENFORCEMENT TARGET):
 - strategy.domain -> may import: shared_kernel.*
 - portfolio.domain -> may import: shared_kernel.*
 - execution.domain -> may import: shared_kernel.*
 - No domain package imports another context's application/infrastructure.
 - application.* may depend on its own domain + shared_kernel + (optionally) other contexts' published application DTOs (never their domain internals).
 - infrastructure.* may depend on owning application & domain + shared_kernel; not on other context domains.
 - interfaces.* may depend on its own application layer and (read-only) published application DTOs from other contexts.

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
 2. Add Protocol(s) for external dependencies (e.g., MarketDataGateway) inside domain.protocols.
 3. Implement adapters in infrastructure implementing those Protocols.
 4. Create Application use case (PlaceOrderCommandHandler) wiring domain + protocol instances.
 5. Expose stable DTO in application.results (PlaceOrderResult).
 6. Interfaces layer consumes use case; formats output (CLI table, JSON, email).

FLOAT & NUMERIC POLICY:
 - Money/quantity/risk metrics -> Decimal.
 - Statistical ratios -> float permitted but compare with tolerance via helpers.

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
