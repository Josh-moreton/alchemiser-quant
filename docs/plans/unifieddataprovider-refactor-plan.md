# Refactoring Plan for `UnifiedDataProvider`

This plan describes the steps required to decompose the monolithic
`UnifiedDataProvider` into a set of well scoped services that are
easier to test, extend and maintain.  Each phase lists concrete actions
and expected deliverables so that the work can be executed
incrementally.

## Goals
- decouple configuration, secrets management, market data, trading and
  real‑time streaming concerns
- provide typed domain models instead of loose `dict`/`DataFrame`
  structures
- introduce a reusable caching layer and modernised price fetching flow
- centralise error handling and logging
- add comprehensive unit and integration tests
- document migration for downstream users

## Phase 0 – Preparation
**Actions**
- Audit current usages of `UnifiedDataProvider` across the codebase
  (search for imports and call sites).
- Create baseline tests that capture existing behaviour.
- Decide on dependency injection library (plain constructors, `attrs`,
  or similar).
**Deliverables**
- Inventory document of call sites.
- Baseline test suite proving current behaviour.

## Phase 1 – Service modularisation
**Actions**
- Extract the following classes/modules:
  - `ConfigService` for loading configuration.
  - `SecretsService` for credential retrieval.
  - `MarketDataClient` for market‑data REST calls.
  - `TradingClient` for order placement and account data.
  - `StreamingService` for real‑time price subscriptions.
- Wire the new services into a thin `UnifiedDataProvider` façade that
  composes them through dependency injection.
**Deliverables**
- New service modules with constructor injection.
- Updated provider façade delegating to the new services.
- Unit tests with mocked clients for each service.

## Phase 2 – Typed domain models
**Actions**
- Introduce `dataclasses` or Pydantic models for bars, quotes,
  positions, accounts and portfolio history.
- Replace existing uses of `dict`/`pd.DataFrame` with the new models.
- Provide conversion helpers to and from Pandas where necessary.
**Deliverables**
- `models` package containing typed representations.
- Refactored service methods returning these models.
- Tests validating model serialisation/deserialisation.

## Phase 3 – Caching layer
**Actions**
- Implement `CacheManager` using `cachetools.TTLCache` with configurable
  time‑to‑live per data type.
- Replace ad‑hoc dictionaries in `get_data` with the cache manager.
- Expose cache configuration through `ConfigService`.
**Deliverables**
- Reusable cache component and tests for expiry behaviour.
- Services updated to use the cache manager.
- Documentation on tuning cache parameters.

## Phase 4 – Modern price fetching
**Actions**
- Move subscription and reconnection logic into `StreamingService`.
- Provide async or callback‑based API for current price requests.
- Implement graceful REST fallback when streaming is unavailable.
**Deliverables**
- Non‑blocking price retrieval interface.
- Integration tests covering streaming and REST fallback paths.

## Phase 5 – Separate trading and account operations
**Actions**
- Implement `AccountService` for account information, positions and
  portfolio history.
- Limit `MarketDataClient` to data‑retrieval responsibilities only.
- Update call sites to use `AccountService` where appropriate.
**Deliverables**
- Dedicated account service with tests.
- Updated modules free from unnecessary market data dependencies.

## Phase 6 – Centralised error handling and logging
**Actions**
- Implement `log_and_raise` decorator/context manager wrapping service
  methods.
- Define custom exception hierarchy (`DataProviderError`,
  `StreamingError`, `TradingError`).
- Replace scattered try/except blocks with decorator usage.
**Deliverables**
- Consistent logging format and exception types across services.
- Tests ensuring exceptions are logged and propagated correctly.

## Phase 7 – Testing and continuous integration
**Actions**
- Write unit tests for each service using mocked Alpaca responses.
- Add integration tests that exercise caching, streaming fallback and
  trading operations together.
- Update CI configuration to run the new tests.
**Deliverables**
- Minimum 80% coverage for service modules.
- Passing CI pipeline demonstrating new test suite.

## Phase 8 – Migration and roll‑out
**Actions**
- Update modules importing `UnifiedDataProvider` to depend on specific
  services.
- Maintain a backwards‑compatible façade that internally delegates to
  new services for one release cycle.
- Document migration steps for downstream consumers.
**Deliverables**
- Updated call sites throughout the repository.
- Deprecation notice and migration guide in `docs/`.
- Removal of façade after deprecation period.

## Final deliverables checklist
- [ ] Service modules with dependency injection
- [ ] Typed domain models
- [ ] CacheManager with configuration hooks
- [ ] Streaming price service with REST fallback
- [ ] AccountService separated from market data
- [ ] Centralised error handling utilities
- [ ] Comprehensive unit & integration tests with CI
- [ ] Migration guide and updated documentation

## Testing
No tests have been run for this plan; it is a design document only.

## Notes
This plan assumes further investigation of real‑time components
(`RealTimePricingManager`) and utilities (`price_fetching_utils`) for
consistent interfaces and naming conventions.
