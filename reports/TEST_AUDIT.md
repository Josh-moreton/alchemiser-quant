# Test Suite Audit

## Executive Summary
- Existing suite covers only a thin slice of the codebase (14% line coverage). Core trading and strategy logic is largely untested.
- Tests are focused on feature-flag transitions for trading services; mocking is manual and duplicated.
- No mutation testing or network isolation existed; added network guard and fixtures for flag control.

## Coverage & Mutation Metrics

### Table 1: Coverage by Package
| Package | Line % | Branch % |
|---------|--------|----------|
| application.mapping | 80.6 | 57.1 |
| application.execution | 8.9 | 6.2 |
| services.trading | 20.4 | 8.4 |
| interface.cli | 17.9 | 10.2 |
| utils | 82.1 | 50.0 |

### Table 2: Mutation Score (planned)
| Package | Mutation % |
|---------|------------|
| the_alchemiser (utils, mapping subset) | *n/a* - import errors prevented run |

### Table 3: Top Risk Areas
| Module | Reason |
|--------|-------|
| `application.execution.smart_execution` | 0% coverage yet orchestrates order placement |
| `services.trading.trading_service_manager` | 44% coverage but central to money movement |
| `services.account.account_service` | 8% coverage handling account state |
| `services.errors.*` | <20% coverage; error paths unverified |
| `application.orders.*` | 0% coverage - order validation logic |
| `domain.strategies.*` | <20% coverage, core strategy engines |
| `infrastructure.s3.s3_utils` | 26% coverage; external side effects |
| `interface.cli.cli_formatter` | 16% coverage; presentation logic prone to regressions |
| `utils.num` | 45% coverage; numeric comparisons underpin pricing |
| `services.market_data.*` | ≤14% coverage; boundary with data providers |

## Prioritised Fix Plan
- **P1**
  - Add unit tests for `smart_execution`, `order_validation`, and `trading_service_manager` edge cases.
  - Cover error-handling modules to ensure resilience paths.
  - Stabilise mutation infrastructure and achieve ≥60% on utils & mapping.
- **P2**
  - Expand integration tests across strategy↔portfolio↔broker boundaries.
  - Property-based tests for pricing and signal transforms.
  - Introduce contract tests for Alpaca and S3 stubs.
- **P3**
  - Regression tests for CLI formatting and reporting.
  - Broader strategy engine simulations and performance tests.

## Kill List (low value tests)
- `tests/unit/interface/cli/test_cli_enriched_orders_rendering.py` – checks static rendering only.

## Add List (high value tests)
| Title | Intent | Module | AAA Sketch |
|-------|--------|--------|-----------|
| "smart execution respects price bands" | Ensure orders honour spread limits | `application.execution.smart_execution` | Arrange engine with mock prices → Act execute → Assert price constraint |
| "order validation rejects negative qty" | Guard against invalid orders | `application.orders.order_validation` | Build invalid order → validate → assert error |
| "strategy engine handles empty signals" | Robustness | `domain.strategies.strategy_engine` | Provide empty data → run → assert no trade |
