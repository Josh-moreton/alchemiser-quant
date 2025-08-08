# Alpaca Integration Architecture Refactor Plan

Status: DRAFT (Day 1 Consolidation Plan)
Owner: (assign after review)
Target Start: ASAP
Target Completion (Phase 1–3 baseline): <set date>

---
## 1. Why This Refactor Exists
We currently have multiple overlapping, partially implemented or duplicated layers touching the Alpaca APIs:

| Concern | Duplicate / Fragmented Components |
|---------|------------------------------------|
| Account & Positions | `execution/account_service.py`, `core/services/account_service.py`, logic in data providers, `trading_client_service.py` |
| Market Data (historical) | `core/services/market_data_client.py`, legacy `core/data/data_provider.py`, new `core/data/unified_data_provider_v2.py` |
| Real-time Pricing | `core/data/real_time_pricing.py`, `core/services/streaming_service.py`, `price_service.py` wrappers |
| Unified Facade | Legacy `UnifiedDataProvider` (two variants), `UnifiedDataProviderFacade` |
| Order / Trading Ops | `execution/alpaca_client.py`, `trading_client_service.py`, pieces inside other helpers |
| Price Retrieval Fallback Chains | Spread across `streaming_service`, `price_service`, `real_time_pricing`, utils |
| Data Modeling | Mixture of raw dicts, `TypedDict`, dataclasses, Pydantic (`ValidatedOrder`), partial conversions |

This creates:
- Drift in method semantics (same name, different return shapes)
- Hidden coupling and exponential test surface
- Difficulty introducing validation / caching / observability
- Risk of inconsistent business decisions (e.g., different cost basis calculations)

---
## 2. Target Architecture (Ports & Adapters / Hexagonal)
We apply a layered model:
```
          +---------------------------+
          |    Orchestration / Facade |  (UnifiedTradingContext)
          +-------------+-------------+
                        |
        +---------------+-----------------+
        | Domain Services (pure logic)    |
        | - AccountDomainService          |
        | - PortfolioAnalyticsService     |
        | - OrderExecutionService         |
        | - PriceDiscoveryService         |
        +----------------+----------------+
                         |
            +------------+-------------+
            |  Adapters / Infra Ports  |
            |  - TradingPort           |
            |  - MarketDataPort        |
            |  - StreamingPricePort    |
            |  - AccountHistoryPort    |
            +------------+-------------+
                         |
                +--------+--------+
                |  Alpaca SDK(s)  |
                +-----------------+
```

### 2.1 Port Interfaces (Python Protocols)
Each *port* defines the boundary (Stable API surface). Implementation(s) wrap Alpaca clients.

| Port | Responsibilities | Key Methods (illustrative) |
|------|------------------|----------------------------|
| `TradingPort` | Orders, account, positions | `get_account()`, `list_positions()`, `submit_order()`, `cancel_orders()`, `close_position()` |
| `MarketDataPort` | Historical bars & quotes | `get_bars(symbol, start, end, timeframe)`, `get_latest_quote(symbol)` |
| `StreamingPricePort` | Live subscription & price snapshots | `subscribe(symbol)`, `unsubscribe(symbol)`, `get_price(symbol)` |
| `AccountHistoryPort` | Portfolio history & activities | `get_portfolio_history(params)`, `list_activities(filters)` |

> One concrete adapter can implement multiple ports if the underlying SDK client supports them.

### 2.2 Facade / Context
`UnifiedTradingContext` (replaces all `UnifiedDataProvider*`, price fallback utilities) consolidates service wiring & provides a high-level ergonomics API (thin delegation):
- `.account.get_account_model()`
- `.account.get_positions_map()`
- `.prices.get_current(symbol)`
- `.execution.place_order(validated_order)`
- `.analytics.positions_summary()`

No heavy logic—central DI & lifecycle (start/stop streaming, caching policies, environment selection).

---
## 3. Data Modeling Strategy

| Layer | Representation | Rationale |
|-------|----------------|-----------|
| External boundary I/O | `TypedDict` schemas (e.g. `AccountInfo`, `PositionInfo`, `PortfolioHistoryData`, `QuoteData`, `PriceData`, `OrderDetails`) | Clear JSON-like shapes, static key checking, serialization friendliness |
| Domain objects | Pydantic models (immutable) (`AccountModel`, `PositionModel`, `PortfolioHistoryModel`, `OrderModel` or reuse `ValidatedOrder`, `BarModel`, `QuoteModel`, `PriceDataModel`) | Runtime validation + transformation (string -> float, ISO date parsing) |
| Aggregations / Reports | `TypedDict` or lightweight Pydantic (if computed invariants) (`PositionsSummary`, `ExecutionSummary`) | Choose Pydantic if derived metrics require validation |
| Execution validation | `ValidatedOrder` (already Pydantic) | Keep single source for order shape & constraints |

Rules:
1. ASAP convert raw SDK objects -> `TypedDict` boundary forms.
2. Domain services only ingest Pydantic models.
3. Presenters / CLI / API serialisation use `TypedDict` conversions.
4. Eliminate duplicated dataclasses (we already flagged migrations with TODOs).

---
## 4. Module Reorganization Plan

| Current Artifact | Action | Target Module / Replacement |
|------------------|--------|-----------------------------|
| `core/data/data_provider.py` | DEPRECATE & DELETE after migration | Superseded by ports/adapters |
| `core/data/unified_data_provider_v2.py` | DO NOT EXTEND | Fold concepts into `facade/unified_context.py` |
| `core/data/unified_data_provider_facade.py` | Replace | Rename & shrink into `facade/unified_trading_context.py` |
| `execution/account_service.py` | Remove (duplicate) | Merge logic into `core/services/account_domain_service.py` |
| `core/services/account_service.py` | Rename & refactor | `account_domain_service.py` (domain only) |
| `core/services/market_data_client.py` | Split responsibilities | Adapter: `adapters/alpaca_market_data_adapter.py` (implements `MarketDataPort`) |
| `core/services/streaming_service.py` | Rename / narrow | Adapter: `adapters/alpaca_streaming_adapter.py` (implements `StreamingPricePort`) |
| `core/data/real_time_pricing.py` | Inline / Refactor | Logic merged into streaming adapter + dedicated Pydantic quote models |
| `core/services/price_service.py` | Merge logic | Into `price_discovery_service.py` (domain) |
| `core/services/trading_client_service.py` | Rename | `adapters/alpaca_trading_adapter.py` implementing `TradingPort` & parts of `AccountHistoryPort` |
| `execution/alpaca_client.py` | Extract order logic | Move order placement + smart pricing into `execution/order_execution_service.py` (domain) using `TradingPort` + `PriceDiscoveryService` |
| Utils related to pricing / subscriptions | Absorb or delete | Replace with cohesive service methods |

Create new package structure:
```
core/
  ports/
    trading_port.py
    market_data_port.py
    streaming_port.py
    account_history_port.py
  adapters/
    alpaca_trading_adapter.py
    alpaca_market_data_adapter.py
    alpaca_streaming_adapter.py
    alpaca_account_history_adapter.py (or combined)
  models/
    (pydantic domain models, replacing dataclasses)
  converters/
    account_converters.py
    position_converters.py
    market_data_converters.py
  services/
    account_domain_service.py
    portfolio_analytics_service.py
    price_discovery_service.py
    order_execution_service.py
    risk_management_service.py (future)
  facade/
    unified_trading_context.py
execution/
  (retain order_validation, orchestrators)
```

---
## 5. Domain Service Responsibilities

| Service | Responsibilities | Dependencies |
|---------|------------------|--------------|
| `AccountDomainService` | Fetch + convert account & positions; caching basic; mapping to models | `TradingPort` |
| `PortfolioAnalyticsService` | Derived metrics: concentration, PnL summaries, risk ratios | Account service + price service |
| `PriceDiscoveryService` | Single authoritative method to get price (strategy: RT -> cached -> quote mid -> fallback REST) | `StreamingPricePort`, `MarketDataPort` |
| `OrderExecutionService` | Place validated orders, smart limit pricing, cancellation, liquidation | `TradingPort`, `PriceDiscoveryService` |
| `RiskManagementService` (future) | Pre-trade checks (exposure, leverage, per-symbol cap) | Account service, price service |
| `UnifiedTradingContext` | Wire dependencies; orchestrate lifecycles; provide simplified outward API | All above |

---
## 6. Pricing Strategy Normalization
Current inconsistency: multiple functions choose price differently.

Standard algorithm (inside `PriceDiscoveryService.get_current_price(symbol)`):
1. If streaming connected & fresh quote (< N seconds): use last trade or mid (configurable) with spread sanity check.
2. Else attempt recent cached bar/quote (cache TTL configurable).
3. Else fetch latest quote via MarketDataPort.
4. Else return None (call-site decides fallback logic).

Add method: `get_limit_price(symbol, side, aggressiveness)` returns price using spread-based interpolation.

---
## 7. Error Handling & Observability

| Aspect | Strategy |
|--------|----------|
| Exception Taxonomy | Keep existing custom exceptions (`MarketDataError`, `TradingClientError`, etc.). Ports raise them; domain services translate if needed. |
| Unified Error Wrapper | Decorator similar to existing `handle_service_errors`, applied consistently at facade boundary only. |
| Structured Logging | Add context dict: `{"component": "price_discovery", "symbol": symbol, "phase": "fetch_quote"}` |
| Metrics (future) | Hooks for timing (histogram) + success/failure counters (Prometheus/OpenTelemetry ready). |
| Retry Policy | Idempotent reads (quotes, bars) get exponential backoff; writes (orders) NO automatic retry except safe-cancel-resubmit with idempotency key (future). |

---
## 8. Caching Strategy
| Data | TTL | Store | Invalidation |
|------|-----|-------|--------------|
| Latest quote / price | 2–5s | In-memory dict (thread-safe) | Time-based only |
| Positions snapshot | 5–15s (configurable) | LRU / simple timestamp cache | Explicit invalidate after order fill events |
| Account info | 5–15s | Same as above | Invalidate on order completion or balance-affecting events |
| Portfolio history | On-demand (no aggressive caching) | Optional | N/A |
| Historical bars | 1h+ | LRU keyed by (symbol,timeframe,window) | Evict by capacity |

---
## 9. Migration Phases & Deliverables

### Phase 0 (Prep) - DONE / PARTIAL
- Inventory & classification (this document)
- Add TODO markers (already started)

### Phase 1 – Introduce Ports & Adapters (No Behavior Change)
- Create `ports/*.py` with Protocols
- Implement `alpaca_trading_adapter` wrapping `AlpacaTradingClient`
- Implement `alpaca_market_data_adapter` wrapping historical + quote methods
- Implement `alpaca_streaming_adapter` merging `real_time_pricing` + `streaming_service`
- Write unit tests for adapters using fakes

Acceptance: Existing high-level calls can be re-routed via adapters with feature parity.

### Phase 2 – Pydantic Domain Models & Converters
- Implement Pydantic versions of all core models (replace dataclasses gradually)
- Add converter functions (TypedDict <-> Model)
- Update `ValidatedOrder` integration to unify with `OrderModel` (decide single representation; deprecate duplicate naming)
- Adjust tests / mypy config

Acceptance: Domain services use only Pydantic models internally.

### Phase 3 – Domain Services Assembly
- Implement `AccountDomainService`, `PriceDiscoveryService`, `OrderExecutionService`, `PortfolioAnalyticsService`
- Add caching policy abstractions
- Introduce unified error/log decorators

Acceptance: Services tested independently; old services still intact for fallback.

### Phase 4 – UnifiedTradingContext Facade
- Implement unified context & dependency injection
- Replace usages of legacy `UnifiedDataProvider*` across codebase
- Provide deprecation warnings & mapping table

Acceptance: All production code uses new facade; legacy classes unused.

### Phase 5 – Decommission Legacy
- Delete: old unified_data_provider variants, duplicate account service, stale pricing utils
- Remove TODO comments referencing migration
- Update README + architecture docs

Acceptance: Dead code ratio reduced; coverage intact or improved.

### Phase 6 – Enhancements (Optional / Future)
- Async streaming integration with backpressure
- Metrics + health endpoint
- Risk service integration
- Order idempotency keys & partial fill reconciler

---
## 10. Naming & API Normalization
| Old | New Canonical |
|-----|---------------|
| `get_current_price_for_order` | `get_price_for_order(symbol)` (returns price + context object) |
| `get_current_price_rest` | (Remove – handled inside price strategy) |
| `UnifiedDataProvider` | `UnifiedTradingContext` |
| `AccountService` (duplicate) | `AccountDomainService` |
| `trading_client_service` | `AlpacaTradingAdapter` |
| `market_data_client` | `AlpacaMarketDataAdapter` |
| `streaming_service` + `real_time_pricing` | `AlpacaStreamingAdapter` |
| `alpaca_client` | `OrderExecutionService` |

---
## 11. Risk & Mitigation
| Risk | Mitigation |
|------|------------|
| Hidden runtime dependencies rely on legacy class attributes | Introduce facade shim with deprecation warnings + grep audit |
| Behavior drift in price selection | Codify deterministic pricing policy test suite |
| Order execution regression | Golden path integration test before & after migration |
| Overlapping refactors cause merge conflicts | Land Phase 1 quickly; small PRs per layer |
| Test flakiness (streaming) | Abstract streaming behind in-memory fake for tests |

---
## 12. Test Plan Overview
| Category | Tests |
|----------|-------|
| Adapters | Mock Alpaca responses, error mapping |
| Converters | Round-trip TypedDict <-> Model fidelity |
| Services | Price fallback ordering, caching TTL expiry, analytics metrics correctness |
| Execution | Order validation + submission path, settlement tracking interplay |
| Facade | End-to-end smoke: fetch account, place mock order, get price |
| Regression | Snapshot diff of positions summary pre/post migration |

---
## 13. Incremental Implementation Order (Concrete Task List)
1. Create `ports/` with Protocols + test stubs
2. Implement trading & market data adapters (basic methods only) + tests
3. Implement streaming adapter merging real-time pricing logic
4. Add Pydantic models & converters (account, position, bar, quote, price)
5. Build `AccountDomainService` + caching + tests
6. Build `PriceDiscoveryService` (include fallback logic) + tests
7. Build `OrderExecutionService` (reuse `ValidatedOrder`) + tests
8. Build unified facade `UnifiedTradingContext`
9. Migrate references (automated search & replace with review)
10. Delete legacy artifacts & update docs

---
## 14. Open Design Decisions (To Resolve Early)
| Topic | Options | Default Proposed |
|-------|---------|------------------|
| Order model duplication | Keep only `ValidatedOrder` or wrap? | Keep `ValidatedOrder`, add `to_domain()` alias for clarity |
| Streaming freshness threshold | 1s / 2s / 5s | 2 seconds |
| Quote mid calculation | (bid+ask)/2 raw vs filtered | Raw average, add safeguard if spread > X% of mid |
| Converters location | Per model vs consolidated module | Consolidated `converters/` for discoverability |
| Caching lib | DIY dict + timestamps vs functools.lru_cache vs cachetools | Simple dict + monotonic timestamps (explicit policy) |
| Async adoption | Immediate vs deferred | Defer full async; design interfaces future-safe |

---
## 15. Acceptance Criteria (Phase 1–4 Minimum)
- Single public import path: `from the_alchemiser.core.facade import UnifiedTradingContext`
- No production references to: `unified_data_provider_v2`, legacy `execution/account_service.py`
- All account/position/price retrieval passes through ports + domain services
- 90%+ of duplication (method or logic) in attached legacy files removed
- Test suite green; new tests cover ≥80% of new modules

---
## 16. Immediate Next Actions (Today)
1. Approve this plan / edit open decisions.
2. Scaffold `ports/*` + baseline adapters with pass-through logic.
3. Introduce Pydantic `AccountModel`, `PositionModel` (if not already started) under new `core/models/` path.
4. Add converter functions & unit tests.

Once confirmed, I can begin Phase 1 implementation.

---
*End of Document*
