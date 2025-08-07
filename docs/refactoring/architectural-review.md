# Architectural Review for alchemiser-quant

1. Project Architecture
Configuration & centralised settings
The Settings model aggregates logging, Alpaca API, execution, and other config concerns in one file, but the module is lengthy and mixes domain defaults with environment loading logic.

Service and execution layers
Two separate account service implementations exist: a Pydantic‑model–based service in core/services and a composition‑based version in execution, leading to ambiguity about which layer should own account functionality.

Utility vs domain code
Business logic such as position validation lives in utils/position_manager.py, blurring boundaries between helper code and core trading logic.

Large multi‑responsibility modules
portfolio_rebalancer.py interleaves strategy attribution, order placement, liquidation, and tracking in a single class, making it difficult to reason about or reuse.

2. Code Duplication & Helper Logic
Account services
core/services/account_service.py and execution/account_service.py both wrap position/account retrieval, causing duplication and inconsistent APIs. These should be consolidated into a single reusable service.

Error handling
A comprehensive error handler with retry logic sits under core/error_handler.py, while core/services/error_handling.py defines separate logging/decorator utilities. Maintaining two parallel approaches increases maintenance overhead.

Price fetching
Real‑time and REST price helpers appear both in a dedicated service (core/services/price_service.py) and in standalone utilities (utils/price_fetching_utils.py).

Mathematical helpers
utils/trading_math.py offers pure functions for position sizing and limit pricing, yet the same calculations appear embedded in other modules such as portfolio_rebalancer.py. These should remain in a shared math/portfolio module to avoid drift.

3. Overall Structure Sensibility
Directory layout
The root the_alchemiser package has core, execution, tracking, and utils folders. Both core/utils and top-level utils exist, leading to confusion about where helpers belong.

Service and data provider evolution
core/data includes both a monolithic UnifiedDataProvider and a newer UnifiedDataProviderFacade, suggesting an unfinished migration to the service-based architecture.

Infrastructure leakage
Logging utilities pull in S3 concerns directly, coupling storage with logging configuration and making local vs cloud deployment harder to separate.

4. Suggestions for Improvement
Clarify package boundaries

Merge core/services and execution helpers into a single services/ package and move business logic out of utils/.

Use subpackages such as infrastructure/ (logging, S3, config), domain/ (strategies, models), execution/ (trading engine, rebalancing), and shared/utils/ (pure helpers like math).

Consolidate duplicated services

Create one AccountService used by both execution and reporting layers.

Deduplicate error-handling and price-fetching logic into single modules or classes.

Split monolithic modules

Break portfolio_rebalancer.py into smaller components (e.g., strategy attribution, liquidation, order batching).

Consider separating pure computation (calculate_rebalance_amounts, math helpers) into dedicated modules.

Complete data-provider migration

Finalize transition to the facade/service architecture and remove legacy providers to reduce confusion.

5. Bonus: Best Practices
Typing & docstrings
Many modules provide rich type hints (e.g., config), yet others rely on Any or omit docstrings, reducing clarity and IDE support.

Single Responsibility & DRY
Mixing IO, computation, and orchestration in single classes violates SRP and repeats logic already available in helpers (e.g., position checks in both PortfolioRebalancer and PositionManager).

Explicitness and interface design
Protocols are used in places, but the presence of multiple ad‑hoc utility modules makes it hard to understand the primary interface for trading operations. Clearly defined service interfaces would improve maintainability.

By consolidating duplicated modules, clarifying package boundaries, and adopting a more modular service-oriented architecture, the project can become easier to navigate, test, and evolve.