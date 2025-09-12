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
5. Keep BUSINESS_UNITS_REPORT.md consistent when adding/removing files.
6. No legacy fallbacks: never reintroduce removed legacy providers or silent downgrade paths.

-------------------------------------------------------------------------------
MODULAR ARCHITECTURE: FIVE TOP-LEVEL MODULES
-------------------------------------------------------------------------------
The codebase is organized around five main modules with clear responsibilities
and controlled dependencies:

1. strategy/
     Purpose: Signal generation, indicator calculation, ML models, regime detection
     Contains: Strategy engines, technical indicators, ML pipelines, signal processors
     Examples: Nuclear strategy, TECL strategy, market regime detection, volatility indicators
     
2. portfolio/
     Purpose: Portfolio state management, sizing, rebalancing logic, risk management
     Contains: Portfolio valuation, position tracking, allocation calculations, rebalancing algorithms
     Examples: Portfolio rebalancer, position manager, risk constraints, allocation optimizer
     
3. execution/
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

MODULE DEPENDENCY RULES:
 - strategy/ → shared/ (allowed)
 - portfolio/ → shared/ (allowed)  
 - execution/ → shared/ (allowed)
 - orchestration/ → strategy/, portfolio/, execution/, shared/ (allowed)
 - strategy/ → portfolio/ (FORBIDDEN)
 - strategy/ → execution/ (FORBIDDEN)
 - portfolio/ → execution/ (FORBIDDEN)
 - shared/ → any other module (FORBIDDEN - shared must be leaf dependencies)

IMPORT HYGIENE & API BOUNDARIES:
 - Use module APIs, not deep subfolders. Import from strategy.indicators, not strategy.indicators.technical.sma
 - Each module should expose a clean public API through __init__.py  
 - Avoid importing private/internal implementations from other modules
 - Cross-module communication should use well-defined interfaces and DTOs

CODE PLACEMENT EXAMPLES:
 - New indicator (SMA, RSI, etc.) → strategy/indicators/
 - New strategy engine → strategy/engines/  
 - New broker connector → execution/brokers/
 - Portfolio rebalancing logic → portfolio/rebalancing/
 - New position tracker → portfolio/positions/
 - Order execution strategy → execution/strategies/
 - Workflow orchestrator → orchestration/
 - Cross-module coordination logic → orchestration/
 - Common DTO classes → shared/dto/
 - Utility functions → shared/utils/
 - Logging setup → shared/logging/
 - Configuration types → shared/config/

TARGET MODULE STRUCTURE:
strategy/
├── indicators/              # Technical indicators, market signals
├── engines/                 # Strategy implementations (Nuclear, TECL, etc.)
├── dsl/                     # Domain-specific language for strategy definition
└── data/                    # Data access and management

portfolio/  
├── positions/               # Position tracking and management
├── rebalancing/             # Rebalancing algorithms and logic
├── valuation/               # Portfolio valuation and metrics
└── risk/                    # Risk management and constraints

execution/
├── brokers/                 # Broker API integrations (Alpaca, etc.)
├── orders/                  # Order management and lifecycle
├── strategies/              # Smart execution strategies  
└── core/                    # Core execution logic and account management

orchestration/
├── signal_orchestrator.py   # Signal analysis workflow coordination
├── trading_orchestrator.py  # Trading execution workflow coordination
├── strategy_orchestrator.py # Multi-strategy coordination and conflict resolution
└── portfolio_orchestrator.py # Portfolio rebalancing workflow coordination

shared/
├── dto/                     # Data transfer objects
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

ERROR HANDLING:
 - Never fail silently. Raise typed exceptions with module context.
 - Module-specific error types: StrategyError, PortfolioError, ExecutionError, ConfigurationError
 - Include module="strategy.indicators.sma" in error metadata for traceability.
 - Central error handler categorizes by module and severity.

CONCURRENCY & STATE MANAGEMENT:
 - Avoid shared mutable state between modules
 - Pass immutable data structures and DTOs between modules
 - Each module manages its own internal state
 - Recompute derived values instead of caching cross-module state

IMPORT RULES (TO BE ENFORCED VIA import-linter):
 - Module isolation: strategy/, portfolio/, execution/ cannot import from each other
 - Shared dependencies: All modules may import from shared/ only
 - Deep imports forbidden: Use public module APIs, not internal submodules
 - Legacy cleanup: Never import from deprecated services/ or utils/ directories
 - Example valid imports:
   * from shared.types import Money, Symbol
   * from strategy.indicators import MovingAverage
   * from portfolio.positions import PositionTracker
   * from execution.brokers import AlpacaConnector
 - Example forbidden imports:
   * from strategy.internal.calculations import sma  # Deep import
   * from portfolio import rebalance_portfolio # Cross-module import 
   * from services.legacy_service import helper # Legacy import

LEGACY & MIGRATION:
 - Mark temporary shims with module docstring Status: legacy and schedule removal.
 - Do not extend legacy modules; create current replacements in proper modules.
 - When touching deprecated services/ or utils/ code, migrate to appropriate module first.

PERFORMANCE & OBSERVABILITY:
 - Functions should be deterministic and minimize side effects within modules.
 - Include structured logging with module context (module="strategy.indicators").
 - Focus on clarity with O(1)/O(n) reasoning documented when non-trivial.

SECURITY & CONFIGURATION:
 - All secrets via environment variables or secure configuration management.
 - No hard-coded API keys or credentials in any module.
 - Configuration should be centralized in shared/config/.

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

RECOMMENDED WORKFLOW:
 1. Identify which module the new code belongs to based on responsibility.
 2. Define interfaces and DTOs for any cross-module communication.
 3. Implement functionality within the appropriate module.
 4. Create clean public APIs through module __init__.py files.
 5. Use shared/ for common utilities, types, and cross-cutting concerns.
 6. Test module boundaries and ensure proper isolation.

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

FINAL NOTE:
This document supersedes older references to DDD bounded contexts and layered architecture. 
All new code must align with the four-module structure and dependency rules outlined above.
"""
