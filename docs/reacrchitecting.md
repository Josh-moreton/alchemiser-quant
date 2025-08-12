# reacrchitecting

### Proposed high‑level directory structure

```
the_alchemiser/
│
├── domain/            # Pure trading domain logic
│   ├── models/        # account.py, order.py, position.py, strategy.py …
│   ├── strategies/    # trading strategies and signals (currently core/trading)
│   └── math/          # math_utils.py, trading_math.py, pure computation
│
├── services/          # Application services exposing APIs to the domain
│   ├── account_service.py   # unify core/services and execution/account_service.py
│   ├── price_service.py     # unify price_service and price_fetching_utils.py
│   ├── cache_manager.py, streaming_service.py, trading_client_service.py …
│   └── error_handling.py    # unify error_handler and service error utilities
│
├── infrastructure/    # External integrations and low‑level concerns
│   ├── config/        # config.py, config_service.py, config_utils.py
│   ├── data_providers/      # unified_data_provider_facade.py, data_provider.py
│   ├── logging/       # logging_utils.py (with S3 moved here)
│   ├── secrets/       # secrets_manager.py, secrets_service.py
│   ├── websocket/     # websocket_connection_manager.py, websocket_order_monitor.py
│   └── s3/            # s3_utils.py
│
├── application/       # Orchestration and use‑cases (formerly execution/)
│   ├── portfolio_rebalancer/  # break portfolio_rebalancer.py into smaller modules
│   ├── trading_engine.py, execution_manager.py, smart_execution.py
│   ├── reporting.py, order_validation.py
│   └── tracking/      # strategy_order_tracker.py, integration.py
│
├── interface/         # Presentation layer / CLI / UI
│   ├── cli/           # cli.py, cli_formatter.py, core/ui email client
│   └── email/         # email templates, client.py, config.py
│
├── utils/             # Truly generic helpers
│   ├── math.py        # pure maths, random utilities
│   ├── config.py      # small helpers not tied to business logic
│   └── tests/         # any shared test utilities (if added)
│
└── main.py, lambda_handler.py, etc.   # entry points
```

### Steps to perform the move and fix imports

1. **Consolidate duplicate services:** Decide which implementation of `account_service`, `price_service` and other helpers to keep.  Merge the logic from `execution/account_service.py` into `core/services/account_service.py` and place the result in `services/account_service.py`.  Do similar consolidation for error handling and price fetching.

2. **Create new packages:**  Add `domain`, `services`, `infrastructure`, `application`, `interface`, and `utils` directories under `the_alchemiser` and add `__init__.py` files to each.  Move files as outlined above.  For example, move `core/models/*` into `domain/models/`, `core/trading/nuclear_signals.py` into `domain/strategies/nuclear_signals.py`, `execution/portfolio_rebalancer.py` into `application/portfolio_rebalancer/` (and break it into smaller modules for strategy attribution, liquidation and order batching), and move `core/logging/logging_utils.py` and `core/utils/s3_utils.py` into `infrastructure/logging/`.

3. **Relocate business logic out of utils:**  Move domain‑specific functions such as `position_manager.py`, `order_validation_utils.py` and `smart_pricing_handler.py` into the appropriate domain or service modules.  Keep only pure helpers (e.g. `math_utils.py`) in `utils`.

4. **Finalise data‑provider migration:**  Keep only the new `unified_data_provider_facade.py` and remove or archive the legacy `unified_data_provider_v2.py`.  Put the unified provider under `infrastructure/data_providers/`.

5. **Update import paths:**  Once files are moved, replace imports throughout the codebase.  For example:

   ```python
   # Old
   from the_alchemiser.core.services.account_service import AccountService
   # New
   from the_alchemiser.services.account_service import AccountService
   ```

   Use a search‑and‑replace tool or `sed` to update imports.  Within packages use relative imports (`from .models import Account`) where appropriate to simplify paths.

6. **Add explicit public interfaces:**  Create `__init__.py` files that re‑export commonly used classes (e.g. `services/__init__.py` could import and expose `AccountService`), so external code only imports from the package root.

7. **Run your tests or CLI:**  After the move, run `poetry install` then execute your CLI commands in a virtual environment.  Fix any import errors by adjusting paths or adding missing `__init__.py` files.

8. **Plan for further refactoring:**  Once the code compiles after the move, you can focus on **separating concerns**, improving single‑responsibility and deduplicating logic, as suggested in the architectural review.

By following this plan, you will convert the current sprawling structure into a layered architecture that clearly separates domain, services, infrastructure and interface code.  This will eliminate duplication, make imports predictable and enable you to iterate on separation of concerns and testing more easily.