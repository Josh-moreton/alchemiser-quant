# The Alchemiser

Internal notes on how the trading engine is put together and how the pieces interact.

## Business Unit Classification

Every source file begins with a module-level docstring that declares:

- **Business Unit** – one of
  - strategy & signal generation
  - portfolio assessment & management
  - order execution/placement
  - utilities
- **Status** – `current` or `legacy`

See `BUSINESS_UNITS_REPORT.md` for the complete, auto-generated inventory.
Contributors must keep these docstrings accurate when files are created or
significantly changed.

## System Architecture

### Layered DDD Architecture (Domain-Driven Design)

- **Domain Layer** (`the_alchemiser/domain/`): Pure business logic, strategy engines (Nuclear, TECL, KLM), interfaces, and domain types
- **Services Layer** (`the_alchemiser/services/`): Business logic orchestration and enhanced services facade
- **Infrastructure Layer** (`the_alchemiser/infrastructure/`): External integrations (Alpaca API, AWS services, WebSocket streaming)
- **Application Layer** (`the_alchemiser/application/`): Trading orchestration, smart execution, portfolio rebalancing
- **Interface Layer** (`the_alchemiser/interface/`): Modular CLI with clean separation of concerns

## Typed Domain System (V2)

We’re migrating to a strongly-typed, framework-free domain model with incremental rollout behind a feature flag. The goal is >95% precise typing, clearer boundaries, and safer refactors.

### Key Concepts
- Shared Kernel Value Objects (immutable): `Money`, `Percentage`, `Identifier` under `the_alchemiser/domain/shared_kernel/value_objects/`
- Trading Domain: Entities `Order`, `Position`, `Account`; Value Objects `Symbol`, `Quantity`, `OrderStatus` under `the_alchemiser/domain/trading/`
- Strategies Domain: `StrategySignal`, `Confidence`, `Alert` under `the_alchemiser/domain/strategies/value_objects/`
- Anti‑corruption Mappers: `the_alchemiser/application/mapping/` handles DTO ↔ Domain ↔ Infra translations
- Infra Adapters: Alpaca requests/responses mapped in `the_alchemiser/infrastructure/`; domain stays pure


### What's Implemented
- Portfolio value parity via `TradingServiceManager`
- Enriched positions summary and CLI rendering (status)
- Enriched account summary and CLI status integration
- Order placement (market and limit): typed request build + domain `Order` mapping
- Open orders retrieval mapped to domain `Order`
- StrategySignal typed mapping through Execution and CLI

### Contributor Notes
- Domain purity: no framework imports (no Pydantic, requests, logging) in `the_alchemiser/domain/**`
- Use `@dataclass(frozen=True)` for value objects; entities encapsulate behavior
- Keep Pydantic DTOs in `the_alchemiser/interfaces/schemas/`
- Place all boundary mapping in `the_alchemiser/application/mapping/`
- Use `Decimal` for all financial/quantity values; normalize in mappers
- Prefer `Protocol` for repository/service interfaces under `domain/**/protocols/`; implemented in `infrastructure/` or `services/`

### Validation for the Typed Path
- Validate behavior consistency between flag ON vs OFF where applicable
- Use runtime validation with Pydantic at system boundaries; mock external APIs for development
- CI runs mypy across the codebase; value objects and entities must be fully typed

### Entry Point and CLI Architecture

- **Main Entry Point** (`main.py`): Clean, focused entry point (180 lines) with `TradingSystem` orchestrator
- **Signal Analyzer** (`interface/cli/signal_analyzer.py`): Dedicated signal analysis and display logic
- **Trading Executor** (`interface/cli/trading_executor.py`): Dedicated trading execution with comprehensive error handling
- **Dependency Injection**: Default DI mode with `--legacy` flag support for traditional initialization

### Configuration and Settings

- `the_alchemiser.infrastructure.config` uses Pydantic settings models to load configuration from environment variables and `.env` files.

### Data Layer

- `AlpacaManager` and `StrategyMarketDataService` provide unified Alpaca REST and WebSocket access for account details, quotes and historical data.

### Strategy Layer

- Strategy engines live in `the_alchemiser.domain.strategies`.
- `MultiStrategyManager` instantiates enabled strategies and keeps per‑strategy position tracking and allocation.

### Execution Layer

- `TradingEngine` orchestrates the full trading cycle: it gathers strategy signals, invokes `PortfolioRebalancer` to compute target allocations and delegates order placement to `SmartExecution`.
- `ExecutionManager` drives multi‑strategy execution; enhanced services provide unified access to trading operations.

### Error Handling and Monitoring

- **Enhanced Error Handler** (`the_alchemiser.core.error_handler`): Comprehensive error categorization, reporting, and email notification system
- **Error Categories**: CRITICAL, TRADING, DATA, STRATEGY, CONFIGURATION, NOTIFICATION, WARNING
- **Automatic Email Alerts**: Detailed error reports with specific remediation actions sent via email
- **Dead Letter Queue**: Failed Lambda executions captured in SQS for investigation
- **Reduced Retry Policy**: EventBridge scheduler limited to 1 retry to prevent cascade failures
- **Silent Failure Prevention**: All critical operations now raise proper exceptions instead of failing silently

### Tracking and Reporting

- `the_alchemiser.tracking` stores fills, positions and P&L history, while reporting helpers summarise runs for the CLI and email output.

### Command Line Interface

- `the_alchemiser.cli` is built with Typer and provides the `alchemiser` command (`bot`, `trade`, `status`, `deploy`, etc.).

## Execution Flow

1. `load_settings()` builds a typed `Settings` object.
2. `AlpacaManager` and `TradingServiceManager` connect to Alpaca using those settings.
3. `MultiStrategyManager` runs each strategy and merges their desired portfolios.
4. `TradingEngine` uses `PortfolioRebalancer` to derive required trades.
# The Alchemiser

Modern quantitative trading platform refactored around explicit Domain‑Driven Design (DDD) with THREE bounded contexts: Strategy, Portfolio, and Execution. Each context is internally layered (Domain, Application, Infrastructure, Interfaces) and communicates only through stable, typed DTO contracts. Generic `services/` and grab‑bag `utils/` packages are being retired – their code is re‑homed into the correct context and layer. Architectural constraints are enforced via typing, lint rules, and import discipline.

---
## High-Level Goals
1. Strong modularity: independent evolution of Strategy, Portfolio, and Execution.
2. Explicit boundaries: no cross-context domain imports; only published Application DTOs.
3. Deterministic domain core: pure, framework-free domain code (entities, value objects, policies).
4. Testability & refactor safety: strict mypy + value objects for all monetary & quantity calculations.
5. Operational resilience: typed errors, categorized handling, observable execution paths.

---
## Bounded Contexts Overview

### 1. Strategy Context
Purpose: Generate and score trading signals from market data, indicators, and regime detection.

Domain: Strategy engines (Nuclear, TECL, KLM), value objects (StrategySignal, Confidence, Alert), allocation policies.
Application: Multi-strategy orchestration, signal normalization, ranking, conflict resolution, DTO mapping.
Infrastructure: Market data gateways (Alpaca REST/WebSocket adapters), indicator caches, computed feature stores.
Interfaces: CLI signal views, validation commands, potential HTTP endpoints for signal export.

Bounded Outputs: StrategySignalResult, StrategyAttributionView.
Inputs (from Portfolio): Requested universe (symbols), risk parameters (max allocation per symbol/group).

### 2. Portfolio Context
Purpose: Represent current holdings, valuation, risk analytics, and compute target allocations.

Domain: Account, Position, Portfolio Aggregate, Policies (cash reserve, exposure limits), Value Objects (Money, Percentage, Symbol, Quantity).
Application: Rebalancing (ComputeTargetAllocationsCommand), drift analysis, performance aggregation, mapping to/from broker DTOs.
Infrastructure: Account & position repository adapters (Alpaca), historical equity/time-series fetchers, persistence layers.
Interfaces: Portfolio status CLI, P&L dashboards, email/report generation.

Bounded Outputs: TargetAllocationResult, PortfolioValuationView.
Inputs (from Strategy): StrategySignalResult feed.
Outputs (to Execution): ExecutionPlanCommand (desired trades / adjustments).

### 3. Execution Context
Purpose: Validate, route, and monitor orders to achieve target portfolio adjustments with minimal slippage and risk.

Domain: Order, OrderIntent, ExecutionPolicy, OrderStatus, SlippageModel, FillEvent.
Application: Smart execution pipeline (PlaceOrderCommand, ExecutePlanCommand), order sizing, batching, cancellation, retry logic.
Infrastructure: Broker order adapters, WebSocket listeners, fill/quote stream integration, backoff and rate-limit controls.
Interfaces: Trading CLI, deployment (Lambda handler), execution monitoring views.

Bounded Outputs: OrderExecutionResult, FillStreamEvent.
Inputs (from Portfolio): ExecutionPlanCommand specifying desired adjustments.

### Shared Kernel (Minimal)
Immutable primitives used across all contexts: Money, Percentage, Identifier, Symbol, basic time utilities. Zero dependencies back into contexts.

---
## Layered Structure (Per Context)
Each context replicates a consistent internal layering model:

domain/        Pure business objects & policies (no I/O, no frameworks)
application/   Use cases (Commands, Queries, Results), orchestration, mapping, validation
infrastructure/Adapters & gateways (broker APIs, data feeds, persistence, messaging)
interfaces/    CLI, presentation, external surface schemas (Pydantic), email views

Cross-context communication: application → application via explicit DTOs (no domain leakage).

---
## Architectural Invariants
1. Domain purity: no `requests`, `pydantic`, `logging`, network calls, or file I/O.
2. Money & quantities: `Decimal` only; rounding localized to infrastructure or presentation.
3. No direct cross-context domain imports – use exported DTO contracts.
4. Anti-corruption mapping lives strictly in each context's application.mapping module.
5. Infrastructure implements Domain-declared Protocols; Domain never imports infrastructure classes.
6. Interfaces layer: formatting & transport only – no business logic.
7. Errors are typed and categorized; no silent fallback to legacy implementations.

---
## Business Unit Docstrings
Every source file starts with:
"""Business Unit: <strategy & signal generation | portfolio assessment & management | order execution/placement | utilities> | Status: current

Short purpose sentence.
"""
Legacy modules must be marked `Status: legacy` and scheduled for removal.

See `BUSINESS_UNITS_REPORT.md` for the generated inventory.

---
## Data & Flow Summary
1. Strategy Context produces normalized StrategySignalResult (universe weight intentions + rationale).
2. Portfolio Context ingests StrategySignalResult, current holdings, risk policies → emits TargetAllocationResult.
3. Portfolio Application converts target vs current into ExecutionPlanCommand.
4. Execution Context validates plan, builds OrderIntents, applies ExecutionPolicy, routes orders via broker adapter.
5. Fills and status events feed back (for now) into Portfolio valuation and Strategy attribution through published Result DTOs.

---
## Key Use Case Contracts (Illustrative Names)
Strategy:
 - GenerateSignalsCommand -> StrategySignalResult
 - ListStrategiesQuery -> StrategyCatalogView

Portfolio:
 - ComputeTargetAllocationsCommand -> TargetAllocationResult
 - GetPortfolioValuationQuery -> PortfolioValuationView

Execution:
 - ExecutePlanCommand (from Portfolio) -> OrderExecutionResult
 - PlaceOrderCommand -> SingleOrderResult

Shared Event (Execution -> Portfolio/Strategy):
 - TradeExecutedEventV1 (symbol, qty, price, strategy_ref, correlation_id)

---
## Typing & DTO Guidelines
Domain: dataclasses / frozen value objects.
Application I/O: Pydantic models or TypedDicts suffixed with Command, Query, Result.
Interfaces: Request / Response / View models.
Events: Event suffix + version when externally published.

Avoid ambiguous duplicates; if a clash occurs, introduce context-specific naming or suffix (e.g., StrategyOrderIntent vs OrderIntent if required).

---
## Error Handling
Categories align to contexts for triage: STRATEGY, PORTFOLIO, EXECUTION, DATA, CONFIGURATION, NOTIFICATION, WARNING, CRITICAL.
Use central error handler to record context metadata: component="portfolio.application.rebalancer.ComputeTargetAllocationsHandler".
Never catch Exception without re-raising a typed domain/application exception.

---
## Example Workflow (Happy Path)
1. CLI `alchemiser signal` invokes Strategy Application GenerateSignalsCommand.
2. CLI `alchemiser trade` orchestrates: GenerateSignals -> ComputeTargetAllocations -> ExecutePlan.
3. Execution monitors fills; emits TradeExecutedEventV1 consumed (future) by Portfolio for reconciliation.

---
## Repository (In-Progress Target Layout)
```
the_alchemiser/
    shared_kernel/
        value_objects/               # Money, Percentage, Identifier, Symbol
    strategy/
        domain/                      # Engines, signals, policies
        application/                 # Orchestration, mapping, commands
        infrastructure/              # Market data gateways
        interfaces/                  # CLI signal views
    portfolio/
        domain/                      # Account, Position, Portfolio, risk policies
        application/                 # Rebalancing, valuation
        infrastructure/              # Account/position adapters
        interfaces/                  # Status & reporting views
    execution/
        domain/                      # Order, OrderIntent, ExecutionPolicy
        application/                 # Smart execution commands
        infrastructure/              # Broker APIs, WebSocket listeners
        interfaces/                  # Trade CLI, deployment
    main.py
    lambda_handler.py
```

Retired / To Remove: legacy `services/`, broad `utils/` modules (in flight – avoid adding new code there).

---
## Development Standards
Environment: Use Poetry ALWAYS (no bare `python`).
Formatting & Lint: `make format` (ruff format + fix). Line length 100.
Type Checking: `poetry run mypy the_alchemiser/` must pass cleanly.
Money/Quantity: `Decimal`; never compare floats directly.
Cross-Context DTO Imports: only from another context's application layer (or shared_kernel primitives).
No logic in __init__.py beyond safe re-exports.

---
## Quick Start
```bash
poetry install
poetry run mypy the_alchemiser/
poetry run alchemiser signal      # Generate and display strategy signals
poetry run alchemiser trade       # Compute allocations + execute (paper by default)
poetry run alchemiser status      # Portfolio & P&L view
```

Optional environment variables (Pydantic settings resolve these):
```
ALPACA_API_KEY=...
ALPACA_SECRET_KEY=...
PAPER_TRADING=true
EMAIL_RECIPIENT=you@example.com
```

---
## Contributing Within the New Model
1. Decide the owning bounded context (e.g., new risk metric -> Portfolio Domain).
2. Define/extend value objects & policies (pure domain).
3. Declare Protocols in domain.protocols for external dependencies.
4. Implement adapters in infrastructure implementing those Protocols.
5. Expose use cases via application Command/Query handlers.
6. Expose DTOs to other contexts via application.results (only what is stable & necessary).
7. Update CLI / Interfaces to consume new application outputs.
8. Add Business Unit docstring & update `BUSINESS_UNITS_REPORT.md` generator if needed.

---
## Migration Notes (Epic #375)
The current epic transitions from a monolithic service façade to context-focused layers. Pending tasks typically involve:
 - Moving residual market data helpers into Strategy Infrastructure.
 - Splitting combined order/portfolio logic: ensure sizing lives in Portfolio, execution tactics in Execution.
 - Replacing any remaining direct broker calls inside Strategy with Protocol-driven abstractions.
 - Pruning deprecated legacy wrappers flagged `Status: legacy`.

---
## Observability & Operations
 - Execution infrastructure logs order lifecycle with correlation IDs linking back to StrategySignal.
 - Portfolio valuation snapshots emitted before/after execution cycles for drift auditing.
 - Error emails include context category + remediation suggestions.

---
## Style & Safety Summary
| Concern          | Rule |
|------------------|------|
| Float comparison | Disallowed (use Decimal or tolerance) |
| Cross-domain import | Only via application DTOs |
| Domain side-effects | Forbidden |
| Money math rounding | Defer to infrastructure/presentation |
| Error swallowing | Forbidden |

---
## Roadmap (Selected Next Steps)
 - Event propagation channel (Execution -> Portfolio) for asynchronous fill reconciliation.
 - Strategy feature store versioning in Strategy Infrastructure.
 - Portfolio risk scenario engine (stress & factor exposures) in Portfolio Domain.
 - Execution adaptive slippage model with feedback loop.

---
## License / Internal Use
Internal system – distribution restricted. Treat credentials & broker access with care; never commit secrets.

---
## Contact
For architectural questions: open a discussion referencing Epic #375.

Happy alchemising.

- Dashboard data updated in real-time

## Troubleshooting Guide for AI Agents

### Common Error Patterns and Solutions

1. **StrategyExecutionError in Volatility Calculations**
   - **Location**: `core/trading/strategy_engine.py`
   - **Cause**: Missing volatility data for bear strategy allocation
   - **Solution**: Check data provider connectivity and symbol availability
   - **Fallback**: System uses conservative equal-weight allocation (60/40)

2. **IndicatorCalculationError in Technical Analysis**
   - **Location**: `core/trading/strategy_engine.py._get_14_day_volatility()`
   - **Cause**: Insufficient price history or invalid indicators
   - **Solution**: Verify data availability and indicator calculation logic
   - **Fallback**: Uses RSI-based estimates or fixed volatility values

3. **TradingClientError in Order Execution**
   - **Location**: `execution/alpaca_client.py`
   - **Cause**: API limits, market hours, insufficient funds, position validation
   - **Solution**: Check account status, market hours, and position limits
   - **Fallback**: Order validation prevents invalid orders

4. **MarketDataError in Price Fetching**
   - **Location**: `core/data/data_provider.py`
   - **Cause**: API connectivity, rate limits, symbol unavailability
   - **Solution**: Check API credentials and rate limit status
   - **Fallback**: Historical price fallback and multiple data sources

### Error Handling Flow for AI Agents

When encountering errors in the codebase:

1. **Check Error Category**: Look for error types (CRITICAL, TRADING, DATA, STRATEGY)
2. **Review Context**: Error handler provides component and operation context
3. **Apply Suggested Actions**: Each error includes specific remediation steps
4. **Use Conservative Fallbacks**: System designed with safe defaults
5. **Monitor Email Alerts**: Detailed reports sent automatically

### Key Files for Error Investigation

- `SILENT_FAILURES_FIXED.md`: Documents all silent failure fixes applied
- `ERROR_HANDLING_IMPLEMENTATION.md`: Detailed error handling architecture
- `core/error_handler.py`: Central error handling and categorization
- `core/exceptions.py`: Custom exception definitions with context

### Testing Error Handling

```python
# Test strategy error handling
from the_alchemiser.core.trading.strategy_engine import NuclearStrategyEngine
engine = NuclearStrategyEngine()

try:
    engine._get_14_day_volatility('INVALID_SYMBOL', {})
except IndicatorCalculationError as e:
    print(f"SUCCESS: Proper exception: {e}")
```

## Key Files Reference for AI Agents

### Core Trading Logic

- **`main.py`**: Entry point for strategy execution with comprehensive error handling
- **`lambda_handler.py`**: AWS Lambda wrapper with enhanced error reporting
- **`cli.py`**: Command-line interface for local testing and debugging

### Configuration and Settings

- **`core/config.py`**: Pydantic-based settings with environment variable support
- **`core/exceptions.py`**: Custom exception hierarchy for proper error categorization
- **`core/error_handler.py`**: Centralized error handling and email notification system

### Strategy Implementation

- **`core/trading/strategy_manager.py`**: Multi-strategy coordination and allocation
- **`core/trading/strategy_engine.py`**: Nuclear strategy with bear/bull market detection
- **`core/trading/tecl_strategy_engine.py`**: TECL technology strategy with volatility protection

### Order Execution

- **`execution/trading_engine.py`**: Main trading orchestration and portfolio management
- **`execution/smart_execution.py`**: Professional order execution with Better Orders methodology
- **`execution/alpaca_client.py`**: Direct Alpaca API client with validation and fallbacks
- **`execution/portfolio_rebalancer.py`**: Sell-then-buy rebalancing with attribution tracking

### Data and Market Access

- **`core/data/data_provider.py`**: Unified Alpaca REST/WebSocket data access with caching
- **`utils/price_fetching_utils.py`**: Price retrieval with multiple fallback strategies
- **`utils/market_timing_utils.py`**: Market hours detection and execution timing

### Monitoring and Tracking

- **`tracking/strategy_order_tracker.py`**: Per-strategy order and P&L attribution
- **`utils/portfolio_pnl_utils.py`**: Portfolio performance calculation utilities
- **`core/ui/email/`**: Email templates and notification system

### Development and Documentation

- **`pyproject.toml`**: Poetry dependencies, mypy, and ruff configuration (Ruff replaces Black)
- **`template.yaml`**: AWS CloudFormation infrastructure with retry policies
- **`Makefile`**: Development workflow automation (format, lint, test)

### Important Constants and Enums

- **`StrategyType`**: Enum for strategy identification (NUCLEAR, TECL)
- **`OrderSide`**: Buy/sell order direction
- **`ErrorCategory`**: Error classification for proper handling

### Environment Variables Required

```bash
# Alpaca API (separate keys for paper/live)
ALPACA_API_KEY=your_api_key
ALPACA_SECRET_KEY=your_secret_key
PAPER_TRADING=true  # false for live trading

# Email notifications
EMAIL_RECIPIENT=your_email@domain.com
AWS_ACCESS_KEY_ID=your_aws_key
AWS_SECRET_ACCESS_KEY=your_aws_secret

# Optional configurations
IGNORE_MARKET_HOURS=false
VALIDATE_BUYING_POWER=true
```

### Critical Dependencies to Monitor

- **`alpaca-py`**: Primary trading API client
- **`pydantic`**: Configuration and data validation
- **`rich`**: Terminal formatting and progress display
- **`boto3`**: AWS services (S3, SQS, SES)
- **`pandas`**: Data analysis and technical indicators

---

This README is for personal reference and intentionally omits marketing material.
