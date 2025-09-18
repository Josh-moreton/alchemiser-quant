"""Alchemiser Copilot Instructions

This file defines enforced rules and architectural guidance for AI-driven contributions.

CORE ENFORCED RULES:
1. Never use == or != with floats (use Decimal for money; math.isclose for non-financial floats).
2. Use assert_close()/numpy.testing.assert_allclose for numerical test comparisons (when tests exist).
3. Do NOT create new tests or introduce testing frameworks (project currently excludes them for AI agents).
4. Each new module MUST start with a module docstring declaring Business Unit and Status (current|legacy).
     Business Units (module-aligned):
         - strategy – signal generation, indicators, ML models
         - portfolio – portfolio state, sizing, rebalancing logic
         - execution – broker API integrations, order placement, error handling
         - orchestration – cross-module workflow coordination and business process orchestration
         - shared – DTOs, utilities, logging, cross-cutting concerns
5. No legacy fallbacks: never reintroduce removed legacy providers or silent downgrade paths.
6. Event-driven reliability: all event producers and consumers MUST be idempotent and include
     correlation IDs; handlers must be safe under at-least-once delivery and tolerate reordering.

-------------------------------------------------------------------------------
MODULAR ARCHITECTURE: FIVE TOP-LEVEL MODULES
-------------------------------------------------------------------------------
The codebase is organized around five main modules with clear responsibilities
and controlled dependencies:

1. strategy_v2/
     Purpose: Signal generation, indicator calculation, ML models, regime detection
     Contains: Strategy engines, technical indicators, ML pipelines, signal processors
     Examples: Nuclear strategy, TECL strategy, market regime detection, volatility indicators

2. portfolio_v2/
     Purpose: Portfolio state management, sizing, rebalancing logic, risk management
     Contains: Portfolio valuation, position tracking, allocation calculations, rebalancing algorithms
     Examples: Portfolio rebalancer, position manager, risk constraints, allocation optimizer

3. execution_v2/
     Purpose: Broker API integrations, order placement, smart execution, error handling
     Contains: Order routing, broker connectors, execution strategies, order lifecycle management
     Examples: Alpaca integration, smart execution algorithms, order validation, fill monitoring

4. orchestration/
     Purpose: Cross-module workflow coordination and business process orchestration
     Contains: Workflow orchestrators that coordinate between business units
     Examples: SignalOrchestrator, TradingOrchestrator, StrategyOrchestrator, PortfolioOrchestrator

5. shared/
     Purpose: DTOs, utilities, logging, cross-cutting concerns, common value objects
     Contains: Data transfer objects, utility functions, logging setup, shared types
     Examples: Money/Decimal types, Symbol classes, DTOs, configuration, error handling

-------------------------------------------------------------------------------
EVENT-DRIVEN ARCHITECTURE (EDA)
-------------------------------------------------------------------------------
The system coordinates work using an event-driven approach. Follow these rules when
adding or modifying evented workflows:

- Event contracts live in shared/events/ (envelopes, factories) and shared/schemas/ (validation).
- Orchestrators in orchestration/ compose cross-module workflows by publishing and
     subscribing to events. Orchestrators remain stateless and deterministic.
- Handlers belong to the responsible module but communicate only via shared DTOs/events.
     Example: strategy_v2 produces StrategySignal events; portfolio_v2 consumes them to produce
     RebalancePlan events; execution_v2 consumes plans to produce ExecutionResult events.
- Delivery is at-least-once. All consumers MUST be idempotent and tolerate duplicates and reordering.
- No hidden side effects: persist state only within the owning module. Cross-module state flows
     through explicit events/DTOs.
- Use correlation IDs for end-to-end traceability. Include causation IDs when chaining events.
- Version events with schema_version and additive, backward-compatible changes.
- Prefer immutable, append-only payloads and explicit status transitions.
- Do not import between business modules; use events to cross boundaries.

Required event envelope fields (defined in shared/events):
- event_id: UUID4
- type: string (see naming)
- timestamp: ISO-8601 UTC
- correlation_id: UUID4 (stable across a workflow)
- causation_id: UUID4 (the triggering event_id, when applicable)
- source: module identifier (e.g., "strategy_v2.signals")
- schema_version: integer

Event type naming convention:
- domain.action.phase.v<number>
     Examples: "strategy.signal.generated.v1", "portfolio.rebalance.planned.v1",
     "execution.order.submitted.v1", "execution.order.settled.v1".

Retries, DLQs, and ordering:
- Assume retries may occur and order is not guaranteed; implement idempotent upserts or
     sequence checks keyed by correlation_id + business keys (e.g., symbol, plan_id).
- On poison messages, raise typed errors; orchestration will route to DLQ handlers where applicable.

Observability for events:
- Log with structured context: module, event_id, correlation_id, type, schema_version.
- Keep logs concise and privacy-aware; no secrets in payloads or logs.

MODULE DEPENDENCY RULES:
 - strategy_v2/ → shared/ (allowed)
 - portfolio_v2/ → shared/ (allowed)
 - execution_v2/ → shared/ (allowed)
 - orchestration/ → strategy_v2/, portfolio_v2/, execution_v2/, shared/ (allowed)
 - strategy_v2/ → portfolio_v2/ (FORBIDDEN)
 - strategy_v2/ → execution_v2/ (FORBIDDEN)
 - portfolio_v2/ → execution_v2/ (FORBIDDEN)
 - shared/ → any other module (FORBIDDEN - shared must be leaf dependencies)

IMPORT HYGIENE & API BOUNDARIES:
 - Use module APIs, not deep subfolders. Import from strategy_v2.indicators, not strategy_v2.indicators.technical.sma
 - Each module should expose a clean public API through __init__.py
 - Avoid importing private/internal implementations from other modules
 - Cross-module communication should use well-defined interfaces and DTOs

CODE PLACEMENT EXAMPLES:
 - New indicator (SMA, RSI, etc.) → strategy_v2/indicators/
 - New strategy engine → strategy_v2/engines/
 - New broker connector → execution_v2/brokers/
 - Portfolio rebalancing logic → portfolio_v2/rebalancing/
 - New position tracker → portfolio_v2/positions/
 - Order execution strategy → execution_v2/strategies/
 - Workflow orchestrator → orchestration/
 - Cross-module coordination logic → orchestration/
 - Event contracts/envelopes → shared/events/
 - Event schema validation → shared/schemas/
 - Common DTO classes → shared/dto/
 - Utility functions → shared/utils/
 - Logging setup → shared/logging/
 - Configuration types → shared/config/

TARGET MODULE STRUCTURE:
strategy_v2/
├── indicators/              # Technical indicators, market signals
├── engines/                 # Strategy implementations (Nuclear, TECL, etc.)
├── dsl/                     # Domain-specific language for strategy definition
└── data/                    # Data access and management

portfolio_v2/
├── positions/               # Position tracking and management
├── rebalancing/             # Rebalancing algorithms and logic
├── valuation/               # Portfolio valuation and metrics
└── risk/                    # Risk management and constraints

execution_v2/
├── brokers/                 # Broker API integrations (Alpaca, etc.)
├── orders/                  # Order management and lifecycle
├── strategies/              # Smart execution strategies
└── core/                    # Core execution logic and account management

orchestration/
├── signal_orchestrator.py   # Signal analysis workflow coordination
├── event_driven_orchestrator.py # Event bus integration and dispatching
├── trading_orchestrator.py  # Trading execution workflow coordination
├── strategy_orchestrator.py # Multi-strategy coordination and conflict resolution
└── portfolio_orchestrator.py # Portfolio rebalancing workflow coordination

shared/
├── dto/                     # Data transfer objects
├── events/                  # Event envelopes, types, factories
├── types/                   # Common value objects (Money, Symbol, etc.)
├── utils/                   # Utility functions and helpers
├── config/                  # Configuration management
└── logging/                 # Logging setup and utilities

-------------------------------------------------------------------------------
TYPING & CODE QUALITY
-------------------------------------------------------------------------------
 - 100% mypy compliance: disallow_untyped_defs, disallow_incomplete_defs.
 - Every function annotated (parameters + explicit return). Use None explicitly.
 - Money & quantities: Decimal only (no float arithmetic for financial values).
 - Non-financial float comparisons: math.isclose or explicit epsilon helpers.
 - Prefer Protocol over ABC for interface definitions.
 - Each module should be internally cohesive with minimal external dependencies.
 - Event payloads and handlers must be fully typed; envelope fields must be explicit.

DTO & MESSAGE NAMING CONVENTIONS:
 - Domain types: Plain nouns (Order, Position, Signal, Portfolio)
 - Cross-module DTOs: Descriptive names with context (StrategySignalDTO, PortfolioStateDTO)
 - Request/Response types: Clear suffixes (CreateOrderRequest, ExecutionResponse)
 - Configuration types: Config suffix (StrategyConfig, ExecutionConfig)
 - Prefer semantic names over generic *Dto

INTER-MODULE COMMUNICATION:
 - Modules communicate via well-defined DTOs and interfaces
 - Strategy module generates signals consumed by portfolio module
 - Portfolio module creates execution plans consumed by execution module
 - All communication through explicit contracts, not shared state
 - Use correlation IDs for traceability across module boundaries
 - Events are the primary cross-module integration mechanism, coordinated by orchestrators.
 - No direct imports across business modules; communicate via shared DTOs/events only.

ERROR HANDLING:
 - Never fail silently. Raise typed exceptions with module context.
 - Module-specific error types: StrategyError, PortfolioError, ExecutionError, ConfigurationError
 - Include module="strategy.indicators.sma" in error metadata for traceability.
 - Central error handler categorizes by module and severity.
 - Event handling errors must include event metadata (event_id, type, correlation_id) for triage.
 - Consumers must avoid partial commits; prefer atomic write-or-fail for idempotent processing.

CONCURRENCY & STATE MANAGEMENT:
 - Avoid shared mutable state between modules
 - Pass immutable data structures and DTOs between modules
 - Each module manages its own internal state
 - Recompute derived values instead of caching cross-module state
 - Event handlers must be safe for concurrent execution.
 - Use deterministic keys for deduplication where necessary (e.g., plan_id, order_id).

IMPORT RULES (TO BE ENFORCED VIA import-linter):
 - Module isolation: strategy_v2/, portfolio_v2/, execution_v2/ cannot import from each other
 - Shared dependencies: All modules may import from shared/ only
 - Deep imports forbidden: Use public module APIs, not internal submodules
 - Legacy cleanup: Never import from deprecated services/ or utils/ directories
     - Example valid imports:
   * from shared.types import Money, Symbol
      * from strategy_v2.indicators import MovingAverage
      * from portfolio_v2.positions import PositionTracker
      * from execution_v2.brokers import AlpacaConnector
     - Example forbidden imports:
      * from strategy_v2.internal.calculations import sma  # Deep import
      * from portfolio_v2 import rebalance_portfolio # Cross-module import
   * from services.legacy_service import helper # Legacy import

LEGACY & MIGRATION:
 - Mark temporary shims with module docstring Status: legacy and schedule removal.
 - Do not extend legacy modules; create current replacements in proper modules.
 - When touching deprecated services/ or utils/ code, migrate to appropriate module first.

PERFORMANCE & OBSERVABILITY:
 - Functions should be deterministic and minimize side effects within modules.
 - Include structured logging with module context (module="strategy.indicators").
 - Focus on clarity with O(1)/O(n) reasoning documented when non-trivial.
 - Emit concise, structured logs at event boundaries. Include correlation_id and event_id.
 - Prefer constant-time idempotency checks using properly indexed keys.

SECURITY & CONFIGURATION:
 - All secrets via environment variables or secure configuration management.
 - No hard-coded API keys or credentials in any module.
 - Configuration should be centralized in shared/config/.
 - Do not log credentials or PII; scrub sensitive fields before logging or emitting events.
 - Use environment-aware credential loading (local .env for paper; cloud secrets for live).

STYLE SUMMARY:
 - Line length 100. Ruff formatter enforced.
 - Import order auto (ruff). No unused imports.
 - Use Decimal quantize only for formatting, not for internal math unless rounding policy documented.

PROHIBITED PATTERNS:
 - Cross-module direct imports (strategy → portfolio, portfolio → execution, etc.).
 - Logic mixed between modules without clear interfaces.
 - Silent except: or broad except Exception without re-raise via typed error.
 - Adding new code to legacy services/ or utils/ directories.
 - Float equality checks for financial calculations.
 - Non-idempotent event handlers or handlers without correlation_id propagation.
 - Cross-module synchronous calls that bypass orchestrators and events.

RECOMMENDED WORKFLOW:
 1. Identify which module the new code belongs to based on responsibility.
 2. Define interfaces and DTOs for any cross-module communication.
 3. Implement functionality within the appropriate module.
 4. Create clean public APIs through module __init__.py files.
 5. Use shared/ for common utilities, types, and cross-cutting concerns.
 6. Test module boundaries and ensure proper isolation.
 7. Validate event schemas and idempotency paths with representative payloads.

FLOAT & NUMERIC POLICY:
 - Money/quantity/risk metrics → Decimal.
 - Statistical ratios → float permitted but compare with tolerance via helpers.

MODULE-SPECIFIC GUIDELINES:

strategy/:
 - Focus on signal generation and analysis logic
 - Should be stateless where possible
 - Communicate results via clear signal DTOs
 - No direct market access (use data providers via interfaces)

portfolio/:
 - Manages all portfolio state and positions
 - Handles rebalancing calculations and constraints
 - Provides portfolio analytics and reporting
 - Never directly places orders (delegates to execution)

execution/:
 - Handles all broker integrations and order placement
 - Implements smart execution algorithms
 - Manages order lifecycle and error handling
 - Should be the only module that touches external trading APIs

shared/:
 - Provides common types and utilities used across modules
 - Should have no dependencies on other modules
 - Keep minimal and focused on truly shared concerns
 - Include logging, configuration, DTOs, and base types

BUSINESS UNIT DOCSTRINGS:
Example top-of-file docstring for each module:

strategy module:
"""Business Unit: strategy | Status: current

Signal generation and indicator calculation for trading strategies.
"""

portfolio module:
"""Business Unit: portfolio | Status: current

Portfolio state management and rebalancing logic.
"""

execution module:
"""Business Unit: execution | Status: current

Broker API integrations and order placement.
"""

orchestration module:
"""Business Unit: orchestration | Status: current

Cross-module workflow coordination and business process orchestration.
"""

Event-driven orchestration specifics:
- Orchestrators translate between DTOs and events but do not own business state.
- Orchestrators must be resilient: deduplicate work, propagate correlation IDs, and prefer
     eventual consistency over synchronous coupling.

shared module:
"""Business Unit: shared | Status: current

DTOs, utilities, and cross-cutting concerns.
"""

LINT & TYPE COMMANDS (always with poetry run):
 - make format
 - make lint
 - poetry run mypy the_alchemiser/

DEPLOYMENT:
 - Lambda entrypoint remains top-level for backward compatibility.
 - Consider gradual migration to module-based entry points.

EVENT INFRASTRUCTURE (REFERENCE):
- Local development: simple in-process event dispatch or lightweight queue; keep behaviors
     equivalent to cloud semantics (at-least-once, possible reordering).
- Cloud: AWS EventBridge/SQS/Lambda commonly used. Use retries with backoff and DLQs configured
     per handler. Do not encode provider-specific logic into business modules.

FINAL NOTE:
This document supersedes older references to DDD bounded contexts and layered architecture.
All new code must align with the five-module structure and dependency rules outlined above.
"""

# Extended Typing Architecture Rules (Authoritative)

The following rules extend and clarify the TYPING & CODE QUALITY section. They are binding for all
changes and supersede conflicting older patterns.

## Problem Statement

Mixed usage of data types across layers creates type confusion and protocol violations. The same
logical data must not appear alternately as external SDK objects, ad-hoc dicts, and `Any`.

## Core Architectural Rules

1) Layer-Specific Type Ownership

     - External SDK: e.g., `TradeAccount`, `Order`, `Position` (SDK boundary only)
     - Execution layer: `AccountInfoDTO`, `ExecutionResultDTO` (domain representations)
     - Strategy layer: `StrategySignalDTO`
     - Portfolio layer: `PortfolioStateDTO`, `RebalancePlanDTO`
     - Shared/protocol: Cross-module DTOs and Protocols (authoritative interfaces)
     - Orchestration: Consumes/produces DTOs/events only (no SDK objects, no raw dicts)
     - Serialization: Use `dict[str, ...]` strictly at IO boundaries via Pydantic v2 methods

2) Conversion Points (Pydantic v2)

     - SDK → Domain DTO at adapters only
     - Domain DTO → dict via `model_dump()` for transport/logging
     - dict → Domain DTO via `model_validate()` for input
     - Never let raw dicts flow through business logic

3) Naming Conventions

     - Private SDK accessors: `_get_*_raw() -> Any  # type: ignore[misc]`
     - Primary business interface: typed DTO return, e.g., `get_account() -> AccountInfoDTO | None`
     - Optional serialization helpers: `get_*_dict() -> dict[str, Any] | None`

## ANN401 Policy (No unbounded Any)

- Prohibited:
  - Business logic parameters/returns typed as `Any`
  - DTO fields as plain `Any`
  - Protocol methods with `Any` parameters

- Acceptable with `# type: ignore[misc]` and comment:
  - External SDK client/objects at adapter boundaries
  - Generic decorator internals
  - DTO `.metadata` fields used strictly for JSON passthrough

## Replacement Patterns

- Use concrete unions instead of `Any` for inputs.
- Use `TypeVar`/`ParamSpec` for reusable utilities.
- Use Protocols to express behavioral interfaces instead of `Any`.
- Prefer specific dict value unions over `dict[str, Any]` where dicts are required.

## Implementation Strategy (Pydantic v2)

1) Create DTOs in `shared/dto/` with `ConfigDict(strict=True, frozen=True, validate_assignment=True)`
     and typed Decimal fields for money/quantities.

2) Update Protocols in `shared/protocols/` to return DTOs, not dicts.

3) Implement adapters (e.g., Alpaca manager) to convert SDK → DTO at the edge; expose legacy
     `*_dict()` only as temporary shims during migration.

4) Migrate callers to consume DTOs incrementally, then remove dict-based methods.

## Migration Order (Priority)

- Phase 1 (Quick wins): remove `| Any` unions, fix CLI param/return types, tighten utils.
- Phase 2 (SDK integration): broker/data adapters return DTOs with proper types.
- Phase 3 (Business logic): strategy/portfolio/execution consume DTOs, no raw dict usage.
- Phase 4 (Infrastructure): generics for helpers, decorators with precise Parameter specs.

## Numeric & Money Policy

- Decimal for all money/quantities; no float arithmetic for finance.
- Non-financial float comparisons via `math.isclose` or epsilon helpers only.

## Enforcement

- MyPy strict: disallow_untyped_defs, disallow_incomplete_defs.
- ANN401 violations must be resolved per above; if a temporary exception is unavoidable at an SDK
  boundary, include `# type: ignore[misc]` with a justification comment and a migration TODO.
